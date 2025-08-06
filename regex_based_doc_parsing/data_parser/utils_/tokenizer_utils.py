
def chunk_text_with_offsets(text: str) -> List[Tuple[str, int]]:
    enc = tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)
    ids = enc["input_ids"]
    offsets = enc["offset_mapping"]
    chunks: List[Tuple[str,int]] = []
    start = 0
    while start < len(ids):
        end = min(len(ids), start + MAX_LEN)
        char_s = offsets[start][0]
        char_e = offsets[end-1][1]
        chunks.append((text[char_s:char_e], char_s))
        if end == len(ids):
            break
        start = end - STRIDE
    return chunks