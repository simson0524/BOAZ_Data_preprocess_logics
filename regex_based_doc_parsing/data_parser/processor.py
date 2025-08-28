import json
import re
import time
from pathlib import Path
from typing import Dict, List, Type

# 개별 파서 클래스 import (당신이 정의한 파서들)
from regex_based_doc_parsing.data_parser.parsers.court_parser import CourtParser
from regex_based_doc_parsing.data_parser.parsers.paper_parser import PaperParser
from regex_based_doc_parsing.data_parser.parsers.prec_parser import PrecParser
from regex_based_doc_parsing.data_parser.parsers.paper_parser import get_filtered_text 
from regex_based_doc_parsing.data_parser.parsers.openai_parser import OpenAIParser

# 파서 타입 매핑
PARSER_REGISTRY: Dict[str, Type] = {
    "PrecService": PrecParser,
    "paper": PaperParser,
    "default": CourtParser,
    "OpenAI": OpenAIParser
}

# 파서 선택 로직
def select_parser(data: Dict, source_folder: str) -> Type:
    if "openai" in source_folder.lower():
        return PARSER_REGISTRY["OpenAI"]()

    elif "PrecService" in data:
        return PARSER_REGISTRY["PrecService"]()
    elif "info" in data and "body" in data:
        return PARSER_REGISTRY["paper"]()
    else:
        return PARSER_REGISTRY["default"]()

# --------------------------- 법률 데이터 처리 -------------------------------------------------
# 메인 처리 함수
# def process_all(root_folder: Path, output_folder: Path, num_files: int = None, prefix_code: str = "05") -> None:
#     start_time = time.time()
#     output_folder.mkdir(parents=True, exist_ok=True)

#     # 📂 중간 저장 폴더 (민사 JSON 저장용)
#     mid_json_folder = Path(r"C:\Users\megan\onestone\BOAZ_Data_preprocess_logics\regex_based_doc_parsing\data_\json_data\형사\set1")
#     mid_json_folder.mkdir(parents=True, exist_ok=True)

#     counter = 1  # ID 부여용
#     processed_files = 0  # ⬅️ 처리한 파일 수
    
#     for file in sorted(root_folder.glob("**/*"))[:num_files]:
#         if file.suffix == ".pdf":
#                 data = get_filtered_text(str(file))
#                  # 중간 JSON 저장
#                 mid_json_path = mid_json_folder / (file.stem + ".json")
#                 mid_json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
#                 print(f"💾 중간 JSON 저장 완료: {mid_json_path}")
#         elif file.suffix == ".json":
#                 data = json.loads(file.read_text(encoding="utf-8"))
#         else:
#             print(f"⚠️ Unsupported file skipped: {file.name}")
#             continue

#         parser = select_parser(data)
#         records = parser.extract_and_split(data)

#         for seq, rec in enumerate(records, start=1):
#             rec["id"] = f"sample_{prefix_code}_000_{counter:06d}"
#             rec["sequence"] = f"{seq:04d}"

#             # 🔹 문장 클린업
#             rec["sentence"] = re.sub(r"[\r\n\u2028\u2029\u000b\u000c]+", " ", rec["sentence"]).strip()
#             rec["sentence"] = re.sub(r"\s{2,}", " ", rec["sentence"])

#             counter += 1

#         # 저장
#         out_name = file.stem + ".json"
#         out_path = output_folder /out_name
#         print(f"저장 경로: {out_path}")  
#         out_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

#         processed_files += 1  # ⬅️ 파일 개수 카운트
#         print(f"✔ [{parser.__class__.__name__}] file.name: {len(records)} sentences (up to ID {counter-1})")

#     elapsed_time = time.time() - start_time
#     print(f"\n🎉 Done! Total sentences: {counter-1}")
#     print(f"📂 Total processed files: {processed_files}")
#     print(f"⏱ Total elapsed time: {elapsed_time:.2f} seconds")  # 소수점 2자리까지 표시

# if __name__ == "__main__":
#     from pathlib import Path

#     # 경로 설정 (윈도우 경로는 r"..." 또는 \\ 사용)python -m regex_based_doc_parsing.data_parser.processor

#     input_path = Path(r"C:\Users\megan\onestone\BOAZ_Data_preprocess_logics\regex_based_doc_parsing\data_\raw_data\형사\set1")
#     output_path = Path(r"C:\Users\megan\onestone\BOAZ_Data_preprocess_logics\regex_based_doc_parsing\data_\sentence_split_json\5.형사\set1")


#     # 실행
#     process_all(input_path, output_path, prefix_code="05")


# --------------------------- openai 데이터 처리-------------------------------------------------

# 메인 처리 함수
def process_all(root_folder: Path, output_folder: Path, prefix_code: str = "01") -> None:
    print(root_folder)
    print(root_folder.exists())
    print(root_folder.is_dir())
    print(f"Root folder exists: {root_folder.exists()}, is_dir: {root_folder.is_dir()}")
    print(f"Files found by rglob: {list(root_folder.rglob('*.json'))}")

    start_time = time.time()
    output_folder.mkdir(parents=True, exist_ok=True)

    counter = 1  # ID 부여용
    processed_files = 0
    
    for file in sorted(root_folder.rglob("*.json")):
        print("Detected file:", file)
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"❌ JSON 로드 실패: {file.name} -> {e}")
            continue
        parser = select_parser(data, str(file.parent))
        records = parser.extract_and_split(data)

        for seq, rec in enumerate(records, start=1):
            rec["id"] = f"sample_{prefix_code}_000_{counter:06d}"
            rec["sequence"] = f"{seq:04d}"

            # 문장 클린업
            rec["sentence"] = re.sub(r"[\r\n\u2028\u2029\u000b\u000c]+", " ", rec["sentence"]).strip()
            rec["sentence"] = re.sub(r"\s{2,}", " ", rec["sentence"])

            counter += 1

        # 저장
        out_name = file.stem + ".json"
        out_path = output_folder / out_name
        out_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"💾 저장 완료: {out_path} ({len(records)} sentences)")

        processed_files += 1

    elapsed_time = time.time() - start_time
    print(f"\n🎉 Done! Total sentences: {counter-1}")
    print(f"📂 Total processed files: {processed_files}")
    print(f"⏱ Total elapsed time: {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    from pathlib import Path
    input_path = Path(r"C:\Users\megan\onestone\BOAZ_Data_preprocess_logics\regex_based_doc_parsing\data_\raw_data\openai")
    output_path = Path(r"C:\Users\megan\onestone\BOAZ_Data_preprocess_logics\regex_based_doc_parsing\data_\sentence_split_json\openai")

    
    process_all(input_path, output_path, prefix_code="01")