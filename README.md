# data-extraction

한국어 뉴스 기사 수집 파이프라인. Google News RSS와 AIHub 공공데이터에서 뉴스 본문을 추출한다.

## 구조

```
data_extraction/
├── rss/                        # Google News RSS 수집
│   ├── main.py                 #   진입점 (collect / decode / extract)
│   ├── collect.py              #   RSS 링크 수집
│   ├── decode.py               #   Google URL → 실제 URL 디코딩
│   ├── extract.py              #   본문 추출 (병렬)
│   ├── config.py               #   설정 (경로, 런타임)
│   ├── config.json             #   런타임 설정
│   └── categories.json         #   카테고리 + 키워드 (gitignore)
├── aihub/                      # AIHub 공공데이터 추출
│   ├── main.py                 #   진입점 (extract)
│   ├── extract.py              #   ZIP → JSON 텍스트 추출
│   ├── config.py               #   설정
│   └── config.json             #   데이터셋 스키마 매핑
├── shared/                     # 공용 유틸리티
│   ├── io_utils.py             #   JSON I/O, config 로딩
│   └── notify.py               #   SMTP 이메일 알림
├── utils/                      # 도메인별 유틸리티
│   └── rss/                    #   RSS 피드 파싱, 본문 추출
│       ├── rss_fetcher.py      #     피드 수집 (feedparser)
│       └── article_extractor.py #    본문 추출 (newspaper3k, bs4)
├── .env                        # SMTP 인증 (gitignore)
└── data/                       # 수집 결과 (gitignore)
    ├── rss/
    │   ├── links/              #   collect: RSS 기사 링크
    │   ├── urls/               #   decode: 실제 URL
    │   └── articles/           #   extract: 본문
    ├── aihub/
    │   └── articles/           #   AIHub 추출 본문
    └── all_articles.json       #   전체 병합 (중복 제거)
```

## 설치

```bash
pip install -r requirements.txt
```

## 환경 설정

루트에 `.env` 파일 생성:

```env
# SMTP 알림 (선택)
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TO=your@gmail.com
```

## 사용법

### RSS 뉴스 수집

```bash
cd rss/

# 1단계: RSS 링크 수집
python main.py collect                        # 전체 카테고리 (기본 500건/카테고리)
python main.py collect --categories BUSINESS  # 특정 카테고리만
python main.py collect --target 300           # 총 목표 건수 변경
python main.py collect --additional 200       # 기존 데이터에 200건 추가

# 2단계: URL 디코딩
python main.py decode                         # Google News URL → 실제 URL
python main.py decode --categories BUSINESS

# 3단계: 본문 추출
python main.py extract                        # 기본 5 워커
python main.py extract --workers 10           # 워커 수 변경
```

카테고리별 검색 키워드는 `rss/categories.json`에서 설정 (gitignore 대상):

```json
{
  "카테고리코드": {
    "name": "string — 표시용 한글 이름",
    "keywords": ["string — Google News 검색 키워드 목록"]
  }
}
```

예시:

```json
{
  "BUSINESS": {
    "name": "비즈니스",
    "keywords": ["주식 시장", "환율 달러", "기업 실적"]
  },
  "TECHNOLOGY": {
    "name": "기술",
    "keywords": ["인공지능 AI", "반도체 칩", "클라우드 컴퓨팅"]
  }
}
```

카테고리 코드는 [Google News 토픽 코드](https://news.google.com/)와 일치해야 한다 (WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SCIENCE, SPORTS, HEALTH).

런타임 설정은 `rss/config.json`에서 변경:

```json
{
  "target_per_category": 500,
  "extract_workers": 5,
  "categories": ["BUSINESS", "TECHNOLOGY"],
  "date_range": { "days": 30, "step": 5 }
}
```

### AIHub 데이터 추출

```bash
cd aihub/

python main.py extract
```

다른 AIHub 데이터셋을 사용할 경우 `aihub/config.json`의 스키마만 변경:

```json
{
  "dataset": {
    "id": "017",
    "name": "뉴스 기사 기계독해 데이터",
    "raw_path": "data/017.뉴스 기사 기계독해 데이터/01.데이터",
    "zip_prefixes": ["TS_", "VS_"]
  },
  "schema": {
    "items_key": "data",
    "sub_list_key": "paragraphs",
    "text_key": "context",
    "metadata": {
      "doc_title": "doc_title",
      "category": "doc_class.code"
    }
  }
}
```

`sub_list_key`를 `null`로 설정하면 하위 리스트 없이 아이템에서 직접 텍스트를 추출한다.

## 알림

`.env`에서 SMTP를 활성화하면 다음 상황에서 이메일 알림 발송:

- **오류**: 연속 실패, 레이트 리밋 감지, ZIP 파싱 실패
- **진행**: 50% 도달 시 현황 리포트

## Failsafe

- 네트워크 오류, ZIP 손상 등 개별 실패 시 스킵 후 계속 진행
- 키워드/ZIP 단위로 중간 저장 — 중단 후 재실행 시 이어서 수집
- 연속 실패 감지 시 자동 대기 (레이트 리밋 대응)
- 중복 자동 제거 (링크/URL 기준 + 본문 앞 200자 비교)
