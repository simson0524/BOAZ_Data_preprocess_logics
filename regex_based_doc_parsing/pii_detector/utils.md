

pii_detector/
│
├── detectors/
│   ├── base.py                 # 공통 Detector 추상 클래스
│   ├── name_detector.py        # 이름 탐지기
│   ├── address_detector.py     # 주소 탐지기
│   ├── birth_detector.py       # 생년월일 탐지기
│   └── ...                     # 성별, 전화번호 등
│
├── patterns/
│   ├── names.py                # sn1, nn1, nn2
│   ├── locations.py            # sido_list, sigungu_list, ...
│   └── ...
│
├── scorer/
│   └── score_registry.py       # 점수 계산기
│
├── main.py                     # 메인 실행 로직
└── utils.py                    # 공통 유틸 함수