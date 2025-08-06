# BOAZ_Data_preprocess_logics\regex_based_doc_parsing\data_parser\parsers\paper_parser.py

from typing import Dict, List
from parsers.base import BaseParser  # 추상 클래스
from utils.text_utils import split_sentences  # 공통 유틸


class PaperParser(BaseParser):
    def __init__(self):
        # 필요한 경우 다른 옵션이나 tokenizer도 인자로 받을 수 있음
        self.section_field_map = {
            "info": ["title"],
            "body": ["body"],
        }

    def extract_and_split(self, data: Dict) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []

        for section, fields in self.section_field_map.items():
            nested = data.get(section, {})
            for field in fields:
                value = nested.get(field)

                if isinstance(value, str):
                    for sent in split_sentences(value):
                        out.append({
                            "section": section,
                            "field": field,
                            "sentence": sent
                        })

        return out
