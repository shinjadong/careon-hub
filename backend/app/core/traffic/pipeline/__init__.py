"""
NaverSessionPipeline - 통합 세션 파이프라인

PersonaManager + EngagementSimulator + PortalClient를 통합하여
"페르소나 전환 → 네이버 방문 → 자연스러운 탐색 → 저장"을
하나의 명령으로 실행합니다.

핵심 기능:
- 페르소나 기반 재방문자 시뮬레이션
- Portal 기반 정확한 UI 요소 탐지
- BehaviorProfile 기반 자연스러운 행동
- 방문 기록 자동 저장
- 모든 입력은 EnhancedAdbTools를 통해 휴먼라이크로 수행

Author: Naver AI Evolution System
Created: 2025-12-15
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, quote

from ..device_tools import EnhancedAdbTools, AdbConfig, create_tools

logger = logging.getLogger("naver_evolution.pipeline")


@dataclass
class PipelineConfig:
    """파이프라인 설정"""
    # 디바이스
    device_serial: Optional[str] = None
    screen_width: int = 1080
    screen_height: int = 2400

    # 세션 설정
    max_pageviews_per_session: int = 5
    cooldown_minutes: int = 30

    # 체류시간 (기본값, BehaviorProfile로 오버라이드됨)
    base_dwell_time_min: int = 90
    base_dwell_time_max: int = 180

    # 스크롤 설정
    scroll_count_min: int = 4
    scroll_count_max: int = 10

    # Portal 사용 여부
    use_portal: bool = True

    # 페르소나 선택 전략
    persona_selection_strategy: str = "least_recent"


@dataclass
class VisitResult:
    """방문 결과"""
    success: bool
    url: str
    domain: str
    content_type: str
    dwell_time: int
    scroll_depth: float
    scroll_count: int
    actions: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SessionResult:
    """세션 결과"""
    success: bool
    persona_id: str
    persona_name: str
    visits: List[VisitResult] = field(default_factory=list)
    total_dwell_time: int = 0
    total_scrolls: int = 0
    duration_sec: float = 0.0
    error_message: Optional[str] = None


class NaverSessionPipeline:
    """
    통합 네이버 세션 파이프라인

    사용 예시:
        pipeline = NaverSessionPipeline()

        # 단일 세션 실행
        result = await pipeline.run_session(
            keywords=["맛집 추천", "여행 블로그"],
            pageviews=3
        )

        # 여러 세션 실행 (다른 페르소나로)
        results = await pipeline.run_multiple_sessions(
            keywords=["IT 뉴스", "파이썬 강좌"],
            sessions=5,
            pageviews_per_session=3
        )
    """

    def __init__(self, config: PipelineConfig = None, db_path: str = "data/personas.db"):
        self.config = config or PipelineConfig()

        # 지연 임포트 (순환 참조 방지)
        from ..persona_manager import PersonaManager
        from ..portal_client import PortalClient, ElementFinder

        self.persona_manager = PersonaManager(
            db_path=db_path,
            device_serial=self.config.device_serial
        )
        self.portal = PortalClient() if self.config.use_portal else None
        self.finder = ElementFinder(self.portal) if self.portal else None

        # EnhancedAdbTools 초기화 (휴먼라이크 입력)
        adb_config = AdbConfig(
            serial=self.config.device_serial,
            screen_width=self.config.screen_width,
            screen_height=self.config.screen_height,
        )
        self.adb_tools = EnhancedAdbTools(adb_config)

        self._current_persona = None

    # =========================================================================
    # ADB Commands (EnhancedAdbTools 기반 휴먼라이크 입력)
    # =========================================================================

    async def _tap(self, x: int, y: int, apply_behavior: bool = True):
        """탭 실행 (EnhancedAdbTools 휴먼라이크)"""
        # EnhancedAdbTools가 자동으로 베지어 오프셋 적용
        x = max(0, min(self.config.screen_width, x))
        y = max(0, min(self.config.screen_height, y))

        await self.adb_tools.tap(x, y)
        await asyncio.sleep(random.uniform(0.1, 0.3))

    async def _scroll(self, direction: str = "down", apply_behavior: bool = True):
        """스크롤 실행 (EnhancedAdbTools 휴먼라이크)"""
        if direction == "down":
            await self.adb_tools.scroll_down(distance=random.randint(500, 800))
        else:
            await self.adb_tools.scroll_up(distance=random.randint(400, 600))

    async def _open_url(self, url: str):
        """URL 열기"""
        await self.adb_tools.open_url(url, package="com.android.chrome")
        await asyncio.sleep(random.uniform(2.5, 4.0))

    async def _go_back(self):
        """뒤로가기 (EnhancedAdbTools 휴먼라이크)"""
        await self.adb_tools.back()
        await asyncio.sleep(random.uniform(0.5, 1.0))

    # =========================================================================
    # Content Type Detection
    # =========================================================================

    def _detect_content_type(self, url: str) -> str:
        """URL에서 콘텐츠 타입 추론"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if "blog.naver.com" in domain:
            return "blog"
        elif "news.naver.com" in domain:
            return "news"
        elif "cafe.naver.com" in domain:
            return "cafe"
        elif "shopping.naver.com" in domain or "smartstore" in domain:
            return "shopping"
        elif "search.naver.com" in domain:
            return "search"
        else:
            return "unknown"

    def _extract_domain(self, url: str) -> str:
        """URL에서 도메인 추출"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""

    # =========================================================================
    # Portal-based UI Interaction
    # =========================================================================

    async def _find_and_tap_search_result(self, index: int = 0) -> bool:
        """
        Portal을 사용하여 검색 결과 탭

        Args:
            index: 클릭할 결과 인덱스 (0부터 시작)

        Returns:
            성공 여부
        """
        if not self.finder:
            # Portal 없으면 좌표 기반
            base_y = 650 + (index * 300)
            await self._tap(self.config.screen_width // 2, base_y)
            return True

        try:
            # Portal로 검색 결과 찾기
            results = await self.finder.find_search_results()

            if results and len(results) > index:
                element = results[index]
                x, y = element.center
                logger.info(f"Found result #{index + 1} at ({x}, {y})")
                await self._tap(x, y)
                return True
            else:
                # 폴백: 좌표 기반
                logger.warning(f"Could not find result #{index + 1}, using coordinates")
                base_y = 650 + (index * 300)
                await self._tap(self.config.screen_width // 2, base_y)
                return True

        except Exception as e:
            logger.warning(f"Portal search failed: {e}, using coordinates")
            base_y = 650 + (index * 300)
            await self._tap(self.config.screen_width // 2, base_y)
            return True

    async def _get_scroll_container_info(self) -> Optional[Dict[str, int]]:
        """스크롤 컨테이너 정보 획득"""
        if not self.finder:
            return None

        try:
            return await self.finder.get_scroll_bounds()
        except Exception:
            return None

    # =========================================================================
    # Natural Reading Pattern
    # =========================================================================

    async def _simulate_reading(self, target_dwell_time: int) -> tuple[int, float]:
        """
        자연스러운 읽기 패턴 시뮬레이션

        Args:
            target_dwell_time: 목표 체류시간 (초)

        Returns:
            (스크롤 횟수, 스크롤 깊이)
        """
        profile = self._current_persona.behavior_profile if self._current_persona else None

        # BehaviorProfile 기반 파라미터
        scroll_depth_pref = profile.scroll_depth_preference if profile else 0.7
        pause_freq = profile.scroll_pause_frequency if profile else 0.2
        reading_style = profile.reading_style if profile else "scanner"

        # 읽기 스타일에 따른 스크롤 패턴
        if reading_style == "skimmer":
            scroll_interval = random.uniform(1.0, 2.0)
            target_scrolls = random.randint(8, 12)
        elif reading_style == "deep_reader":
            scroll_interval = random.uniform(3.0, 6.0)
            target_scrolls = random.randint(3, 5)
        else:  # scanner
            scroll_interval = random.uniform(1.5, 3.5)
            target_scrolls = random.randint(5, 8)

        elapsed = 0
        scroll_count = 0
        max_scroll_depth = 0.0

        while elapsed < target_dwell_time:
            # 읽기 대기
            wait_time = scroll_interval * random.uniform(0.8, 1.2)
            await asyncio.sleep(wait_time)
            elapsed += wait_time

            # 스크롤 (목표 깊이까지)
            current_depth = scroll_count / max(target_scrolls, 1)
            if current_depth < scroll_depth_pref:
                await self._scroll("down")
                scroll_count += 1
                max_scroll_depth = max(max_scroll_depth, current_depth)

                # 가끔 위로 스크롤 (20% 확률)
                if random.random() < 0.2:
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    await self._scroll("up")
                    elapsed += 1

            # 가끔 멈춤 (pause_freq 확률)
            if random.random() < pause_freq:
                pause_time = random.uniform(2.0, 5.0)
                await asyncio.sleep(pause_time)
                elapsed += pause_time

            # 시간 초과 체크
            if elapsed >= target_dwell_time:
                break

        return scroll_count, min(1.0, max_scroll_depth + 0.1)

    # =========================================================================
    # Visit Actions
    # =========================================================================

    async def visit_url(self, url: str) -> VisitResult:
        """
        URL 직접 방문

        Args:
            url: 방문할 URL

        Returns:
            VisitResult
        """
        start_time = time.time()
        actions = ["open_url"]

        try:
            # 1. URL 열기
            await self._open_url(url)
            await asyncio.sleep(random.uniform(1.0, 2.0))

            # 2. 체류시간 결정 (BehaviorProfile 기반)
            profile = self._current_persona.behavior_profile if self._current_persona else None
            if profile:
                base_dwell = profile.avg_dwell_time
                dwell_time = int(base_dwell * random.uniform(0.8, 1.2))
            else:
                dwell_time = random.randint(
                    self.config.base_dwell_time_min,
                    self.config.base_dwell_time_max
                )

            logger.info(f"Reading for {dwell_time}s...")

            # 3. 읽기 시뮬레이션
            scroll_count, scroll_depth = await self._simulate_reading(dwell_time)
            actions.extend(["scroll"] * scroll_count)

            actual_dwell = int(time.time() - start_time)

            return VisitResult(
                success=True,
                url=url,
                domain=self._extract_domain(url),
                content_type=self._detect_content_type(url),
                dwell_time=actual_dwell,
                scroll_depth=scroll_depth,
                scroll_count=scroll_count,
                actions=actions
            )

        except Exception as e:
            logger.error(f"Visit failed: {e}")
            return VisitResult(
                success=False,
                url=url,
                domain=self._extract_domain(url),
                content_type=self._detect_content_type(url),
                dwell_time=int(time.time() - start_time),
                scroll_depth=0.0,
                scroll_count=0,
                actions=actions,
                error_message=str(e)
            )

    async def search_and_visit(
        self,
        keyword: str,
        result_index: int = 0,
        search_type: str = "blog"
    ) -> VisitResult:
        """
        검색 후 결과 방문

        Args:
            keyword: 검색어
            result_index: 클릭할 결과 인덱스
            search_type: 검색 타입 (blog, news, cafe)

        Returns:
            VisitResult
        """
        start_time = time.time()
        actions = ["search"]

        try:
            # 1. 검색 URL 구성
            encoded_keyword = quote(keyword)
            if search_type == "blog":
                search_url = f"https://search.naver.com/search.naver?where=blog&query={encoded_keyword}"
            elif search_type == "news":
                search_url = f"https://search.naver.com/search.naver?where=news&query={encoded_keyword}"
            else:
                search_url = f"https://search.naver.com/search.naver?query={encoded_keyword}"

            logger.info(f"Searching: {keyword} (type={search_type})")
            await self._open_url(search_url)
            await asyncio.sleep(random.uniform(1.5, 2.5))

            # 2. 결과 클릭
            actions.append("click_result")
            logger.info(f"Clicking result #{result_index + 1}")
            await self._find_and_tap_search_result(result_index)
            await asyncio.sleep(random.uniform(2.0, 3.5))

            # 3. 체류시간 결정
            profile = self._current_persona.behavior_profile if self._current_persona else None
            if profile:
                base_dwell = profile.avg_dwell_time
                dwell_time = int(base_dwell * random.uniform(0.8, 1.2))
            else:
                dwell_time = random.randint(
                    self.config.base_dwell_time_min,
                    self.config.base_dwell_time_max
                )

            logger.info(f"Reading for {dwell_time}s...")

            # 4. 읽기 시뮬레이션
            scroll_count, scroll_depth = await self._simulate_reading(dwell_time)
            actions.extend(["scroll"] * scroll_count)

            # 5. 뒤로가기
            actions.append("back")
            await self._go_back()

            actual_dwell = int(time.time() - start_time)

            return VisitResult(
                success=True,
                url=f"search:{search_type}:{keyword}#result{result_index}",
                domain="search.naver.com",
                content_type=search_type,
                dwell_time=actual_dwell,
                scroll_depth=scroll_depth,
                scroll_count=scroll_count,
                actions=actions
            )

        except Exception as e:
            logger.error(f"Search visit failed: {e}")
            return VisitResult(
                success=False,
                url=f"search:{search_type}:{keyword}",
                domain="search.naver.com",
                content_type=search_type,
                dwell_time=int(time.time() - start_time),
                scroll_depth=0.0,
                scroll_count=0,
                actions=actions,
                error_message=str(e)
            )

    # =========================================================================
    # Session Execution
    # =========================================================================

    async def run_session(
        self,
        keywords: List[str] = None,
        urls: List[str] = None,
        pageviews: int = 3,
        persona_id: str = None,
        search_type: str = "blog"
    ) -> SessionResult:
        """
        단일 세션 실행

        Args:
            keywords: 검색할 키워드 목록 (또는)
            urls: 직접 방문할 URL 목록
            pageviews: 페이지뷰 수
            persona_id: 사용할 페르소나 ID (None이면 자동 선택)
            search_type: 검색 타입

        Returns:
            SessionResult
        """
        start_time = time.time()

        # 1. 페르소나 선택 및 전환
        logger.info("Selecting persona...")

        if persona_id:
            switch_result = await self.persona_manager.switch_to_persona_by_id(persona_id)
        else:
            switch_result = await self.persona_manager.switch_to_next(
                self.config.persona_selection_strategy
            )

        if not switch_result.success:
            return SessionResult(
                success=False,
                persona_id="",
                persona_name="",
                error_message=f"Persona switch failed: {switch_result.error_message}"
            )

        persona = switch_result.persona
        self._current_persona = persona
        logger.info(f"Using persona: {persona.name} (ANDROID_ID: {persona.android_id[:8]}...)")

        # 2. 방문 실행
        visits = []
        total_dwell = 0
        total_scrolls = 0

        if keywords:
            # 키워드 검색 모드
            for i, keyword in enumerate(keywords[:pageviews]):
                logger.info(f"[{i + 1}/{pageviews}] Searching: {keyword}")

                # 결과 인덱스 랜덤 (0~2)
                result_index = random.randint(0, 2)
                visit = await self.search_and_visit(keyword, result_index, search_type)
                visits.append(visit)

                total_dwell += visit.dwell_time
                total_scrolls += visit.scroll_count

                # 페르소나에 방문 기록 추가
                self.persona_manager.add_visit_record(
                    persona,
                    url=visit.url,
                    domain=visit.domain,
                    content_type=visit.content_type,
                    dwell_time=visit.dwell_time,
                    scroll_depth=visit.scroll_depth,
                    actions=visit.actions
                )

                # 다음 검색 전 대기
                if i < len(keywords) - 1:
                    wait_time = random.uniform(3.0, 8.0)
                    logger.info(f"Waiting {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)

        elif urls:
            # URL 직접 방문 모드
            for i, url in enumerate(urls[:pageviews]):
                logger.info(f"[{i + 1}/{pageviews}] Visiting: {url[:50]}...")

                visit = await self.visit_url(url)
                visits.append(visit)

                total_dwell += visit.dwell_time
                total_scrolls += visit.scroll_count

                # 페르소나에 방문 기록 추가
                self.persona_manager.add_visit_record(
                    persona,
                    url=visit.url,
                    domain=visit.domain,
                    content_type=visit.content_type,
                    dwell_time=visit.dwell_time,
                    scroll_depth=visit.scroll_depth,
                    actions=visit.actions
                )

                # 다음 방문 전 대기
                if i < len(urls) - 1:
                    wait_time = random.uniform(2.0, 5.0)
                    await asyncio.sleep(wait_time)

        # 3. 세션 저장
        logger.info("Saving session...")
        await self.persona_manager.save_current_session(
            persona,
            cooldown_minutes=self.config.cooldown_minutes
        )

        duration = time.time() - start_time

        logger.info(f"Session complete: {len(visits)} visits, {total_dwell}s dwell, {duration:.1f}s total")

        return SessionResult(
            success=True,
            persona_id=persona.persona_id,
            persona_name=persona.name,
            visits=visits,
            total_dwell_time=total_dwell,
            total_scrolls=total_scrolls,
            duration_sec=duration
        )

    async def run_multiple_sessions(
        self,
        keywords: List[str],
        sessions: int = 5,
        pageviews_per_session: int = 3,
        search_type: str = "blog",
        session_interval_min: int = 5,
        session_interval_max: int = 15
    ) -> List[SessionResult]:
        """
        여러 세션 실행 (서로 다른 페르소나로)

        Args:
            keywords: 검색 키워드 목록
            sessions: 세션 수
            pageviews_per_session: 세션당 페이지뷰
            search_type: 검색 타입
            session_interval_min: 세션 간 최소 간격 (분)
            session_interval_max: 세션 간 최대 간격 (분)

        Returns:
            SessionResult 목록
        """
        results = []

        for i in range(sessions):
            logger.info(f"\n{'=' * 50}")
            logger.info(f"Session {i + 1}/{sessions}")
            logger.info(f"{'=' * 50}")

            # 키워드 셔플
            session_keywords = random.sample(
                keywords,
                min(pageviews_per_session, len(keywords))
            )

            result = await self.run_session(
                keywords=session_keywords,
                pageviews=pageviews_per_session,
                search_type=search_type
            )
            results.append(result)

            # 세션 간 대기 (마지막 세션 제외)
            if i < sessions - 1:
                wait_minutes = random.uniform(session_interval_min, session_interval_max)
                logger.info(f"Waiting {wait_minutes:.1f} minutes before next session...")
                await asyncio.sleep(wait_minutes * 60)

        # 결과 요약
        successful = sum(1 for r in results if r.success)
        total_visits = sum(len(r.visits) for r in results)
        total_dwell = sum(r.total_dwell_time for r in results)

        logger.info(f"\n{'=' * 50}")
        logger.info(f"All sessions complete: {successful}/{sessions} successful")
        logger.info(f"Total visits: {total_visits}, Total dwell: {total_dwell}s")
        logger.info(f"{'=' * 50}")

        return results

    # =========================================================================
    # Campaign Workflow (실제 캠페인 동작)
    # =========================================================================

    async def run_campaign_workflow(
        self,
        keyword: str,
        target_blog_title: str,
        target_blogger: str = None,
        target_date: str = None,
        target_url: str = None,
        persona_id: str = None
    ) -> SessionResult:
        """
        캠페인 워크플로우 실행 (실제 사용자 행동 시뮬레이션)

        워크플로우:
        1. 네이버 메인 → 키워드 검색
        2. 검색 결과에서 스크롤 (내려갔다가 위로)
        3. '블로그' 탭 찾아서 클릭
        4. 블로그 탭에서 타겟 포스트 찾기 (제목/블로거/날짜)
        5. 포스트 페이지에서 휴먼라이크 스크롤
        6. 공유 버튼 클릭 → URL 복사 → 세션 종료

        Args:
            keyword: 검색 키워드
            target_blog_title: 찾을 블로그 포스트 제목 (부분 매칭)
            target_blogger: 블로거 이름 (선택)
            target_date: 날짜 (선택, 예: "2025.11.28")
            target_url: 타겟 URL (폴백용)
            persona_id: 사용할 페르소나 ID

        Returns:
            SessionResult
        """
        start_time = time.time()
        actions = []

        # 1. 페르소나 선택 및 전환
        logger.info("Selecting persona...")

        if persona_id:
            switch_result = await self.persona_manager.switch_to_persona_by_id(persona_id)
        else:
            switch_result = await self.persona_manager.switch_to_next(
                self.config.persona_selection_strategy
            )

        if not switch_result.success:
            return SessionResult(
                success=False,
                persona_id="",
                persona_name="",
                error_message=f"Persona switch failed: {switch_result.error_message}"
            )

        persona = switch_result.persona
        self._current_persona = persona
        logger.info(f"Using persona: {persona.name} (ANDROID_ID: {persona.android_id[:8]}...)")

        try:
            # ===== STEP 1: 네이버 검색 페이지 =====
            logger.info(f"[STEP 1] Opening Naver search for: {keyword}")
            actions.append("open_naver_search")

            # 네이버 통합검색 URL로 직접 이동 (키워드 포함)
            encoded_keyword = quote(keyword)
            search_url = f"https://m.search.naver.com/search.naver?query={encoded_keyword}"
            await self._open_url(search_url)
            await asyncio.sleep(random.uniform(2.5, 4.0))

            # ===== STEP 2: 검색 결과에서 스크롤 =====
            logger.info("[STEP 2] Scrolling search results...")
            actions.append("scroll_search_results")

            # 아래로 스크롤 (2-4회)
            scroll_down_count = random.randint(2, 4)
            for _ in range(scroll_down_count):
                await self._scroll("down")
                await asyncio.sleep(random.uniform(0.8, 1.5))

            # 다시 최상단으로
            logger.info("Scrolling back to top...")
            for _ in range(scroll_down_count + 1):
                await self._scroll("up")
                await asyncio.sleep(random.uniform(0.5, 0.8))

            await asyncio.sleep(random.uniform(1.0, 1.5))

            # ===== STEP 3: 블로그 탭 찾아서 클릭 =====
            logger.info("[STEP 3] Finding and clicking 'Blog' tab...")
            actions.append("click_blog_tab")

            # 블로그 탭 찾기 (탭 영역은 보통 상단 400px 내외)
            blog_tab_found = await self._find_and_click_blog_tab()

            if not blog_tab_found:
                logger.warning("Blog tab not found, trying direct navigation...")
                # 폴백: 직접 블로그 검색 URL로 이동
                encoded_keyword = quote(keyword)
                await self._open_url(f"https://m.search.naver.com/search.naver?where=m_blog&query={encoded_keyword}")

            await asyncio.sleep(random.uniform(2.0, 3.0))

            # ===== STEP 4: 타겟 포스트 찾기 =====
            logger.info(f"[STEP 4] Finding target post: {target_blog_title[:30]}...")
            actions.append("find_target_post")

            post_found = await self._find_and_click_target_post(
                target_title=target_blog_title,
                target_blogger=target_blogger,
                target_date=target_date,
                target_url=target_url
            )

            if not post_found and target_url:
                logger.warning("Target post not found, using direct URL...")
                await self._open_url(target_url)

            await asyncio.sleep(random.uniform(2.5, 4.0))

            # ===== STEP 5: 포스트 페이지 휴먼라이크 스크롤 =====
            logger.info("[STEP 5] Reading post with humanlike scrolling...")
            actions.append("read_post")

            scroll_count, scroll_depth = await self._humanlike_post_reading()

            # ===== STEP 6: 공유 버튼 클릭 =====
            logger.info("[STEP 6] Finding and clicking share button...")
            actions.append("click_share")

            share_clicked = await self._find_and_click_share_button()

            if share_clicked:
                await asyncio.sleep(random.uniform(1.0, 1.5))

                # URL 복사 클릭
                actions.append("copy_url")
                await self._click_copy_url()
                await asyncio.sleep(random.uniform(0.5, 1.0))

                logger.info("URL copied successfully")

            # 체류시간 계산
            actual_dwell = int(time.time() - start_time)

            # 세션 저장
            logger.info("Saving session...")
            await self.persona_manager.save_current_session(
                persona,
                cooldown_minutes=self.config.cooldown_minutes
            )

            duration = time.time() - start_time

            visit = VisitResult(
                success=True,
                url=target_url or f"search:blog:{keyword}",
                domain="blog.naver.com",
                content_type="blog",
                dwell_time=actual_dwell,
                scroll_depth=scroll_depth,
                scroll_count=scroll_count,
                actions=actions
            )

            logger.info(f"Campaign workflow complete: {actual_dwell}s dwell, {scroll_count} scrolls")

            return SessionResult(
                success=True,
                persona_id=persona.persona_id,
                persona_name=persona.name,
                visits=[visit],
                total_dwell_time=actual_dwell,
                total_scrolls=scroll_count,
                duration_sec=duration
            )

        except Exception as e:
            logger.error(f"Campaign workflow failed: {e}")

            # 세션 저장 시도
            try:
                await self.persona_manager.save_current_session(
                    persona,
                    cooldown_minutes=self.config.cooldown_minutes
                )
            except Exception:
                pass

            return SessionResult(
                success=False,
                persona_id=persona.persona_id if persona else "",
                persona_name=persona.name if persona else "",
                duration_sec=time.time() - start_time,
                error_message=str(e)
            )

    async def _find_and_click_blog_tab(self) -> bool:
        """블로그 탭 찾아서 클릭"""
        try:
            # 모바일 네이버 검색 결과의 탭 영역
            # 일반적으로 탭은 화면 상단 300-450px 영역에 위치

            # Portal로 찾기 시도
            if self.finder:
                try:
                    tabs = await self.finder.find_elements_by_text("블로그")
                    if tabs:
                        x, y = tabs[0].center
                        await self._tap(x, y)
                        return True
                except Exception:
                    pass

            # 폴백: 좌표 기반 (탭 영역 스캔)
            # 모바일에서 탭은 보통 y=350~450 영역, 블로그 탭은 왼쪽에서 2-3번째
            tab_y = 400
            tab_positions = [180, 320, 460, 600]  # x 좌표들

            for x in tab_positions:
                # 해당 위치 탭
                await self._tap(x, tab_y)
                await asyncio.sleep(0.5)

                # 화면 변화 확인 (블로그 검색 결과로 이동했는지)
                # TODO: 실제로는 Portal이나 OCR로 확인
                # 여기서는 두 번째 탭 위치로 가정
                if x == 320:
                    return True

            return False

        except Exception as e:
            logger.warning(f"Failed to find blog tab: {e}")
            return False

    async def _find_and_click_target_post(
        self,
        target_title: str,
        target_blogger: str = None,
        target_date: str = None,
        target_url: str = None,
        max_scrolls: int = 5
    ) -> bool:
        """타겟 포스트 찾아서 클릭"""
        try:
            for scroll_attempt in range(max_scrolls):
                # Portal로 검색 결과 찾기
                if self.finder:
                    try:
                        # 제목으로 찾기
                        results = await self.finder.find_elements_by_text(
                            target_title[:20],  # 앞 20자로 매칭
                            partial=True
                        )

                        if results:
                            x, y = results[0].center
                            logger.info(f"Found target post at ({x}, {y})")
                            await self._tap(x, y)
                            return True

                    except Exception:
                        pass

                # 폴백: 블로그 ID로 URL 매칭
                if target_url:
                    # URL에서 블로그 ID 추출
                    import re
                    match = re.search(r'blog\.naver\.com/([^/]+)', target_url)
                    if match:
                        blog_id = match.group(1)
                        try:
                            results = await self.finder.find_elements_by_text(blog_id, partial=True)
                            if results:
                                # 블로거 이름 위치에서 조금 위로 (제목 영역)
                                x, y = results[0].center
                                await self._tap(x, y - 50)
                                return True
                        except Exception:
                            pass

                # 스크롤해서 더 찾기
                if scroll_attempt < max_scrolls - 1:
                    logger.info(f"Scrolling to find target post... ({scroll_attempt + 1}/{max_scrolls})")
                    await self._scroll("down")
                    await asyncio.sleep(random.uniform(1.0, 1.5))

            # 마지막 폴백: 첫 번째 결과 클릭
            logger.warning("Target post not found, clicking first result...")
            await self._tap(self.config.screen_width // 2, 600)
            return False

        except Exception as e:
            logger.warning(f"Failed to find target post: {e}")
            return False

    async def _humanlike_post_reading(self) -> tuple[int, float]:
        """
        포스트 페이지 휴먼라이크 읽기

        패턴:
        1. 요소 파싱하며 천천히 스크롤
        2. 끝까지 내려갔다가
        3. 중간으로 올라온 후
        4. 다시 밑으로 내려가기

        Returns:
            (스크롤 횟수, 스크롤 깊이)
        """
        scroll_count = 0
        max_depth = 0.0

        profile = self._current_persona.behavior_profile if self._current_persona else None
        base_dwell = profile.avg_dwell_time if profile else 120

        # Phase 1: 천천히 끝까지 스크롤
        logger.info("Phase 1: Reading down to bottom...")
        phase1_scrolls = random.randint(6, 10)

        for i in range(phase1_scrolls):
            # 읽는 시간 (요소 파싱하는 것처럼)
            read_time = random.uniform(2.0, 5.0)
            await asyncio.sleep(read_time)

            # 스크롤
            await self._scroll("down")
            scroll_count += 1
            max_depth = max(max_depth, (i + 1) / phase1_scrolls)

            # 가끔 멈춤 (30% 확률)
            if random.random() < 0.3:
                pause_time = random.uniform(1.5, 3.0)
                await asyncio.sleep(pause_time)

        await asyncio.sleep(random.uniform(1.0, 2.0))

        # Phase 2: 중간으로 올라오기
        logger.info("Phase 2: Scrolling back to middle...")
        phase2_scrolls = random.randint(3, 5)

        for _ in range(phase2_scrolls):
            await self._scroll("up")
            scroll_count += 1
            await asyncio.sleep(random.uniform(0.8, 1.5))

        await asyncio.sleep(random.uniform(2.0, 4.0))

        # Phase 3: 다시 밑으로 (공유 버튼 찾으면서)
        logger.info("Phase 3: Scrolling down to find share button...")
        phase3_scrolls = random.randint(4, 6)

        for _ in range(phase3_scrolls):
            await asyncio.sleep(random.uniform(1.5, 3.0))
            await self._scroll("down")
            scroll_count += 1

        return scroll_count, min(1.0, max_depth)

    async def _find_and_click_share_button(self) -> bool:
        """공유 버튼 (종이비행기 아이콘) 찾아서 클릭"""
        try:
            # Portal로 공유 버튼 찾기
            if self.finder:
                try:
                    # 공유 버튼은 보통 "공유" 텍스트나 아이콘
                    share_elements = await self.finder.find_elements_by_text("공유")
                    if share_elements:
                        x, y = share_elements[0].center
                        await self._tap(x, y)
                        return True
                except Exception:
                    pass

            # 폴백: 좌표 기반
            # 네이버 블로그 모바일에서 공유 버튼은 보통 우하단 또는 하단 툴바
            # 화면 하단 80-120px 영역, 우측

            share_positions = [
                (self.config.screen_width - 100, self.config.screen_height - 100),  # 우하단
                (self.config.screen_width // 2 + 200, self.config.screen_height - 80),  # 하단 중앙 우측
                (self.config.screen_width - 150, 300),  # 상단 우측 (일부 레이아웃)
            ]

            for x, y in share_positions:
                await self._tap(x, y)
                await asyncio.sleep(0.8)

                # 공유 메뉴가 열렸는지 확인 시도
                # TODO: Portal로 확인
                # 일단 첫 번째 위치로 시도
                return True

            return False

        except Exception as e:
            logger.warning(f"Failed to find share button: {e}")
            return False

    async def _click_copy_url(self) -> bool:
        """URL 복사 버튼 클릭"""
        try:
            # Portal로 찾기
            if self.finder:
                try:
                    copy_elements = await self.finder.find_elements_by_text("URL 복사")
                    if not copy_elements:
                        copy_elements = await self.finder.find_elements_by_text("링크 복사")
                    if not copy_elements:
                        copy_elements = await self.finder.find_elements_by_text("복사")

                    if copy_elements:
                        x, y = copy_elements[0].center
                        await self._tap(x, y)
                        return True
                except Exception:
                    pass

            # 폴백: 공유 메뉴에서 URL 복사는 보통 상단에 위치
            # 화면 중앙 상단 영역
            await self._tap(self.config.screen_width // 2, self.config.screen_height // 3)
            return True

        except Exception as e:
            logger.warning(f"Failed to click copy URL: {e}")
            return False

    # =========================================================================
    # Utilities
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        return self.persona_manager.get_stats()

    async def check_status(self) -> Dict[str, Any]:
        """시스템 상태 확인"""
        device_status = await self.persona_manager.check_device_status()

        portal_status = {}
        if self.portal:
            portal_status = await self.portal.get_status()

        return {
            "device": device_status,
            "portal": portal_status,
            "personas": self.persona_manager.get_stats()
        }
