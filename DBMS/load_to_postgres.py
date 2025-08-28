import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import sys

# PostgreSQL 연결 설정
def get_connection():
    return psycopg2.connect(
        host="localhost",     # docker-compose 사용 시 service name
        port="5432",          # PostgreSQL 포트 (docker-compose.yml 확인)
        dbname="postgres",     # DB 이름
        user="postgres",     # 사용자
        password="postgres"  # 비밀번호
    )

# 테이블 생성 함수
def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS 개인정보 (
            단어 TEXT,
            부서명 TEXT,
            문서명 TEXT,
            단어유형 TEXT,
            구분 TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS 준식별자 (
            단어 TEXT,
            부서명 TEXT,
            문서명 TEXT,
            단어유형 TEXT,
            구분 TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS 기밀정보 (
            단어 TEXT,
            부서명 TEXT,
            문서명 TEXT,
            단어유형 TEXT,
            구분 TEXT
        );
    """)
    conn.commit()
    cursor.close()

# 데이터 삽입 함수
def insert_data(conn, table, rows):
    cursor = conn.cursor()
    query = f"INSERT INTO {table} (단어, 부서명, 문서명, 단어유형, 구분) VALUES %s"
    execute_values(cursor, query, rows)
    conn.commit()
    cursor.close()

# CSV 처리 함수
def process_csv(file_path):
    print(f"[INFO] CSV 적재 시작: {file_path}")
    conn = get_connection()
    create_tables(conn)
    df = pd.read_csv(file_path, sep=",", encoding='utf-8-sig')
    print("CSV 컬럼명:", df.columns.tolist())
    df.columns = df.columns.str.strip()

    for category in ["개인정보", "준식별자", "기밀정보"]:
        filtered = df[df["개인정보/준식별자/기밀정보"] == category]
        if not filtered.empty:
            rows = [tuple(row) for row in filtered.values]
            insert_data(conn, category, rows)

    conn.close()
    print(f"[INFO] {file_path} → DB 적재 완료")



import glob
import os

if __name__ == "__main__":
    csv_folder = r"C:\Users\megan\onestone\BOAZ_Data_preprocess_logics\DBMS\개발부"
    csv_files = glob.glob(os.path.join(csv_folder, "*.csv"))

    if not csv_files:
        print("❌ CSV 파일이 없습니다.")
    else:
        for csv_file in csv_files:
            process_csv(csv_file)
