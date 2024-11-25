from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnableParallel
from dotenv import load_dotenv
from llm.log_callback_handler import LogCallbackHandler
from langchain.prompts import ChatPromptTemplate
from preprocess import PDFLoader
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
