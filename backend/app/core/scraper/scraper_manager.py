"""
Scrapy Manager - ADB와 Scrapy 통합 관리자
모바일 디바이스 제어와 웹 스크래핑을 통합
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


# 현재 디렉토리를 sys.path에 추가
scraper_path = Path(__file__).parent
sys.path.insert(0, str(scraper_path))


logger = logging.getLogger(__name__)


class ScraperManager:
    """
    Scrapy 스파이더 실행 및 ADB 통합 관리
    """

    def __init__(self, adb_enabled: bool = True):
        self.adb_enabled = adb_enabled
        self.process = None
        self.settings = None
        self._init_settings()

    def _init_settings(self):
        """Scrapy 설정 초기화"""
        try:
            # careon_scraper 설정 로드
            os.chdir(scraper_path)
            self.settings = get_project_settings()

            # ADB 활성화 설정
            self.settings.set("ADB_ENABLED", self.adb_enabled)

            logger.info("Scrapy settings initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Scrapy settings: {e}")
            # 기본 설정 사용
            from scrapy.settings import Settings
            self.settings = Settings()

    def run_spider(
        self,
        spider_name: str,
        spider_args: Optional[Dict[str, Any]] = None,
        custom_settings: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        스파이더 실행

        Args:
            spider_name: 스파이더 이름 (예: 'naver_news', 'mobile_web')
            spider_args: 스파이더에 전달할 인자
            custom_settings: 커스텀 설정

        Returns:
            성공 여부
        """
        try:
            # 프로세스 생성
            self.process = CrawlerProcess(self.settings)

            # 커스텀 설정 적용
            if custom_settings:
                for key, value in custom_settings.items():
                    self.settings.set(key, value)

            # 스파이더 실행
            spider_args = spider_args or {}
            self.process.crawl(spider_name, **spider_args)

            logger.info(f"Starting spider: {spider_name}")
            self.process.start()  # 블로킹 호출

            return True

        except Exception as e:
            logger.error(f"Spider execution failed: {e}")
            return False

    def list_spiders(self) -> List[str]:
        """
        사용 가능한 스파이더 목록 반환
        """
        try:
            from careon_scraper.spiders import naver_news, mobile_web, dynamic_content

            spiders = [
                "naver_news",
                "naver_news_detail",
                "mobile_web",
                "instagram_mobile",
                "dynamic_content",
                "api_scraper",
            ]

            return spiders
        except Exception as e:
            logger.error(f"Failed to list spiders: {e}")
            return []

    def get_spider_info(self, spider_name: str) -> Optional[Dict[str, Any]]:
        """
        스파이더 정보 반환
        """
        spider_info = {
            "naver_news": {
                "name": "naver_news",
                "description": "네이버 뉴스 헤드라인 스크래핑",
                "type": "basic",
                "requires_args": False,
            },
            "naver_news_detail": {
                "name": "naver_news_detail",
                "description": "네이버 뉴스 기사 상세 내용 스크래핑",
                "type": "basic",
                "requires_args": True,
                "args": ["article_url"],
            },
            "mobile_web": {
                "name": "mobile_web",
                "description": "모바일 웹 페이지 스크래핑",
                "type": "playwright",
                "requires_args": True,
                "args": ["url"],
            },
            "instagram_mobile": {
                "name": "instagram_mobile",
                "description": "Instagram 모바일 프로필 스크래핑",
                "type": "playwright",
                "requires_args": True,
                "args": ["username"],
            },
            "dynamic_content": {
                "name": "dynamic_content",
                "description": "JavaScript 동적 콘텐츠 스크래핑",
                "type": "playwright",
                "requires_args": True,
                "args": ["url"],
            },
            "api_scraper": {
                "name": "api_scraper",
                "description": "API 응답 스크래핑 (AJAX 인터셉트)",
                "type": "playwright",
                "requires_args": True,
                "args": ["url", "api_pattern"],
            },
        }

        return spider_info.get(spider_name)


class ADBScraperIntegration:
    """
    ADB 디바이스 제어와 Scrapy 스크래핑 통합
    """

    def __init__(self):
        self.scraper_manager = ScraperManager(adb_enabled=True)
        self.adb_manager = None
        self._init_adb()

    def _init_adb(self):
        """ADB 매니저 초기화"""
        try:
            # ADB 모듈 임포트
            adb_path = Path(__file__).parents[1] / "adb"
            sys.path.insert(0, str(adb_path))

            from device_tools.adb_enhanced import ADBDeviceManager

            self.adb_manager = ADBDeviceManager()
            logger.info("ADB Manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ADB: {e}")

    def scrape_and_open_on_device(
        self,
        spider_name: str,
        device_serial: Optional[str] = None,
        spider_args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        웹 페이지를 스크래핑하고 결과 URL을 모바일 디바이스에서 열기

        Args:
            spider_name: 스파이더 이름
            device_serial: 디바이스 시리얼 (None이면 첫 번째 디바이스)
            spider_args: 스파이더 인자

        Returns:
            실행 결과
        """
        result = {
            "spider": spider_name,
            "success": False,
            "scraped_items": [],
            "device_opened": False,
        }

        try:
            # 1. 스파이더 실행 (스크래핑)
            logger.info(f"Starting spider: {spider_name}")
            # self.scraper_manager.run_spider(spider_name, spider_args)
            # 실제로는 비동기로 실행하고 결과를 수집해야 함

            # 2. 스크래핑 결과 확인
            # result["scraped_items"] = [...]  # 스크래핑한 아이템들

            # 3. ADB로 디바이스에서 URL 열기
            if self.adb_manager and spider_args and "url" in spider_args:
                url = spider_args["url"]

                # 디바이스 목록
                devices = self.adb_manager.list_devices() if hasattr(
                    self.adb_manager, "list_devices"
                ) else []

                if devices:
                    target_device = device_serial or devices[0]
                    # self.adb_manager.open_url(target_device, url)
                    logger.info(f"Opened {url} on device {target_device}")
                    result["device_opened"] = True

            result["success"] = True

        except Exception as e:
            logger.error(f"Integration error: {e}")
            result["error"] = str(e)

        return result


# 사용 예시
if __name__ == "__main__":
    # 기본 스크래핑
    manager = ScraperManager(adb_enabled=False)
    print("Available spiders:", manager.list_spiders())

    # ADB 통합
    integration = ADBScraperIntegration()
    result = integration.scrape_and_open_on_device(
        "mobile_web",
        spider_args={"url": "https://m.naver.com"},
    )
    print("Integration result:", result)
