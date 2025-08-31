#pip install huggingface_hub
#pip install transformers
from ner_module import run_ner
from pii_list import extract_entities

sentence = "레드재혁 나라를 구할 남자 26세"

if __name__ == "__main__":
    # (1) NER 수행 (JSON 저장 없이 메모리 반환)
    ner_results = run_ner(sentence)  # 파일별로 sentence에 대해 ner실행 + BI결합

    # (2) 후처리 → DataFrame 변환
    ner_dictionary = extract_entities(ner_results)  #결합된 BI 목록중 (이름 나이 날짜만 남기기)

    print(ner_dictionary)
    # 필요시 저장