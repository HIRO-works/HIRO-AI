from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnableParallel
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from llm.log_callback_handler import LogCallbackHandler
from langchain.prompts import ChatPromptTemplate
from preprocess.load_pdf import PDFLoader
from schemas.response import ResumeInfoResponse
from langchain.schema import Document

load_dotenv()


summarize_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "이력서 정보를 요약해주는 전문가야\n" "이력서의 요점을 요약해줘 \n",
        ),
        (
            "human",
            "Resume : \n{question}\n",
        ),
    ],
)

summarize_llm = ChatOpenAI(
    temperature=0.1,
    model="gpt-4o-mini",
    callbacks=[
        LogCallbackHandler("summarize resume"),
    ],
)

section_llm = ChatOpenAI(
    temperature=0.1,
    model="gpt-4o-mini",
    callbacks=[
        LogCallbackHandler("section resume"),
    ],
)

section_prompt = ChatPromptTemplate.from_messages([
    (
            "system",
            "너는 이력서 전문가야. 이력서에서 주요 정보를 이 항목에 따라 정보를 찾아줘\n",
        ),
    (
        "system",
        """항목:  
        인적사항: 이름, 성별, 생년월일, 주소, 연락처, 이메일
        학력: list[학교, 전공, 학점, 졸업일자]
        경력: list[회사명, 직무, 근무기간, 근무내용]
        자격증: list[자격증명, 취득일자, 취득기관]
        교육: list[교육기관, 교육내용, 교육기간]
        프로젝트: list[프로젝트명, 프로젝트 기간, 프로젝트 내용, 프로젝트 역할]
        자기소개서: 자기소개서 내용"""
    ),
    (
            "human",
            "Resume:\n{question}\n",
        ),
])

refine_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "이력서에서 주요 정보를 추출하여 다음 데이터 구조에 맞게 정보를 찾아줘\n",
        ),
        (
            "system",
            "Data Structure:\n"
            "\n### ResumeInfo\n"
            "- resume_id: INTEGER\n"
            "- applicant_name: TEXT\n"
            "- job_category: ENUM ('frontend', 'backend', 'ai', 'fullstack')\n"
            "- years: ENUM ('0-3', '3-7', '7-10')\n"
            "- language: ENUM ('python', 'java', 'javascript', 'typescript', 'kotlin', 'c++', 'c' 중 하나)\n",
        ),
        (
            "human",
            "Resume:\n{question}\n",
        ),
    ]
)

refine_llm = ChatOpenAI(
    temperature=0.1,
    model="gpt-4o-mini",
    callbacks=[
        LogCallbackHandler("refine json"),
    ],
)

refine_llm_with_schema = refine_llm.with_structured_output(ResumeInfoResponse)




def split_content(content: str)->list[str]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, 
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", "\n\n\n"]
        )
    return text_splitter.split_text(content)


section_chain = (
            RunnableParallel(
                question=(section_prompt | section_llm | (lambda x: x.content))
            )
            | RunnableParallel(
                resume_info=refine_prompt | refine_llm_with_schema,
                summary=lambda x: x["question"],
            )
        )

split_chain = (
            RunnableParallel(
                resume_info=refine_prompt | refine_llm_with_schema,
                summary=lambda x: split_content(x),  
            )
        )

summarize_chain = (
            RunnableParallel(
                question=(summarize_prompt | summarize_llm | (lambda x: x.content))
            )
            | RunnableParallel(
                resume_info=refine_prompt | refine_llm_with_schema,
                summary=lambda x: x["question"],
            )
        )

class ContentExtractor:
    def __init__(self, chain):
        self.chain = chain

    def extract_content(self, documents: list[Document]):
        resume = ''
        for doc in documents:
            resume += doc.page_content
        return self.chain.invoke(resume)


def pdf_to_documents(documents: list[Document]):

    resume = ""
    for doc in documents:
        resume += doc.page_content
    response = (
        RunnableParallel(
            question=(summarize_prompt | summarize_llm | (lambda x: x.content))
        )
        | RunnableParallel(
            resume_info=refine_prompt | refine_llm_with_schema,
            summary=lambda x: x["question"],
        )
    ).invoke(resume)
    return response


if __name__ == "__main__":

    file_path = "./pdf_data/backend_추만석.pdf"

    pdf_loader = PDFLoader(storage_type="local")
    pdf_data = pdf_loader.load_pdf(file_path)

    response = pdf_to_documents(pdf_data)
    json_response = {
        "resume_id": response["resume_info"].resume_id,
        "applicant_name": response["resume_info"].applicant_name,
        "job_category": response["resume_info"].job_category,
        "years": response["resume_info"].years,
        "language": response["resume_info"].language,
    }
    print(json_response)
