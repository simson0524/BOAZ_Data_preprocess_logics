# BOAZ_Data_preprocess_logics\regex_based_doc_parsing\data_parser\parsers\prec_parser.py

from typing import Dict, List, Any
from regex_based_doc_parsing.data_parser.parsers.base import BaseParser
from regex_based_doc_parsing.data_parser.utils_.text_utils import split_sentences 
from pykospacing import Spacing

class PrecParser(BaseParser):
    def __init__(self):
        self.spacer = Spacing()
        
    def extract_and_split(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        prec = data.get("PrecService", {})

        section_field_map = {
            "판시사항": "판시사항",
            "참조판례": "참조판례",
            "판결요지": "판결요지",
            "참조조문": "참조조문",
            "판례내용": "판례내용",
        }

        for section, field in section_field_map.items():
            txt = prec.get(field, "")
            if not isinstance(txt, str) or not txt.strip():
                continue

            txt = txt.replace("<br/>", " ")

            for sent in split_sentences(txt):
                for txt in split_sentences(sent):
                    txt = self.spacer(txt)
                    out.append({
                        "section": section,
                        "field": field,
                        "sentence": txt
                    })

        return out
