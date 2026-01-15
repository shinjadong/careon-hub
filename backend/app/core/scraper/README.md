# CareOn Scraper - 통합 웹 스크래핑 모듈

ADB 모바일 디바이스 제어와 통합된 Scrapy 기반 웹 스크래핑 시스템

## 구조

```
scraper/
├── careon_scraper/          # Scrapy 프로젝트
│   ├── spiders/             # 스파이더들
│   │   ├── naver_news.py    # 네이버 뉴스 스크래핑
│   │   ├── mobile_web.py    # 모바일 웹 스크래핑
│   │   └── dynamic_content.py  # 동적 콘텐츠 스크래핑
│   ├── settings.py          # Scrapy 설정
│   ├── pipelines.py         # 데이터 파이프라인 (ADB/Supabase 통합)
│   ├── items.py             # 데이터 모델
│   └── middlewares.py       # 커스텀 미들웨어
├── scraper_manager.py       # 스크래핑 관리자
├── scrapy.cfg               # Scrapy 설정 파일
└── README.md                # 이 문서
```

## 주요 기능

### 1. 다양한 스파이더

- **naver_news**: 네이버 뉴스 헤드라인 및 랭킹 뉴스
- **naver_news_detail**: 네이버 뉴스 기사 상세 내용
- **mobile_web**: 모바일 웹 페이지 (Playwright 사용)
- **instagram_mobile**: Instagram 모바일 프로필
- **dynamic_content**: JavaScript 동적 콘텐츠 (무한 스크롤 지원)
- **api_scraper**: API 응답 인터셉트 및 수집

### 2. 통합 파이프라인

- **CareonScraperPipeline**: 데이터 정제 및 검증
- **ADBIntegrationPipeline**: ADB 디바이스 제어 통합
- **SupabasePipeline**: Supabase 데이터베이스 저장
- **JSONFilePipeline**: 로컬 JSON 백업

### 3. 고급 기능

- **User-Agent 로테이션**: 다양한 브라우저/디바이스 에뮬레이션
- **Playwright 통합**: 동적 콘텐츠 렌더링
- **모바일 디바이스 에뮬레이션**: 모바일 뷰포트 설정
- **HTTP 캐싱**: 개발 시 빠른 반복
- **Auto-Throttle**: 자동 속도 조절

## 사용 방법

### 1. Playwright 브라우저 설치

```bash
source .venv/bin/activate
playwright install chromium
```

### 2. 스파이더 실행

```bash
cd backend/app/core/scraper

# 네이버 뉴스 스크래핑
scrapy crawl naver_news

# 모바일 웹 스크래핑
scrapy crawl mobile_web -a url=https://m.naver.com

# Instagram 프로필
scrapy crawl instagram_mobile -a username=instagram

# 동적 콘텐츠
scrapy crawl dynamic_content -a url=https://example.com
```

### 3. Python에서 사용

```python
from scraper_manager import ScraperManager, ADBScraperIntegration

# 기본 스크래핑
manager = ScraperManager()
manager.run_spider("naver_news")

# ADB 통합
integration = ADBScraperIntegration()
result = integration.scrape_and_open_on_device(
    "mobile_web",
    spider_args={"url": "https://m.naver.com"}
)
```

### 4. FastAPI에서 사용

```python
from fastapi import APIRouter
from scraper_manager import ScraperManager

router = APIRouter()

@router.post("/scrape")
async def scrape(spider_name: str, url: str = None):
    manager = ScraperManager()
    result = manager.run_spider(
        spider_name,
        spider_args={"url": url} if url else None
    )
    return {"success": result}
```

## 설정

### 주요 설정 (settings.py)

```python
# User-Agent 로테이션
"scrapy_user_agents.middlewares.RandomUserAgentMiddleware": 400

# Playwright 동적 콘텐츠
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}

# 모바일 에뮬레이션
PLAYWRIGHT_CONTEXTS = {
    "default": {
        "viewport": {"width": 412, "height": 915},
        "user_agent": "Mozilla/5.0 (Linux; Android 13...)"
    }
}

# ADB 통합
ADB_ENABLED = True
ADB_DEVICES_PATH = "/path/to/adb/module"

# Supabase 통합
SUPABASE_ENABLED = True
SUPABASE_TABLE = "scraped_data"
```

## ADB 통합

스크래핑한 데이터를 모바일 디바이스에서 직접 확인:

1. **자동 URL 열기**: 스크래핑한 URL을 디바이스에서 자동으로 열기
2. **디바이스 메타데이터**: 스크래핑 결과에 디바이스 정보 추가
3. **세션 관리**: ADB 연결 자동 관리

```python
# 스크래핑 후 디바이스에서 열기
integration = ADBScraperIntegration()
result = integration.scrape_and_open_on_device(
    "mobile_web",
    device_serial="RF8NA0ABCDE",  # 특정 디바이스
    spider_args={"url": "https://example.com"}
)
```

## 데이터 출력

스크래핑한 데이터는 다음 위치에 저장:

1. **Supabase**: `scraped_data` 테이블
2. **로컬 JSON**: `/home/tlswkehd/projects/careon-hub/backend/data/scraped/`
3. **HTTP 캐시**: `httpcache/` (개발용)

## 스파이더 추가

새 스파이더 생성:

```bash
scrapy genspider myspider example.com
```

Playwright 사용 예시:

```python
def start_requests(self):
    yield scrapy.Request(
        url,
        meta={
            "playwright": True,
            "playwright_include_page": True,
            "playwright_page_methods": [
                ("wait_for_load_state", "networkidle"),
            ],
        }
    )
```

## 문제 해결

### Playwright 에러

```bash
# 브라우저 재설치
playwright install --force chromium
```

### ADB 연결 실패

```python
# settings.py에서 ADB 비활성화
ADB_ENABLED = False
```

### 메모리 부족

```python
# settings.py에서 동시 요청 수 줄이기
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 1
```

## 참고 문서

- [Scrapy 공식 문서](https://docs.scrapy.org/)
- [Scrapy-Playwright](https://github.com/scrapy-plugins/scrapy-playwright)
- [CareOn Hub README](../../../../../README.md)
