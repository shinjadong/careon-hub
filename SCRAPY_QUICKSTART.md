# Scrapy 빠른 시작 가이드

## 🚀 즉시 사용하기

### 1. 스파이더 실행

```bash
cd backend/app/core/scraper

# 네이버 뉴스 헤드라인
scrapy crawl naver_news

# 모바일 웹 스크래핑
scrapy crawl mobile_web -a url=https://m.naver.com

# 동적 콘텐츠 (JavaScript)
scrapy crawl dynamic_content -a url=https://example.com
```

### 2. 스파이더 목록 확인

```bash
cd backend/app/core/scraper
scrapy list
```

### 3. 테스트 실행

```bash
cd backend
source .venv/bin/activate
python test_scraper.py
```

## 📋 사용 가능한 스파이더

1. **naver_news** - 네이버 뉴스 헤드라인
2. **naver_news_detail** - 뉴스 기사 상세 (요구: article_url)
3. **mobile_web** - 모바일 웹 페이지 (요구: url)
4. **instagram_mobile** - Instagram 프로필 (요구: username)
5. **dynamic_content** - 동적 콘텐츠 (요구: url)
6. **api_scraper** - API 응답 수집 (요구: url, api_pattern)

## 📁 주요 파일

- **설정**: `backend/app/core/scraper/careon_scraper/settings.py`
- **스파이더**: `backend/app/core/scraper/careon_scraper/spiders/`
- **파이프라인**: `backend/app/core/scraper/careon_scraper/pipelines.py`
- **관리자**: `backend/app/core/scraper/scraper_manager.py`

## 💡 팁

- 데이터는 자동으로 `/backend/data/scraped/` 및 Supabase에 저장
- ADB 통합: `settings.py`에서 `ADB_ENABLED = True`
- Playwright 자동 설치: `playwright install chromium`

상세 문서: `docs/SCRAPY_INTEGRATION.md`
