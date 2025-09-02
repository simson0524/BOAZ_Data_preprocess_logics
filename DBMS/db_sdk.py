from psycopg2.extras import execute_values
from psycopg2 import sql
import psycopg2
import re

def get_connection():
    return psycopg2.connect(
        host="127.0.0.1",     # docker-compose 사용 시 service name
        port="55432",          # PostgreSQL 포트 (docker-compose.yml 확인)
        dbname="postgres",     # DB 이름
        user="student1",     # 사용자
        password="onestone"  # 비밀번호
    )

def create_tables():
    conn = get_connection()
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
    conn.close()

def truncate_tables():
    conn = get_connection()
    cursor = conn.cursor()
    for table in ["개인정보", "준식별자", "기밀정보"]:
        cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY;")
    conn.commit()
    cursor.close()
    conn.close()
    print("🗑️ 모든 테이블 데이터 초기화 완료")


def add_rows(table_name, rows):
    conn = get_connection()
    cursor = conn.cursor()
    query = f"""
        INSERT INTO {table_name}
        (단어, 부서명, 문서명, 단어유형, 구분)
        VALUES %s
    """
    execute_values(cursor, query, rows)
    conn.commit()
    cursor.close()
    conn.close()

def delete_row(table_name, word):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE 단어 = %s", (word,))
    conn.commit()
    cursor.close()
    conn.close()

# 특정 sentence에 정답지에 포함된 단어들과 class를 모두 반환하는
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


def fetch_rows(table_name, column_name, keyword):
    conn = get_connection()
    cursor = conn.cursor()
    query = f"SELECT * FROM {table_name} WHERE {column_name} LIKE %s"
    cursor.execute(query, (f"%{keyword}%",))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows



def cnt(table_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT count(*) FROM {table_name}")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows