"""Campaign-related Pydantic models."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class CampaignBase(BaseModel):
    """캠페인 기본 정보."""

    name: str = Field(description="캠페인 이름")
    description: Optional[str] = Field(None, description="캠페인 설명")
    keyword: str = Field(description="검색 키워드")
    target_blog_url: str = Field(description="타겟 블로그 URL")
    read_time_seconds: int = Field(default=120, ge=30, le=600, description="콘텐츠 읽기 시간 (초)")


class CampaignCreate(CampaignBase):
    """캠페인 생성 요청."""

    pass


class CampaignUpdate(BaseModel):
    """캠페인 업데이트 요청."""

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|paused|completed)$")
    keyword: Optional[str] = None
    target_blog_url: Optional[str] = None
    read_time_seconds: Optional[int] = Field(None, ge=30, le=600)


class CampaignResponse(CampaignBase):
    """캠페인 응답."""

    id: str = Field(description="캠페인 ID")
    status: str = Field(description="캠페인 상태")
    total_executions: int = Field(description="총 실행 횟수")
    successful_executions: int = Field(description="성공한 실행 횟수")
    failed_executions: int = Field(description="실패한 실행 횟수")
    created_at: datetime = Field(description="생성 시간")
    updated_at: datetime = Field(description="수정 시간")

    model_config = ConfigDict(from_attributes=True)


class CampaignListResponse(BaseModel):
    """캠페인 목록 응답."""

    items: List[CampaignResponse] = Field(description="캠페인 목록")
    total: int = Field(description="전체 개수")
    limit: int = Field(description="페이지 크기")
    offset: int = Field(description="페이지 오프셋")


class CampaignExecuteRequest(BaseModel):
    """캠페인 실행 요청."""

    campaign_id: str = Field(description="캠페인 ID")
    persona_count: int = Field(default=1, ge=1, le=10, description="사용할 페르소나 수")
    min_trust_score: int = Field(default=0, ge=0, description="최소 신뢰도 점수")


class CampaignExecuteResponse(BaseModel):
    """캠페인 실행 응답."""

    campaign_id: str = Field(description="캠페인 ID")
    execution_id: str = Field(description="실행 ID (UUID)")
    personas_assigned: List[str] = Field(description="할당된 페르소나 UUID 목록")
    status: str = Field(description="실행 상태 (queued, running, completed, failed)")
    started_at: datetime = Field(description="시작 시간")


class CampaignStatsResponse(BaseModel):
    """캠페인 통계 응답."""

    campaign_id: str = Field(description="캠페인 ID")
    total_executions: int = Field(description="총 실행 횟수")
    successful_executions: int = Field(description="성공한 실행 횟수")
    failed_executions: int = Field(description="실패한 실행 횟수")
    average_duration_seconds: float = Field(description="평균 지속 시간 (초)")
    total_traffic_volume: int = Field(description="총 트래픽 볼륨")
    success_rate: float = Field(description="성공률 (%)")


class CampaignControlRequest(BaseModel):
    """캠페인 제어 요청 (일시정지/재개/중지)."""

    action: str = Field(description="액션 (pause, resume, stop)", pattern="^(pause|resume|stop)$")


class CampaignControlResponse(BaseModel):
    """캠페인 제어 응답."""

    campaign_id: str = Field(description="캠페인 ID")
    action: str = Field(description="실행한 액션")
    success: bool = Field(description="성공 여부")
    message: Optional[str] = Field(None, description="응답 메시지")
