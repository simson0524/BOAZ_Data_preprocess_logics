# BOAZ_Data_preprocess_logics\regex_based_doc_parsing\pii_detector\detectors\address_detector.py

import re
from typing import List, Dict
from detectors.base import BaseDetector  # base.py에 정의된 추상클래스

class AddressDetector:
    def __init__(self, sido_list: List[str], sigungu_list: List[str], dong_list: List[str]):
        self.sido_pattern = re.compile(f"({'|'.join(map(re.escape, sido_list))})")
        self.sigungu_pattern = re.compile(f"({'|'.join(map(re.escape, sigungu_list))})")
        self.dong_pattern = re.compile(f"({'|'.join(map(re.escape, dong_list))})")
        self.apt_pattern = re.compile(r"[가-힣]{2,20}(아파트|오피스텔|빌라|타워|센트럴|팰리스|스퀘어|리버|하우스|레지던스)")
        self.ho_pattern = re.compile(r"\d+동\s*\d+호|\d+호|\d+층")

        # 전체 주소 블록 패턴
        self.address_block_pattern = re.compile(
            f"({self.sido_pattern.pattern})\\s*"
            f"({self.sigungu_pattern.pattern})\\s*"
            f"({self.dong_pattern.pattern})?\\s*"
            f"({self.apt_pattern.pattern})?\\s*"
            f"({self.ho_pattern.pattern})?"
        )

    def detect(self, text: str) -> List[Dict]:
        results = []

        # ✅ 1. 전체 주소 블록 탐지 반복
        for match in self.address_block_pattern.finditer(text):
            matched_text = match.group().strip()
            start, end = match.start(), match.end()

            if matched_text:
                score = self.score(matched_text)
                results.append({
                    "start": start,
                    "end": end,
                    "label": "address_block",
                    "match": matched_text,
                    "score": score
                })

                # ✅ 2. 아파트 + ho/층 패턴을 이 블록 안에서 다시 탐지
                apt_match = self.apt_pattern.search(text, start, end)
                if apt_match:
                    apt_end = apt_match.end()
                    ho_match = self.ho_pattern.match(text, pos=apt_end)
                    if ho_match and ho_match.end() <= end:  # ho가 블록 범위 내에 있을 때만
                        results.append({
                            "start": ho_match.start(),
                            "end": ho_match.end(),
                            "label": "ho",
                            "match": ho_match.group(),
                            "score": None
                        })

        # ✅ 3. 개별 주소 성분도 계속 탐지
        for pattern, label in [
            (self.sido_pattern, "sido"),
            (self.sigungu_pattern, "sigungu"),
            (self.dong_pattern, "dong"),
            (self.apt_pattern, "apartment"),
        ]:
            for m in pattern.finditer(text):
                results.append({
                    "start": m.start(),
                    "end": m.end(),
                    "label": label,
                    "match": m.group(),
                    "score": None
                })

        return results


    def score(self, match: str) -> float:
        address = match.strip()
        has_sido = bool(self.sido_pattern.search(address))
        has_sigungu = bool(self.sigungu_pattern.search(address))
        has_dong = bool(self.dong_pattern.search(address))
        has_apt = bool(self.apt_pattern.search(address))
        has_ho = bool(self.ho_pattern.search(address))

        # 점수 기준
        if has_sido and has_sigungu and has_apt and has_ho:
            return 1.0
        if has_sido and has_sigungu and has_apt:
            return 0.8
        if has_sigungu and has_apt:
            return 0.6
        if has_dong and has_apt:
            return 0.6
        if has_sido and has_sigungu and has_dong:
            return 0.5
        if has_sido and has_sigungu:
            return 0.3
        if has_sido:
            return 0.2
        return None
