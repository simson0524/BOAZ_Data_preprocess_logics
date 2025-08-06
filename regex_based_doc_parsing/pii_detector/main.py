# main.py
import json
from pathlib import Path
from typing import List, Dict
from detectors.name_detector import NameDetector
from detectors.address_detector import AddressDetector
from detectors.birth_age_detector import BirthAgeDetector
from detectors.email_detector import EmailDetector
from detectors.personal_id_detector import JuminDetector
from detectors.phone_num_detector import PhoneDetector
from Dict.address_dict import sido_list, sigungu_list, dong_list
from Dict.name_dict import sn1, nn1, nn2, name
from Dict.stopwords_dict import stopwords
import pandas as pd

# 사용할 디텍터 리스트 (필요에 따라 주석 해제 및 추가)
detectors = [
    NameDetector(sn1, nn1, nn2, name,stopwords=stopwords),
    AddressDetector(sido_list, sigungu_list, dong_list),
    BirthAgeDetector(),
    EmailDetector(),
    JuminDetector(),
    PhoneDetector()
    # 
    # ,
]

# detector_label_map.py
DETECTOR_TYPE_MAP = {
    "Name": {"개인/기밀": "개인", "식별/준식별": "식별"},
    "Address": {"개인/기밀": "개인", "식별/준식별": "준식별"},
    "BirthAge": {"개인/기밀": "개인", "식별/준식별": "식별"},
    "Email": {"개인/기밀": "개인", "식별/준식별": "식별"},
    "Jumin": {"개인/기밀": "개인", "식별/준식별": "식별"},
    "Phone": {"개인/기밀": "개인", "식별/준식별": "식별"},

    # 필요 시 디텍터 추가
}


def run_pii_detection(text: str) -> List[Dict]:
    """
    주어진 텍스트에서 모든 디텍터를 돌며 PII를 탐지하고 결과 리스트 반환
    """
    results = []

    for detector in detectors:
        matches = detector.detect(text) # detect 하는 부분
        for m in matches: 
            # detector.score()에 넘길 'match' 문자열이 없으면 추출해서 넣음
            if "match" not in m: # m안에 match 키가 없다면
                m["match"] = text[m["start"]:m["end"]]  # start부터 end까지 토큰을 match:토큰 형식으로 넣어라

            m["label"] = detector.__class__.__name__.replace("Detector", "") #detector 이름에서 detector만 빼면 AddressDetector -> Address
            m["score"] = detector.score(m["match"])
            results.append(m)

    return results


# ✅ 변환 함수: 원하는 JSON 포맷으로 가공
def convert_to_target_format(entry: Dict, results: List[Dict], filename: str, case_field: str, detail_field: str) -> Dict:
    sent_id = entry["id"]
    sentence = entry["sentence"]
    
    # sequence는 숫자로 변환
    sequence = entry.get("sequence")
    if isinstance(sequence, str) and sequence.isdigit():
        sequence = int(sequence)
    elif not isinstance(sequence, int):
        sequence = 0

    return {
        "data": [
            {
                "sentence": sentence,
                "id": sent_id,
                "filename": filename,
                "caseField": case_field,
                "detailField": detail_field,
                "sequence": sequence
            }
        ],
        "annotations": [
            {
                "id": sent_id,
                "annotations": [
                    {
                        "start": r["start"],
                        "end": r["end"],
                        "label": r["label"],
                        "score": r["score"]
                    } for r in results
                ]
            }
        ]
    }


# def process_sentence_split_json(input_folder: Path, output_folder: Path):
#     output_folder.mkdir(parents=True, exist_ok=True)
#     all_rows = [] 

#     for file_path in input_folder.glob("*.json"):
#         print(f"📄 처리 중: {file_path.name}")
#         try:
#             data = json.loads(file_path.read_text(encoding="utf-8"))
#             output_list = []

#             for entry in data: # [{entry1},{entry2} ]
#                 sentence = entry["sentence"] #entry에서 sentence 가져와서
#                 results = run_pii_detection(sentence) #detection 진행
#                 # ✅ CSV용 데이터 누적
#                 for r in results:
#                     label_type = r["label"]
#                     label_info = DETECTOR_TYPE_MAP.get(label_type, {"개인/기밀": "", "식별/준식별": ""})
#                     all_rows.append({
#                         "도메인": detail_field,
#                         "단어": r["match"],
#                         "개인/기밀": label_info["개인/기밀"],
#                         "식별/준식별": label_info["식별/준식별"],
#                         "정보 유형": r["label"],
#                         "점수": r.get("score", None),
#                         "저장 경로": str(file_path)
#                     })
#                 formatted = convert_to_target_format(
#                     entry,
#                     results,
#                     filename=str(file_path),
#                     case_field=case_field,
#                     detail_field=detail_field
#                 )
#                 output_list.append(formatted)

               

#             output_path = output_folder / file_path.name
#             output_path.write_text(json.dumps(output_list, ensure_ascii=False, indent=2), encoding="utf-8")
#             print(f"✔ 저장 완료: {file_path.name}")

#         except Exception as e:
#             print(f"❌ 에러 발생 - {file_path.name}: {e}")
    
#     # ✅ DataFrame 저장
#     df = pd.DataFrame(all_rows)
#     df.to_csv(df_save_path, index=False, encoding="utf-8-sig")
#     print(f"🧾 전체 CSV 저장 완료 → {df_save_path}")

def process_sentence_split_json(input_folder: Path, output_folder: Path):
    output_folder.mkdir(parents=True, exist_ok=True)
    all_rows = [] 

    for file_path in input_folder.glob("*.json"):
        print(f"📄 처리 중: {file_path.name}")
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            output_list = []

            for entry in data:
                sentence = entry["sentence"]
                results = run_pii_detection(sentence)

                for r in results:
                    label_type = r["label"]
                    label_info = DETECTOR_TYPE_MAP.get(label_type, {"개인/기밀": "", "식별/준식별": ""})
                    all_rows.append({
                        "도메인": detail_field,
                        "단어": r["match"],
                        "개인/기밀": label_info["개인/기밀"],
                        "식별/준식별": label_info["식별/준식별"],
                        "정보 유형": r["label"],
                        "점수": r.get("score", None),
                        "저장 경로": str(file_path)
                    })

                formatted = convert_to_target_format(
                    entry,
                    results,
                    filename=str(file_path),
                    case_field=case_field,
                    detail_field=detail_field
                )
                output_list.append(formatted)

            output_path = output_folder / file_path.name
            output_path.write_text(json.dumps(output_list, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"✔ 저장 완료: {file_path.name}")

        except Exception as e:
            print(f"❌ 에러 발생 - {file_path.name}: {e}")

    # ✅ DataFrame 저장
    df = pd.DataFrame(all_rows)

    # 준식별 / 그 외 분리
    df_j = df[df["식별/준식별"] == "준식별"]
    df_p = df[df["식별/준식별"] != "준식별"]

    base_path = Path("C:/Users/megan/onestone/BOAZ_Data_preprocess_logics/regex_based_doc_parsing/data_/")
    df_j.to_csv(base_path / "output_j.csv", index=False, encoding="utf-8-sig")
    df_p.to_csv(base_path / "output_p.csv", index=False, encoding="utf-8-sig")

    print(f"📁 output_j.csv → {len(df_j)} rows 저장 완료")
    print(f"📁 output_p.csv → {len(df_p)} rows 저장 완료")

if __name__ == "__main__":
    print("🚀 PII Detector 시작됨") 
    input_path = Path("regex_based_doc_parsing/data_/sentence_split_json")
    output_path = Path("regex_based_doc_parsing/data_/pii_detection_output")
    df_save_path = Path("regex_based_doc_parsing/data_/summary.csv")
    # 🔧 caseField, detailField는 여기서 직접 설정 가능
    case_field = "1"
    detail_field = "1"
    
    process_sentence_split_json(input_path, output_path)
