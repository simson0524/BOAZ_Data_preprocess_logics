import pandas as pd
import labelbox as lb
from labelbox import OntologyBuilder, Classification, Option
from uuid import uuid4
import time
import os
import tempfile
import json

# ------------------------
# 1️⃣ Labelbox 연결
# ------------------------

API_KEY = os.getenv("LABELBOX_API_KEY")  # 🔑 환경변수에서 API Key 불러오기
client = lb.Client(api_key=API_KEY)


# ------------------------
# 2️⃣ Project & Dataset 생성 
# ------------------------
project_name = f"generation_project_{int(time.time())}"
project = client.create_project(name=project_name)


dataset_name = f"generation_Dataset_{int(time.time())}"
dataset = client.create_dataset(name=dataset_name)



# ------------------------
# 3️⃣ Ontology 생성 및 Project 연결
# ------------------------
ontology_builder = OntologyBuilder(
    classifications=[
        Classification(
            class_type=Classification.Type.RADIO,
            name="정보 유형 선택",
            options=[
                Option(value="일반정보"),
                Option(value="개인정보"),
                Option(value="준식별자"),
                Option(value="기밀정보")
            ]
        )
    ]
)

# 기존에 같은 이름의 Ontology 검색
existing_ontologies = list(client.get_ontologies(name_contains="Span-Ontology"))
ontology = next((o for o in existing_ontologies if o.name == "Span-Ontology"), None)

if ontology is None:
    ontology = client.create_ontology("Span-Ontology", ontology_builder.asdict())
project.ontology = ontology
project.update()
print("✅ Ontology 연결 완료")




# ------------------------
# 4️⃣ DataFrame 불러오기
# ------------------------


csv_path = "data.csv"   # 🔥 실제 CSV 경로로 교체
df = pd.read_csv(csv_path)

print(f"📂 CSV 로드 완료: {len(df)} rows")



# 예시 DataFrame
# ------------------------
# df = pd.DataFrame([
#     {
#         "generated_sentence": "검사 김철수가 환자를 검사했다",
#         "span_text": "검사",
#         "generation_target_label": "일반정보",
#         "inference_label": "개인정보"
#     }
# ])


# ------------------------
# 6️⃣ JSONL 파일을 이용해 DataRow 업로드 (수정)
# ------------------------
 # JSONL 파일 읽기

for _, row in df.iterrows():
    sentence = row["generated_sentence"]
    span_text = row["span_text"]
    candidates = [row["generation_target_label"], row["inference_label"]]

    guide_text = (
        f"문장: {sentence}\n"
        f"👉 라벨링 대상 단어: {span_text}\n"
        f"👉 후보 라벨: {' vs '.join(candidates)}"
    )

    dr = dataset.create_data_row(
        row_data=guide_text,
        global_key=str(uuid4())
        #metadata={"instructions": guide_text}
    )
    print(dr.uid, dr.row_data)