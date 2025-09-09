# DataPreprocessLogics/document_generation/document_generator.py

from pathlib import Path
from openai import OpenAI
from typing import List, Dict
from prompts.company_info import COMPANY_INFO_PROMPT
from prompts.employment_info import EMPLOYMENT_INFO_PROMPT
from prompts.document_form import DOCUMENT_FORM_LIST, DEPARTMENT_LIST
from tqdm.auto import tqdm
import pandas as pd
import json
import csv
import re
import os

### API KEY ###
WW_GPT_API_KEY = os.environ.get("WW_GPT_API_KEY")
HJ_GPT_API_KEY = os.environ.get("HJ_GPT_API_KEY")
JH_GPT_API_KEY = os.environ.get("JH_GPT_API_KEY")


def generate_data(target_department, target_document_name, target_document_form, n=1, company_info=COMPANY_INFO_PROMPT, employment_info=EMPLOYMENT_INFO_PROMPT, model_name="gpt-5-mini", api_key=JH_GPT_API_KEY):
    client = OpenAI(api_key=api_key)

    # Prompt
    main_prompt = f"""
    {company_info}

    {employment_info}

    위는 회사에 대한 설명과 직원 리스트야.
    이 회사에는 각 부서에서 다양한 내부문건들이 생성되는데, 너에게 이 문건들을 생성해달라고 부탁하고 싶어.

    생성해야하는 문서는 '{target_department}의 {target_document_name} {n}개'이고, 
    {target_document_name}의 문서형식은 {target_document_form}으로 이루어져있어. 
    
    맨 처음 알려준 회사정보와 직원정보, 그리고 아래 사항들을 잘 반영해서 내부문건을 현실성 있게 생성해줘!


    [추가정보]
    -개인정보 : 단 하나만으로도 특정 개인을 지칭하거나 추정할 수 있는 정보(이름, 주소, 주민번호, 사번 등)

    -준식별자 : 하나로는 특정 개인을 지칭할 수 없지만 여러 준식별정보가 결합하는 경우나, 소량의 준식별정보와 주변에 개인정보가 분포하는 경우.
    특정 개인을 지칭하거나 추정이 가능한 정보
    (직업, 시군구 주소, 신체관련정보, 생일 등)
    (시+군+구+세부주소가 나오면 시,군,구 까지는 각각 준식별자로 처리해야 해)
    (생년월일일 경우에는 년,월,일이 각각 준식별자로 처리되어야해.)

    -일반정보 : 개인정보와 준식별정보가 아닌 모든 정보

    -기밀정보 : 
    1. 조직/단체 운영 정보
    직위/역할과 결합된 내부 직원명 (예: “회장 김민수”, “간사 이영희”)
    내부 의사결정 라인(결재선, 승인자, 지도교수, 운영진 명단 등)

    2. 기술·보안 정보
    시스템 접근 정보(계정, 링크, 비밀번호 힌트)
    내부 공유 문서명, 파일명, 설계도, 절차 문서
    미공개 URL, 회의 링크, 공유 드라이브 주소

    3.재무/운영 기밀
    개인 귀속 재정 정보(계좌번호, 후원자 명단, 회비 납부 내역)
    외부 공개되지 않은 지원금, 예산 세부내역, 협력 기관
    단순한 수치(총액, 기간, 날짜)는 기밀 아님

        ### 기밀정보 탐지 규칙
    - **항목명(label)은 기밀 아님.** → “승인 요청 예산 같은 단어 자체는 기밀이 아님.  
    - **항목값(value)만 탐지한다.** → “₩120,000,000”은 단순 수치이므로 기밀 아님.  
    - **유출 시 의미가 있는 값만 기밀로 본다.**  
    - ✔️ “김영선”, “031-555-1010”, “youngsun.kim@hanbitsolutions.com” → 기밀  
    - ❌ “6개월”, “₩120,000,000”, “2025-09-01” → 기밀 아님  

    [주의사항]
    *직원 명부는 가상으로 만든것이니 개인정보 보호와 관계없이 자유롭게 사용해도 좋아
    *문서는 주어진 정보를 반영하여 사실감 있게 작성되어야 한다.
    **중요** 문서는 개별 문서 하나 당 *15000자 이상*으로 작성되어야하며 구체적이고 세부적이어야한다. 문서가 길고 자세할 수록 좋다. 
    *문서 내에는 서술되는 내용이 풍부해야 한다.
    **문서의  출력 형태는 json 형식이다.(json의 구조를 명확히 지켜.(괄호와 따옴표 누락하지 않도록 표기에 주의))
    *문서내에 "\n" 이런 줄바꿈 문자를 생성하지마.
    *생략 없이 *{n}개*의 문서를 다 생성해줘.
    *문서명은 그동안 출력한 문서명 값과 겹치지 않게 해줘 
    *문서 하나를 생성하면 그 문서 안에 있는 개인정보와 준식별자 정보를 찾아서 정리할거야.
    *정리 양식은 "단어", "부서명", "문서명", "단어 유형", "개인정보/준식별자/기밀정보"를 칼럼으로 하는 csv 형식 표에 맞춰서 정리하면 돼. 
    "개인정보/준식별자/기밀정보"컬럼은 <개인정보, 준식별자, 기밀정보> 중 하나의 값으로 들아가면 돼.
    *만약 한 단어가 개인정보/준식별자/기밀정보 를 복수로 만족한다면 서로다른 행으로 나누어서 표를 만들어줘.
    *표의 "문서명" 칼럼은 생성된 json 문서명을 따라 가면 돼
    <출력 양식>
    프롬프트 출력 형식은 아래 포맷을 맞춰 줘.

    ===문서 생성===
    =부서명_문서명=
    [문서 1을 여기에 생성해줘...(파이썬 표준 json 라이브러리로 파싱할수 있는 형태로 제공)]
    =표=
    [문서 1의 개인정보/ 준식별자 표를 여기에 정리해줘.]

    ===문서 생성===
    =부서명_문서명=
    [문서 n-2를 여기에 생성해줘...(파이썬 표준 json 라이브러리로 파싱할수 있는 형태로 제공)]
    =표=
    [문서 n-2의 개인정보/ 준식별자 표를 여기에 정리해줘.]
    ...
    ===문서 생성===
    =부서명_문서명=
    [문서 n-1을 여기에 생성해줘...(파이썬 표준 json 라이브러리로 파싱할수 있는 형태로 제공)]
    =표=
    [문서 n-1의 개인정보/ 준식별자 표를 여기에 정리해줘.]

    ===문서 생성===
    =부서명_문서명=
    [문서 n을 여기에 생성해줘...(파이썬 표준 json 라이브러리로 파싱할수 있는 형태로 제공)]
    =표=
    [문서 n의 개인정보/ 준식별자 표를 여기에 정리해줘.]
    """

    # Get response from OpenAI client
    response = client.responses.create(
        model=model_name,
        input=main_prompt,
        max_output_tokens=128000
    )

    # Log
    print( response )

    form_log = response.output_text or ""

    return form_log

def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]+', '_', name)
    name = name.strip().strip('.')
    return name or "untitled"

def split_sections(raw: str) -> List[str]:
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    parts = re.split(r'(?m)^\s*===\s*문서\s*생성\s*===\s*$', raw)
    return [p.strip() for p in parts if p.strip()]

def find_title(section: str):
    return re.search(r'(?m)^\s*=\s*(?P<title>[^=\n]+?)\s*=\s*$', section)

def find_table_marker(section: str):
    return re.search(r'(?m)^\s*=\s*표\s*=\s*$', section)

def extract_json_text(block: str) -> str:
    """
    API가 JSON으로 준다고 하셨으니 그대로 저장합니다.
    우선 ```json ... ``` 블록을 찾고, 없으면 블록에서 첫 '{' ~ 짝 '}'까지를 사용합니다.
    """
    m = re.search(r'```json\s*(.*?)```', block, flags=re.DOTALL|re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r'```(?!json)\s*(.*?)```', block, flags=re.DOTALL|re.IGNORECASE)
    if m:
        return m.group(1).strip()
    start = block.find('{')
    if start == -1:
        raise ValueError("JSON 시작 '{' 를 찾지 못했습니다.")
    depth = 0
    for i, ch in enumerate(block[start:], start=start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return block[start:i+1].strip()
    raise ValueError("JSON 닫는 '}' 를 찾지 못했습니다.")

def parse_table_to_df(table_text: str, HEADER=["단어","부서명","문서명","단어 유형","개인정보/준식별자/기밀정보"]) -> pd.DataFrame:
    lines = [ln.strip() for ln in table_text.strip().splitlines() if ln.strip()]
    rows: List[List[str]] = []
    for ln in lines:
        if re.match(r'^\s*===\s*문서\s*생성\s*===\s*$', ln):  # 혹시 섞인 구분선 제거
            continue
        if re.match(r'^\s*=\s*표\s*=\s*$', ln):
            continue
        for parsed in csv.reader([ln], delimiter=',', quotechar='"'):
            rows.append([cell.strip() for cell in parsed])

    # 헤더 라인이 여러 번 섞여도 제거
    data_rows = [r for r in rows if [c.replace(" ", "") for c in r] != [h.replace(" ", "") for h in HEADER]]

    # 컬럼 개수 보정
    fixed = []
    for r in data_rows:
        if len(r) < len(HEADER):
            r = r + [""] * (len(HEADER) - len(r))
        else:
            r = r[:len(HEADER)]
        fixed.append(r)

    df = pd.DataFrame(fixed, columns=HEADER)
    return df, HEADER


if __name__ == "__main__":
    ### CONFIG
    OUT_DIR = Path("document_data_3")  # 출력 폴더(원하면 바꾸세요)
    JSON_DIR = OUT_DIR / "json"
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    
    for i, dept in enumerate(DEPARTMENT_LIST):
        for doc_name, doc_form in tqdm(DOCUMENT_FORM_LIST[i].items(), desc=f"{dept} 문서 생성 중"):
            try:    
                form_log = generate_data(
                    target_department=dept, 
                    target_document_name=doc_name, 
                    target_document_form=doc_form, 
                    n=1, 
                    company_info=COMPANY_INFO_PROMPT, 
                    employment_info=EMPLOYMENT_INFO_PROMPT, 
                    model_name="gpt-5-mini", 
                    api_key=WW_GPT_API_KEY
                    )
                all_tables: List[pd.DataFrame] = []
                dfs_by_title: Dict[str, pd.DataFrame] = {}  # 문서별 DF가 필요할 때 사용

                sections = split_sections(form_log)
                for sec in sections:
                    m_title = find_title(sec)
                    if not m_title:
                        # 문서명 라인이 없는 섹션은 건너뜀
                        continue
                    title = m_title.group("title").strip()
                    title_sanitized = sanitize_filename(title)

                    m_table = find_table_marker(sec)
                    if m_table:
                        json_block = sec[m_title.end():m_table.start()]
                        table_text = sec[m_table.end():]
                    else:
                        json_block = sec[m_title.end():]
                        table_text = ""

                    # (2) JSON 파일 저장 - 그대로 저장
                    json_text = extract_json_text(json_block)
                    obj = json.loads(json_text)  # API가 올바른 JSON이라 가정
                    with open(JSON_DIR / f"{title_sanitized}.json", "w", encoding="utf-8") as f:
                        json.dump(obj, f, ensure_ascii=False, indent=2)

                    # (3) 표를 DF로 파싱
                    if table_text.strip():
                        df, HEADER = parse_table_to_df(table_text)
                        # 문서명 컬럼 보정(비어있거나 불일치할 수 있으므로 통일)
                        if "문서명" in df.columns:
                            if df["문서명"].nunique(dropna=False) != 1 or (df["문서명"].astype(str).str.strip() == "").any():
                                df["문서명"] = title
                        else:
                            df["문서명"] = title
                            df = df.reindex(columns=HEADER)
                        all_tables.append(df)
                        dfs_by_title[title] = df.copy()

                # (4) 모든 문서 표를 concat → CSV 저장
                csv_path = None
                if all_tables:
                    all_df = pd.concat(all_tables, ignore_index=True)
                    all_df = all_df.reindex(columns=HEADER)
                    all_df = all_df[all_df.apply(lambda r: any(str(x).strip() for x in r.values), axis=1)]
                    csv_path = OUT_DIR / f"all_tables_{dept}_{doc_name}.csv"
                    OUT_DIR.mkdir(parents=True, exist_ok=True)
                    all_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

                print(f"[완료] JSON 저장 경로: {JSON_DIR.resolve()}")
                if csv_path:
                    print(f"[완료] 통합 CSV: {csv_path.resolve()}")
                else:
                    print("[알림] 표 데이터가 없어 CSV는 생성되지 않았습니다.")
            except Exception as e:
                print(e)
