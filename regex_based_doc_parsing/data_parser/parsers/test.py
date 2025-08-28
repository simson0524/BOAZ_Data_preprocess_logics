from pathlib import Path
import json

# OpenAI 폴더 경로
input_path = Path(r"C:\Users\megan\onestone\BOAZ_Data_preprocess_logics\regex_based_doc_parsing\data_\raw_data\openai")

# 모든 JSON 파일 재귀적으로 탐색
json_files = list(input_path.glob("**/*.json"))

print(f"총 {len(json_files)}개 JSON 파일 발견")

# 발견된 파일 경로 출력
for f in json_files:
    print(f"Detected file: {f}")

# 각 파일 첫 줄만 확인 (optional)
for f in json_files:
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        print(f"\n[{f.name}] JSON 첫 항목 확인:")
        if isinstance(data, dict):
            for i, key in enumerate(data.keys()):
                print(f"  Key {i+1}: {key}")
                if i >= 4:  # 상위 5개만 확인
                    break
        elif isinstance(data, list):
            print(f"  리스트 길이: {len(data)}")
    except Exception as e:
        print(f"  ❌ JSON 로드 실패: {e}")
