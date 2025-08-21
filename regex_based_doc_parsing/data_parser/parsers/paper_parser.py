# BOAZ_Data_preprocess_logics\regex_based_doc_parsing\data_parser\parsers\paper_parser.py

from typing import Dict, List
from regex_based_doc_parsing.data_parser.parsers.base import BaseParser  # 추상 클래스
import pdfplumber
import collections
import re
import json
from typing import Dict
from regex_based_doc_parsing.data_parser.utils_.text_utils import split_sentences  # 공통 유틸
from pykospacing import Spacing #띄어쓰기 라이브러리
import hanja # 한자 to 한글 변환 라이브러리

def get_filtered_text(pdf_path: str) -> Dict[str, Dict[str, str]]:
    spacing = Spacing()
    with pdfplumber.open(pdf_path) as pdf:
        all_chars = []

        for page_num, page in enumerate(pdf.pages, start=1):
            
            # print(f"\n=== Page {page_num}===")
            # print(page.chars[:200])
            all_chars.extend(page.chars)

        # 전체 페이지에서 폰트 크기 분석
        font_sizes = collections.Counter(char['size'] for char in all_chars)

        # 본문: 가장 많이 등장한 글꼴 크기
        main_body_size = font_sizes.most_common(1)[0][0]
        # 제목: 가장 큰 글꼴 크기
        max_font_size = max(font_sizes)

        title_chars = [char['text'] for char in all_chars if char['size'] == max_font_size]
        body_chars = [char['text'] for char in all_chars if main_body_size - 1 <= char['size'] < max_font_size]
        # 제목과 본문 텍스트 결합
        title_text = ''.join(title_chars).strip()
        body_text = ''.join(body_chars)

        # 한자 → 한글 변환
        title_text = hanja.translate(title_text, 'substitution')
        body_text = hanja.translate(body_text, 'substitution')

        # 본문에서 쓸모없는 개행 및 번호 제거
        body_text = re.sub(r'(?<=[\s\S])\n\d*(?=[\s\S])', '', body_text)

        title_text = spacing(title_text)
        body_text = spacing(body_text)
        #print(body_text)

        return {
            "info": {
                "title": title_text
            },
            "body": {
                "body": body_text
            }
        }



def is_reference_line(text):
    keywords = [
        "references", "참고문헌", "bibliography", "reference", "literature cited",
        "<참고문헌>", "≪参考文献≫", "< 참고문헌 >", "[참고문헌]", "[ 참고문헌 ]"
    ]
    return text.strip().lower() in [k.lower() for k in keywords]


class PaperParser(BaseParser):
    def __init__(self):
        # 필요한 경우 다른 옵션이나 tokenizer도 인자로 받을 수 있음
        self.section_field_map = {
            "info": ["title"],
            "body": ["body"],
        }



    def extract_and_split(self, data: Dict) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        stop_processing = False 

        for section, fields in self.section_field_map.items():
            nested = data.get(section, {})
            for field in fields:
                value = nested.get(field)

                if isinstance(value, str):
                    for sent in split_sentences(value):
                        if is_reference_line(sent):
                            stop_processing = True
                            break
                        if not stop_processing:
                            out.append({
                            "section": section,
                            "field": field,
                            "sentence": sent
                        })
            if stop_processing:
                break  # body 안에서 참조문헌 발견 시 전체 종료

        return out

# if __name__ == "__main__":
#     sample_pdf = r"C:\Users\megan\onestone\BOAZ_Data_preprocess_logics\regex_based_doc_parsing\data_\raw_data\민사\set1\민사2.pdf"

#     # 1. PDF에서 텍스트 추출
#     parsed_data = get_filtered_text(sample_pdf)

#     # info, body 형식 JSON 예쁘게 출력
#     print("=== Extracted raw data (info, body) ===")
#     print(json.dumps(parsed_data, ensure_ascii=False, indent=2))

#     # 2. JSON 파일로 저장 (get_filtered_text 결과)
#     output_path = r"C:\Users\megan\onestone\BOAZ_Data_preprocess_logics\regex_based_doc_parsing\data_\testoutput.json"
#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump(parsed_data, f, ensure_ascii=False, indent=2)

#     print(f"저장 완료: {output_path}")

