"""
동적 콘텐츠 스크래핑 (JavaScript 렌더링)
Playwright를 사용한 SPA(Single Page Application) 및 동적 웹사이트 스크래핑
"""

import scrapy
from scrapy.http import Response
from typing import Iterator, Dict, Any
import json


class DynamicContentSpider(scrapy.Spider):
    """
    JavaScript로 렌더링되는 동적 콘텐츠 스크래핑
    """
    name = "dynamic_content"
    allowed_domains = []

    custom_settings = {
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "DOWNLOAD_DELAY": 3,
    }

    def __init__(self, url: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if url:
            self.start_urls = [url]
        else:
            self.start_urls = ["https://example.com"]

    def start_requests(self):
        """Playwright를 사용하여 JavaScript 렌더링"""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        ("wait_for_load_state", "networkidle"),
                        ("wait_for_timeout", 2000),
                    ],
                }
            )

    async def parse(self, response: Response) -> Iterator[Dict[str, Any]]:
        """동적으로 로드된 콘텐츠 파싱"""
        page = response.meta.get("playwright_page")

        # 페이지 정보
        yield {
            "type": "dynamic_page",
            "url": response.url,
            "title": response.css("title::text").get(),
            "rendered": True,
            "source": "dynamic_content",
        }

        # 스크롤 후 추가 콘텐츠 로드 (무한 스크롤 지원)
        if page:
            try:
                # 페이지 끝까지 스크롤
                for i in range(3):  # 3번 스크롤
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000)

                # 최종 콘텐츠 추출
                content = await page.content()

                yield {
                    "type": "scrolled_content",
                    "url": response.url,
                    "content_length": len(content),
                    "scrolls": 3,
                    "source": "dynamic_content",
                }

            except Exception as e:
                self.logger.error(f"Scroll error: {e}")
            finally:
                await page.close()


class APIScraperSpider(scrapy.Spider):
    """
    API 응답 스크래핑 (AJAX 요청 인터셉트)
    """
    name = "api_scraper"

    custom_settings = {
        "PLAYWRIGHT_CONTEXTS": {
            "default": {
                "viewport": {"width": 1920, "height": 1080},
            }
        },
    }

    def __init__(self, url: str = None, api_pattern: str = "/api/*", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [url] if url else ["https://example.com"]
        self.api_pattern = api_pattern

    def start_requests(self):
        """API 응답을 인터셉트하는 Playwright 요청"""
        for url in self.start_urls:
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

    async def parse(self, response: Response) -> Iterator[Dict[str, Any]]:
        """API 응답 수집"""
        page = response.meta.get("playwright_page")

        if page:
            try:
                # 네트워크 요청 모니터링
                api_responses = []

                async def handle_response(response):
                    if self.api_pattern in response.url:
                        try:
                            json_data = await response.json()
                            api_responses.append({
                                "url": response.url,
                                "status": response.status,
                                "data": json_data,
                            })
                        except Exception:
                            pass

                page.on("response", handle_response)

                # 페이지 인터랙션 (버튼 클릭 등)
                await page.wait_for_timeout(3000)

                # 수집한 API 응답 yield
                for api_resp in api_responses:
                    yield {
                        "type": "api_response",
                        "api_url": api_resp["url"],
                        "status": api_resp["status"],
                        "data": api_resp["data"],
                        "source": "api_scraper",
                    }

            except Exception as e:
                self.logger.error(f"API scraping error: {e}")
            finally:
                await page.close()
