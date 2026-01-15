"""Device-related Pydantic models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class DeviceInfo(BaseModel):
    """디바이스 정보."""

    device_id: str = Field(description="디바이스 ID")
    model: str = Field(description="디바이스 모델명")
    manufacturer: str = Field(description="제조사")
    android_version: str = Field(description="Android 버전")
    status: str = Field(description="연결 상태 (connected, disconnected, offline)")
    battery_level: Optional[int] = Field(None, description="배터리 레벨 (%)")
    sdk_version: Optional[int] = Field(None, description="Android SDK 버전")


class DeviceStatus(BaseModel):
    """디바이스 상태."""

    device_id: str = Field(description="디바이스 ID")
    is_connected: bool = Field(description="연결 여부")
    last_seen: datetime = Field(description="마지막 확인 시간")


class DeviceAction(BaseModel):
    """디바이스 액션 요청."""

    action: str = Field(description="액션 타입 (reboot, screenshot, clear_cache)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="액션 파라미터")


class DeviceActionResponse(BaseModel):
    """디바이스 액션 응답."""

    device_id: str = Field(description="디바이스 ID")
    action: str = Field(description="실행한 액션")
    success: bool = Field(description="성공 여부")
    message: Optional[str] = Field(None, description="응답 메시지")
    data: Optional[Dict[str, Any]] = Field(None, description="추가 데이터")


class DeviceListResponse(BaseModel):
    """디바이스 목록 응답."""

    devices: list[DeviceInfo] = Field(description="디바이스 목록")
    total: int = Field(description="전체 디바이스 수")
