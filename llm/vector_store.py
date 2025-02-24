from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os
from typing import List, Dict
from uuid import UUID
from schemas.enums import JobCategory, YearsOfExperience, ProgrammingLanguage


class VectorStoreManager:
    def __init__(self, 
                 embeddings, 
                 persist_directory: str = "db/chroma.sqlite3"):
        load_dotenv()

        self.embeddings = embeddings
        self.persist_directory = persist_directory
        self.vector_store = self._load_or_create_vector_store()

    def _load_or_create_vector_store(self) -> Chroma:
        try:
            return Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
            )
        except Exception as e:
            print(f"Creating new vector store: {str(e)}")
            return Chroma(
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory,
            )

    def create_resume_document(
        self,
        content: str,
        resume_id: UUID,
        applicant_name: str,
        job_category: JobCategory,
        years: YearsOfExperience,
        language: ProgrammingLanguage,
        additional_metadata: Dict = None,
    ) -> Document:
        """이력서 Document 객체 생성"""
        metadata = {
            "resume_id": resume_id,
            "applicant_name": applicant_name,
            "job_category": job_category.value,
            "years": years.value,
            "language": language.value,
        }

        # 추가 메타데이터가 있다면 병합
        if additional_metadata:
            metadata.update(additional_metadata)

        return Document(page_content=content, metadata=metadata)

    def add_resume(
        self,
        content: str,
        resume_id: UUID,
        applicant_name: str,
        job_category: JobCategory,
        years: YearsOfExperience,
        language: ProgrammingLanguage,
        additional_metadata: Dict = None,
    ):
        """단일 이력서 추가"""
        doc = self.create_resume_document(
            content=content,
            resume_id=resume_id,
            applicant_name=applicant_name,
            job_category=job_category,
            years=years,
            language=language,
            additional_metadata=additional_metadata,
        )

        self.vector_store.add_documents([doc])
        self.vector_store.persist()

    async def add_resume_async(
        self,
        content: str,
        resume_id: UUID,
        applicant_name: str,
        job_category: JobCategory,
        years: YearsOfExperience,
        language: ProgrammingLanguage,
        additional_metadata: Dict = None,
    ):
        """단일 이력서 추가"""
        doc = self.create_resume_document(
            content=content,
            resume_id=resume_id,
            applicant_name=applicant_name,
            job_category=job_category,
            years=years,
            language=language,
            additional_metadata=additional_metadata,
        )

        self.vector_store.add_documents([doc])
        self.vector_store.persist()

        
    def add_resumes(self, resumes: List[Dict]):
        """여러 이력서 일괄 추가"""
        docs = []
        for resume in resumes:
            doc = self.create_resume_document(
                content=resume["content"],
                resume_id=resume["resume_id"],
                applicant_name=resume["applicant_name"],
                job_category=JobCategory(resume["job_category"]),
                years=YearsOfExperience(resume["years"]),
                language=ProgrammingLanguage(resume["language"]),
                additional_metadata=resume.get("additional_metadata"),
            )
            docs.append(doc)

        self.vector_store.add_documents(docs)
        self.vector_store.persist()

    def search_resumes(
        self, query: str, k: int = 5, filter_metadata: Dict = None
    ) -> List[Document]:
        if filter_metadata:
            # 여러 조건을 $and로 결합
            where_clause = (
                {"$and": [{key: value} for key, value in filter_metadata.items()]}
                if len(filter_metadata.items()) > 1
                else filter_metadata
            )
        else:
            where_clause = None

        return self.vector_store.similarity_search(
            query=query, k=k, filter=where_clause
        )

    def get_resume_info(self, resume_id: int) -> Document:
        return self.vector_store.get(where={"resume_id": resume_id})


# 사용 예시
if __name__ == "__main__":
    # 벡터 스토어 매니저 초기화
    vector_store = VectorStoreManager(persist_directory="db")

    # 테스트 문서 추가
    # 단일 이력서 추가
    vector_store.add_resume(
        content="""
        이력서 내용
        - Python 백엔드 개발 3년 경력
        - AWS 클라우드 환경에서의 개발 경험
        - FastAPI, Django 프레임워크 사용 경험
        """,
        resume_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        applicant_name="홍길동",
        job_category=JobCategory.BACKEND,
        years=YearsOfExperience.JUNIOR,
        language=ProgrammingLanguage.PYTHON,
    )

    # 여러 이력서 일괄 추가
    resumes = [
        {
            "content": "프론트엔드 개발자 이력서...",
            "resume_id": UUID("223e4567-e89b-12d3-a456-426614174000"),
            "applicant_name": "김철수",
            "job_category": "frontend",
            "years": "3-7",
            "language": "javascript",
        },
        {
            "content": "AI 엔지니어 이력서...",
            "resume_id": UUID("323e4567-e89b-12d3-a456-426614174000"),
            "applicant_name": "이영희",
            "job_category": "ai",
            "years": "0-3",
            "language": "python",
        },
    ]

    vector_store.add_resumes(resumes)

    # 검색 예시
    results = vector_store.search_resumes(
        query="Python 백엔드 개발자",
        k=2,
        filter_metadata={"job_category": "backend", "language": "python"},
    )

    # 결과 출력
    for doc in results:
        print("\n=== 검색 결과 ===")
        print(f"이름: {doc.metadata['applicant_name']}")
        print(f"직무: {doc.metadata['job_category']}")
        print(f"경력: {doc.metadata['years']}")
        print(f"언어: {doc.metadata['language']}")
        print(f"내용: {doc.page_content}")
