"""
EnhancedAdbTools - 탐지 회피 기능이 강화된 ADB 도구

DroidRun AdbTools 기반 + BehaviorInjector 통합

Features:
- 베지어 커브 기반 자연스러운 탭
- motionevent 기반 커브 스와이프 (droidrun 스타일)
- 인간적인 타이핑
- 자동 SRT 쿠키 갱신 지원

Author: Naver AI Evolution System
Created: 2025-12-13
Updated: 2026-01-10 - Added motionevent curved swipe from droidrun
"""

import asyncio
import logging
import math
import random
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

from .behavior_injector import (
    BehaviorInjector,
    BehaviorConfig,
    TouchPoint,
    SwipeSegment,
    TypingEvent,
    ScrollStyle,
    create_stealth_injector,
)

logger = logging.getLogger("naver_evolution.device_tools")


# =============================================================================
# Curved Path Generation (from droidrun stealth_adb.py)
# =============================================================================

def ease_in_out_cubic(t: float) -> float:
    """
    휴먼라이크 속도 프로파일을 위한 가속/감속 커브.
    시작 시 가속, 끝에서 감속하는 자연스러운 움직임 생성.
    """
    if t < 0.5:
        return 4 * t**3
    else:
        return 1 - pow(-2 * t + 2, 3) / 2


def perlin_noise_1d(x: float, seed: int = 0) -> float:
    """
    손 떨림 시뮬레이션을 위한 1D 펄린 노이즈.
    순수 랜덤과 달리 부드럽고 유기적인 패턴 생성.
    """
    random.seed(seed + int(x * 1000))
    freq1 = random.uniform(0.5, 1.5)
    freq2 = random.uniform(2.0, 3.0)
    freq3 = random.uniform(4.0, 6.0)

    noise = (
        math.sin(x * freq1) * 0.5
        + math.sin(x * freq2) * 0.3
        + math.sin(x * freq3) * 0.2
    )
    return noise


def generate_curved_path(
    start_x: int, start_y: int,
    end_x: int, end_y: int,
    num_points: int = 15
) -> List[Tuple[int, int]]:
    """
    휴먼라이크 특성을 가진 베지어 커브 경로 생성.

    특징:
    - 속도 프로파일: 시작 시 가속, 끝에서 감속
    - 마이크로 지터: 손 떨림 시뮬레이션
    - 랜덤 제어점: 유기적인 커브

    Args:
        start_x, start_y: 시작 좌표
        end_x, end_y: 끝 좌표
        num_points: 경로 포인트 수

    Returns:
        [(x, y), ...] 좌표 리스트
    """
    # 거리 계산
    distance = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5

    # 짧은 스와이프는 포인트 수 줄임
    if distance <= 100:
        num_points = max(5, int(num_points / 3))

    # 중간점 계산
    mid_x = (start_x + end_x) / 2
    mid_y = (start_y + end_y) / 2

    # 제어점 오프셋 (커브 강도 10-25%)
    curve_intensity = random.uniform(0.1, 0.25)
    max_offset = distance * curve_intensity
    offset = random.uniform(-max_offset, max_offset)

    # 수직 방향 계산
    dx = end_x - start_x
    dy = end_y - start_y

    if distance > 0:
        perp_x = -dy / distance
        perp_y = dx / distance
        control_x = mid_x + perp_x * offset
        control_y = mid_y + perp_y * offset
    else:
        control_x = mid_x
        control_y = mid_y

    # 노이즈 시드 (일관성을 위해)
    noise_seed = random.randint(0, 10000)

    # 지터 강도 (거리에 비례)
    jitter_intensity = min(2.0, distance * 0.01)

    # 베지어 커브 경로 생성
    points = []
    for i in range(num_points):
        linear_t = i / (num_points - 1)

        # ease-in-out 적용
        eased_t = ease_in_out_cubic(linear_t)

        # 2차 베지어 공식: B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
        x = (
            (1 - eased_t) ** 2 * start_x
            + 2 * (1 - eased_t) * eased_t * control_x
            + eased_t**2 * end_x
        )
        y = (
            (1 - eased_t) ** 2 * start_y
            + 2 * (1 - eased_t) * eased_t * control_y
            + eased_t**2 * end_y
        )

        # 마이크로 지터 추가 (손 떨림)
        jitter_x = perlin_noise_1d(linear_t * 10, noise_seed) * jitter_intensity
        jitter_y = perlin_noise_1d(linear_t * 10, noise_seed + 1000) * jitter_intensity

        final_x = int(x + jitter_x)
        final_y = int(y + jitter_y)

        points.append((final_x, final_y))

    return points


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class AdbConfig:
    """ADB 도구 설정"""
    serial: Optional[str] = None           # 디바이스 시리얼 (None이면 자동 감지)
    default_timeout_ms: int = 30000        # 기본 타임아웃
    action_interval_min_ms: int = 100      # 액션 간 최소 간격
    action_interval_max_ms: int = 500      # 액션 간 최대 간격
    retry_count: int = 3                   # 재시도 횟수
    screen_width: int = 1080               # 화면 너비
    screen_height: int = 2400              # 화면 높이
    # Note: 모든 입력은 항상 휴먼라이크 (stealth_mode 제거됨)


@dataclass
class ActionResult:
    """액션 실행 결과"""
    success: bool
    message: str
    action_type: str
    duration_ms: int = 0
    details: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# EnhancedAdbTools Class
# =============================================================================

class EnhancedAdbTools:
    """
    탐지 회피 기능이 강화된 ADB 도구

    DroidRun의 AdbTools를 기반으로 BehaviorInjector를 통합하여
    자연스러운 인간 행동 패턴을 적용합니다.

    사용 예시:
        tools = EnhancedAdbTools(stealth_mode=True)
        await tools.connect()

        # 자연스러운 탭
        await tools.tap(540, 700)

        # 가변 속도 스크롤
        await tools.swipe(540, 1600, 540, 800)

        # 인간적인 타이핑
        await tools.input_text("검색어")
    """

    def __init__(
        self,
        config: AdbConfig = None,
        behavior_config: BehaviorConfig = None
    ):
        """
        Args:
            config: ADB 설정
            behavior_config: 행동 시뮬레이션 설정 (None이면 스텔스 모드 기본값)
        """
        self.config = config or AdbConfig()

        # 항상 휴먼라이크 BehaviorInjector 사용
        if behavior_config:
            self.behavior = BehaviorInjector(behavior_config)
        else:
            self.behavior = create_stealth_injector()

        # 상태
        self._connected = False
        self._serial = self.config.serial
        self._last_action_time = 0.0

        # 메모리 (에이전트용)
        self.memory: List[str] = []

        # UI 상태 캐시
        self.clickable_elements_cache: List[Dict[str, Any]] = []

    # =========================================================================
    # Connection Management
    # =========================================================================

    async def connect(self, serial: str = None) -> bool:
        """
        디바이스 연결

        Args:
            serial: 디바이스 시리얼 (None이면 자동 감지)

        Returns:
            연결 성공 여부
        """
        if serial:
            self._serial = serial
        elif not self._serial:
            # 자동 감지
            devices = await self._get_devices()
            if devices:
                self._serial = devices[0]
                logger.info(f"Auto-detected device: {self._serial}")
            else:
                logger.error("No devices found")
                return False

        # 연결 테스트
        result = await self._shell("echo connected")
        if "connected" in result:
            self._connected = True
            logger.info(f"Connected to device: {self._serial}")
            return True

        logger.error(f"Failed to connect to device: {self._serial}")
        return False

    async def disconnect(self):
        """디바이스 연결 해제"""
        self._connected = False
        logger.info("Disconnected from device")

    async def _get_devices(self) -> List[str]:
        """연결된 디바이스 목록 조회"""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=10
            )

            devices = []
            for line in result.stdout.strip().split('\n')[1:]:
                if '\tdevice' in line:
                    serial = line.split('\t')[0]
                    devices.append(serial)

            return devices
        except Exception as e:
            logger.error(f"Failed to get devices: {e}")
            return []

    async def _ensure_connected(self):
        """연결 상태 확인"""
        if not self._connected:
            success = await self.connect()
            if not success:
                raise ConnectionError("Device not connected")

    # =========================================================================
    # Shell Commands
    # =========================================================================

    async def _shell(self, command: str, timeout: int = None) -> str:
        """
        ADB 쉘 명령 실행

        Args:
            command: 쉘 명령어
            timeout: 타임아웃 (초)

        Returns:
            명령 출력
        """
        if timeout is None:
            timeout = self.config.default_timeout_ms // 1000

        try:
            adb_cmd = ["adb"]
            if self._serial:
                adb_cmd.extend(["-s", self._serial])
            adb_cmd.extend(["shell", command])

            result = subprocess.run(
                adb_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode != 0:
                logger.warning(f"Shell command failed: {result.stderr}")

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            logger.error(f"Shell command timeout: {command}")
            return ""
        except Exception as e:
            logger.error(f"Shell command error: {e}")
            return ""

    async def shell(self, command: str) -> str:
        """공개 쉘 명령 실행 (에이전트용)"""
        await self._ensure_connected()
        return await self._shell(command)

    # =========================================================================
    # Action Interval
    # =========================================================================

    async def _wait_action_interval(self):
        """액션 간 간격 대기"""
        now = time.time()
        elapsed = (now - self._last_action_time) * 1000

        min_interval = self.config.action_interval_min_ms
        max_interval = self.config.action_interval_max_ms

        if elapsed < min_interval:
            wait_time = self.behavior.random_delay(
                min_interval - int(elapsed),
                max_interval - int(elapsed)
            )
            await asyncio.sleep(wait_time / 1000)

        self._last_action_time = time.time()

    # =========================================================================
    # Tap Actions
    # =========================================================================

    async def tap(
        self,
        x: int,
        y: int,
        duration_ms: int = None
    ) -> ActionResult:
        """
        탭 실행 (항상 휴먼라이크 - 오프셋 및 지속시간 변화 적용)

        Args:
            x: X 좌표
            y: Y 좌표
            duration_ms: 탭 지속시간 (None이면 자동)

        Returns:
            ActionResult
        """
        await self._ensure_connected()
        await self._wait_action_interval()

        start_time = time.time()

        # 항상 휴먼라이크 탭 생성 (오프셋 + 지속시간 변화)
        tap_result = self.behavior.generate_human_tap(x, y)
        actual_x = tap_result.x
        actual_y = tap_result.y
        actual_duration = duration_ms or tap_result.duration_ms

        # 탭 실행 (베지어 커브 기반)
        if actual_duration > 100:
            # 롱 탭 - swipe로 구현
            cmd = f"input swipe {actual_x} {actual_y} {actual_x} {actual_y} {actual_duration}"
        else:
            # 일반 탭
            cmd = f"input tap {actual_x} {actual_y}"

        await self._shell(cmd)

        elapsed = int((time.time() - start_time) * 1000)

        logger.debug(f"Humanlike tap at ({actual_x}, {actual_y}) offset=({tap_result.offset_x}, {tap_result.offset_y})")

        return ActionResult(
            success=True,
            message=f"Tapped at ({actual_x}, {actual_y})",
            action_type="tap",
            duration_ms=elapsed,
            details={
                "original_x": x,
                "original_y": y,
                "actual_x": actual_x,
                "actual_y": actual_y,
                "offset_x": actual_x - x,
                "offset_y": actual_y - y,
            }
        )

    async def tap_by_index(self, index: int) -> ActionResult:
        """
        인덱스로 UI 요소 탭

        Args:
            index: 요소 인덱스 (clickable_elements_cache 기준)

        Returns:
            ActionResult
        """
        if not self.clickable_elements_cache:
            return ActionResult(
                success=False,
                message="No UI elements cached. Call get_state first.",
                action_type="tap_by_index"
            )

        # 인덱스로 요소 찾기
        element = self._find_element_by_index(self.clickable_elements_cache, index)

        if not element:
            return ActionResult(
                success=False,
                message=f"Element with index {index} not found",
                action_type="tap_by_index"
            )

        # 바운드에서 중심점 계산
        bounds = element.get("bounds", "")
        if not bounds:
            return ActionResult(
                success=False,
                message=f"Element {index} has no bounds",
                action_type="tap_by_index"
            )

        try:
            left, top, right, bottom = map(int, bounds.split(","))
            x = (left + right) // 2
            y = (top + bottom) // 2
        except ValueError:
            return ActionResult(
                success=False,
                message=f"Invalid bounds format: {bounds}",
                action_type="tap_by_index"
            )

        result = await self.tap(x, y)
        result.details["element_index"] = index
        result.details["element_text"] = element.get("text", "")
        result.details["element_class"] = element.get("className", "")

        return result

    def _find_element_by_index(
        self,
        elements: List[Dict],
        target_index: int
    ) -> Optional[Dict]:
        """인덱스로 요소 재귀 탐색"""
        for element in elements:
            if element.get("index") == target_index:
                return element

            children = element.get("children", [])
            result = self._find_element_by_index(children, target_index)
            if result:
                return result

        return None

    # =========================================================================
    # Swipe Actions (motionevent-based curved swipe from droidrun)
    # =========================================================================

    async def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration_ms: int = 1000,
        use_curved_path: bool = True
    ) -> ActionResult:
        """
        커브 스와이프 실행 (motionevent DOWN/MOVE/UP 사용)

        droidrun의 StealthAdbTools 방식 적용:
        - 베지어 커브 경로
        - ease-in-out 속도 프로파일
        - 마이크로 지터 (손 떨림)

        Args:
            start_x: 시작 X 좌표
            start_y: 시작 Y 좌표
            end_x: 끝 X 좌표
            end_y: 끝 Y 좌표
            duration_ms: 총 지속시간
            use_curved_path: 커브 경로 사용 여부 (False면 직선)

        Returns:
            ActionResult
        """
        await self._ensure_connected()
        await self._wait_action_interval()

        start_time = time.time()

        try:
            if use_curved_path:
                # 커브 경로 생성
                path_points = generate_curved_path(start_x, start_y, end_x, end_y)

                # motionevent로 터치 시작
                x0, y0 = path_points[0]
                await self._shell(f"input motionevent DOWN {x0} {y0}")

                # 포인트 간 딜레이 계산
                delay_between_points = (duration_ms / 1000) / len(path_points)

                # 중간 포인트들 이동
                for x, y in path_points[1:]:
                    await asyncio.sleep(delay_between_points)
                    await self._shell(f"input motionevent MOVE {x} {y}")

                # 터치 종료
                x_end, y_end = path_points[-1]
                await self._shell(f"input motionevent UP {x_end} {y_end}")

                path_type = "curved"
                num_points = len(path_points)
            else:
                # 기본 직선 스와이프 (fallback)
                cmd = f"input swipe {start_x} {start_y} {end_x} {end_y} {duration_ms}"
                await self._shell(cmd)
                path_type = "linear"
                num_points = 2

            elapsed = int((time.time() - start_time) * 1000)

            logger.debug(
                f"Humanlike {path_type} swipe from ({start_x}, {start_y}) to ({end_x}, {end_y}) "
                f"points={num_points}"
            )

            return ActionResult(
                success=True,
                message=f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})",
                action_type="swipe",
                duration_ms=elapsed,
                details={
                    "start_x": start_x,
                    "start_y": start_y,
                    "end_x": end_x,
                    "end_y": end_y,
                    "path_type": path_type,
                    "num_points": num_points,
                }
            )
        except Exception as e:
            logger.error(f"Swipe failed: {e}")
            return ActionResult(
                success=False,
                message=f"Swipe failed: {e}",
                action_type="swipe",
                duration_ms=int((time.time() - start_time) * 1000)
            )

    async def swipe_segmented(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        style: ScrollStyle = ScrollStyle.NATURAL
    ) -> ActionResult:
        """
        세그먼트 기반 스와이프 (중간 멈춤 포함, 레거시 호환)

        읽기 시뮬레이션처럼 중간에 멈추는 패턴이 필요할 때 사용.

        Args:
            start_x: 시작 X 좌표
            start_y: 시작 Y 좌표
            end_x: 끝 X 좌표
            end_y: 끝 Y 좌표
            style: 스크롤 스타일

        Returns:
            ActionResult
        """
        await self._ensure_connected()
        await self._wait_action_interval()

        start_time = time.time()

        # 세그먼트 생성 (BehaviorInjector)
        segments = self.behavior.generate_variable_scroll(
            start_y, end_y,
            screen_width=self.config.screen_width,
            style=style
        )

        # 각 세그먼트 실행
        for segment in segments:
            if segment.is_pause:
                await asyncio.sleep(segment.pause_duration_ms / 1000)
            else:
                # 세그먼트도 커브 스와이프로 실행
                await self.swipe(
                    segment.start_x, segment.start_y,
                    segment.end_x, segment.end_y,
                    duration_ms=segment.duration_ms,
                    use_curved_path=True
                )
                await asyncio.sleep(0.1)  # 세그먼트 간 간격

        elapsed = int((time.time() - start_time) * 1000)

        logger.debug(
            f"Segmented swipe from ({start_x}, {start_y}) to ({end_x}, {end_y}) "
            f"segments={len(segments)}"
        )

        return ActionResult(
            success=True,
            message=f"Segmented swipe from ({start_x}, {start_y}) to ({end_x}, {end_y})",
            action_type="swipe_segmented",
            duration_ms=elapsed,
            details={
                "start_x": start_x,
                "start_y": start_y,
                "end_x": end_x,
                "end_y": end_y,
                "style": style.value,
                "segments": len(segments),
            }
        )

    async def scroll_down(self, distance: int = 600) -> ActionResult:
        """아래로 스크롤"""
        center_x = self.config.screen_width // 2
        start_y = int(self.config.screen_height * 0.7)
        end_y = start_y - distance

        return await self.swipe(center_x, start_y, center_x, end_y)

    async def scroll_up(self, distance: int = 600) -> ActionResult:
        """위로 스크롤"""
        center_x = self.config.screen_width // 2
        start_y = int(self.config.screen_height * 0.3)
        end_y = start_y + distance

        return await self.swipe(center_x, start_y, center_x, end_y)

    # =========================================================================
    # Text Input
    # =========================================================================

    async def input_text(
        self,
        text: str,
        clear: bool = False
    ) -> ActionResult:
        """
        텍스트 입력 (항상 인간적 타이핑 - 지연 + 오타 + 백스페이스)

        Args:
            text: 입력할 텍스트
            clear: 기존 텍스트 지우기 여부

        Returns:
            ActionResult
        """
        await self._ensure_connected()
        await self._wait_action_interval()

        start_time = time.time()

        if clear:
            # 기존 텍스트 선택 및 삭제
            await self._shell("input keyevent KEYCODE_CTRL_LEFT KEYCODE_A")
            await asyncio.sleep(0.1)
            await self._shell("input keyevent KEYCODE_DEL")
            await asyncio.sleep(0.1)

        # 항상 인간적인 타이핑 시퀀스 생성 (지연 + 오타 + 수정)
        events = self.behavior.generate_human_typing(text)

        for event in events:
            if event.char == '\b':
                # 백스페이스 (오타 수정)
                await self._shell("input keyevent KEYCODE_DEL")
            else:
                # 문자 입력 (특수문자 이스케이프)
                escaped_char = self._escape_for_shell(event.char)
                await self._shell(f"input text '{escaped_char}'")

            # 가변 지연 (인간적 타이핑 속도)
            await asyncio.sleep(event.delay_ms / 1000)

        elapsed = int((time.time() - start_time) * 1000)

        logger.debug(f"Input text: {text[:20]}{'...' if len(text) > 20 else ''}")

        return ActionResult(
            success=True,
            message=f"Input text: {text[:30]}{'...' if len(text) > 30 else ''}",
            action_type="input_text",
            duration_ms=elapsed,
            details={
                "text_length": len(text),
                "cleared": clear,
            }
        )

    def _escape_for_shell(self, text: str) -> str:
        """쉘 명령용 텍스트 이스케이프"""
        # 공백을 %s로, 특수문자 이스케이프
        escaped = text.replace("'", "'\"'\"'")
        escaped = escaped.replace(" ", "%s")
        escaped = escaped.replace("&", "\\&")
        escaped = escaped.replace("|", "\\|")
        escaped = escaped.replace(";", "\\;")
        escaped = escaped.replace("$", "\\$")
        return escaped

    # =========================================================================
    # Key Press
    # =========================================================================

    async def press_key(self, keycode: Union[str, int]) -> ActionResult:
        """
        키 입력

        Args:
            keycode: 키 코드 (예: "KEYCODE_BACK", 4)

        Returns:
            ActionResult
        """
        await self._ensure_connected()
        await self._wait_action_interval()

        if isinstance(keycode, int):
            cmd = f"input keyevent {keycode}"
        else:
            cmd = f"input keyevent {keycode}"

        await self._shell(cmd)

        logger.debug(f"Press key: {keycode}")

        return ActionResult(
            success=True,
            message=f"Pressed key: {keycode}",
            action_type="press_key",
            details={"keycode": keycode}
        )

    async def back(self) -> ActionResult:
        """뒤로 가기"""
        return await self.press_key("KEYCODE_BACK")

    async def home(self) -> ActionResult:
        """홈 버튼"""
        return await self.press_key("KEYCODE_HOME")

    async def enter(self) -> ActionResult:
        """엔터 키"""
        return await self.press_key("KEYCODE_ENTER")

    # =========================================================================
    # App Control
    # =========================================================================

    async def start_app(
        self,
        package: str,
        activity: str = None,
        intent_args: str = None
    ) -> ActionResult:
        """
        앱 실행

        Args:
            package: 패키지명
            activity: 액티비티명 (None이면 메인)
            intent_args: 추가 인텐트 인자

        Returns:
            ActionResult
        """
        await self._ensure_connected()

        if activity:
            cmd = f"am start -n {package}/{activity}"
        elif intent_args:
            cmd = f"am start -a {intent_args} {package}"
        else:
            cmd = f"monkey -p {package} -c android.intent.category.LAUNCHER 1"

        await self._shell(cmd)

        logger.info(f"Started app: {package}")

        return ActionResult(
            success=True,
            message=f"Started app: {package}",
            action_type="start_app",
            details={"package": package, "activity": activity}
        )

    async def open_url(self, url: str, package: str = None) -> ActionResult:
        """
        URL 열기

        Args:
            url: 열 URL
            package: 브라우저 패키지 (None이면 기본)

        Returns:
            ActionResult
        """
        await self._ensure_connected()

        if package:
            cmd = f"am start -a android.intent.action.VIEW -d '{url}' {package}"
        else:
            cmd = f"am start -a android.intent.action.VIEW -d '{url}'"

        await self._shell(cmd)

        logger.info(f"Opened URL: {url}")

        return ActionResult(
            success=True,
            message=f"Opened URL: {url[:50]}{'...' if len(url) > 50 else ''}",
            action_type="open_url",
            details={"url": url, "package": package}
        )

    async def stop_app(self, package: str) -> ActionResult:
        """앱 강제 종료"""
        await self._ensure_connected()
        await self._shell(f"am force-stop {package}")

        logger.info(f"Stopped app: {package}")

        return ActionResult(
            success=True,
            message=f"Stopped app: {package}",
            action_type="stop_app",
            details={"package": package}
        )

    # =========================================================================
    # Screenshot
    # =========================================================================

    async def take_screenshot(self) -> Tuple[bool, Optional[bytes]]:
        """
        스크린샷 촬영

        Returns:
            (성공 여부, 스크린샷 바이트)
        """
        await self._ensure_connected()

        try:
            adb_cmd = ["adb"]
            if self._serial:
                adb_cmd.extend(["-s", self._serial])
            adb_cmd.extend(["exec-out", "screencap", "-p"])

            result = subprocess.run(
                adb_cmd,
                capture_output=True,
                timeout=10
            )

            if result.returncode == 0:
                return (True, result.stdout)
            else:
                return (False, None)

        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return (False, None)

    # =========================================================================
    # UI State
    # =========================================================================

    async def get_ui_hierarchy(self) -> Optional[str]:
        """UI 계층 구조 (XML) 가져오기"""
        await self._ensure_connected()

        # uiautomator dump
        await self._shell("uiautomator dump /sdcard/ui_dump.xml")
        result = await self._shell("cat /sdcard/ui_dump.xml")

        return result if result else None

    # =========================================================================
    # Memory (Agent Support)
    # =========================================================================

    def remember(self, information: str) -> str:
        """정보 기억 (에이전트용)"""
        if information and isinstance(information, str):
            self.memory.append(information.strip())

            # 최대 10개 유지
            if len(self.memory) > 10:
                self.memory = self.memory[-10:]

            return f"Remembered: {information}"
        return "Error: Invalid information"

    def get_memory(self) -> List[str]:
        """저장된 메모리 조회"""
        return self.memory.copy()

    def clear_memory(self):
        """메모리 초기화"""
        self.memory.clear()


# =============================================================================
# Factory Functions
# =============================================================================

def create_stealth_tools(serial: str = None) -> EnhancedAdbTools:
    """휴먼라이크 ADB 도구 생성 (기본값)"""
    config = AdbConfig(
        serial=serial,
        action_interval_min_ms=200,
        action_interval_max_ms=800,
    )
    return EnhancedAdbTools(config)


def create_fast_tools(serial: str = None) -> EnhancedAdbTools:
    """
    빠른 모드 도구 생성 (테스트용)

    NOTE: 여전히 휴먼라이크 동작 적용됨.
    단지 액션 간 간격이 짧을 뿐.
    """
    config = AdbConfig(
        serial=serial,
        action_interval_min_ms=50,
        action_interval_max_ms=100,
    )
    return EnhancedAdbTools(config)


def create_tools(serial: str = None) -> EnhancedAdbTools:
    """EnhancedAdbTools 생성 (기본 휴먼라이크)"""
    return create_stealth_tools(serial)
