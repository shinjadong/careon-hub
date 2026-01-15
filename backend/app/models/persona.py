"""Persona-related Pydantic models."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class PersonaBase(BaseModel):
    """페르소나 기본 정보."""

    name: str = Field(..., max_length=100, description="페르소나 이름")
    device_config: Dict[str, Any] = Field(description="디바이스 설정 (ANDROID_ID, IMEI 등)")
    behavior_profile: Dict[str, Any] = Field(default_factory=dict, description="행동 프로필")
    location: Optional[Dict[str, Any]] = Field(None, description="GPS 위치 정보")
    tags: List[str] = Field(default_factory=list, description="태그 목록")


class PersonaCreate(PersonaBase):
    """페르소나 생성 요청."""

    pass


class PersonaUpdate(BaseModel):
    """페르소나 업데이트 요청."""

    name: Optional[str] = Field(None, max_length=100)
    trust_score: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(idle|active|cooling_down|banned|retired)$")
    behavior_profile: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class PersonaResponse(PersonaBase):
    """페르소나 응답."""

    id: str = Field(description="페르소나 UUID")
    trust_score: int = Field(description="신뢰도 점수")
    status: str = Field(description="현재 상태")
    last_used_at: Optional[datetime] = Field(None, description="마지막 사용 시간")
    cooldown_until: Optional[datetime] = Field(None, description="쿨다운 종료 시간")
    total_sessions: int = Field(description="총 세션 수")
    successful_sessions: int = Field(description="성공한 세션 수")
    failed_sessions: int = Field(description="실패한 세션 수")
    performance_score: float = Field(description="성능 점수 (0-100)")
    created_at: datetime = Field(description="생성 시간")
    updated_at: datetime = Field(description="수정 시간")

    model_config = ConfigDict(from_attributes=True)


class PersonaListResponse(BaseModel):
    """페르소나 목록 응답."""

    items: List[PersonaResponse] = Field(description="페르소나 목록")
    total: int = Field(description="전체 개수")
    limit: int = Field(description="페이지 크기")
    offset: int = Field(description="페이지 오프셋")


class SoulSwapRequest(BaseModel):
    """Soul Swap 요청."""

    persona_id: str = Field(description="페르소나 UUID")
    apps: List[str] = Field(
        default=['naver_search', 'naver_blog'],
        description="백업/복원할 앱 목록"
    )


class SoulSwapResponse(BaseModel):
    """Soul Swap 응답."""

    persona_id: str = Field(description="페르소나 UUID")
    success: bool = Field(description="성공 여부")
    phase_completed: int = Field(description="완료된 Phase (1-5)")
    duration_seconds: float = Field(description="소요 시간 (초)")
    error_message: Optional[str] = Field(None, description="에러 메시지")


class SessionStartRequest(BaseModel):
    """세션 시작 요청."""

    persona_id: str = Field(description="페르소나 UUID")
    campaign_id: str = Field(description="캠페인 ID")


class SessionStartResponse(BaseModel):
    """세션 시작 응답."""

    session_id: str = Field(description="세션 UUID")
    persona_id: str = Field(description="페르소나 UUID")
    campaign_id: str = Field(description="캠페인 ID")
    started_at: datetime = Field(description="시작 시간")


class PersonaStatsResponse(BaseModel):
    """페르소나 통계 응답."""

    persona_id: str = Field(description="페르소나 UUID")
    total_sessions: int = Field(description="총 세션 수")
    successful_sessions: int = Field(description="성공한 세션 수")
    failed_sessions: int = Field(description="실패한 세션 수")
    success_rate: float = Field(description="성공률 (%)")
    average_duration: int = Field(description="평균 지속 시간 (초)")
    total_traffic: int = Field(description="총 트래픽 볼륨")
    total_conversions: int = Field(description="총 전환 수")


class BanPersonaRequest(BaseModel):
    """페르소나 밴 요청."""

    persona_id: str = Field(description="페르소나 UUID")
    reason: str = Field(description="밴 사유")


class UnbanPersonaRequest(BaseModel):
    """페르소나 밴 해제 요청."""

    persona_id: str = Field(description="페르소나 UUID")
