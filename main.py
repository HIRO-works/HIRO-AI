from fastapi import FastAPI, APIRouter, BackgroundTasks, HTTPException, Depends
from uuid import UUID
from langchain_openai import OpenAIEmbeddings
from llm.model import llm
from llm.vector_store import VectorStoreManager
from llm.generate_question import generate_question
from llm.extract import ContentExtractor, section_chain, split_chain, summarize_chain
from llm.recommend import QueryInfoExtractor

from containers import Container
from dependency_injector.wiring import inject, Provide

from preprocess.load_pdf import PDFLoader
from preprocess.parse_pdf import PyPDFParser

from schemas.request import ResumeRecommendRequest, ResumeExtractRequest
from schemas.response import RecommendedResumeResponse, ResumeInfoResponse, InterviewQuestionResponse

from dotenv import load_dotenv
import os

container = Container()
container.config.chain_type.override("section")

load_dotenv()

app = FastAPI()
app.llm = llm
app.pdf_loader = PDFLoader(storage_type="local")
app.pdf_parser = PyPDFParser()
app.content_extractor = ContentExtractor(section_chain)
app.query_info_extractor = QueryInfoExtractor(llm=app.llm)

app.embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
app.vector_store = VectorStoreManager(embeddings=app.embeddings, persist_directory="db")


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
@inject
def recommend_resumes(req: ResumeRecommendRequest, 
                      container: Container = Depends(Provide(Container))
                      ) -> list[RecommendedResumeResponse]:
    return container.query_info_extractor.select_fit_resumes(req.message, container.vector_store_manager)



@ai_router.post(
    "/resumes/{resume_id}/generate-questions",
    summary="이력서를 기반으로 질문 생성",
    description="이력서를 기반으로 질문 생성",
    response_description="질문은 직군별 질문, 컬쳐핏 질문, 경험 질문, 프로젝트 질문으로 나눌 수 있음.",
)
@inject
def generate_questions(resume_id: str,
                       container: Container = Depends(Provide(Container))
                       ) -> list[InterviewQuestionResponse]:

    resume_info = container.vector_store_manager.get_resume_info(resume_id) 
    questions = generate_question(''.join(resume_info['documents']))

    return questions



@ai_router.post(
    "/process-resume",
    summary="전달받은 이력서를 전처리(PDF->텍스트)하고, 필요한 정보 추출 및 벡터DB에 저장",
    description="엠베딩 벡터 DB저장은 백그라운드로 실행",
    response_description="",
)
@inject
def process_resume(req: ResumeExtractRequest,  background_tasks: BackgroundTasks,
                   container: Container = Depends(Provide(Container))
                   ) -> ResumeInfoResponse:
    
    try:
        pdf_data = app.pdf_loader.load_pdf(req.file_path)
        parsed_documents = app.pdf_parser.parse_pdf(pdf_data)
        content = app.content_extractor.extract_content(parsed_documents['documents'])
        
        response = ResumeInfoResponse(
            resume_id=req.resume_id,
            applicant_name=content['resume_info'].applicant_name,
            job_category=content['resume_info'].job_category,
            years=content['resume_info'].years,
            language=content['resume_info'].language,
        )
        
        background_tasks.add_task(
            container.vector_store_manager.add_resume_async, 
            content['summary'],
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
