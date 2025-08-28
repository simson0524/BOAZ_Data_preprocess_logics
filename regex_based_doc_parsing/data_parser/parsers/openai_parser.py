from typing import Dict, List, Any, Union
from regex_based_doc_parsing.data_parser.parsers.base import BaseParser
from regex_based_doc_parsing.data_parser.utils_.text_utils import split_sentences
import re

class OpenAIParser(BaseParser):
    """
    Spacing 없이 JSON의 모든 텍스트 필드를 문장 단위로 분리
    """

    def extract_and_split(self, data: Union[Dict[str, Any], List[Any]]) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []

        def recurse(field_path: str, value: Any):
            if isinstance(value, dict):
                for k, v in value.items():
                    recurse(f"{field_path}.{k}" if field_path else k, v)
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    recurse(f"{field_path}[{idx}]", item)
            elif isinstance(value, str):
                if not value.strip():
                    return
                value_clean = value.replace("<br/>", " ")
                for sent in split_sentences(value_clean):
                    # 공백 정리
                    sent = re.sub(r"[\r\n\u2028\u2029\u000b\u000c]+", " ", sent).strip()
                    sent = re.sub(r"\s{2,}", " ", sent)
                    out.append({
                        "field": field_path,
                        "sentence": sent
                    })
            else:
                # 숫자, 불리언 등은 문자열로 변환 후 처리 가능
                pass

        recurse("", data)
        return out
