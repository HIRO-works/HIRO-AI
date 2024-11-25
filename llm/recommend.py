from llm.vector_store import VectorStoreManager
from schemas.request import ResumeRecommendRequest
from schemas.response import ResumeFilter

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import Optional, Dict, Any
from schemas.enums import QuestionType, JobCategory, YearsOfExperience, ProgrammingLanguage


from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from schemas.enums import JobCategory, YearsOfExperience, ProgrammingLanguage

load_dotenv()

question_llm = ChatOpenAI(
    temperature=0.1,
    model="gpt-4o-mini",
)


question_llm_with_schema = question_llm.with_structured_output(ResumeFilter)

vector_store = VectorStoreManager(persist_directory="db")


# def filter_matching_resumes(req: ResumeRecommendRequest):
    # filter = question_llm_with_schema.invoke(req.message)
    # filter_metadata = {
    #     key: value
    #     for key, value in {
    #         "applicant_name": (
    #             f"{getattr(filter, 'applicant_name', None)}"
    #             if getattr(filter, "applicant_name", None) is not None
    #             else None
    #         ),
    #         "job_category": (
    #             f"{getattr(filter, 'job_category', None)}"
    #             if (getattr(filter, "job_category", None) is not None)
    #             or (
    #                 getattr(filter, "job_category", None)
    #                 in [job.value for job in JobCategory]
    #             )
    #             else None
    #         ),
    #         "years": (
    #             f"{getattr(filter, 'years', None)}"
    #             if (getattr(filter, "years", None) is not None)
    #             or (
    #                 getattr(filter, "years", None)
    #                 in [experience.value for experience in YearsOfExperience]
    #             )
    #             else None
    #         ),
    #         "language": (
    #             f"{getattr(filter, 'language', None)}"
    #             if (getattr(filter, "language", None) is not None)
    #             or (
    #                 getattr(filter, "language", None)
    #                 in [language.value for language in ProgrammingLanguage]
    #             )
    #             else None
    #         ),
    #     }.items()
    #     if value is not None
    # }
    # return [
    #     doc.metadata
    #     for doc in vector_store.search_resumes(
    #         req.message,
    #         k=5,
    #         filter_metadata=filter_metadata,
    #     )
    # ]



class QueryInfoExtractor:
    def __init__(self, llm):
        self.llm = llm
        self.prompt = PromptTemplate(
            input_variables=["message"],
            template="""
            다음 메시지에서 이력서 관련 정보를 추출해주세요:
            {message}
            
            다음 형식으로 정확히 답변해주세요:
            job_category: (BACKEND/FRONTEND/FULLSTACK/MOBILE/DATA/AI/DEVOPS 중 하나 또는 NONE)
            years: (JUNIOR/MIDDLE/SENIOR 중 하나 또는 NONE)
            language: (PYTHON/JAVA/JAVASCRIPT/KOTLIN/SWIFT/GO 중 하나 또는 NONE)
            """
        )
        self.chain = self.llm.bind(
            prompt=self.prompt,
        ).with_structured_output(ResumeFilter)

    def extract(self, message: str) -> Dict[str, Optional[str]]:
        try:
            # LLM으로부터 응답 받기
            response = self.chain.run(message=message)
            
            # 응답 파싱
            result = {}
            for line in response.strip().split('\n'):
                key, value = line.split(': ')
                value = value.strip()
                
                # Enum 매핑
                if key == 'job_category':
                    result[key] = getattr(JobCategory, value) if value != 'NONE' else None
                elif key == 'years':
                    result[key] = getattr(YearsOfExperience, value) if value != 'NONE' else None
                elif key == 'language':
                    result[key] = getattr(ProgrammingLanguage, value) if value != 'NONE' else None
                    
            return result
            
        except Exception as e:
            # 에러 발생시 모든 필드에 None 반환
            return {
                'job_category': None,
                'years': None,
                'language': None
            }

def select_fit_resumes(req: ResumeRecommendRequest, 
                       query_info_extractor: QueryInfoExtractor, 
                       vector_store: VectorStoreManager):
    filter_metadata = query_info_extractor.extract(req.message)
    # req.message를 기반으로 적합한 이력서  0     
    return [doc.metadata for doc in vector_store.search_resumes(req.message, k=5, filter_metadata=filter_metadata)]
