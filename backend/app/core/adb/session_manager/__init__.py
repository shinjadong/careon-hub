"""
Session Manager - 세션 리셋 및 IP 회전 관리

핑거프린트 실험 결과 기반:
- IP + 쿠키 변경 = 새로운 사용자로 인식
- NNB 쿠키가 1차 식별자
- 30분 쿨다운으로 재방문 제한 회피
"""

from .device_session_manager import (
    DeviceSessionManager,
    SessionConfig,
    SessionState,
    SessionResetResult,
)
from .engagement_simulator import (
    EngagementSimulator,
    EngagementConfig,
    EngagementResult,
)

__all__ = [
    "DeviceSessionManager",
    "SessionConfig",
    "SessionState",
    "SessionResetResult",
    "EngagementSimulator",
    "EngagementConfig",
    "EngagementResult",
]
