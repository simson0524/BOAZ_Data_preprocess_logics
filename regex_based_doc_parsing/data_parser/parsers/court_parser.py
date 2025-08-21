# BOAZ_Data_preprocess_logics\regex_based_doc_parsing\data_parser\parsers\court_parser.py

from typing import Dict, List
from regex_based_doc_parsing.data_parser.parsers.base import BaseParser
from regex_based_doc_parsing.data_parser.utils_.text_utils import split_sentences
from pykospacing import Spacing

class CourtParser(BaseParser):
    def __init__(self):
        self.spacer = Spacing()  # spacing 객체를 한 번만 생성
        
    def extract_and_split(self, data: Dict) -> List[Dict[str, str]]:
        section_field_map = {
            "info": ["caseField", "detailField", "caseNm", "courtNm", "caseNo", "relateLaword", "qotatPrcdnt"],
            "concerned": ["acusr", "dedat"],
            "org": ["orgJdgmnCourtNm", "orgJdgmnAdjuDe", "orgJdgmnCaseNo"],
            "disposal": ["disposalform", "disposalcontent"],
            "mentionedItems": ["rqestObjet"],
            "assrs": ["acusrAssrs", "dedatAssrs"],
            "facts": ["bsisFacts"],
            "dcss": ["courtDcss"],
            "close": ["cnclsns"],
        }

        out = []
        for section, fields in section_field_map.items():
            sec_data = data.get(section, {})
            for field in fields:
                raw = sec_data.get(field, [])
                items = [raw] if isinstance(raw, str) else raw if isinstance(raw, list) else []
                for txt in items:
                    if not txt or not isinstance(txt, str):
                        continue
                    for sent in split_sentences(txt):
                        sent = self.spacer(sent)
                        out.append({"section": section, "field": field, "sentence": sent})
        return out
