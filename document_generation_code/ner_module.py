# ner_module.py
from __future__ import annotations
import os, time
from typing import Any, Dict, List
from huggingface_hub import InferenceClient
from transformers import AutoTokenizer

# 너가 준 labels / ner_code 그대로 붙여넣기
labels = [ ... ]           # 너무 길어 생략. 네 리스트 그대로 사용
ner_code = { ... }         # 네 딕셔너리 그대로 사용
label2id = {label: i for i, label in enumerate(labels)}
id2label = {i: label for label, i in label2id.items()}

def run_kpf_ner_on_records(
    records: List[Dict[str, Any]],
    model_name: str = "KPF/KPF-bert-ner",
    max_len: int = 510,
    stride: int = 50,
    max_retries: int = 3,
    wait_sec: int = 30,
) -> List[Dict[str, Any]]:
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("환경변수 HF_TOKEN 이 설정되어 있지 않습니다.")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    client = InferenceClient(provider="auto", api_key=token)

    def chunk_text_with_offsets(text: str):
        enc = tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)
        ids, offsets = enc["input_ids"], enc["offset_mapping"]
        chunks, start = [], 0
        while start < len(ids):
            end = min(len(ids), start + max_len)
            char_s, char_e = offsets[start][0], offsets[end-1][1]
            chunks.append((text[char_s:char_e], char_s))
            if end == len(ids): break
            start = end - stride
        return chunks

    def safe_inference(text: str) -> List[Dict[str, Any]]:
        for attempt in range(1, max_retries + 1):
            try:
                return client.token_classification(text, model=model_name)
            except Exception as e:
                if "500" in str(e) and attempt < max_retries:
                    print(f"⚠️ 서버 500 — {wait_sec}s 대기 후 재시도 ({attempt}/{max_retries})")
                    time.sleep(wait_sec); continue
                print(f"❌ 추론 실패: {e}")
                return []
        return []

    outputs: List[Dict[str, Any]] = []
    for item in records:
        sent    = item.get("sentence", "")
        section = item.get("section", "")
        field   = item.get("field", "")
        orig_id = item.get("id", "")

        enc_len = len(tokenizer.encode(sent, add_special_tokens=False))
        chunks = [(sent, 0)] if enc_len <= max_len else chunk_text_with_offsets(sent)

        for chunk_text, offset in chunks:
            toks = safe_inference(chunk_text)
            if not toks:
                print("⚠️ 추론 실패 청크 스킵"); continue

            entities = []
            for ent in toks:
                try:
                    _, idx_str = ent["entity_group"].split("_")
                    bio_lbl = id2label.get(int(idx_str), "O")
                except Exception:
                    bio_lbl = ent.get("entity_group", "O")
                ent_type = bio_lbl.split("-", 1)[-1] if "-" in bio_lbl else bio_lbl
                entities.append({
                    "token":       str(ent.get("word","")).lstrip("##"),
                    "bio_label":   bio_lbl,
                    "entity_type": ent_type,
                    "description": ner_code.get(ent_type, ent_type),
                    "score":       round(float(ent.get("score", 0.0)), 3),
                    "span":        [int(ent.get("start",0)+offset), int(ent.get("end",0)+offset)],
                })

            outputs.append({
                "section":  section,
                "field":    field,
                "sentence": chunk_text,
                "id":       orig_id,
                "entities": entities
            })
    return outputs

