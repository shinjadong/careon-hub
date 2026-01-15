# Scrapy 통합 완료 - CareOn Hub

> **작업 완료일**: 2026-01-16
> **통합 모듈**: Scrapy + ADB 디바이스 제어

---

## 📋 통합 개요

CareOn Hub에 **Scrapy 웹 스크래핑** 기능이 통합되었습니다. 모바일 디바이스 제어(ADB)와 함께 작동하여 웹 데이터를 수집하고 모바일 디바이스에서 직접 확인할 수 있습니다.

---

## 🎯 주요 기능

### 1. **6개의 프로덕션급 스파이더**

| 스파이더 | 설명 | 타입 | 필수 인자 |
|---------|------|------|----------|
| `naver_news` | 네이버 뉴스 헤드라인 | basic | 없음 |
| `naver_news_detail` | 네이버 뉴스 상세 기사 | basic | article_url |
| `mobile_web` | 모바일 웹 페이지 | playwright | url |
| `instagram_mobile` | Instagram 프로필 | playwright | username |
| `dynamic_content` | 동적 JavaScript 콘텐츠 | playwright | url |
| `api_scraper` | API 응답 인터셉트 | playwright | url, api_pattern |

### 2. **통합 파이프라인**

- ✅ **CareonScraperPipeline**: 데이터 정제 및 검증
- ✅ **ADBIntegrationPipeline**: ADB 디바이스 제어 통합
- ✅ **SupabasePipeline**: Supabase 데이터베이스 자동 저장
- ✅ **JSONFilePipeline**: 로컬 JSON 백업

### 3. **고급 기능**

- 🔄 **User-Agent 로테이션**: 다양한 브라우저/디바이스 에뮬레이션
- 🎭 **Playwright 통합**: JavaScript 렌더링, 무한 스크롤 지원
- 📱 **모바일 에뮬레이션**: iPhone/Android 뷰포트 설정
- 💾 **HTTP 캐싱**: 개발 시 빠른 반복
- ⚡ **Auto-Throttle**: 자동 속도 조절로 서버 부하 최소화

---

## 🚀 사용 방법

### 1️⃣ 기본 스크래핑

```bash
cd backend/app/core/scraper

# 네이버 뉴스
scrapy crawl naver_news

# 모바일 웹
scrapy crawl mobile_web -a url=https://m.naver.com

# Instagram
scrapy crawl instagram_mobile -a username=instagram
```

### 2️⃣ Python에서 사용

```python
from app.core.scraper.scraper_manager import ScraperManager

manager = ScraperManager()
manager.run_spider("naver_news")
```

### 3️⃣ ADB와 통합 사용

```python
from app.core.scraper.scraper_manager import ADBScraperIntegration

integration = ADBScraperIntegration()
result = integration.scrape_and_open_on_device(
    "mobile_web",
    device_serial="RF8NA0ABCDE",
    spider_args={"url": "https://m.naver.com"}
)
```

---

## 📁 프로젝트 구조

```
backend/app/core/scraper/
├── careon_scraper/              # Scrapy 프로젝트
│   ├── spiders/                 # 스파이더
│   │   ├── naver_news.py        # 네이버 뉴스
│   │   ├── mobile_web.py        # 모바일 웹
│   │   └── dynamic_content.py   # 동적 콘텐츠
│   ├── settings.py              # 설정 (ADB/Playwright 통합)
│   ├── pipelines.py             # 파이프라인 (ADB/Supabase)
│   ├── items.py                 # 데이터 모델
│   └── middlewares.py           # 미들웨어
├── scraper_manager.py           # 관리자 클래스
├── scrapy.cfg                   # Scrapy 설정
└── README.md                    # 상세 문서
```

---

## 🔧 설정 및 커스터마이징

### 주요 설정 파일: `careon_scraper/settings.py`

```python
# ADB 디바이스 통합
ADB_ENABLED = True
ADB_DEVICES_PATH = "/path/to/adb"

# Supabase 통합
SUPABASE_ENABLED = True
SUPABASE_TABLE = "scraped_data"

# Playwright 모바일 에뮬레이션
PLAYWRIGHT_CONTEXTS = {
    "default": {
        "viewport": {"width": 412, "height": 915},
        "user_agent": "Mozilla/5.0 (Linux; Android 13...)"
    }
}

# 성능 최적화
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 2
AUTOTHROTTLE_ENABLED = True
```

---

## 💾 데이터 저장

스크래핑한 데이터는 3곳에 자동 저장:

1. **Supabase**: `scraped_data` 테이블
2. **로컬 JSON**: `/home/tlswkehd/projects/careon-hub/backend/data/scraped/`
3. **HTTP 캐시**: `httpcache/` (개발용)

---

## 🧪 테스트

```bash
cd backend
source .venv/bin/activate
python test_scraper.py
```

**테스트 결과**:
```
✅ 총 6개의 스파이더 발견
✅ 모든 스파이더 정상 작동
✅ ADB 통합 준비 완료
✅ Supabase 연동 준비 완료
```

---

## 🔗 통합 시나리오

### 시나리오 1: 뉴스 스크래핑 → 모바일 디바이스 확인

```python
# 1. 뉴스 헤드라인 수집
integration = ADBScraperIntegration()
result = integration.scrape_and_open_on_device(
    "naver_news",
    device_serial="your-device-id"
)

# 2. 수집한 URL을 디바이스에서 자동 열기
# 3. Supabase에 자동 저장
```

### 시나리오 2: 동적 콘텐츠 스크래핑

```bash
# JavaScript로 렌더링되는 SPA 스크래핑
scrapy crawl dynamic_content -a url=https://example.com

# 무한 스크롤 자동 처리
# API 응답 인터셉트
```

### 시나리오 3: Instagram 데이터 수집

```bash
scrapy crawl instagram_mobile -a username=target_user

# 모바일 뷰포트 에뮬레이션
# 공개 프로필 정보 수집
```

---

## 📦 설치된 패키지

```
scrapy>=2.11.0
scrapy-playwright>=0.0.34
scrapy-user-agents>=0.1.1
scrapy-rotating-proxies>=0.6.2
```

---

## 🎓 다음 단계

### 1. FastAPI 라우터 추가

`backend/app/api/scraper.py` 생성:

```python
from fastapi import APIRouter
from app.core.scraper.scraper_manager import ScraperManager

router = APIRouter(prefix="/scraper", tags=["scraper"])

@router.post("/run")
async def run_spider(spider_name: str, url: str = None):
    manager = ScraperManager()
    result = manager.run_spider(
        spider_name,
        spider_args={"url": url} if url else None
    )
    return {"success": result}

@router.get("/spiders")
async def list_spiders():
    manager = ScraperManager()
    return {"spiders": manager.list_spiders()}
```

### 2. 프론트엔드 UI 추가

```typescript
// frontend/src/pages/Scraper.tsx
const ScraperPage = () => {
  const [spiders, setSpiders] = useState([]);

  useEffect(() => {
    fetch('/api/scraper/spiders')
      .then(res => res.json())
      .then(data => setSpiders(data.spiders));
  }, []);

  return (
    <div>
      <h1>웹 스크래핑</h1>
      {/* 스파이더 선택 UI */}
    </div>
  );
};
```

### 3. 스케줄링 (Cron)

```bash
# 매일 오전 9시 뉴스 수집
0 9 * * * cd /path/to/careon-hub/backend/app/core/scraper && scrapy crawl naver_news
```

---

## 📚 참고 문서

- **상세 문서**: `backend/app/core/scraper/README.md`
- **Scrapy 공식**: https://docs.scrapy.org/
- **Playwright 통합**: https://github.com/scrapy-plugins/scrapy-playwright
- **프로젝트 메인**: `/home/tlswkehd/projects/careon-hub/README.md`

---

## ✅ 완료 체크리스트

- [x] Scrapy 프로젝트 생성
- [x] 6개 스파이더 구현 (뉴스, 모바일, 동적)
- [x] ADB 통합 파이프라인
- [x] Supabase 저장 파이프라인
- [x] Playwright 동적 콘텐츠 지원
- [x] User-Agent 로테이션
- [x] 모바일 디바이스 에뮬레이션
- [x] HTTP 캐싱
- [x] 관리자 클래스 (ScraperManager)
- [x] 통합 테스트 스크립트
- [x] 문서 작성

---

**🎉 통합 완료! 이제 CareOn Hub에서 강력한 웹 스크래핑 기능을 사용할 수 있습니다.**
