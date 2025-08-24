# make__dataset.py

from google import genai
import pandas as pd
import os
import re
from pathlib import Path
WW_GEMINI_API_KEY ="WW_GEMINI_API_KEY"
def generate_company(Department, n, api_key=WW_GEMINI_API_KEY):
    client = genai.Client(api_key=api_key)
    prompt1 = f"""
    안녕
    나는 가상의 회사를 하나 만드려고 해.
    회사에는 "{Department}" 이렇게 "{n}"개 부서가 있어.
    이 정보를 반영해서 가상의 회사를 아래 양식에 맞춰 현실에 가깝게 소개 해줘.
    ===회사정보 ===
    <회사 개요>
    회사명 :
    설립연도:
    본사위치:
    기업형태:
    주요업종:
    주요고객층:
    기업 슬로건:

    <성장 배경>

    <조직 구성 및 역할>

    <주요 제품 & 서비스>

    <시장 입지>

    <향후 전략>

    ===회사정보끝==="""
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents= prompt1
    )
    # 로그용
    print( response )
    company = response
    return company 




def generate_member(company, Department,n, api_key=WW_GEMINI_API_KEY):
    client = genai.Client(api_key = api_key)

    prompt2 = f"""
    ===직원명부===
    "{company}" 이런 회사가 있어.
    회사에는 "{Department}" 이렇게 "{n}"개의 부서가 있고 여기에는 각 8명의 사원들이 근무 하고 있어.
    각 부서 총 40명에 대해서 이름, 성별, 생년월일, 나이 , 전화번호, 이메일, 직책, 가족관계, 집주소, 주민등록번호, 입사년도, 근속연수, 학력, 연봉의 개인정보가 담긴 직원명부을 만들어줘

    주의 사항은 다음과 같아.
    1. 생년월일 , 나이, 전화번호, 이메일의 칼럼을 전체 공개 형태로 제공할 것
    2. 주민등록번호는 앞자리 생년월일과 뒷자리 첫 숫자는 형식을 맞추되, (7~13자리 숫자)는 개인정보를 고려하여 가상의 숫자로 생성할 것(*이나 x 같은 기호로 마스킹 되지 않도록 할것 )
    3. 집주소는 번지 까지 생성할 것.
    4. 각 부서의 직책의 비율이 현실과 비슷하도록 생성될것
    5. 출력 결과는 코드가 아닌 아래 형식을 따를것

    ===직원 명부===

    부서|이름|성별|생년월일|나이|전화번호|이메일|직책|가족관계|집주소|주민등록번호|입사년도|근속연수|학력|연봉
    ===직원 명부 끝==="""
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt2
    )
    # 로그용
    print( response )
    employment = response
    return employment 



### 사내 문건 보고서 정보 ###
document_form = f"""
1. 
유형: 보고서
공통 주요 내용: 문서번호, 작성일자, 처리기한, 시행일자, 보고자, 제목, 주요내용, 주관부서, 기안 책임자, 업무 협력 부서
부서: 공통
2.
유형: 기안서
공통 주요 내용: 문서번호, 작성부서, 협력부서, 기안자/작성자, 보존년한, 성명·직위·사번·연락처, 검토자(책임자), 기안일자, 결제일자, 제목, 배경, 주요 내용, 기대효과, 리스크 및 대안, 예상비용, 일정, 근거 규정(계약, 판결, 사내규정 조항), 관련 문서번호, 첨부 목록
부서: 공통
3.
유형: 지침서/매뉴얼
공통 주요 내용: 문서명, 제목, 문서번호, 개정번호, 작성부서, 작성자, 검토자, 승인자(성명·직위), 시행일자, 목적, 적용 범위, 용어 정의, 부서별 책임자, 담당자 직위/직무, 절차 및 방법, 관련 서식, 관련 규정/법규, 첨부자료, 개정이력
부서: 공통
4.
유형: 공문(내부)
공통 주요 내용: 문서번호, 작성일자, 처리기한, 회신 요청일, 수신 부서/수신자, 참조부서/참조자, 작성 부서명, 작성자 이름 및 직위, 기안 책임자 이름 및 직위, 연락처(내선·이메일), 제목, 주요 내용, 첨부 자료, 결재선, 회신 방식 및 기한, 담당자 지정
부서: 공통
5.
유형: 세금 신고서
공통 주요 내용: 직원 이름, 주민등록번호, 사번, 근로소득세, 소득세 원천징수 내역, 신고기간, 제출일, 담당자 연락처
부서: 재무 관련 문서
6.
유형: 예산안 / 예산집행 보고서
공통 주요 내용: 작성자/검토자/승인자 이름·직위, 예산 항목, 금액, 집행 현황, 잔액, 작성일, 처리기한
부서: 재무 관련 문서
7.
유형: 자금 관리 보고서
공통 주요 내용: 담당자 이름·직위·연락처, 계좌별 잔액, 입출금 내역, 자금 계획, 작성일, 결재선
부서: 재무 관련 문서
8.
유형: 품질 검사(QC) 보고서
공통 주요 내용: 검사자 이름, 사번, 검사 일자, 제품 코드, 검사 항목, 합격/불합격 여부, 불량 원인, 첨부 사진/자료, 결재선
부서: 생산 관련 문서
9.
유형: 생산 성과 보고서 / KPI 보고서
공통 주요 내용: 담당자 이름, 사번, 생산량, 생산 효율, 불량률, 작업자별 실적, 작성일, 기안자/검토자
부서: 생산 관련 문서
10.
유형: 안전 사고/사고 보고서
공통 주요 내용: 사고자 이름, 사번, 연락처, 응급 연락처, 사고 일시, 장소, 상황, 부상 정도, 조치 내용, 작성자, 승인자
부서: 생산 관련 문서
11.
유형: 영업 실적 보고서
공통 주요 내용: 작성자 이름, 사번, 연락처, 거래처별 매출, 수주 내역, 목표 대비 달성률, 작성일, 기안자, 승인자
부서: 영업 관련 문서
12.
유형: 고객사 관리 기록 / CRM 보고서
공통 주요 내용: 고객 담당자 이름, 연락처, 이메일, 거래처명, 담당자, 계약 내용, 상담 내역, 방문 일시, 작성자, 검토자
부서: 영업 관련 문서
13.
유형: 영업 회의 보고서 / 미팅 기록
공통 주요 내용: 참석자 이름, 사번, 연락처, 회의 일시, 참석자, 논의 내용, 결론 및 액션 아이템, 작성자, 승인자
부서: 영업 관련 문서
14.
유형: 고객 불만/클레임 처리 보고서
공통 주요 내용: 고객 이름, 연락처, 담당자 이름, 사번, 불만 내용, 처리 과정, 처리 결과, 대응 담당자, 작성일, 승인자
부서: 영업 관련 문서
15.
유형: 현장 점검 보고서 / 설비 점검 기록
공통 주요 내용: 점검 담당자 이름, 사번, 연락처, 점검 일시, 설비 번호, 점검 항목, 이상 유무, 조치 내용, 작성자, 승인자, 처리 기한
부서: 기술 관련 문서
16.
유형: 유지보수 계획서 / 유지보수 일정표
공통 주요 내용: 담당 엔지니어 이름, 사번, 연락처, 고객사명, 설비명, 작업일시, 작업 내용, 투입 인력, 작성일, 검토자
부서: 기술 관련 문서
17.
유형: 긴급 대응 기록 / 사고 대응 보고서
공통 주요 내용: 담당자 이름, 사번, 연락처, 고객 연락처, 사고 일시, 장소, 장애 내용, 조치 내역, 사용 부품, 대응 엔지니어, 작성자, 승인자
부서: 기술 관련 문서
18.
유형: 설비 개선/업그레이드 보고서
공통 주요 내용: 담당 엔지니어 이름, 사번, 개선 내용, 적용 설비, 작업 일시, 예상 효과, 테스트 결과, 작성일, 승인자
부서: 기술 관련 문서
"""

def generate_data(company, Department, n, document_form, save_dir, api_key=WW_GEMINI_API_KEY):
    # 파일명 안전화
    def sanitize_filename(name: str) -> str:
        name = re.sub(r'[\\/:*?"<>|]+', '_', name)  # 금지문자 치환
        return name.strip()

    # 중복 방지 파일 경로 반환
    def unique_json_path(base_dir: str, base_name: str) -> Path:
        base_name = sanitize_filename(base_name)
        p = Path(base_dir) / f"{base_name}.json"
        i = 1
        while p.exists():
            p = Path(base_dir) / f"{base_name}_{i}.json"
            i += 1
        return p

    # 저장 폴더 생성
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    client = genai.Client(api_key=api_key)

    prompt3 = f"""
    ===직원명부===
    회사정보 :"{company}"
    직원정보 :"{Department}"
    다음은 회사의 정보와 직원 리스트야.
    이 회사에서는 다양한 내부문건들이 생성되는데, 그 종류와 형태는 "{document_form}" 이렇게 구성되어있어.
    회사 정보와 직원 명부를 반영해서 내부문건을 현실성 있게 생성해줘.
    생성해야 하는 문서는 "{Department}"부서 중 [관리부, 영업부]대상 문서 이며 각 부서별 25개의 문서, 총 50개의 문서를 다양한 문서 종류로 생성 해야해.

    <주의사항>
    *보고서는 사실감 있게 작성되어야 한다.
    **보고서는 10000자 이상으로 작성되어야하며 구체적이고 세부적이어야한다. 문서가 길고 자세할 수록 좋다.**
    *보고서의 출력 형태는 json 형식이다.
    *줄바꿈 문자와 같은 개행 문자를 생성하지 않는다.

    <출력 양식>
    프롬프트 출력 형식은 아래 포맷을 맞춰 줘.
   
    === 부서명_문서명 ===
    [문서 1을 여기에 생성해줘...]
    === 부서명_문서명 ===
    [문서 2를 여기에 생성해줘...]
    ...
    === 부서명_문서명 ===
    [문서 49을 여기에 생성해줘...]
    === 부서명_문서명 ===
    [문서 50을 여기에 생성해줘...]

    """
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt3
    )

    # 파싱 + 파일 저장
    try:
        text = response.text
        # "=== 부서명_문서명 ===" 기준으로 분리
        parts = text.split("=== ")[1:]  # 맨 앞 머리말 제거

        docs = []
        for p in parts:
            # header: 부서명_문서명 / content: 본문(JSON 문자열)
            header, content = p.split(" ===", 1)
            content = content.strip()

            # 리스트에는 문서 '내용'만 저장
            docs.append(content)

            # 파일 저장 (그대로 문자열 저장: 프롬프트가 이미 JSON 형식으로 출력)
            out_path = unique_json_path(save_dir, header)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)

    except Exception as e:
        print(f"[### Exception occurred ###]\n{e}")
        return []

    # 로그용
    print("\n\n[생성된 문서 리스트]\n")
    for i, doc in enumerate(docs):
        print(f"{i}번 문서 ->\n{doc}\n")

    return docs



#실행
save_dir = r"C:\Users\wan09\OneDrive\Desktop\code\data"                      #저장할 경로 
Department = "인사부, 생산부, 관리부, 영업부,기술부"  
n = 5      #전체 부서 개수
company = generate_company(Department , n , api_key=WW_GEMINI_API_KEY)
employment =generate_member(company, Department,n, api_key=WW_GEMINI_API_KEY)
dataset = generate_data(company, Department, n, document_form, save_dir, api_key=WW_GEMINI_API_KEY)