import matplotlib.pyplot as plt
from matplotlib import rc
import numpy as np
import os
import labelbox as lb
from labelbox import OntologyBuilder, Classification, Option
import pandas as pd
from sklearn.metrics import confusion_matrix

# --------------------
# 0. 한글 폰트 설정 (Windows 기준)
rc('font', family='Malgun Gothic')



# --------------------
# 1. confusion matrix CSV → numpy 변환 함수

# CSV 파일 리스트 정의 [각 단계별 예측 결과.csv 경로 지정]
pii_files = [
    "data/pii_step1.csv",
    "data/pii_step2.csv",
    "data/pii_step3.csv"
]

conf_files = [
    "data/conf_step1.csv",
    "data/conf_step2.csv",
    "data/conf_step3.csv"
]



def load_confusion_from_csv(filepath, labels):
    df = pd.read_csv(filepath)
    cm = confusion_matrix(df["y_true"], df["y_pred"], labels=labels)
    return cm


labels_pii = ["개인정보", "준식별자", "일반정보"]
labels_conf = ["기밀정보", "일반정보"]

pii_matrices = [load_confusion_from_csv(f, labels_pii) for f in pii_files]
conf_matrices = [load_confusion_from_csv(f, labels_conf) for f in conf_files]


# --------------------
# 가상 데이터 제작 (테스트용)
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


# --------------------
# 2. 2행 3열 subplot으로 합치기
fig, axes = plt.subplots(2, 3, figsize=(15, 10))  # 2행 3열

# 개인정보 3개
for i, mat in enumerate(pii_matrices):
    ax = axes[0, i]
    im = ax.imshow(mat, cmap="Blues")
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

# 기밀정보 3개
for i, mat in enumerate(conf_matrices):
    ax = axes[1, i]
    im = ax.imshow(mat, cmap="Blues")
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
print(f"✅ 2행3열 합쳐서 저장 → {combined_png}")

# --------------------
# 3. Labelbox 연결

API_KEY = os.environ["LABELBOX_API_KEY"]
client = lb.Client(api_key=API_KEY)

# 4. 한 프로젝트 생성
project = client.create_project(
    name="ConfusionMatrix_Eval",
    media_type=lb.MediaType.Image
)

# 5. Ontology 생성 + 연결 (Yes/No 버튼)
ontology_builder = OntologyBuilder(
    classifications=[
        Classification(
            class_type=Classification.Type.RADIO,
            name="다음 학습으로 넘어가시겠습니까?",
            options=[Option(value="Yes"), Option(value="No")]
        )
    ]
)
ontology = client.create_ontology("Confusion-Matrix-Ontology", ontology_builder.asdict())
project.ontology = ontology
project.update()  # 반드시 호출

# 6. 데이터셋 생성 + PNG 업로드
dataset = client.create_dataset(name="ConfusionMatrix_Dataset")
rows = [{"row_data": combined_png, "global_key": "combined_matrix"}]
task = dataset.create_data_rows(rows)
task.wait_till_done()

print(f"🎯 프로젝트 UID={project.uid}, 데이터셋 UID={dataset.uid} 업로드 완료 ✅")
