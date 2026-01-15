"""Device management API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.services.device_service import get_device_service
from app.models.device import (
    DeviceInfo,
    DeviceStatus,
    DeviceActionResponse,
    DeviceListResponse
)

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("/", response_model=DeviceListResponse)
async def list_devices():
    """
    연결된 디바이스 목록 조회.

    Returns:
        DeviceListResponse containing list of devices
    """
    service = get_device_service()
    devices = await service.list_devices()

    return DeviceListResponse(
        devices=devices,
        total=len(devices)
    )


@router.get("/{device_id}", response_model=DeviceInfo)
async def get_device(device_id: str):
    """
    디바이스 상세 정보 조회.

    Args:
        device_id: Device serial number

    Returns:
        DeviceInfo object

    Raises:
        HTTPException: If device not found or error occurs
    """
    service = get_device_service()

    try:
        info = await service.get_device_info(device_id)
        return info
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Device {device_id} not found or unavailable: {str(e)}"
        )


@router.get("/{device_id}/status", response_model=DeviceStatus)
async def get_device_status(device_id: str):
    """
    디바이스 연결 상태 확인.

    Args:
        device_id: Device serial number

    Returns:
        DeviceStatus object
    """
    service = get_device_service()
    return await service.get_device_status(device_id)


@router.post("/{device_id}/reboot", response_model=DeviceActionResponse)
async def reboot_device(device_id: str):
    """
    디바이스 재부팅.

    Args:
        device_id: Device serial number

    Returns:
        DeviceActionResponse with success status
    """
    service = get_device_service()
    return await service.reboot_device(device_id)


@router.post("/{device_id}/screenshot", response_model=DeviceActionResponse)
async def take_screenshot(
    device_id: str,
    save_path: str = Query(
        default="/tmp/screenshot.png",
        description="로컬 저장 경로"
    )
):
    """
    스크린샷 촬영.

    Args:
        device_id: Device serial number
        save_path: Local file path to save screenshot

    Returns:
        DeviceActionResponse with file path
    """
    service = get_device_service()
    return await service.take_screenshot(device_id, save_path)


@router.post("/{device_id}/clear-app", response_model=DeviceActionResponse)
async def clear_app_data(
    device_id: str,
    package_name: str = Query(..., description="앱 패키지 이름")
):
    """
    앱 데이터 초기화.

    Args:
        device_id: Device serial number
        package_name: App package name

    Returns:
        DeviceActionResponse
    """
    service = get_device_service()
    return await service.clear_app_data(device_id, package_name)


@router.post("/{device_id}/force-stop", response_model=DeviceActionResponse)
async def force_stop_app(
    device_id: str,
    package_name: str = Query(..., description="앱 패키지 이름")
):
    """
    앱 강제 종료.

    Args:
        device_id: Device serial number
        package_name: App package name

    Returns:
        DeviceActionResponse
    """
    service = get_device_service()
    return await service.force_stop_app(device_id, package_name)
