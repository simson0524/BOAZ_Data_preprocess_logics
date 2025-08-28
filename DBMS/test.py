import pandas as pd

#  SDK import
from  DBMS.db_sdk import create_tables, add_rows, fetch_all, delete_row, truncate_tables,cnt,fetch_rows

if __name__ == "__main__":
    # 1. 테이블 생성
    create_tables()
    print("✅ 테이블 생성 완료")

    # 2. 테스트 데이터 준비 (DataFrame 대신 리스트로 바로 삽입)
    test_rows = [
        ("lee", "관리부", "인사문서", "이름", "개인정보"),
        ("kim", "기술부", "개발보고서", "사번", "준식별자"),
        ("park", "생산부", "생산계획서", "고객정보", "기밀정보"),
    ]

    # 3. 개인정보 테이블에 데이터 삽입
    add_rows("개인정보", [test_rows[0]])  
    add_rows("준식별자", [test_rows[1]])
    add_rows("기밀정보", [test_rows[2]])
    print("✅ 샘플 데이터 삽입 완료")
    

    

    # 4. 특정 행 삭제 테스트 (예: 이병헌 삭제)
    delete_row("개인정보", "lee")
    delete_row("준식별자","kim")
    delete_row("기밀정보","park")

    print("✅ 샘플 데이터 삭제 완료")

    


    # 5. 전체 조회

    print(cnt("개인정보"))
    print(cnt("준식별자"))
    print(cnt("기밀정보"))

    print("\n📌 개인정보 테이블 데이터")
    print(fetch_all("개인정보"))
    
    print("\n📌 준식별자 테이블 데이터")
    print(fetch_all("준식별자"))
    

    print("\n📌 기밀정보 테이블 데이터")
    print(fetch_all("기밀정보"))


    # 6. 특정 단어 포함한 행 조회 
    print("\n📌 특장 단어 포함 행 조회 ")
    print(fetch_rows("개인정보","단어","오세훈"))
    
    
    

    # 6. 테이블 데이터 전체 초기화 (TRUNCATE)
    truncate_tables()
    print("\n🧹 모든 테이블 데이터 초기화 후 조회:")
    print("개인정보:", fetch_all("개인정보"))
    print("준식별자:", fetch_all("준식별자"))
    print("기밀정보:", fetch_all("기밀정보"))
