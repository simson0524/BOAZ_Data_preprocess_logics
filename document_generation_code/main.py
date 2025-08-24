# main.py
import os
from pathlib import Path

from sentence_split import set_prefix_code, get_prefix_code, run_sentence_split_all
from ner_module import run_kpf_ner_on_records
from make_span import run_merge_spans
from make_tables import run_build_tables

if __name__ == "__main__":
    # (A) 접두 코드 설정
    set_prefix_code("01")  # 도메인 코드로도 재사용할 값        #**************도메인 넘버

    # (B) 1단계: 폴더 → 문장 레코드 리스트
    split_record = run_sentence_split_all(
        root_folder=Path(r"C:\data\input"),                 #**************최초폴더경로
        num_files=None
    )
    print(f"[split] records: {len(split_record)}")

    # (C) 2단계: 문장 레코드 리스트 → NER 결과 리스트
    os.environ["HF_TOKEN"] = os.environ.get("HF_TOKEN", "hf_...your-token...")
    ner_record = run_kpf_ner_on_records(split_record)
    print(f"[ner] outputs: {len(ner_record)}")

    # (D) 3단계: NER 결과 리스트 → B/I 병합 리스트
    span_record = run_merge_spans(ner_record)
    print(f"[span] outputs: {len(span_record)}")

    # (E) 4단계: 스팬 리스트 → 테이블(DataFrame) 두 개
    domain_code = get_prefix_code()           # ← "01" 값 사용
    df_id, df_quasi = run_build_tables(span_record, domain_code=domain_code)
    print(f"[tables] df_id: {df_id.shape}, df_quasi: {df_quasi.shape}")

    # 여기서 df_id/df_quasi 를 다음 단계로 바로 넘겨 쓰면 됩니다.
    # (원하면 CSV 저장도 가능: df_id.to_csv(...), df_quasi.to_csv(...))
