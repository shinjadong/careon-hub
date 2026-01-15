"""
모바일 웹 페이지 스크래핑
모바일 디바이스 에뮬레이션을 통한 데이터 수집
"""

import scrapy
from scrapy.http import Response
from typing import Iterator, Dict, Any


class MobileWebSpider(scrapy.Spider):
    """
    모바일 최적화 웹사이트 스크래핑
    Playwright를 사용한 동적 콘텐츠 처리
    """
    name = "mobile_web"
    allowed_domains = []  # 도메인 제한 없음

    custom_settings = {
        "PLAYWRIGHT_CONTEXTS": {
            "default": {
                "viewport": {"width": 375, "height": 812},  # iPhone 13 크기
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
                              "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 "
                              "Mobile/15E148 Safari/604.1",
            }
        },
        "DOWNLOAD_DELAY": 3,
    }

    def __init__(self, url: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if url:
            self.start_urls = [url]
        else:
            self.start_urls = ["https://m.naver.com"]

    def start_requests(self):
        """Playwright를 사용하여 요청 시작"""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        # 페이지 로드 대기
                        ("wait_for_load_state", "networkidle"),
                    ],
                }
            )

    async def parse(self, response: Response) -> Iterator[Dict[str, Any]]:
        """모바일 페이지 파싱"""
        page = response.meta.get("playwright_page")

        # 메타 정보 수집
        yield {
            "type": "mobile_page",
            "url": response.url,
            "title": response.css("title::text").get(),
            "viewport_width": 375,
            "viewport_height": 812,
            "links_count": len(response.css("a::attr(href)").getall()),
            "images_count": len(response.css("img::attr(src)").getall()),
            "source": "mobile_web",
        }

        # 페이지 스크린샷 (선택사항)
        if page:
            # screenshot_path = f"/tmp/mobile_{response.url.split('/')[-1]}.png"
            # await page.screenshot(path=screenshot_path)
            await page.close()


class InstagramMobileSpider(scrapy.Spider):
    """
    Instagram 모바일 웹 스크래핑 (예시)
    로그인 필요 없는 공개 프로필
    """
    name = "instagram_mobile"
    allowed_domains = ["instagram.com"]

    custom_settings = {
        "PLAYWRIGHT_CONTEXTS": {
            "default": {
                "viewport": {"width": 375, "height": 812},
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
                              "AppleWebKit/605.1.15",
            }
        },
        "DOWNLOAD_DELAY": 5,
    }

    def __init__(self, username: str = "instagram", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [f"https://www.instagram.com/{username}/"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        ("wait_for_timeout", 3000),  # 3초 대기
                    ],
                }
            )

    async def parse(self, response: Response) -> Dict[str, Any]:
        """Instagram 프로필 정보 추출"""
        page = response.meta.get("playwright_page")

        # 기본 정보 추출 (선택자는 Instagram 구조에 따라 변경 필요)
        yield {
            "type": "instagram_profile",
            "url": response.url,
            "username": response.url.split("/")[-2],
            "profile_scraped": True,
            "source": "instagram_mobile",
        }

        if page:
            await page.close()
