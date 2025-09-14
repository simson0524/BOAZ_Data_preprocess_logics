import subprocess
import requests
import time
import psycopg2
import pandas as pd
from label_studio_sdk.client import LabelStudio
from label_studio_sdk.label_interface import LabelInterface
from label_studio_sdk.label_interface.create import choices

class LabelStudioProjectManager:
    def __init__(self, base_url: str, api_key: str,db_conn_info=None):
        self.label_studio_url = base_url
        self.api_key = api_key
        self.db_conn_info = db_conn_info 
        self.ls = None
        self.project = None
        self.processed_task_ids = set()

    # ------------------------
    # Label Studio SDK 연결
    # ------------------------
    def connect_sdk(self):
        self.ls = LabelStudio(base_url=self.label_studio_url, api_key=self.api_key)
        try:
            headers = {"Authorization": f"Token {self.api_key}"}
            r = requests.get(f"{self.label_studio_url}/api/version", headers=headers)
            r.raise_for_status()
            print(f"✅ SDK 연결 성공, Label Studio 버전: {r.json().get('version')}")
        except Exception as e:
            raise RuntimeError(f"SDK 연결 실패: {e}")
        

    # ------------------------
    # PostgreSQL 데이터 로드
    # ------------------------
    def load_from_postgres(self, table_name: str):
        if not self.db_conn_info:
            raise ValueError("PostgreSQL 연결 정보(db_conn_info)가 필요합니다.")

        query = f"""
        SELECT generated_sent, "단어", generation_target_label, validated_label
        FROM {table_name};
        """

        conn = psycopg2.connect(**self.db_conn_info)
        df = pd.read_sql(query, conn)
        conn.close()

        return df.to_dict(orient="records")


    # ------------------------
    # 프로젝트 생성 (중복 방지)
    # ------------------------
    
    def create_project(self, dataset_name: str, labels=None):
        if labels is None:
            labels = ['일반정보', '개인정보', '준식별자', '기밀정보']

        label_config = """
                <View>
                    <Text name="text" value="$text"/>
                    <View style="margin-top: 50px"/>
                    <Header value="위 문장에서 하이라이트 된 단어(span)가 '$vl' 의 문맥을 갖는가?"/>
                    <Choices name="label" toName="text" choice = "single">
                        <Choice value="Yes"/>
                        <Choice value="No"/>
                    </Choices>
                    <View style="margin-top: 20px"/>
                    <Header value="📌 참고 정보: Ground Truth=$gt / Validated Label=$vl"/>
                    <View style="margin-top: 20px"/>
                </View>
                """

        self.project = self.ls.projects.create(
            title=dataset_name,
            label_config=label_config
        )
        print(f"✅ 프로젝트 생성 완료: {self.project.id} ({dataset_name})")
        return self.project

    
    def prepare_tasks(self, df):
        tasks = []
        manual_validation = []
        for _, row in df.iterrows():
            sentence = row["generated_sent"]
            span = row["단어"]
            start_positions = []
            start = 0
            while True:
                idx = sentence.find(span, start)
                if idx == -1:
                    break
                start_positions.append(idx)
                start = idx + len(span)
            for i, start_idx in enumerate(start_positions):
                end_idx = start_idx + len(span)

                # validation 정보 저장
                if row.get("generation_target_label", "") == "Yes":
                    manual_validation.append({
                        "text": sentence,
                        "span": span,
                        "start": start_idx,
                        "end": end_idx,
                        "gt": row["generation_target_label"],
                        "vl": row.get("validated_label", "")
                    })

               
                tasks.append({
                    "data": {
                        "text": sentence,
                        "gt": row.get("generation_target_label", ""),
                        "vl": row.get("validated_label", "")
                    },
                    "predictions": [
                        {
                            "result": [
                                {
                                    "from_name": "label",     # Label Interface에서 정의한 name과 일치
                                    "to_name": "text",        # Text name과 일치
                                    "type": "labels",         # span 하이라이트용 타입
                                    "value": {
                                        "start": start_idx,   # span 시작 인덱스
                                        "end": end_idx,       # span 끝 인덱스
                                        "text": span,         # span 텍스트
                                        "labels": []
                                    }
                                }
                            ]
                        }
                    ]
                })


        return tasks, manual_validation

    # ------------------------
    # Task 업로드
    # ------------------------
    def upload_tasks(self, tasks):
        if not tasks:
            print("⚠️ 업로드할 Task가 없습니다.")
            return
        self.ls.projects.import_tasks(id=self.project.id, request=tasks)
        print(f"✅ {len(tasks)}개의 Task 업로드 완료!")


    def fetch_results(self):
        if not self.project:
            raise ValueError("프로젝트가 존재하지 않습니다.")

        results = []
        print("📌 라벨링 결과 fetch 시작...")

        while True:
            tasks = list(self.ls.tasks.list(project=self.project.id, page=1))
            new_task_processed = False

            for task in tasks:
                task_id = task.id
                if task_id in self.processed_task_ids:
                    continue

                annotations = task.annotations or []
                for ann in annotations:
                    result_list = ann.get("result", []) or ann.get("results", [])
                    for r in result_list:
                        val = r.get("value", {})

                        # ✅ 하이라이트 span 값
                        span_text = val.get("text")
                        start = val.get("start")
                        end = val.get("end")

                        # ✅ 사용자가 선택한 라벨 (Yes / No)
                        choices = val.get("choices", [])
                        if not choices or choices[0].lower() != "yes":
                            continue  # No는 스킵

                        # ✅ Label Studio에 저장된 데이터
                        text = task.data.get("text", "")
                        gt = task.data.get("gt", "")
                        vl = task.data.get("vl", "")

                        results.append({
                            "generated_sent": text,
                            "단어": span_text,   # 하이라이트된 단어 그대로
                            "generation_target_label": gt,
                            "validated_label": vl,
                            #"span_range": (start, end)
                        })

                        self.processed_task_ids.add(task_id)
                        new_task_processed = True
                        print(f"✅ Task {task_id} 처리 완료 (Yes 라벨)")

            if not new_task_processed:
                break

            print("📌 대기 중인 Task 처리 중...")
            time.sleep(2)

        print("✅ 모든 Task 처리 완료")
        return results


    # ------------------------
    # end-to-end 실행
    # ------------------------
    def run_from_postgres(self, dataset_name, table_name):
        #self.start_label_studio()
        self.connect_sdk()
        df = self.load_from_postgres(table_name)
        self.create_project(dataset_name)
        tasks, manual_validation = self.prepare_tasks(pd.DataFrame(df))
        self.upload_tasks(tasks)
        # return manual_validation
        print("📌 웹에서 라벨링 후 fetch_results() 호출하여 결과 확인 가능")
        return self.project

# ------------------------
# 실행 예시
# ------------------------
def manual_validation(db_host, db_port, db_name, db_user, db_password, LABEL_STUDIO_URL="http://localhost:8080", api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6ODA2NDczNzUxMCwiaWF0IjoxNzU3NTM3NTEwLCJqdGkiOiI2M2UyOTdkZmQ1NmM0N2NkYmYyZGQ0ZDNjZTlhN2JlYyIsInVzZXJfaWQiOiIxIn0.GAP15UfCY29IU0GDlpcmlWlxsWOTDEyC8gXM-ROkXRg"):
    DB_CONN_INFO = {
        "host": db_host,
        "port": db_port,
        "dbname": db_name,
        "user": db_user,
        "password": db_password
    }
    LABEL_STUDIO_URL = LABEL_STUDIO_URL
    API_KEY = api_key

    manager = LabelStudioProjectManager(base_url=LABEL_STUDIO_URL,api_key=API_KEY, db_conn_info=DB_CONN_INFO)
    project = manager.run_from_postgres("Manual_Validation_Dataset_Labeling", "confid_validation")


    # 라벨링 완료 후 결과 가져오기
    input("✅ 웹에서 라벨링 완료 후 엔터를 누르세요...")
    final_results = manager.fetch_results()
    for r in final_results:
        print(r)
