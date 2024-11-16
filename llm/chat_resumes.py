from llm.vector_store import VectorStoreManager
from schemas.request import ResumeRecommendRequest
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from schemas.response import ResumeFilter
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from schemas.enums import JobCategory, YearsOfExperience, ProgrammingLanguage

load_dotenv()

question_llm = ChatOpenAI(
    temperature=0.1,
    model="gpt-4o-mini",
)


question_llm_with_schema = question_llm.with_structured_output(ResumeFilter)

vector_store = VectorStoreManager(persist_directory="chroma_wang")


def chat_resumes_retrieval(req: ResumeRecommendRequest):
    filter = question_llm_with_schema.invoke(req.message)
    filter_metadata = {
        key: value
        for key, value in {
            "applicant_name": (
                f"{getattr(filter, 'applicant_name', None)}"
                if getattr(filter, "applicant_name", None) is not None
                else None
            ),
            "job_category": (
                f"{getattr(filter, 'job_category', None)}"
                if (getattr(filter, "job_category", None) is not None)
                or (
                    getattr(filter, "job_category", None)
                    in [job.value for job in JobCategory]
                )
                else None
            ),
            "years": (
                f"{getattr(filter, 'years', None)}"
                if (getattr(filter, "years", None) is not None)
                or (
                    getattr(filter, "years", None)
                    in [experience.value for experience in YearsOfExperience]
                )
                else None
            ),
            "language": (
                f"{getattr(filter, 'language', None)}"
                if (getattr(filter, "language", None) is not None)
                or (
                    getattr(filter, "language", None)
                    in [language.value for language in ProgrammingLanguage]
                )
                else None
            ),
        }.items()
        if value is not None
    }
    return [
        doc.metadata
        for doc in vector_store.search_resumes(
            req.message,
            k=5,
            filter_metadata=filter_metadata,
        )
    ]
