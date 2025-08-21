from regex_based_doc_parsing.data_parser.parsers.court_parser import CourtParser
from regex_based_doc_parsing.data_parser.parsers.paper_parser import PaperParser
from regex_based_doc_parsing.data_parser.parsers.prec_parser import PrecParser

def get_parser(data: dict) -> BaseParser:
    if "PrecService" in data:
        return PrecParser()
    elif "sections" in data:
        return PaperParser()
    elif "info" in data and "body" in data:
        return PaperParser()
    else:
        return CourtParser()
