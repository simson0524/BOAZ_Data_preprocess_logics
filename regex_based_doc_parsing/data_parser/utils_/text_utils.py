def split_sentences(text: str) -> List[str]:
    # 🔹 모든 줄바꿈 관련 문자 제거 (\n, \r, 유니코드 줄바꿈 등)
    text = re.sub(r"[\r\n\u2028]+", "", text)

    # 🔹 문장 분리 (마침표 뒤 공백 포함 기준)
    parts = re.split(r'(?<!\d)\.\s+', text)

    sents: List[str] = []
    for i, p in enumerate(parts):
        p = p.strip()
        if not p:
            continue
        if i < len(parts) - 1 or text.endswith('.'):
            p += '.'
        sents.append(p)
    return sents

