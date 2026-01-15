"""
EngagementSimulator - 블로그 조회수 증가 시뮬레이터

핑거프린트 실험 결과 기반:
- 고유 NNB 쿠키 (세션 리셋으로 생성)
- 적절한 체류시간 (SRT11 이벤트: 2-3분)
- 스크롤 이벤트 (SRT12)
- 세션당 최대 5개 페이지뷰
- 모든 입력은 EnhancedAdbTools를 통해 휴먼라이크로 수행

Author: Naver AI Evolution System
Created: 2025-12-15
"""

import asyncio
import random
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from ..device_tools import EnhancedAdbTools, AdbConfig

logger = logging.getLogger("naver_evolution.engagement")


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class EngagementConfig:
    """인게이지먼트 설정"""
    # 디바이스
    device_serial: Optional[str] = None
    screen_width: int = 1080
    screen_height: int = 2400

    # 체류시간 (초)
    dwell_time_min: int = 120   # 2분
    dwell_time_max: int = 180   # 3분

    # 스크롤 설정
    scroll_count_min: int = 4
    scroll_count_max: int = 8
    scroll_interval_min: float = 1.5
    scroll_interval_max: float = 3.0

    # 탭 설정
    tap_offset_max: int = 15    # 탭 위치 오프셋

    # 세션 제한
    max_pageviews: int = 5


@dataclass
class EngagementResult:
    """인게이지먼트 결과"""
    success: bool
    url: str
    dwell_time_sec: float
    scroll_count: int
    pageview_recorded: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SessionEngagementStats:
    """세션 인게이지먼트 통계"""
    session_id: str
    total_engagements: int = 0
    total_dwell_time: float = 0.0
    total_scrolls: int = 0
    results: List[EngagementResult] = field(default_factory=list)


# =============================================================================
# EngagementSimulator Class
# =============================================================================

class EngagementSimulator:
    """
    블로그 조회수 증가 시뮬레이터

    핑거프린트 실험 기반 조건:
    1. 고유 NNB 쿠키 (DeviceSessionManager가 생성)
    2. 적절한 체류시간 (2-3분)
    3. 스크롤 이벤트 (4-8회)
    4. 자연스러운 행동 패턴 (EnhancedAdbTools 휴먼라이크)

    사용 예시:
        simulator = EngagementSimulator()

        # 블로그 방문 시뮬레이션
        result = await simulator.simulate_blog_visit(
            "https://blog.naver.com/example/12345"
        )
    """

    def __init__(self, config: EngagementConfig = None):
        self.config = config or EngagementConfig()
        self.current_stats: Optional[SessionEngagementStats] = None

        # EnhancedAdbTools 초기화 (휴먼라이크 입력)
        adb_config = AdbConfig(
            serial=self.config.device_serial,
            screen_width=self.config.screen_width,
            screen_height=self.config.screen_height,
        )
        self.adb_tools = EnhancedAdbTools(adb_config)

    # =========================================================================
    # ADB 명령 (EnhancedAdbTools 기반 휴먼라이크)
    # =========================================================================

    async def _tap(self, x: int, y: int) -> None:
        """탭 실행 (EnhancedAdbTools 휴먼라이크)"""
        actual_x = max(0, min(self.config.screen_width, x))
        actual_y = max(0, min(self.config.screen_height, y))
        await self.adb_tools.tap(actual_x, actual_y)

    async def _scroll_down(self) -> None:
        """아래로 스크롤 (EnhancedAdbTools 휴먼라이크)"""
        await self.adb_tools.scroll_down(distance=random.randint(500, 800))

    async def _scroll_up(self) -> None:
        """위로 스크롤 (EnhancedAdbTools 휴먼라이크)"""
        await self.adb_tools.scroll_up(distance=random.randint(400, 600))

    async def _open_url(self, url: str) -> None:
        """URL 열기"""
        await self.adb_tools.open_url(url)

    async def _go_back(self) -> None:
        """뒤로가기 (EnhancedAdbTools 휴먼라이크)"""
        await self.adb_tools.back()

    # =========================================================================
    # 자연스러운 행동 패턴
    # =========================================================================

    async def _natural_reading_pattern(self, total_time_sec: int) -> int:
        """
        자연스러운 읽기 패턴 시뮬레이션 (EnhancedAdbTools 휴먼라이크)

        Returns:
            실행된 스크롤 횟수
        """
        elapsed = 0
        scroll_count = 0
        target_scrolls = random.randint(
            self.config.scroll_count_min,
            self.config.scroll_count_max
        )

        while elapsed < total_time_sec and scroll_count < target_scrolls:
            # 읽기 대기 (가변)
            wait_time = random.uniform(
                self.config.scroll_interval_min,
                self.config.scroll_interval_max
            )
            await asyncio.sleep(wait_time)
            elapsed += wait_time

            # 스크롤 (EnhancedAdbTools 휴먼라이크)
            await self._scroll_down()
            scroll_count += 1

            # 가끔 위로 스크롤 (20% 확률)
            if random.random() < 0.2:
                await asyncio.sleep(random.uniform(0.5, 1.0))
                await self._scroll_up()
                elapsed += 1

            # 가끔 멈춤 (콘텐츠 집중 읽기)
            if random.random() < 0.3:
                pause_time = random.uniform(2.0, 5.0)
                await asyncio.sleep(pause_time)
                elapsed += pause_time

        # 남은 시간 대기
        remaining = total_time_sec - elapsed
        if remaining > 0:
            await asyncio.sleep(remaining)

        return scroll_count

    # =========================================================================
    # 인게이지먼트 시뮬레이션
    # =========================================================================

    async def simulate_blog_visit(self, url: str) -> EngagementResult:
        """
        블로그 방문 시뮬레이션

        Args:
            url: 블로그 포스트 URL

        Returns:
            EngagementResult
        """
        start_time = time.time()

        try:
            # 1. URL 열기 (EnhancedAdbTools 휴먼라이크)
            logger.info(f"Opening: {url}")
            await self._open_url(url)
            await asyncio.sleep(random.uniform(2.5, 4.0))  # 페이지 로드 대기

            # 2. 체류시간 결정
            dwell_time = random.randint(
                self.config.dwell_time_min,
                self.config.dwell_time_max
            )
            logger.info(f"Dwell time: {dwell_time}s")

            # 3. 자연스러운 읽기
            scroll_count = await self._natural_reading_pattern(dwell_time)

            actual_dwell = time.time() - start_time

            result = EngagementResult(
                success=True,
                url=url,
                dwell_time_sec=actual_dwell,
                scroll_count=scroll_count
            )

            # 통계 업데이트
            if self.current_stats:
                self.current_stats.total_engagements += 1
                self.current_stats.total_dwell_time += actual_dwell
                self.current_stats.total_scrolls += scroll_count
                self.current_stats.results.append(result)

            logger.info(f"Engagement complete: {scroll_count} scrolls, {actual_dwell:.1f}s")
            return result

        except Exception as e:
            logger.error(f"Engagement failed: {e}")
            return EngagementResult(
                success=False,
                url=url,
                dwell_time_sec=time.time() - start_time,
                scroll_count=0,
                error_message=str(e)
            )

    async def simulate_search_and_visit(
        self,
        keyword: str,
        result_index: int = 0
    ) -> EngagementResult:
        """
        검색 후 결과 클릭 시뮬레이션

        Args:
            keyword: 검색어
            result_index: 클릭할 결과 인덱스 (0 = 첫 번째)
        """
        start_time = time.time()

        try:
            # 1. 블로그 검색 열기 (EnhancedAdbTools 휴먼라이크)
            search_url = f"https://search.naver.com/search.naver?where=blog&query={keyword}"
            logger.info(f"Searching: {keyword}")
            await self._open_url(search_url)
            await asyncio.sleep(random.uniform(2.5, 4.0))

            # 2. 결과 클릭 (위치 계산 + EnhancedAdbTools 휴먼라이크)
            # 첫 번째 결과: 대략 y=600-700
            # 두 번째 결과: 대략 y=900-1000
            base_y = 650 + (result_index * 300)
            tap_y = min(base_y, self.config.screen_height - 200)

            logger.info(f"Clicking result #{result_index + 1}")
            await self._tap(self.config.screen_width // 2, tap_y)
            await asyncio.sleep(random.uniform(2.0, 3.5))

            # 3. 콘텐츠 읽기
            dwell_time = random.randint(
                self.config.dwell_time_min,
                self.config.dwell_time_max
            )
            scroll_count = await self._natural_reading_pattern(dwell_time)

            # 4. 뒤로가기 (EnhancedAdbTools 휴먼라이크)
            await self._go_back()
            await asyncio.sleep(random.uniform(1.0, 2.0))

            actual_dwell = time.time() - start_time

            result = EngagementResult(
                success=True,
                url=f"search:{keyword}#result{result_index}",
                dwell_time_sec=actual_dwell,
                scroll_count=scroll_count
            )

            if self.current_stats:
                self.current_stats.total_engagements += 1
                self.current_stats.total_dwell_time += actual_dwell
                self.current_stats.total_scrolls += scroll_count
                self.current_stats.results.append(result)

            return result

        except Exception as e:
            logger.error(f"Search engagement failed: {e}")
            return EngagementResult(
                success=False,
                url=f"search:{keyword}",
                dwell_time_sec=time.time() - start_time,
                scroll_count=0,
                error_message=str(e)
            )

    # =========================================================================
    # 세션 관리
    # =========================================================================

    def start_session(self, session_id: str) -> None:
        """새 세션 시작"""
        self.current_stats = SessionEngagementStats(session_id=session_id)

    def end_session(self) -> Optional[SessionEngagementStats]:
        """세션 종료 및 통계 반환"""
        stats = self.current_stats
        self.current_stats = None
        return stats

    def can_continue(self) -> bool:
        """추가 인게이지먼트 가능 여부"""
        if not self.current_stats:
            return True
        return self.current_stats.total_engagements < self.config.max_pageviews


# =============================================================================
# Full Engagement Session
# =============================================================================

async def run_engagement_session(
    keywords: List[str],
    device_serial: str = None,
    pageviews_per_session: int = 3
) -> SessionEngagementStats:
    """
    완전한 인게이지먼트 세션 실행

    Args:
        keywords: 검색할 키워드 목록
        device_serial: 디바이스 시리얼
        pageviews_per_session: 세션당 페이지뷰 수

    Returns:
        SessionEngagementStats
    """
    from .device_session_manager import DeviceSessionManager, SessionConfig

    # 1. 세션 매니저 생성
    session_mgr = DeviceSessionManager(
        SessionConfig(device_serial=device_serial)
    )

    # 2. 새 ID 생성 (IP 변경 + 쿠키 삭제)
    logger.info("Creating new identity...")
    reset_result = await session_mgr.create_new_identity()

    if not reset_result.success:
        logger.error(f"Failed to create new identity: {reset_result.error_message}")
        return SessionEngagementStats(session_id="failed")

    logger.info(f"New identity created: IP {reset_result.old_ip} -> {reset_result.new_ip}")

    # 3. 인게이지먼트 시뮬레이터 생성
    simulator = EngagementSimulator(
        EngagementConfig(device_serial=device_serial)
    )

    session_id = session_mgr.current_session.session_id
    simulator.start_session(session_id)

    # 4. 각 키워드로 인게이지먼트
    for i, keyword in enumerate(keywords[:pageviews_per_session]):
        if not simulator.can_continue():
            break

        logger.info(f"[{i+1}/{pageviews_per_session}] Keyword: {keyword}")

        # 결과 인덱스 랜덤 (첫 번째 ~ 세 번째)
        result_index = random.randint(0, 2)
        await simulator.simulate_search_and_visit(keyword, result_index)

        # 다음 검색 전 대기
        if i < len(keywords) - 1:
            wait_time = random.uniform(3.0, 8.0)
            logger.info(f"Waiting {wait_time:.1f}s before next search...")
            await asyncio.sleep(wait_time)

    # 5. 세션 종료
    stats = simulator.end_session()
    logger.info(f"Session complete: {stats.total_engagements} engagements, "
                f"{stats.total_dwell_time:.1f}s total dwell time")

    return stats
