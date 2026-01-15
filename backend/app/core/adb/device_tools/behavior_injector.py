"""
BehaviorInjector - 인간 행동 시뮬레이션 모듈

네이버 추적 시스템을 회피하기 위한 자연스러운 인간 행동 패턴 생성

Features:
- 베지어 커브 기반 터치 궤적
- 가변 속도 스크롤 (가속-유지-감속 + 중간 멈춤)
- 인간적인 타이핑 (지연 + 오타 + 백스페이스)
- 탭 위치 오프셋 및 지속시간 변화

Author: Naver AI Evolution System
Created: 2025-12-13
"""

import math
import random
import string
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class TouchPoint:
    """터치 포인트 (베지어 커브의 한 점)"""
    x: float
    y: float
    pressure: float = 1.0       # 터치 압력 (0.0 ~ 1.0)
    timestamp: float = 0.0      # 상대 시간 (0.0 ~ 1.0)

    def to_int_coords(self) -> Tuple[int, int]:
        """정수 좌표로 변환"""
        return (int(round(self.x)), int(round(self.y)))


@dataclass
class SwipeSegment:
    """스와이프 세그먼트 (가변 속도 스크롤의 한 구간)"""
    start_x: int
    start_y: int
    end_x: int
    end_y: int
    duration_ms: int
    is_pause: bool = False      # True면 이 구간에서 멈춤
    pause_duration_ms: int = 0  # 멈춤 시간


@dataclass
class TypingEvent:
    """타이핑 이벤트"""
    char: str                   # 입력 문자 ('\b' = 백스페이스)
    delay_ms: int               # 이전 키와의 지연 시간
    is_correction: bool = False # 오타 수정 여부


@dataclass
class TapResult:
    """탭 결과"""
    x: int
    y: int
    duration_ms: int
    offset_x: int               # 원본 대비 X 오프셋
    offset_y: int               # 원본 대비 Y 오프셋


class ScrollStyle(Enum):
    """스크롤 스타일"""
    NATURAL = "natural"         # 자연스러운 (가속-유지-감속)
    QUICK = "quick"             # 빠른 스킵
    READING = "reading"         # 읽기 모드 (느린 + 자주 멈춤)
    BROWSING = "browsing"       # 브라우징 (중간 속도)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class BehaviorConfig:
    """행동 시뮬레이션 설정"""

    # 타이핑 설정
    typing_delay_min_ms: int = 50
    typing_delay_max_ms: int = 500
    typing_error_rate: float = 0.08         # 8% 오타율
    typing_word_pause_extra_ms: int = 150   # 단어 시작시 추가 지연

    # 탭 설정
    tap_offset_max_px: int = 15             # 최대 위치 오프셋
    tap_offset_std_px: float = 5.0          # 오프셋 표준편차
    tap_duration_min_ms: int = 50
    tap_duration_max_ms: int = 150

    # 스크롤 설정
    scroll_acceleration_ratio: float = 0.25  # 가속 구간 비율
    scroll_deceleration_ratio: float = 0.20  # 감속 구간 비율
    scroll_pause_probability: float = 0.15   # 중간 멈춤 확률
    scroll_pause_min_ms: int = 300
    scroll_pause_max_ms: int = 800
    scroll_x_variance_px: int = 30           # X 좌표 변화 범위

    # 베지어 커브 설정
    bezier_control_point_variance: float = 20.0  # 제어점 분산
    bezier_sample_count_min: int = 10
    bezier_sample_count_max: int = 20

    # 압력 시뮬레이션
    pressure_start: float = 0.3
    pressure_peak: float = 1.0
    pressure_end: float = 0.2


# =============================================================================
# BehaviorInjector Class
# =============================================================================

class BehaviorInjector:
    """
    인간 행동 시뮬레이션 주입기

    네이버 추적 시스템(TIVAN, VETA, NLOG)을 회피하기 위한
    자연스러운 인간 행동 패턴을 생성합니다.

    사용 예시:
        injector = BehaviorInjector()

        # 베지어 커브 터치 궤적
        points = injector.generate_bezier_curve((100, 100), (500, 800))

        # 인간적인 탭
        tap = injector.generate_human_tap(540, 700)

        # 가변 속도 스크롤
        segments = injector.generate_variable_scroll(1600, 800)

        # 인간적인 타이핑
        events = injector.generate_human_typing("검색어")
    """

    def __init__(self, config: BehaviorConfig = None):
        """
        Args:
            config: 행동 시뮬레이션 설정 (None이면 기본값 사용)
        """
        self.config = config or BehaviorConfig()

        # 키보드 레이아웃 (오타 생성용)
        self._keyboard_layout = self._build_keyboard_layout()

    # =========================================================================
    # Bezier Curve Generation
    # =========================================================================

    def generate_bezier_curve(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        control_point_count: int = 2,
        sample_count: int = None
    ) -> List[TouchPoint]:
        """
        베지어 커브 기반 터치 궤적 생성

        Args:
            start: 시작점 (x, y)
            end: 끝점 (x, y)
            control_point_count: 제어점 개수 (2~4 권장)
            sample_count: 샘플링 개수 (None이면 자동)

        Returns:
            터치 포인트 리스트
        """
        if sample_count is None:
            sample_count = random.randint(
                self.config.bezier_sample_count_min,
                self.config.bezier_sample_count_max
            )

        # 제어점 생성
        control_points = self._generate_control_points(
            start, end, control_point_count
        )

        # 모든 점 (시작 + 제어점 + 끝)
        all_points = [start] + control_points + [end]

        # 베지어 곡선 샘플링
        curve_points = []
        for i in range(sample_count + 1):
            t = i / sample_count

            # De Casteljau 알고리즘으로 점 계산
            point = self._de_casteljau(all_points, t)

            # 압력 시뮬레이션 (시작/끝에서 약함, 중간에서 강함)
            pressure = self._calculate_pressure(t)

            curve_points.append(TouchPoint(
                x=point[0],
                y=point[1],
                pressure=pressure,
                timestamp=t
            ))

        return curve_points

    def _generate_control_points(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        count: int
    ) -> List[Tuple[float, float]]:
        """제어점 생성 (시작-끝 사이의 랜덤 위치)"""
        control_points = []
        variance = self.config.bezier_control_point_variance

        for i in range(count):
            # 시작-끝 직선 위의 기준점
            t = (i + 1) / (count + 1)
            base_x = start[0] + (end[0] - start[0]) * t
            base_y = start[1] + (end[1] - start[1]) * t

            # 가우시안 분포 오프셋 추가
            offset_x = random.gauss(0, variance)
            offset_y = random.gauss(0, variance)

            control_points.append((base_x + offset_x, base_y + offset_y))

        return control_points

    def _de_casteljau(
        self,
        points: List[Tuple[float, float]],
        t: float
    ) -> Tuple[float, float]:
        """De Casteljau 알고리즘으로 베지어 곡선의 점 계산"""
        # 점들의 복사본
        temp = list(points)
        n = len(temp) - 1

        for r in range(1, n + 1):
            for j in range(n - r + 1):
                temp[j] = (
                    (1 - t) * temp[j][0] + t * temp[j + 1][0],
                    (1 - t) * temp[j][1] + t * temp[j + 1][1]
                )

        return temp[0]

    def _calculate_pressure(self, t: float) -> float:
        """시간에 따른 터치 압력 계산 (사인 곡선 기반)"""
        # 시작과 끝에서 약하고 중간에서 강함
        cfg = self.config

        # 사인 곡선으로 자연스러운 압력 변화
        base_pressure = math.sin(math.pi * t)

        # 설정된 범위로 스케일링
        pressure_range = cfg.pressure_peak - min(cfg.pressure_start, cfg.pressure_end)
        min_pressure = min(cfg.pressure_start, cfg.pressure_end)

        return min_pressure + base_pressure * pressure_range

    # =========================================================================
    # Human Tap Generation
    # =========================================================================

    def generate_human_tap(
        self,
        x: int,
        y: int,
        precision: float = 1.0
    ) -> TapResult:
        """
        인간적인 탭 생성 (위치 오프셋 + 지속시간 변화)

        Args:
            x: 목표 X 좌표
            y: 목표 Y 좌표
            precision: 정밀도 (0.0~1.0, 낮을수록 더 큰 오프셋)

        Returns:
            TapResult 객체
        """
        cfg = self.config

        # 정밀도에 따른 오프셋 조정
        offset_std = cfg.tap_offset_std_px / max(precision, 0.1)

        # 가우시안 분포로 오프셋 생성
        offset_x = int(random.gauss(0, offset_std))
        offset_y = int(random.gauss(0, offset_std))

        # 최대 오프셋 제한
        max_offset = cfg.tap_offset_max_px
        offset_x = max(-max_offset, min(max_offset, offset_x))
        offset_y = max(-max_offset, min(max_offset, offset_y))

        # 지속시간 (짧은 탭 ~ 긴 탭)
        duration = random.randint(
            cfg.tap_duration_min_ms,
            cfg.tap_duration_max_ms
        )

        return TapResult(
            x=x + offset_x,
            y=y + offset_y,
            duration_ms=duration,
            offset_x=offset_x,
            offset_y=offset_y
        )

    def generate_long_press(
        self,
        x: int,
        y: int,
        duration_ms: int = 800
    ) -> TapResult:
        """롱 프레스 생성"""
        tap = self.generate_human_tap(x, y, precision=0.8)

        # 롱 프레스 지속시간 (약간의 변동)
        jitter = random.randint(-100, 200)
        tap.duration_ms = max(500, duration_ms + jitter)

        return tap

    # =========================================================================
    # Variable Scroll Generation
    # =========================================================================

    def generate_variable_scroll(
        self,
        start_y: int,
        end_y: int,
        screen_width: int = 1080,
        style: ScrollStyle = ScrollStyle.NATURAL
    ) -> List[SwipeSegment]:
        """
        가변 속도 스크롤 생성 (가속-유지-감속 + 중간 멈춤)

        Args:
            start_y: 시작 Y 좌표
            end_y: 끝 Y 좌표
            screen_width: 화면 너비 (X 좌표 계산용)
            style: 스크롤 스타일

        Returns:
            SwipeSegment 리스트
        """
        cfg = self.config
        distance = abs(end_y - start_y)
        direction = 1 if end_y > start_y else -1

        # 스타일별 파라미터
        style_params = self._get_scroll_style_params(style)

        segments = []
        current_y = start_y

        # 세그먼트 분할
        num_segments = random.randint(
            style_params['min_segments'],
            style_params['max_segments']
        )

        for i in range(num_segments):
            # 세그먼트 거리 및 속도 계산
            if i == 0:
                # 가속 구간
                seg_ratio = cfg.scroll_acceleration_ratio
                seg_distance = int(distance * seg_ratio)
                duration = random.randint(100, 200)
            elif i == num_segments - 1:
                # 감속 구간
                remaining = abs(end_y - current_y)
                seg_distance = remaining
                duration = random.randint(200, 400)
            else:
                # 중간 구간 (유지)
                remaining = abs(end_y - current_y)
                seg_ratio = random.uniform(0.3, 0.6)
                seg_distance = min(int(remaining * seg_ratio), remaining)
                duration = random.randint(
                    style_params['duration_min'],
                    style_params['duration_max']
                )

            next_y = current_y + (seg_distance * direction)

            # X 좌표 변화 (자연스러움을 위해)
            center_x = screen_width // 2
            start_x = center_x + random.randint(-cfg.scroll_x_variance_px, cfg.scroll_x_variance_px)
            end_x = center_x + random.randint(-cfg.scroll_x_variance_px, cfg.scroll_x_variance_px)

            segments.append(SwipeSegment(
                start_x=start_x,
                start_y=current_y,
                end_x=end_x,
                end_y=next_y,
                duration_ms=duration
            ))

            current_y = next_y

            # 중간 멈춤 (마지막 세그먼트 제외)
            if i < num_segments - 1:
                if random.random() < style_params['pause_probability']:
                    pause_duration = random.randint(
                        cfg.scroll_pause_min_ms,
                        cfg.scroll_pause_max_ms
                    )
                    segments.append(SwipeSegment(
                        start_x=end_x,
                        start_y=next_y,
                        end_x=end_x,
                        end_y=next_y,
                        duration_ms=0,
                        is_pause=True,
                        pause_duration_ms=pause_duration
                    ))

        return segments

    def _get_scroll_style_params(self, style: ScrollStyle) -> Dict[str, Any]:
        """스크롤 스타일별 파라미터"""
        cfg = self.config

        if style == ScrollStyle.QUICK:
            return {
                'min_segments': 2,
                'max_segments': 3,
                'duration_min': 100,
                'duration_max': 200,
                'pause_probability': 0.05
            }
        elif style == ScrollStyle.READING:
            return {
                'min_segments': 4,
                'max_segments': 6,
                'duration_min': 400,
                'duration_max': 700,
                'pause_probability': 0.35
            }
        elif style == ScrollStyle.BROWSING:
            return {
                'min_segments': 3,
                'max_segments': 4,
                'duration_min': 200,
                'duration_max': 400,
                'pause_probability': 0.20
            }
        else:  # NATURAL
            return {
                'min_segments': 3,
                'max_segments': 5,
                'duration_min': 150,
                'duration_max': 350,
                'pause_probability': cfg.scroll_pause_probability
            }

    # =========================================================================
    # Human Typing Generation
    # =========================================================================

    def generate_human_typing(
        self,
        text: str,
        error_rate: float = None
    ) -> List[TypingEvent]:
        """
        인간적인 타이핑 시퀀스 생성 (지연 + 오타 + 백스페이스)

        Args:
            text: 입력할 텍스트
            error_rate: 오타율 (None이면 설정값 사용)

        Returns:
            TypingEvent 리스트
        """
        cfg = self.config
        if error_rate is None:
            error_rate = cfg.typing_error_rate

        events = []
        prev_char = None

        for i, char in enumerate(text):
            # 기본 지연 시간 (가우시안 분포)
            mean_delay = (cfg.typing_delay_min_ms + cfg.typing_delay_max_ms) / 2
            std_delay = (cfg.typing_delay_max_ms - cfg.typing_delay_min_ms) / 4
            delay = int(random.gauss(mean_delay, std_delay))
            delay = max(cfg.typing_delay_min_ms, min(cfg.typing_delay_max_ms, delay))

            # 단어 시작시 추가 지연
            if prev_char == ' ' or prev_char is None:
                delay += random.randint(50, cfg.typing_word_pause_extra_ms)

            # 특수 문자나 대문자는 약간 더 지연
            if char.isupper() or char in '!@#$%^&*()':
                delay += random.randint(30, 80)

            # 오타 시뮬레이션
            if random.random() < error_rate and char.isalnum():
                wrong_char = self._get_nearby_key(char)
                if wrong_char and wrong_char != char:
                    # 잘못된 문자 입력
                    events.append(TypingEvent(
                        char=wrong_char,
                        delay_ms=delay,
                        is_correction=False
                    ))

                    # 잠시 후 인지
                    recognition_delay = random.randint(100, 400)

                    # 백스페이스
                    events.append(TypingEvent(
                        char='\b',
                        delay_ms=recognition_delay,
                        is_correction=True
                    ))

                    # 올바른 문자
                    events.append(TypingEvent(
                        char=char,
                        delay_ms=random.randint(50, 150),
                        is_correction=True
                    ))
                else:
                    # 오타 생성 실패시 정상 입력
                    events.append(TypingEvent(
                        char=char,
                        delay_ms=delay,
                        is_correction=False
                    ))
            else:
                # 정상 입력
                events.append(TypingEvent(
                    char=char,
                    delay_ms=delay,
                    is_correction=False
                ))

            prev_char = char

        return events

    def _build_keyboard_layout(self) -> Dict[str, List[str]]:
        """키보드 레이아웃 구성 (인접 키 매핑)"""
        # QWERTY 레이아웃 기준 인접 키
        layout = {
            'q': ['w', 'a', 's'],
            'w': ['q', 'e', 'a', 's', 'd'],
            'e': ['w', 'r', 's', 'd', 'f'],
            'r': ['e', 't', 'd', 'f', 'g'],
            't': ['r', 'y', 'f', 'g', 'h'],
            'y': ['t', 'u', 'g', 'h', 'j'],
            'u': ['y', 'i', 'h', 'j', 'k'],
            'i': ['u', 'o', 'j', 'k', 'l'],
            'o': ['i', 'p', 'k', 'l'],
            'p': ['o', 'l'],
            'a': ['q', 'w', 's', 'z', 'x'],
            's': ['q', 'w', 'e', 'a', 'd', 'z', 'x', 'c'],
            'd': ['w', 'e', 'r', 's', 'f', 'x', 'c', 'v'],
            'f': ['e', 'r', 't', 'd', 'g', 'c', 'v', 'b'],
            'g': ['r', 't', 'y', 'f', 'h', 'v', 'b', 'n'],
            'h': ['t', 'y', 'u', 'g', 'j', 'b', 'n', 'm'],
            'j': ['y', 'u', 'i', 'h', 'k', 'n', 'm'],
            'k': ['u', 'i', 'o', 'j', 'l', 'm'],
            'l': ['i', 'o', 'p', 'k'],
            'z': ['a', 's', 'x'],
            'x': ['z', 'a', 's', 'd', 'c'],
            'c': ['x', 's', 'd', 'f', 'v'],
            'v': ['c', 'd', 'f', 'g', 'b'],
            'b': ['v', 'f', 'g', 'h', 'n'],
            'n': ['b', 'g', 'h', 'j', 'm'],
            'm': ['n', 'h', 'j', 'k'],
            # 숫자
            '1': ['2', 'q'],
            '2': ['1', '3', 'q', 'w'],
            '3': ['2', '4', 'w', 'e'],
            '4': ['3', '5', 'e', 'r'],
            '5': ['4', '6', 'r', 't'],
            '6': ['5', '7', 't', 'y'],
            '7': ['6', '8', 'y', 'u'],
            '8': ['7', '9', 'u', 'i'],
            '9': ['8', '0', 'i', 'o'],
            '0': ['9', 'o', 'p'],
        }

        # 대문자 추가
        upper_layout = {}
        for key, neighbors in layout.items():
            if key.isalpha():
                upper_layout[key.upper()] = [n.upper() for n in neighbors if n.isalpha()]

        layout.update(upper_layout)
        return layout

    def _get_nearby_key(self, char: str) -> Optional[str]:
        """인접 키 반환 (오타 생성용)"""
        neighbors = self._keyboard_layout.get(char, [])
        if neighbors:
            return random.choice(neighbors)
        return None

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def add_jitter(
        self,
        value: int,
        jitter_percent: float = 0.1
    ) -> int:
        """값에 지터(변동) 추가"""
        jitter_range = int(value * jitter_percent)
        return value + random.randint(-jitter_range, jitter_range)

    def random_delay(
        self,
        min_ms: int = 100,
        max_ms: int = 500
    ) -> int:
        """랜덤 지연 시간 생성 (가우시안 분포)"""
        mean = (min_ms + max_ms) / 2
        std = (max_ms - min_ms) / 4
        delay = int(random.gauss(mean, std))
        return max(min_ms, min(max_ms, delay))

    def should_pause(self, probability: float = None) -> bool:
        """멈춤 여부 결정"""
        if probability is None:
            probability = self.config.scroll_pause_probability
        return random.random() < probability


# =============================================================================
# Convenience Functions
# =============================================================================

def create_stealth_injector() -> BehaviorInjector:
    """고 회피 모드 인젝터 생성"""
    config = BehaviorConfig(
        typing_delay_min_ms=80,
        typing_delay_max_ms=600,
        typing_error_rate=0.10,
        tap_offset_max_px=20,
        scroll_pause_probability=0.25,
        scroll_pause_min_ms=500,
        scroll_pause_max_ms=1200,
    )
    return BehaviorInjector(config)


def create_fast_injector() -> BehaviorInjector:
    """빠른 모드 인젝터 생성 (테스트용)"""
    config = BehaviorConfig(
        typing_delay_min_ms=20,
        typing_delay_max_ms=100,
        typing_error_rate=0.0,
        tap_offset_max_px=5,
        scroll_pause_probability=0.05,
    )
    return BehaviorInjector(config)
