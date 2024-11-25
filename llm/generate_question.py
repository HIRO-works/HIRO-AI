from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnableParallel, RunnablePassthrough

from dotenv import load_dotenv
from llm.log_callback_handler import LogCallbackHandler
from langchain.prompts import ChatPromptTemplate
from typing import List

from schemas.response import InterviewQuestionResponse

load_dotenv()

question_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "\n"
            "면접담당관이 전달하는 이력서를 확인하고 다음 주제로 질문을 작성해줘\n"
            "Subject: {subject}\n",
        ),
        (
            "human",
            "Resume : \n{question}\n",
        ),
    ],
)

question_llm = ChatOpenAI(
    temperature=0.9,
    model="gpt-4o-mini",
)


question_llm_with_schema = question_llm.with_structured_output(
    InterviewQuestionResponse
)


def generate_question(resume: str):
    response = RunnableParallel(
        job_specific=RunnablePassthrough.assign(subject=lambda _: "직군별 질문")
        | question_prompt
        | question_llm_with_schema,
        culture_fit=RunnablePassthrough.assign(subject=lambda _: "컬쳐핏 질문")
        | question_prompt
        | question_llm_with_schema,
        experience=RunnablePassthrough.assign(subject=lambda _: "경험 질문")
        | question_prompt
        | question_llm_with_schema,
        project=RunnablePassthrough.assign(subject=lambda _: "프로젝트 질문")
        | question_prompt
        | question_llm_with_schema,
    ).invoke({"question": resume})
    return response.values()


if __name__ == "__main__":
    questions = generate_question(
        """홍길동

        📍 서울특별시
        📧 honggildong@example.com
        📞 010-1234-5678

        지원목표 (Objective)

        백엔드 개발자로서 안정적이고 확장 가능한 시스템을 설계하고 구현하여 기업의 성공에 기여하고 싶습니다.

        경력사항 (Work Experience)

        백엔드 개발자
        ABC 테크놀로지, 서울특별시
        2020년 1월 – 현재

            •	Python과 Django를 활용한 웹 애플리케이션 백엔드 설계 및 개발.
            •	RESTful API 설계 및 개발을 통해 프론트엔드와의 효율적인 데이터 통신 지원.
            •	기존 데이터베이스 성능 최적화로 쿼리 속도 40% 개선.
            •	AWS 기반의 클라우드 서비스(EC2, S3, RDS) 구축 및 운영 경험.
                      """
    )
    print(questions)
