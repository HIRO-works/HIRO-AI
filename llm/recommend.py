from llm.vector_store import VectorStoreManager
from schemas.request import ResumeRecommendRequest
from schemas.response import ResumeFilter

from langchain.prompts import PromptTemplate
from langchain.chains.openai_functions import create_structured_output_chain  # 변경된 import 경로
from typing import Optional, Dict, Any, List
from schemas.enums import QuestionType, JobCategory, YearsOfExperience, ProgrammingLanguage

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from llm.result_filter import ResultFilter, NoFilter, RerankFilter, SearchResult
load_dotenv()



class QueryInfoExtractor:
    def __init__(self, llm, result_filter: ResultFilter = NoFilter()):
        # 새로운 방식으로 구현
        parser = PydanticOutputParser(pydantic_object=ResumeFilter)
        
        prompt = PromptTemplate(
            template="Query: {query}\n{format_instructions}\n",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        self.chain = prompt | llm | parser
        self.result_filter = result_filter

    def select_fit_resumes(self, query: str, vector_store: VectorStoreManager) -> List[dict]:
        response = self.chain.invoke({"query": query})
        filter_metadata = self.extract(query)
        
        # 2. 초기 검색 (더 많은 후보)
        initial_results = vector_store.search_resumes(
            query, 
            k=20,  # reranking을 위해 더 많은 후보 검색
            filter_metadata=filter_metadata
        )
        
        # 3. SearchResult 객체로 변환
        search_results = [
            SearchResult(
                metadata=doc.metadata,
                content=doc.page_content
            )
            for doc in initial_results
        ]
        
        # 4. Reranking 수행
        reranked_results = self.result_filter.filter(search_results)
        
        # 5. 메타데이터만 반환
        return [result.metadata for result in reranked_results]
    

    def extract(self, message: str) -> Dict[str, Optional[str]]:
        try:
            # LLM으로부터 응답 받기
            response = self.chain.invoke(message)
            
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
