from psycopg2.extras import execute_values
from psycopg2 import sql
import psycopg2
import yaml
import re


def get_connection(config_path="../../PIIClassifier/test_config.yaml"):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    print(config)

    return psycopg2.connect(
        host=config['db']['host'],     # docker-compose 사용 시 service name
        port=config['db']['port'],          # PostgreSQL 포트 (docker-compose.yml 확인)
        dbname=config['db']['dbname'],     # DB 이름
        user=config['db']['user'],     # 사용자
        password=config['db']['password']  # 비밀번호
    )


def create_tables(conn):
    cursor = conn.cursor()
    for table in ["개인정보", "준식별자", "기밀정보"]:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                단어 TEXT,
                부서명 TEXT,
                문서명 TEXT,
                단어유형 TEXT,
                구분 TEXT
            );
        """)
    conn.commit()
    cursor.close()

# 각 단계별 검증 지표가 저장될 친구들
def create_metric_tables(conn):
    cursor = conn.cursor()
    for table in ["모델_개인", "모델_기밀", "검증1_개인", "검증2_개인", "검증3_개인", "검증1_기밀", "검증2_기밀", "검증3_기밀"]:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                test_name TEXT,
                timestamp TEXT,
                m_0_0 TEXT,
                m_0_1 TEXT,
                m_0_2 TEXT,
                m_1_0 TEXT,
                m_1_1 TEXT,
                m_1_2 TEXT,
                m_2_0 TEXT,
                m_2_1 TEXT,
                m_2_2 TEXT
            );
        """)
    conn.commit()
    cursor.close()


def create_prediction_tables(conn):
    cursor = conn.cursor()
    for table in ["pii_prediction, confid_prediction"]:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                test_name TEXT,
                timestamp TEXT,
                단어 TEXT,
                prediction_level TEXT,
                ground_truth TEXT,
                prediction TEXT
            );
        """)
    conn.commit()
    cursor.close()

# 이게 문장검증2에서 labelbox에 표시될 "아이"들 <- (귀여운 하트)
def create_manual_validation_tables(conn):
    cursor = conn.cursor()
    for table in ["pii_validation, confid_validation"]:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                test_name TEXT,
                timestamp TEXT,
                generated_sent TEXT,
                단어 TEXT,
                generation_target_label TEXT,
                validated_label TEXT,
            );
        """)
    conn.commit()
    cursor.close()


def truncate_tables(conn, table_name):
    cursor = conn.cursor()
    for table in [table_name]:
        cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY;")
    conn.commit()
    cursor.close()
    print("🗑️ 모든 테이블 데이터 초기화 완료")


def add_rows(conn, table_name, rows):
    cursor = conn.cursor()
    query = f"""
        INSERT INTO {table_name}
        (단어, 부서명, 문서명, 단어유형, 구분)
        VALUES %s
    """
    execute_values(cursor, query, rows)
    conn.commit()
    cursor.close()


def add_metric_rows(conn, table_name, rows):
    cursor = conn.cursor()
    query = f"""
        INSERT INTO {table_name}
        (test_name, timestamp, m_0_0, m_0_1, m_0_2, m_1_0, m_1_1, m_1_2, m_2_0, m_2_1, m_2_2)
        VALUES %s
    """
    execute_values(cursor, query, rows)
    conn.commit()
    cursor.close()


def add_prediction_rows(conn, table_name, rows):
    cursor = conn.cursor()
    query = f"""
        INSERT INTO {table_name}
        (test_name, timestamp, 단어, prediction_level, ground_truth, prediction)
        VALUES %s
    """
    execute_values(cursor, query, rows)
    conn.commit()
    cursor.close()


def add_manual_validation_rows(conn, table_name, rows):
    cursor = conn.cursor()
    query = f"""
        INSERT INTO {table_name}
        (test_name, timestamp, generated_sent, 단어, generation_target_label, validated_label)
        VALUES %s
    """
    execute_values(cursor, query, rows)
    conn.commit()
    cursor.close()


def delete_row(conn, table_name, word):
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE 단어 = %s", (word,))
    conn.commit()
    cursor.close()

# 특정 sentence에 정답지에 포함된 단어들과 class를 모두 반환하는(장기적으로 봤을때, 그냥 테이블에 있는 전체 열 값들을 반환하게 해야할 듯)
def find_words_in_sentence_for_doc(conn, sentence, table_name, doc_name=None):
    if doc_name:
        query = sql.SQL(
            """
            SELECT DISTINCT "단어", "구분"
            FROM {table}
            WHERE "문서명" = %s
              AND %s LIKE ('%%' || "단어" || '%%')
            """
        ).format(
            table=sql.Identifier(table_name)
        )
        params = (doc_name, sentence)
    else:
        query = sql.SQL(
            """
            SELECT DISTINCT "단어", "구분"
            FROM {table}
            WHERE %s LIKE ('%%' || "단어" || '%%')
            """
        ).format(
            table=sql.Identifier(table_name)
        )
        params = (sentence,)

    with conn.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    return rows  # [(단어, 구분), (단어, 구분), ...]


def fetch_all_rows(conn, table_name):
    cursor = conn.cursor()
    query = f"SELECT * FROM {table_name};"
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    return rows


def fetch_rows(conn, table_name, column_name, keyword):
    cursor = conn.cursor()
    query = f"SELECT * FROM {table_name} WHERE {column_name} LIKE %s"
    cursor.execute(query, (f"%{keyword}%",))
    rows = cursor.fetchall()
    cursor.close()
    return rows


def cnt(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT count(*) FROM {table_name}")
    rows = cursor.fetchall()
    cursor.close()
    return rows