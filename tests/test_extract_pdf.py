from preprocess.load_pdf import PDFLoader
from preprocess.parse_pdf import PyPDFParser
from llm.extract import ContentExtractor, section_chain, split_chain, summarize_chain

'''
텍스트 추출 방법 3가지 테스트
1. 문단별 추출(split_text)
2. llm 요약 추출
3. 섹션별 추출
'''

def test_extract_summary():
    summary_extractor = ContentExtractor(summarize_chain)
    split_extractor = ContentExtractor(split_chain)
    section_extractor = ContentExtractor(section_chain)
    # 테스트 데이터 로드
    pdf_data = PDFLoader('local').load_pdf('test.pdf')
    documents = PyPDFParser().parse_pdf(pdf_data)

    summary_contents = summary_extractor.extract_content(documents)
    split_contents = split_extractor.extract_content(documents)
    section_contents = section_extractor.extract_content(documents)

    assert isinstance(summary_contents, str)
    assert isinstance(split_contents, str)
    assert isinstance(section_contents, str)

