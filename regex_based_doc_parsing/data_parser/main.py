from parsers.court_parser import CourtParser
from parsers.paper_parser import PaperParser
from parsers.prec_parser import PrecParser

def get_parser(data: dict) -> BaseParser:
    if "PrecService" in data:
        return PrecParser()
    elif "sections" in data:
        return PaperParser()
    elif "info" in data and "body" in data:
        return PaperParser()
    else:
        return CourtParser()
