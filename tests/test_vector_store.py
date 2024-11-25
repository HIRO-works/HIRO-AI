from llm.vector_store import VectorStoreManager
import pytest

from schemas.enums import JobCategory, YearsOfExperience



def test_vector_store_embedding():
    vector_store_manager = VectorStoreManager()
    vector_store_manager.create_resume_document(
        content="""
        이력서 내용
        - Python 백엔드 개발 3년 경력
        - AWS 클라우드 환경에서의 개발 경험
        - FastAPI, Django 프레임워크 사용 경험
        """,
        resume_id='123e4567-e89b-12d3-a456-426614174000',
        applicant_name='김시험',
        job_category=JobCategory.BACKEND,
        years=YearsOfExperience.JUNIOR
    )

    
