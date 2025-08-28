from regex_based_doc_parsing.data_parser.parsers.court_parser import CourtParser
from regex_based_doc_parsing.data_parser.parsers.paper_parser import PaperParser
from regex_based_doc_parsing.data_parser.parsers.prec_parser import PrecParser
from regex_based_doc_parsing.data_parser.parsers.openai_parser import OpenAIParser
from regex_based_doc_parsing.data_parser.parsers.base import BaseParser

def get_parser(data: dict, source_folder: str = "") -> BaseParser:
    """
    JSON 데이터와 source_folder 경로를 기준으로 적절한 Parser 반환
    """
    # openai 폴더 전용
    if "openai" in source_folder.lower():
        return OpenAIParser()
    # 기존 조건 유지
    elif "PrecService" in data:
        return PrecParser()
    elif "sections" in data:
        return PaperParser()
    elif "info" in data and "body" in data:
        return PaperParser()
    else:
        return CourtParser()
