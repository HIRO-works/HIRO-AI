import enum
import os
from io import BytesIO

from PyPDF2 import PdfReader
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document
import boto3


class StorageType(enum.Enum):
    LOCAL = "local"
    S3 = "s3"


class PDFLoader:
    def __init__(self, storage_type: StorageType):
        self.s3_client = boto3.client('s3',
                                      aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                      aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                                      region_name=os.getenv('AWS_REGION'))
        
        self.bucket_name = os.getenv('AWS_S3_BUCKET')
        self.storage_type = storage_type
        self.handler = {'local': self._load_local_pdf, 
                        's3': self._load_s3_pdf}

    def load_pdf(self, file_path: str) -> BytesIO:
        """로컬 PDF 파일 로드"""
        return self.handler[self.storage_type](file_path)
    
    def _load_local_pdf(self, file_path: str) -> BytesIO:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        file_stream = open(file_path, 'rb')
        return file_stream
        

    def _load_s3_pdf(self, file_path: str) -> BytesIO:
        if not hasattr(self, 's3_client'):
            raise ValueError("AWS credentials not provided")
        
        
        response = self.s3_client.get_object(
            Bucket=self.bucket_name,
            Key=file_path
        )
        
        pdf_stream = BytesIO(response['Body'].read())
    
        
        return pdf_stream