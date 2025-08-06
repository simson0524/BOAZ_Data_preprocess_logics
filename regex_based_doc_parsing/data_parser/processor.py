import json
import re
from pathlib import Path
from typing import Dict, List, Type

# 개별 파서 클래스 import (당신이 정의한 파서들)
from parsers.court_parser import CourtParser
from parsers.paper_parser import PaperParser
from parsers.prec_parser import PrecParser


# 파서 타입 매핑
PARSER_REGISTRY: Dict[str, Type] = {
    "PrecService": PrecParser,
    "paper": PaperParser,
    "default": CourtParser,
}

# 파서 선택 로직
def select_parser(data: Dict) -> Type:
    if "PrecService" in data:
        return PARSER_REGISTRY["PrecService"]()
    elif "info" in data and "body" in data:
        return PARSER_REGISTRY["paper"]()
    else:
        return PARSER_REGISTRY["default"]()


# 메인 처리 함수
def process_all(root_folder: Path, output_folder: Path, num_files: int = None, prefix_code: str = "01") -> None:
    output_folder.mkdir(parents=True, exist_ok=True)
    counter = 1  # ID 부여용

    for jp in sorted(root_folder.glob("**/*.json"))[:num_files]:
        data = json.loads(jp.read_text(encoding="utf-8"))

        parser = select_parser(data)
        records = parser.extract_and_split(data)

        for seq, rec in enumerate(records, start=1):
            rec["id"] = f"sample_{prefix_code}_000_{counter:06d}"
            rec["sequence"] = f"{seq:04d}"

            # 🔹 문장 클린업
            rec["sentence"] = re.sub(r"[\r\n\u2028\u2029\u000b\u000c]+", " ", rec["sentence"]).strip()
            rec["sentence"] = re.sub(r"\s{2,}", " ", rec["sentence"])

            counter += 1

        # 저장
        out_path = output_folder / jp.name
        out_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"✔ [{parser.__class__.__name__}] {jp.name}: {len(records)} sentences (up to ID {counter-1})")

    print(f"\n🎉 Done! Total sentences: {counter-1}")
