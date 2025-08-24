# make_tables.py
from typing import Any, Dict, List, Tuple
import pandas as pd

# --- 타입 집합 정의 (원본 로직 그대로) ---
personal_types = {
    'PS_NAME','QT_PHONE','TMI_EMAIL','QT_ADDRESS',
    'DT_YEAR','DT_MONTH','DT_DAY','DT_WEEK','TI_HOUR','TI_MINUTE','TI_SECOND',
    'QT_AGE','LCP_PROVINCE','LCP_COUNTY',
    'CV_OCCUPATION','CV_POSITION','CV_RELATION'
}

confidential_types = {
    'TMI_MODEL','TMI_PROJECT','CV_CURRENCY','CV_TAX','CV_FUNDS'
}

identifier_types = {
    'PS_NAME','QT_PHONE','TMI_EMAIL','QT_ADDRESS','TMI_MODEL','TMI_PROJECT'
}

quasi_identifier_types = {
    'DT_YEAR','DT_MONTH','DT_DAY','DT_WEEK','TI_HOUR','TI_MINUTE','TI_SECOND',
    'QT_AGE','LCP_PROVINCE','LCP_COUNTY',
    'CV_OCCUPATION','CV_POSITION','CV_RELATION',
    'CV_CURRENCY','CV_TAX','CV_FUNDS'
}

interest_types = personal_types | confidential_types | identifier_types | quasi_identifier_types


def run_build_tables(
    span_records: List[Dict[str, Any]],
    domain_code: str,   # 예: set_prefix_code("01")의 "01"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    make_span 결과 리스트(span_records)를 받아,
    '식별자'와 '준식별자'에 해당하는 레코드로 두 개의 DataFrame을 생성해 반환.

    Returns
    -------
    (df_identifier, df_quasi) : Tuple[pd.DataFrame, pd.DataFrame]
    """
    identifier_rows: List[Dict[str, Any]] = []
    quasi_rows: List[Dict[str, Any]] = []

    for item in span_records:
        # item: {"section","field","sentence","id","entities":[{token,entity_type,description,score,span}, ...]}
        for ent in item.get("entities") or []:
            etype = ent.get("entity_type", "")
            if etype not in interest_types:
                continue

            # 개인/기밀 분류 (개인 우선, 아니면 기밀)
            pc = "개인" if etype in personal_types else "기밀"

            row = {
                "도메인":      domain_code,                    # ← "01" 같은 코드 사용
                "단어":        ent.get("token", ""),
                "개인/기밀":   pc,
                "식별/준식별": "식별" if etype in identifier_types else "준식별",
                "정보 유형":   ent.get("description", ""),
                "score":       ent.get("score", ""),
            }

            if etype in identifier_types:
                identifier_rows.append(row)
            else:
                quasi_rows.append(row)

    df_id    = pd.DataFrame(identifier_rows)
    df_quasi = pd.DataFrame(quasi_rows)
    return df_id, df_quasi
