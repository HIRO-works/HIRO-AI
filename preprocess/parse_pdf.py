from abc import ABC, abstractmethod

from langchain.schema import Document
import os
import requests
from io import BytesIO
from dotenv import load_dotenv
from PyPDF2 import PdfReader
load_dotenv()


class BasePDFParser(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    def parse_pdf(self, file_path: str):
        pass


class PyPDFParser(BasePDFParser):    
    '''
    기본 PDF 파서
    '''
    def __init__(self):
        self.pdf_reader = PdfReader
        
    def parse_pdf(self, pdf_object: BytesIO)->list[Document]:
        documents = []
        
        for page in self.pdf_reader(pdf_object).pages:
            documents.append(Document(page_content=page.extract_text()))
        return documents

    


class UpstagePDFParser(BasePDFParser):
    '''
    Upstage Document Parse API 사용
    Text 외에 메타정보(텍스트 위치, 테이블 정보, 텍스트 유형(header, body, footer))를 추출
    '''
    def _call_document_parse(self, pdf_object: BytesIO):
   
        response = requests.post(
            "https://api.upstage.ai/v1/document-ai/document-parse",
            headers={"Authorization": f"Bearer {os.getenv('UPSTAGE_API_KEY')}"},
            data={"base64_encoding": "['figure']"}, # base64 encoding for cropped image of the figure category.
            files={"document": pdf_object})
    
        # Save response
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Unexpected status code {response.status_code}.")

    def parse_pdf(self, pdf_object: BytesIO):
        return self._call_document_parse(pdf_object)

