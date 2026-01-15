"""
ElementFinder - UI 요소 검색 헬퍼

네이버 앱/웹에서 자주 사용되는 요소를 쉽게 찾을 수 있는 헬퍼 클래스

Author: Naver AI Evolution System
Created: 2025-12-15
"""

import logging
from typing import List, Optional, Dict, Any

from .client import PortalClient
from .element import UIElement, UITree

logger = logging.getLogger("naver_evolution.element_finder")


class ElementFinder:
    """
    UI 요소 검색 헬퍼

    PortalClient를 사용하여 특정 요소를 쉽게 찾을 수 있습니다.
    네이버 앱/웹에서 자주 사용되는 패턴을 지원합니다.

    사용 예시:
        finder = ElementFinder(portal_client)

        # 검색창 찾기
        search_box = await finder.find_search_box()

        # 검색 결과 항목들
        results = await finder.find_search_results()

        # 특정 블로그 제목
        blog = await finder.find_blog_item_by_title("맛집 추천")
    """

    def __init__(self, portal: PortalClient):
        """
        Args:
            portal: PortalClient 인스턴스
        """
        self.portal = portal

    # =========================================================================
    # Generic Finders
    # =========================================================================

    async def find_by_text(self, text: str, exact: bool = False) -> Optional[UIElement]:
        """텍스트로 요소 검색"""
        return await self.portal.find_by_text(text, exact)

    async def find_all_by_text(self, text: str, exact: bool = False) -> List[UIElement]:
        """텍스트로 모든 요소 검색"""
        tree = await self.portal.get_ui_tree()
        return tree.find_all_by_text(text, exact)

    async def find_clickable(self, text_contains: str = None) -> List[UIElement]:
        """
        클릭 가능한 요소 검색

        Args:
            text_contains: 텍스트 포함 조건 (None이면 모든 클릭 가능 요소)

        Returns:
            클릭 가능한 요소 목록
        """
        tree = await self.portal.get_ui_tree()

        if text_contains:
            return tree.find_all(clickable=True, text_contains=text_contains)
        else:
            return tree.clickable_elements

    async def find_by_resource_id(self, resource_id: str) -> Optional[UIElement]:
        """리소스 ID로 요소 검색"""
        tree = await self.portal.get_ui_tree()
        return tree.find_by_resource_id(resource_id)

    async def find_at_position(self, x: int, y: int) -> Optional[UIElement]:
        """좌표에 있는 요소 검색"""
        tree = await self.portal.get_ui_tree()
        return tree.find_at_position(x, y)

    # =========================================================================
    # Chrome Browser Finders
    # =========================================================================

    async def find_chrome_url_bar(self) -> Optional[UIElement]:
        """Chrome 주소창 찾기"""
        # Chrome URL 바의 일반적인 리소스 ID
        candidates = [
            "com.android.chrome:id/url_bar",
            "com.android.chrome:id/omnibox_text_field",
            "com.android.chrome:id/search_box_text"
        ]

        for resource_id in candidates:
            element = await self.find_by_resource_id(resource_id)
            if element:
                return element

        return None

    async def find_chrome_tab_button(self) -> Optional[UIElement]:
        """Chrome 탭 버튼 찾기"""
        return await self.find_by_resource_id("com.android.chrome:id/tab_switcher_button")

    async def find_chrome_menu_button(self) -> Optional[UIElement]:
        """Chrome 메뉴 버튼 찾기"""
        return await self.find_by_resource_id("com.android.chrome:id/menu_button")

    # =========================================================================
    # Naver Search Finders
    # =========================================================================

    async def find_search_box(self) -> Optional[UIElement]:
        """
        네이버 검색창 찾기

        모바일 웹과 앱 모두에서 검색창을 찾습니다.
        """
        # 검색창 패턴들
        patterns = [
            {"text_contains": "검색어를 입력"},
            {"text_contains": "Search"},
            {"resource_id": "query"},
            {"class_name": "EditText", "focusable": True},
        ]

        for pattern in patterns:
            element = await self.portal.find_element(**pattern)
            if element:
                return element

        return None

    async def find_search_button(self) -> Optional[UIElement]:
        """검색 버튼 찾기"""
        patterns = [
            {"text": "검색"},
            {"content_desc": "검색"},
            {"resource_id": "search_btn"},
        ]

        for pattern in patterns:
            element = await self.portal.find_element(**pattern)
            if element and element.clickable:
                return element

        return None

    async def find_search_results(self) -> List[UIElement]:
        """
        네이버 검색 결과 항목들 찾기

        Returns:
            검색 결과 항목 목록 (클릭 가능한 컨텐츠)
        """
        tree = await self.portal.get_ui_tree()

        # 검색 결과 영역의 클릭 가능한 항목들
        results = []

        for element in tree.clickable_elements:
            # 너무 작은 요소 제외
            if element.bounds.width < 100 or element.bounds.height < 50:
                continue

            # 상단 UI 요소 제외 (검색창, 탭 등)
            if element.bounds.top < 200:
                continue

            # 텍스트가 있는 항목 우선
            if element.has_text or element.content_desc:
                results.append(element)

        return results

    # =========================================================================
    # Naver Blog Finders
    # =========================================================================

    async def find_blog_items(self) -> List[UIElement]:
        """
        블로그 포스트 항목들 찾기

        Returns:
            블로그 포스트 요소 목록
        """
        tree = await self.portal.get_ui_tree()

        # 블로그 포스트 패턴
        blog_items = []

        for element in tree.clickable_elements:
            # 포스트 크기 조건
            if element.bounds.width < 200 or element.bounds.height < 100:
                continue

            # blog.naver.com 관련 요소
            text = (element.text + element.content_desc).lower()
            if "blog" in text or element.has_text:
                blog_items.append(element)

        return blog_items

    async def find_blog_item_by_title(self, title: str) -> Optional[UIElement]:
        """
        제목으로 블로그 포스트 찾기

        Args:
            title: 포스트 제목 (부분 매칭)

        Returns:
            매칭되는 블로그 포스트 요소 또는 None
        """
        items = await self.find_all_by_text(title)

        for item in items:
            # 클릭 가능한 항목 우선
            if item.clickable:
                return item

            # 부모 요소가 클릭 가능한지 확인 (트리에서)
            tree = await self.portal.get_ui_tree()
            for elem in tree.clickable_elements:
                if elem.bounds.contains(*item.center):
                    return elem

        # 텍스트가 포함된 아무 요소나 반환
        return items[0] if items else None

    # =========================================================================
    # Navigation Finders
    # =========================================================================

    async def find_back_button(self) -> Optional[UIElement]:
        """뒤로가기 버튼 찾기"""
        patterns = [
            {"content_desc": "뒤로"},
            {"content_desc": "Back"},
            {"content_desc": "Navigate up"},
            {"resource_id": "back_button"},
        ]

        for pattern in patterns:
            element = await self.portal.find_element(**pattern)
            if element and element.clickable:
                return element

        return None

    async def find_home_button(self) -> Optional[UIElement]:
        """홈 버튼 찾기"""
        patterns = [
            {"content_desc": "홈"},
            {"content_desc": "Home"},
            {"text": "홈"},
        ]

        for pattern in patterns:
            element = await self.portal.find_element(**pattern)
            if element and element.clickable:
                return element

        return None

    async def find_close_button(self) -> Optional[UIElement]:
        """닫기 버튼 찾기"""
        patterns = [
            {"content_desc": "닫기"},
            {"content_desc": "Close"},
            {"text": "닫기"},
            {"text": "X"},
        ]

        for pattern in patterns:
            element = await self.portal.find_element(**pattern)
            if element and element.clickable:
                return element

        return None

    # =========================================================================
    # Scroll Container Finders
    # =========================================================================

    async def find_main_scroll_container(self) -> Optional[UIElement]:
        """
        메인 스크롤 컨테이너 찾기

        가장 큰 스크롤 가능한 영역을 반환
        """
        containers = await self.portal.find_scrollable_containers()

        if not containers:
            return None

        # 가장 큰 영역의 컨테이너 반환
        return max(
            containers,
            key=lambda e: e.bounds.width * e.bounds.height
        )

    async def get_scroll_bounds(self) -> Optional[Dict[str, int]]:
        """
        스크롤 가능 영역의 경계 반환

        Returns:
            {"top": y, "bottom": y, "left": x, "right": x} 또는 None
        """
        container = await self.find_main_scroll_container()

        if container:
            return container.bounds.to_dict()

        return None

    # =========================================================================
    # Analysis Helpers
    # =========================================================================

    async def get_page_summary(self) -> Dict[str, Any]:
        """
        현재 페이지 요약 정보

        Returns:
            페이지 요약 딕셔너리
        """
        tree = await self.portal.get_ui_tree()

        # 텍스트 수집
        texts = [e.text for e in tree.text_elements if e.text.strip()][:10]

        # 클릭 가능 요소 수
        clickable_count = len(tree.clickable_elements)

        # 스크롤 가능 여부
        has_scroll = len(tree.get_scrollable_containers()) > 0

        return {
            "total_elements": len(tree),
            "clickable_count": clickable_count,
            "has_scroll": has_scroll,
            "sample_texts": texts,
        }

    async def is_on_naver(self) -> bool:
        """네이버 페이지에 있는지 확인"""
        tree = await self.portal.get_ui_tree()

        for element in tree.all_elements:
            text = (element.text + element.content_desc + element.resource_id).lower()
            if "naver" in text:
                return True

        return False

    async def is_on_blog(self) -> bool:
        """블로그 페이지에 있는지 확인"""
        tree = await self.portal.get_ui_tree()

        for element in tree.all_elements:
            text = (element.text + element.content_desc).lower()
            if "blog.naver" in text or "블로그" in text:
                return True

        return False
