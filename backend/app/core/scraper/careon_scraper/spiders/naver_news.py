"""
네이버 뉴스 스크래핑 스파이더
실시간 뉴스 헤드라인 및 콘텐츠 수집
"""

import scrapy
from scrapy.http import Response
from typing import Iterator, Dict, Any


class NaverNewsSpider(scrapy.Spider):
    name = "naver_news"
    allowed_domains = ["news.naver.com"]
    start_urls = ["https://news.naver.com"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 2,
    }

    def parse(self, response: Response) -> Iterator[Dict[str, Any]]:
        """
        메인 페이지에서 뉴스 헤드라인 수집
        """
        # 뉴스 헤드라인 추출
        news_items = response.css("div.cjs_news_new li.cjs_news_a")

        for item in news_items:
            title = item.css("a::text").get()
            link = item.css("a::attr(href)").get()

            if title and link:
                yield {
                    "type": "news_headline",
                    "title": title.strip(),
                    "url": response.urljoin(link),
                    "source": "naver_news",
                }

        # 랭킹 뉴스
        ranking_news = response.css("div.rankingnews_box")
        for box in ranking_news:
            media_name = box.css("strong.rankingnews_name::text").get()
            articles = box.css("ul.rankingnews_list li")

            for article in articles:
                title = article.css("a::text").get()
                link = article.css("a::attr(href)").get()

                if title and link:
                    yield {
                        "type": "ranking_news",
                        "title": title.strip(),
                        "url": link,
                        "media": media_name,
                        "source": "naver_news",
                    }


class NaverNewsDetailSpider(scrapy.Spider):
    """
    네이버 뉴스 상세 기사 스크래핑
    """
    name = "naver_news_detail"
    allowed_domains = ["n.news.naver.com"]

    def __init__(self, article_url: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if article_url:
            self.start_urls = [article_url]
        else:
            self.start_urls = []

    def parse(self, response: Response) -> Dict[str, Any]:
        """기사 상세 내용 추출"""
        yield {
            "type": "news_article",
            "url": response.url,
            "title": response.css("h2#title_area span::text").get(),
            "content": " ".join(response.css("article#dic_area::text").getall()).strip(),
            "media": response.css("img.media_end_head_top_logo_img::attr(alt)").get(),
            "date": response.css("span.media_end_head_info_datestamp_time::text").get(),
            "source": "naver_news_detail",
        }
