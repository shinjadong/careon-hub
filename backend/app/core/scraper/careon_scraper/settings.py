# Scrapy settings for careon_scraper project
#
# CareOn Hub - 통합 CCTV 트래픽 관리 시스템
# AI 기반 트래픽 자동화 + 웹 스크래핑 통합

BOT_NAME = "careon_scraper"

SPIDER_MODULES = ["careon_scraper.spiders"]
NEWSPIDER_MODULE = "careon_scraper.spiders"

ADDONS = {}

# ============================================================================
# USER AGENT & BROWSER SETTINGS
# ============================================================================

# 랜덤 User-Agent 사용 (모바일/데스크톱 혼합)
USER_AGENT = "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36"

# Obey robots.txt rules (필요시 False로 변경)
ROBOTSTXT_OBEY = False

# ============================================================================
# CONCURRENCY & PERFORMANCE
# ============================================================================

CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True

# AutoThrottle 활성화 (자동 속도 조절)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# ============================================================================
# COOKIES & HEADERS
# ============================================================================

COOKIES_ENABLED = True

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
}

# ============================================================================
# MIDDLEWARES
# ============================================================================

DOWNLOADER_MIDDLEWARES = {
    # User-Agent 로테이션
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "scrapy_user_agents.middlewares.RandomUserAgentMiddleware": 400,

    # 프록시 로테이션 (필요시 활성화)
    # "rotating_proxies.middlewares.RotatingProxyMiddleware": 610,
    # "rotating_proxies.middlewares.BanDetectionMiddleware": 620,

    # Playwright 지원 (동적 콘텐츠)
    "scrapy_playwright.middleware.ScrapyPlaywrightDownloadHandler": 800,
}

# ============================================================================
# PLAYWRIGHT SETTINGS (동적 콘텐츠 스크래핑)
# ============================================================================

DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "args": [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
    ],
}

# 모바일 디바이스 에뮬레이션 (선택사항)
PLAYWRIGHT_CONTEXTS = {
    "default": {
        "viewport": {"width": 412, "height": 915},
        "user_agent": "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36",
    }
}

# ============================================================================
# ITEM PIPELINES
# ============================================================================

ITEM_PIPELINES = {
    "careon_scraper.pipelines.CareonScraperPipeline": 300,
    "careon_scraper.pipelines.ADBIntegrationPipeline": 400,
    "careon_scraper.pipelines.SupabasePipeline": 500,
}

# ============================================================================
# HTTP CACHE (개발용)
# ============================================================================

HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [403, 404, 500, 503]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# CUSTOM SETTINGS (CareOn Hub Integration)
# ============================================================================

# ADB 디바이스 통합
ADB_ENABLED = True
ADB_DEVICES_PATH = "/home/tlswkehd/projects/careon-hub/backend/app/core/adb"

# Supabase 통합
SUPABASE_ENABLED = True
SUPABASE_TABLE = "scraped_data"

# 데이터 저장 경로
DATA_OUTPUT_PATH = "/home/tlswkehd/projects/careon-hub/backend/data/scraped"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
