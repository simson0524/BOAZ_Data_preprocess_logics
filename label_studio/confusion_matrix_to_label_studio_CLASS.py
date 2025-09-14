import subprocess
import time
import base64
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc
from label_studio_sdk.client import LabelStudio
import requests
import psycopg2


class ConfusionMatrixPipeline:
    def __init__(self, API_KEY, db_config, label_studio_url="http://localhost:8080"):
        self.api_key = API_KEY
        self.db_config = db_config
        self.label_studio_url = label_studio_url
        self.ls = None
        self.project = None
        self.processed_task_ids = set()
        self.uploaded_task_ids = []  # 업로드된 task id 저장용

    # ------------------------
    # 1️⃣ Label Studio 서버 실행
    # ------------------------
    def start_label_studio(self):
    # 서버 이미 실행 중인지 확인
        try:
            r = requests.get(f"{self.label_studio_url}/api/version", timeout=3)
            if r.status_code == 200:
                print(f"✅ Label Studio 이미 실행 중 ({self.label_studio_url})")
                return
        except requests.exceptions.RequestException:
            pass

        # 서버 새로 실행 (기본 포트가 사용 중이면 8081로 변경 가능)
        new_port = 8080
        while True:
            try:
                r = requests.get(f"http://localhost:{new_port}/api/version", timeout=1)
                # 서버가 있으면 다음 포트로
                new_port += 1
            except requests.exceptions.RequestException:
                break

        print(f"🚀 Label Studio 서버 실행 중... 포트={new_port}")
        subprocess.Popen(["label-studio", "start", "--port", str(new_port)], shell=True)
        self.label_studio_url = f"http://localhost:{new_port}"

        # 서버 준비 대기
        timeout = 60
        for i in range(timeout):
            try:
                r = requests.get(f"{self.label_studio_url}/api/version")
                if r.status_code == 200:
                    print(f"✅ Label Studio 서버 준비 완료! ({self.label_studio_url})")
                    return
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
        raise RuntimeError("Label Studio 서버가 준비되지 않았습니다.")

    # ------------------------
    # 2️⃣ SDK 연결
    # ------------------------
    def connect_sdk(self):
        self.ls = LabelStudio(base_url=self.label_studio_url, api_key=self.api_key)
        rc('font', family='Malgun Gothic')

    # ------------------------
    # 3️⃣ DB 연결
    # ------------------------
    def get_connection(self):
        return psycopg2.connect(**self.db_config)

    def load_last_row_as_matrix(self, table_name, labels, is_confidential=False):
        conn = self.get_connection()
        try:
            query = f"""
                SELECT *
                FROM {table_name}
                ORDER BY timestamp DESC
                LIMIT 1
            """
            df = pd.read_sql(query, conn)
        finally:
            conn.close()

        if df.empty:
            raise ValueError(f"{table_name} 테이블에서 데이터를 가져올 수 없습니다.")

        row = df.iloc[-1]

        if is_confidential:
            values = [row[col] for col in ['m_0_0', 'm_0_1', 'm_1_0', 'm_1_1']]
            return np.array(values, dtype=float).reshape(2, 2)
        else:
            values = [row[col] for col in [
                'm_0_0','m_0_1','m_0_2',
                'm_1_0','m_1_1','m_1_2',
                'm_2_0','m_2_1','m_2_2'
            ]]
            return np.array(values, dtype=float).reshape(3, 3)

    # ------------------------
    # 4️⃣ confusion matrix 생성 및 저장
    # ------------------------
    def generate_confusion_matrix_png(self, pii_tables, conf_tables, labels_pii, labels_conf, output_file="combined_matrix.png"):
        pii_matrices = [self.load_last_row_as_matrix(t, labels_pii, is_confidential=False) for t in pii_tables]
        conf_matrices = [self.load_last_row_as_matrix(t, labels_conf, is_confidential=True) for t in conf_tables]

        fig, axes = plt.subplots(2, 4, figsize=(18, 10))

        # 개인정보
        for i, mat in enumerate(pii_matrices):
            total = mat.sum()
            ax = axes[0, i]
            ax.imshow(mat, cmap="Reds" if "모델" in pii_tables[i] else "Blues")
            for r in range(mat.shape[0]):
                for c in range(mat.shape[1]):
                    val = mat[r, c]
                    perc = (val / total * 100) if total > 0 else 0
                    ax.text(c, r, f"{val}\n({perc:.1f}%)", ha="center", va="center", color="black")
            ax.set_xticks(np.arange(len(labels_pii)))
            ax.set_yticks(np.arange(len(labels_pii)))
            ax.set_xticklabels(labels_pii)
            ax.set_yticklabels(labels_pii)
            ax.set_title(f"개인정보 {pii_tables[i]}")
            ax.set_xlabel("Predicted")
            ax.set_ylabel("Actual")

        # 기밀정보
        for i, mat in enumerate(conf_matrices):
            total = mat.sum()
            ax = axes[1, i]
            ax.imshow(mat, cmap="Reds" if "모델" in conf_tables[i] else "Blues")
            for r in range(mat.shape[0]):
                for c in range(mat.shape[1]):
                    val = mat[r, c]
                    perc = (val / total * 100) if total > 0 else 0
                    ax.text(c, r, f"{val}\n({perc:.1f}%)", ha="center", va="center", color="black")
            ax.set_xticks(np.arange(len(labels_conf)))
            ax.set_yticks(np.arange(len(labels_conf)))
            ax.set_xticklabels(labels_conf)
            ax.set_yticklabels(labels_conf)
            ax.set_title(f"기밀정보 {conf_tables[i]}")
            ax.set_xlabel("Predicted")
            ax.set_ylabel("Actual")

        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()
        print(f"✅ PNG 생성 완료 → {output_file}")
        return output_file

    # ------------------------
    # 5️⃣ 프로젝트 생성 및 태스크 업로드
    # ------------------------
    def setup_project_and_upload_task(self, png_file):
        with open(png_file, "rb") as f:
            img_bytes = f.read()
        img_base64 = "data:image/png;base64," + base64.b64encode(img_bytes).decode()
        task = [{"data": {"image": img_base64}}]

        projects = self.ls.projects.list()
        self.project = next((p for p in projects if p.title == "ConfusionMatrix_Eval"), None)

        if self.project is None:
            self.project = self.ls.projects.create(
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
            print(f"🎯 프로젝트 생성 완료. ID={self.project.id}")
        else:
            print(f"🎯 프로젝트 이미 존재. ID={self.project.id}")

        # ✅ 리턴값 확인
        self.ls.projects.import_tasks(id=self.project.id, request=task)
        #print("🔍 import_tasks response:", response)

         # 업로드 후 프로젝트의 전체 태스크 다시 조회
        tasks = list(self.ls.tasks.list(project=self.project.id))
        self.uploaded_task_ids = [t.id for t in tasks][-len(task):]  # 방금 올린 마지막 N개
        print("✅ 업로드된 태스크 ID:", self.uploaded_task_ids)

       
    def wait_for_task_label(self, task_id, check_interval=5, timeout=3600):
        """
        특정 task_id가 라벨링될 때까지 기다렸다가 Yes/No로 boolean 반환
        - 라벨링 완료 → True (Yes) / False (No)
        - timeout 지나도 라벨링 안 되면 None 반환
        """
        import time

        start_time = time.time()

        while True:
            task = self.ls.tasks.get(task_id)
            annotations = task.annotations or []

            
            for ann in annotations:
                results = getattr(ann, "result", []) or getattr(ann, "results", [])

                for r in results:
                    val = r.get("value", {})
                    choices = val.get("choices", [])
                    text = val.get("text", [])
                    labels = val.get("labels", [])
                    for v in choices + text + labels:
                        if str(v).strip().lower() == "yes":
                            return True
                        elif str(v).strip().lower() == "no":
                            return False
                            

            

            # timeout 체크
            if time.time() - start_time > timeout:
                print(f"⚠️ Task {task_id} 라벨링 대기 timeout ({timeout}초)")
                return None

            time.sleep(check_interval)


    # ------------------------
    # 8️⃣ 전체 실행
    # ------------------------
    def run(self):
        self.start_label_studio()
        self.connect_sdk()

        labels_pii = ["개인정보", "준식별자", "일반정보"]
        labels_conf = ["기밀정보", "일반정보"]
        pii_tables = ["검증1_개인", "검증2_개인", "검증3_개인", '모델_개인']
        conf_tables = ["검증1_기밀", "검증2_기밀", "검증3_기밀", '모델_기밀']

        png_file = self.generate_confusion_matrix_png(pii_tables, conf_tables, labels_pii, labels_conf)
        self.setup_project_and_upload_task(png_file)
        # self.process_tasks()
        # ✅ 업로드된 task id 확인 후, Boolean 값 뽑기
        if self.uploaded_task_ids:
            last_task_id = self.uploaded_task_ids[-1]
            result = self.wait_for_task_label(last_task_id)
            print(f"🔍 Task {last_task_id} 결과: {result}")
        else:
            print("⚠️ 업로드된 태스크가 없습니다.")


###########파이프라인 실행##################
def metric_on_labeling_tool(db_host, db_port, db_name, db_user, db_password, api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6ODA2NDcwNzg2OCwiaWF0IjoxNzU3NTA3ODY4LCJqdGkiOiI3NmU1YWRlNmMzNjI0ZDgyOTgxZWI2MjNlMTBlZTdhZiIsInVzZXJfaWQiOiIxIn0.00Mk2vMGBll4YBzSvbrE1rzu40GpBYkP9MVhiFbv-F0"):
    db_config = {
        "host": db_host,
        "port": db_port,
        "dbname": db_name,
        "user": db_user,
        "password": db_password
    }

    pipeline = ConfusionMatrixPipeline(
        API_KEY = api_key,
        db_config=db_config
    )
    
    pipeline.run()
