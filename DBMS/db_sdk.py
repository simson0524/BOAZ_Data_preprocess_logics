import psycopg2
from psycopg2.extras import execute_values

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port="5432",
        dbname="postgres",
        user="postgres",
        password="postgres"
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

# 특정 단어가 포함 된 행 조회 -> return 특정 행의 전체 col value
def fetch_all(table_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}") 
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

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