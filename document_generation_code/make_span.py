# make_span.py
from typing import Any, Dict, List

def _merge_bi(raw_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """토큰 단위 BIO 엔티티 목록을 B/I 기준으로 병합해 스팬 단위 엔티티로 변환."""
    grouped: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None

    for ent in raw_entities:
        bio = ent.get("bio_label", "O")
        ent_type = ent.get("entity_type", "O")

        # 1) B- 로 시작하면 새로운 그룹 오픈
        if isinstance(bio, str) and bio.startswith("B-"):
            if current:
                grouped.append(current)
            current = {
                "bio_label":   bio,
                "entity_type": ent_type,
                "description": ent.get("description", ent_type),
                "tokens":      [ent.get("token", "")],
                "scores":      [float(ent.get("score", 0.0))],
                "span_start":  int(ent.get("span", [0, 0])[0]),
                "span_end":    int(ent.get("span", [0, 0])[1]),
            }

        # 2) I- 이고 현재 그룹이 동일 타입이면 이어 붙임
        elif isinstance(bio, str) and bio.startswith("I-") and current and ent_type == current["entity_type"]:
            current["tokens"].append(ent.get("token", ""))
            current["scores"].append(float(ent.get("score", 0.0)))
            current["span_end"] = int(ent.get("span", [0, 0])[1])

        # 3) 그 외(O 이거나, 불일치 I-)
        else:
            if current:
                grouped.append(current)
                current = None

            if bio == "O":
                grouped.append({
                    "bio_label":   "O",
                    "entity_type": "O",
                    "description": ent.get("description", "O"),
                    "tokens":      [ent.get("token", "")],
                    "scores":      [float(ent.get("score", 0.0))],
                    "span_start":  int(ent.get("span", [0, 0])[0]),
                    "span_end":    int(ent.get("span", [0, 0])[1]),
                })

            # I-인데 조건 불충족이면 스킵(정책상 버림). 필요시 별도 처리 가능.

    if current:
        grouped.append(current)

    # 최종 출력 형태로 변환
    out: List[Dict[str, Any]] = []
    for grp in grouped:
        token_text = "".join(grp["tokens"])
        avg_score  = round(sum(grp["scores"]) / max(1, len(grp["scores"])), 3)
        out.append({
            "token":       token_text,
            "entity_type": grp["entity_type"],
            "description": grp["description"],
            "score":       avg_score,
            "span":        [grp["span_start"], grp["span_end"]],
        })
    return out


def run_merge_spans(ner_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    NER 모듈 결과 리스트(문장 단위, 토큰 엔티티 포함)를 입력받아
    B/I 병합을 적용한 리스트를 반환.

    입력 원소 예:
      { "section":..., "field":..., "sentence":..., "id":..., "entities":[{token,bio_label,entity_type,score,span}...] }

    반환 원소 예(entities가 스팬 단위로 대체됨):
      { "section":..., "field":..., "sentence":..., "id":..., "entities":[{token,entity_type,description,score,span}...] }
    """
    merged_records: List[Dict[str, Any]] = []

    for item in ner_records:
        raw_entities: List[Dict[str, Any]] = item.get("entities", []) or []
        merged_entities = _merge_bi(raw_entities)

        # 원본 필드 유지 + entities만 병합 결과로 교체
        merged_item = {
            "section":  item.get("section", ""),
            "field":    item.get("field", ""),
            "sentence": item.get("sentence", ""),
            "id":       item.get("id", ""),
            "entities": merged_entities,
        }
        merged_records.append(merged_item)

    return merged_records
