# ------------------------
# 1️⃣ SDK import & 연결
# ------------------------
import subprocess
from label_studio_sdk.client import LabelStudio
import os
import time
import base64
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc
from sklearn.metrics import confusion_matrix
import psycopg2


# ------------------------
# Label Studio 서버 백그라운드 실행
# ------------------------
print("Label Studio 서버 실행 중...")
ls_process = subprocess.Popen(["label-studio", "start"], shell=True)
time.sleep(10)  # 서버가 올라올 시간을 잠시 대기

# ------------------------
# SDK 연결
# ------------------------

LABEL_STUDIO_URL = "http://localhost:8080"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6ODA2NDAyOTAwNywiaWF0IjoxNzU2ODI5MDA3LCJqdGkiOiI3Yzk5MTAxYjk3MDA0N2RhYjg2ZmY0NzkzY2M2Y2RjOCIsInVzZXJfaWQiOiIxIn0.9SQaKpd-e3f5bhodgz2Fe8chlSf1JHTQrzaSU_U9K34"  # PAT 사용

ls = LabelStudio(base_url=LABEL_STUDIO_URL, api_key=API_KEY)

# ------------------------
# 한글 폰트 설정
rc('font', family='Malgun Gothic')

# ------------------------
#  가상 confusion matrix 생성
# labels_pii = ["개인정보", "준식별자", "일반정보"]
# labels_conf = ["기밀정보", "일반정보"]

# pii_matrices = [
#     np.array([[12, 3, 2], [1, 15, 4], [0, 2, 20]]),
#     np.array([[14, 2, 1], [0, 18, 2], [1, 3, 19]]),
#     np.array([[16, 1, 0], [1, 17, 1], [0, 2, 21]])
# ]

# conf_matrices = [
#     np.array([[18, 2], [3, 25]]),
#     np.array([[20, 1], [2, 27]]),
#     np.array([[22, 0], [1, 28]])
# ]

# #---------------------------
# #실제 데이터 불러오기
# # CSV 파일 리스트 정의 [각 단계별 예측 결과.csv 경로 지정]
# pii_files = [
#     "pii_step1 예측 결과.csv 경로",
#     "pii_step2 예측 결과.csv 경로",
#     "pii_step3 예측 결과.csv 경로"
# ]

# conf_files = [
#     "conf_step1 예측 결과.csv 경로",
#     "conf_step2 예측 결과.csv 경로",
#     "conf_step3 예측 결과.csv 경로"
# ]



# def load_confusion_from_csv(filepath, labels):
#     df = pd.read_csv(filepath)
#     cm = confusion_matrix(df["y_true"], df["y_pred"], labels=labels)
#     return cm


# labels_pii = ["개인정보", "준식별자", "일반정보"]
# labels_conf = ["기밀정보", "일반정보"]

# pii_matrices = [load_confusion_from_csv(f, labels_pii) for f in pii_files]
# conf_matrices = [load_confusion_from_csv(f, labels_conf) for f in conf_files]




# ------------------------------------------------------------
# PostgreSQL 연결 
# ------------------------------------------------------------
def get_connection():
    return psycopg2.connect(
        host="localhost",   # docker-compose 사용 시 service name
        port="5432",        # PostgreSQL 포트
        dbname="postgres",  # DB 이름
        user="postgres",    # 사용자
        password="postgres" # 비밀번호
    )

# ------------------------------------------------------------
# DB에서 각 테이블의 마지막 행 불러오는 함수
# ------------------------------------------------------------
def load_last_row_as_matrix(table_name, labels):
    """
    DB 테이블에서 마지막 행을 불러와 confusion matrix numpy array로 변환
    """
    query = f"SELECT * FROM {table_name} ORDER BY train_index DESC LIMIT 1"
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()

    # train_index 제외한 나머지 컬럼만 matrix로 변환
    mat_values = df.drop(columns=["train_index"]).values.flatten()
    size = len(labels)
    return mat_values.reshape(size, size)



# ------------------------------------------------------------
# 레이블 정의
# ------------------------------------------------------------
labels_pii = ["개인정보", "준식별자", "일반정보"]
labels_conf = ["기밀정보", "일반정보"]



# ------------------------------------------------------------
# DB에서 confusion matrix 불러오기
# ------------------------------------------------------------
pii_tables = ["step1_pii", "step2_pii", "step3_pii"] # pii_table 명 입력
conf_tables = ["step1_conf", "step2_conf", "step3_conf"] #conf_table 명 입력

pii_matrices = [load_last_row_as_matrix(t, labels_pii) for t in pii_tables]
conf_matrices = [load_last_row_as_matrix(t, labels_conf) for t in conf_tables]


# ------------------------
#  2행 3열 subplot PNG 생성
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

for i, mat in enumerate(pii_matrices):
    ax = axes[0, i]
    ax.imshow(mat, cmap="Blues")
    for r in range(mat.shape[0]):
        for c in range(mat.shape[1]):
            ax.text(c, r, str(mat[r, c]), ha="center", va="center", color="black")
    ax.set_xticks(np.arange(len(labels_pii)))
    ax.set_yticks(np.arange(len(labels_pii)))
    ax.set_xticklabels(labels_pii)
    ax.set_yticklabels(labels_pii)
    ax.set_title(f"개인정보 {i+1}단계")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")

for i, mat in enumerate(conf_matrices):
    ax = axes[1, i]
    ax.imshow(mat, cmap="Blues")
    for r in range(mat.shape[0]):
        for c in range(mat.shape[1]):
            ax.text(c, r, str(mat[r, c]), ha="center", va="center", color="black")
    ax.set_xticks(np.arange(len(labels_conf)))
    ax.set_yticks(np.arange(len(labels_conf)))
    ax.set_xticklabels(labels_conf)
    ax.set_yticklabels(labels_conf)
    ax.set_title(f"기밀정보 {i+1}단계")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")

plt.tight_layout()
combined_png = "combined_matrix.png"
plt.savefig(combined_png)
plt.close()
print(f"✅ PNG 생성 완료 → {combined_png}")

# ------------------------
#  Label Studio 업로드용 Base64

import base64

with open("combined_matrix.png", "rb") as f:
    img_bytes = f.read()
img_base64 = "data:image/png;base64," + base64.b64encode(img_bytes).decode()

# Label Studio 업로드 시
task = [{
    "image": img_base64
}]





# ------------------------
# 프로젝트 생성 (한번만)
project = ls.projects.create(
    title="ConfusionMatrix_Eval",
    label_config="""
<View>
  <Image name="image" value="$image"/>
  <Header value="학습을 계속하시겠습니까?"/>
  <Choices name="next_step" toName="image" choice="single">
    <Choice value="Yes"/>
    <Choice value="No"/>
  </Choices>
</View>
"""
)
project_id = project.id
print(f"🎯 프로젝트 생성 완료. ID={project_id}")






# ------------------------
#  이미지 URL 태스크 업로드
response = ls.projects.import_tasks(
    id=project_id,
    request=task
)
print("✅ Label Studio에 URL 태스크 업로드 완료")

# ------------------------------------------------------------
# 레이블 진행 + 레이블 결과 반환해서 다음 process 진행
# ------------------------------------------------------------

import time

# 1️⃣ 실행할 함수 정의
def add(a, b):
    print(f"함수 실행! {a} + {b} = {a+b}")
    return a + b

# 2️⃣ Label Studio 태스크 결과 확인

processed_task_ids = set()

while True:
    tasks = ls.tasks.list(project=project_id, page=1,fields="all")

    for task in tasks:
        task_id = task.id
        if task_id in processed_task_ids:
            continue

        annotations = task.annotations or []
        for ann in annotations:
            results = ann.get("result", [])  # dict이므로 get 사용
            for r in results:
                choices = r.get("value", {}).get("choices", [])
                if "Yes" in choices:
                    add(3, 5)
                    processed_task_ids.add(task_id)
                    print(f"Task {task_id} 처리 완료")
                    break  # 하나 처리하면 바로 루프 종료

    if processed_task_ids:
        break  # 이미 처리했으면 무한 루프 탈출

    time.sleep(10)


