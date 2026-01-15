"""Common Pydantic models for CareOn Hub."""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class PaginationParams(BaseModel):
    """페이지네이션 파라미터."""

    limit: int = Field(default=50, ge=1, le=100, description="페이지 크기")
    offset: int = Field(default=0, ge=0, description="페이지 오프셋")


class PaginatedResponse(BaseModel):
    """페이지네이션 응답."""

    items: List[Any] = Field(description="결과 아이템 목록")
    total: int = Field(description="전체 아이템 수")
    limit: int = Field(description="페이지 크기")
    offset: int = Field(description="페이지 오프셋")


class ErrorResponse(BaseModel):
    """에러 응답."""

    error: str = Field(description="에러 메시지")
    detail: Optional[str] = Field(None, description="상세 에러 정보")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="발생 시각")


class HealthResponse(BaseModel):
    """헬스 체크 응답."""

    status: str = Field(description="서비스 상태")
    service: str = Field(description="서비스 이름")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="체크 시각")
    version: Optional[str] = Field(None, description="서비스 버전")


class SuccessResponse(BaseModel):
    """성공 응답."""

    success: bool = Field(True, description="성공 여부")
    message: str = Field(description="응답 메시지")
    data: Optional[Any] = Field(None, description="응답 데이터")
