from fastapi import FastAPI, APIRouter, BackgroundTasks, HTTPException
from langchain_openai import ChatOpenAI
from uuid import UUID
from llm.model import llm
from llm.vector_store import VectorStoreManager
from llm.generate_question import generate_question
from llm.extract import pdf_to_documents
from llm.recommend import QueryInfoExtractor, select_fit_resumes
from preprocess import PDFLoader

from schemas.request import ResumeRecommendRequest, ResumeExtractRequest
from schemas.response import RecommendedResumeResponse, ResumeInfoResponse, InterviewQuestionResponse

from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.llm = llm
app.pdf_loader = PDFLoader(storage_type="local")
app.query_info_extractor = QueryInfoExtractor(llm=app.llm)
app.vector_store = VectorStoreManager(persist_directory="db")

ai_router = APIRouter(
    prefix="/api/ai",
    tags=["AI"],
    responses={404: {"description": "Not found"}, 422: {"description": "Unprocessable Entity"}},
)


@ai_router.post('/recommend',
                summary="질문을 기반으로 적합한 이력서 추천",
                description="채용담당관의 요구사항을 기반으로 적합한 이력서 추천",
                response_description="",
                )
def recommend_resumes(req: ResumeRecommendRequest) -> list[RecommendedResumeResponse]:
    return select_fit_resumes(req, app.query_info_extractor, app.vector_store)



@ai_router.post(
    "/resumes/{resume_id}/generate-questions",
    summary="이력서를 기반으로 질문 생성",
    description="이력서를 기반으로 질문 생성",
    response_description="질문은 직군별 질문, 컬쳐핏 질문, 경험 질문, 프로젝트 질문으로 나눌 수 있음.",
)
def generate_questions(resume_id: str) -> list[InterviewQuestionResponse]:

    resume_info = app.vector_store.get_resume_info(resume_id) 
    questions = generate_question(''.join(resume_info['documents']))

    return questions



@ai_router.post(
    "/process-resume",
    summary="전달받은 이력서를 전처리(PDF->텍스트)하고, 필요한 정보 추출 및 벡터DB에 저장",
    description="엠베딩 벡터 DB저장은 백그라운드로 실행",
    response_description="",
)
def process_resume(req: ResumeExtractRequest,  background_tasks: BackgroundTasks) -> ResumeInfoResponse:
    try:
        pdf_data = app.pdf_loader.load_pdf(req.file_path)
        analyzed_data = pdf_to_documents(pdf_data)
        
        response = ResumeInfoResponse(
            resume_id=req.resume_id,
            applicant_name=analyzed_data['resume_info'].applicant_name,
            job_category=analyzed_data['resume_info'].job_category,
            years=analyzed_data['resume_info'].years,
            language=analyzed_data['resume_info'].language,
        )
        
        background_tasks.add_task(
            app.vector_store.add_resume_async, 
            analyzed_data['summary'],
            req.resume_id, 
            response.applicant_name,
            response.job_category,
            response.years,
            response.language
        )

        return response
        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=422, detail="이력서 분석 중 오류가 발생했습니다")


@ai_router.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}


app.include_router(ai_router)


@ai_router.get("/llm")
def check_llm():
    response = app.llm.invoke("test")
    return {"message": response.content}



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
