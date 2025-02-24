import os
from datetime import datetime
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_core.runnables.history import RunnableWithMessageHistory
from llm.memory import get_session_history
from dotenv import load_dotenv

load_dotenv()
# 현재 날짜 가져오기
current_date = datetime.now()
# 원하는 형식으로 출력하기
formatted_date = current_date.strftime("%Y년 %m월 %d일")


prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f"""
            오늘 날짜 : {formatted_date}
            
            Context: {{context}}
            """,
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ],
)

llm = Ollama(
    model="mistral",  # 또는 "llama2", "codellama" 등
    base_url="http://ollama:11434",
    temperature=0.1,
)

chain_with_history = RunnableWithMessageHistory(
    prompt_template | llm,
    get_session_history,  # 세션 기록을 가져오는 함수
    input_messages_key="question",  # 사용자의 질문이 템플릿 변수에 들어갈 key
    history_messages_key="chat_history",  # 기록 메시지의 키
)
