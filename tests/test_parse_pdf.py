from preprocess.parse_pdf import PyPDFParser
from PyPDF2 import PdfReader


def test_parse_pdf():
    '''
    텍스트와 함께 텍스트의 위치에 대한 정보를 함께 얻는다.
    '''    
    pdf_parser = PyPDFParser()
    parsed_info = pdf_parser.parse_pdf('test.pdf')


    assert isinstance(parsed_info, list)
    assert isinstance(parsed_info[0]['text'], str)
    assert isinstance(parsed_info[0]['metadata'], dict)


