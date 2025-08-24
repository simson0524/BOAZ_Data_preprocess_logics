# sentence_split.py
from pathlib import Path
from typing import Any, Dict, List
import re, json

_PREFIX_CODE: str | None = None  # 외부에서 set_prefix_code(...)로 설정

def set_prefix_code(code: str) -> None:
    """접두 코드(ex. '01')를 외부에서 설정."""
    global _PREFIX_CODE
    _PREFIX_CODE = code

def run_sentence_split_all(root_folder: Path, num_files: int | None = None) -> List[Dict[str, Any]]:
    """폴더의 JSON들을 문장 단위 레코드로 평탄화해 리스트로 반환."""
    if not _PREFIX_CODE:
        raise RuntimeError("접두 코드가 설정되지 않았습니다. set_prefix_code('01')을 먼저 호출하세요.")

    def split_sentences(text: str) -> List[str]:
        text = re.sub(r"[\r\n\u2028]+", "", text)
        parts = re.split(r'(?<!\d)\.\s+', text)
        out: List[str] = []
        for i, p in enumerate(parts):
            p = p.strip()
            if not p: continue
            if i < len(parts) - 1 or text.endswith('.'):
                p += '.'
            out.append(p)
        return out

    def extract_and_split(data: Dict[str, Any]) -> List[Dict[str, str]]:
        section_field_map = {
            "info": ["caseField","detailField","caseNm","courtNm","caseNo","relateLaword","qotatPrcdnt"],
            "concerned": ["acusr","dedat"],
            "org": ["orgJdgmnCourtNm","orgJdgmnAdjuDe","orgJdgmnCaseNo"],
            "disposal": ["disposalform","disposalcontent"],
            "mentionedItems": ["rqestObjet"],
            "assrs": ["acusrAssrs","dedatAssrs"],
            "facts": ["bsisFacts"],
            "dcss": ["courtDcss"],
            "close": ["cnclsns"],
        }
        out: List[Dict[str,str]] = []
        for section, fields in section_field_map.items():
            sd = data.get(section, {})
            for field in fields:
                raw = sd.get(field, [])
                items = [raw] if isinstance(raw, str) else raw if isinstance(raw, list) else []
                for txt in items:
                    if not isinstance(txt, str) or not txt.strip():
                        continue
                    for sent in split_sentences(txt):
                        out.append({"section": section, "field": field, "sentence": sent})
        return out

    def extract_and_split_from_paper_v2(data: Dict[str, Any]) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        for section, fields in {"info":["title"], "body":["body"]}.items():
            nested = data.get(section, {})
            for field in fields:
                value = nested.get(field)
                if isinstance(value, str) and value.strip():
                    for sent in split_sentences(value):
                        out.append({"section": section, "field": field, "sentence": sent})
        return out

    def extract_and_split_from_precservice(data: Dict[str, Any]) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        prec = data.get("PrecService", {})
        for section, key in {"판시사항":"판시사항","참조판례":"참조판례","판결요지":"판결요지","참조조문":"참조조문","판례내용":"판례내용"}.items():
            txt = prec.get(key, "")
            if isinstance(txt, str) and txt.strip():
                txt = txt.replace("<br/>", " ")
                for sent in split_sentences(txt):
                    out.append({"section": section, "field": key, "sentence": sent})
        return out

    all_records: List[Dict[str, Any]] = []
    counter = 1

    for jp in sorted(Path(root_folder).glob("**/*.json"))[:num_files]:
        data = json.loads(jp.read_text(encoding="utf-8"))
        if "PrecService" in data:
            parser = extract_and_split_from_precservice
        elif "info" in data and "body" in data:
            parser = extract_and_split_from_paper_v2
        else:
            parser = extract_and_split

        records = parser(data)
        for seq, rec in enumerate(records, start=1):
            rec["id"] = f"sample_{_PREFIX_CODE}_000_{counter:06d}"
            rec["sequence"] = f"{seq:04d}"
            rec["sentence"] = re.sub(r"[\r\n\u2028\u2029\u000b\u000c]+", " ", rec["sentence"]).strip()
            rec["sentence"] = re.sub(r"\s{2,}", " ", rec["sentence"])
            counter += 1
        all_records.extend(records)

    return all_records
