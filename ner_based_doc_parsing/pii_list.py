import os, glob, json
import pandas as pd

def extract_entities(ner_results, personal_types=None, confidential_types=None, identifier_types=None, quasi_identifier_types=None):
    """
    NER 결과(list[dict])를 받아 DataFrame 반환
    """
    personal_types      = personal_types or {"PS_NAME","DT_YEAR","DT_MONTH","DT_DAY","DT_WEEK","QT_AGE"}
    confidential_types  = confidential_types or set()
    identifier_types    = identifier_types or set()
    quasi_identifier_types = quasi_identifier_types or set()
    interest_types = personal_types | confidential_types | identifier_types | quasi_identifier_types

    records = []
    for item in ner_results:
        for ent in item.get("entities") or []:
            etype = ent.get("entity_type","")
            if etype not in interest_types: continue
            pc = "개인" if etype in personal_types else "기밀"
            iq = "식별" if etype in identifier_types else "준식별"
            records.append({
                "단어": ent.get("token",""),
                "문서명":"",
                "부서명":"",
                "단어유형": ent.get("description",""),
                "구분": pc,
            })
    return pd.DataFrame(records)