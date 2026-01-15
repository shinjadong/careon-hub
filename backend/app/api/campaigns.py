"""Campaign management API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.campaign_service import get_campaign_service
from app.models.campaign import (
    CampaignResponse,
    CampaignListResponse,
    CampaignCreate,
    CampaignUpdate,
    CampaignExecuteRequest,
    CampaignExecuteResponse,
    CampaignStatsResponse,
    CampaignControlRequest,
    CampaignControlResponse
)

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.get("/", response_model=CampaignListResponse)
async def list_campaigns(
    status: Optional[str] = Query(None, description="상태 필터 (active, paused, completed)"),
    limit: int = Query(50, ge=1, le=100, description="페이지 크기"),
    offset: int = Query(0, ge=0, description="페이지 오프셋")
):
    """
    캠페인 목록 조회.

    Returns:
        CampaignListResponse with paginated results
    """
    service = get_campaign_service()
    return await service.list_campaigns(
        status=status,
        limit=limit,
        offset=offset
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str):
    """
    캠페인 단일 조회.

    Args:
        campaign_id: Campaign ID

    Returns:
        CampaignResponse object

    Raises:
        HTTPException: If campaign not found
    """
    service = get_campaign_service()

    try:
        return await service.get_campaign(campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/", response_model=CampaignResponse)
async def create_campaign(request: CampaignCreate):
    """
    캠페인 생성.

    Args:
        request: CampaignCreate request

    Returns:
        Created CampaignResponse
    """
    service = get_campaign_service()

    try:
        return await service.create_campaign(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create campaign: {str(e)}")


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: str, updates: CampaignUpdate):
    """
    캠페인 업데이트.

    Args:
        campaign_id: Campaign ID
        updates: CampaignUpdate request

    Returns:
        Updated CampaignResponse
    """
    service = get_campaign_service()

    try:
        return await service.update_campaign(campaign_id, updates)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.post("/execute", response_model=CampaignExecuteResponse)
async def execute_campaign(request: CampaignExecuteRequest):
    """
    캠페인 실행.

    전체 워크플로우:
    1. 가용 페르소나 선택
    2. Soul Swap 실행 (Phase 1-4)
    3. 세션 레코드 생성
    4. Traffic 실행 (백그라운드)
    5. Soul Swap Backup (Phase 5)
    6. 체크인 및 통계 업데이트

    Args:
        request: CampaignExecuteRequest

    Returns:
        CampaignExecuteResponse with execution_id and status
    """
    service = get_campaign_service()
    return await service.execute_campaign(request)


@router.get("/{campaign_id}/stats", response_model=CampaignStatsResponse)
async def get_campaign_stats(campaign_id: str):
    """
    캠페인 통계 조회.

    Args:
        campaign_id: Campaign ID

    Returns:
        CampaignStatsResponse with execution statistics

    Raises:
        HTTPException: If campaign not found
    """
    service = get_campaign_service()

    try:
        return await service.get_campaign_stats(campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/{campaign_id}/control", response_model=CampaignControlResponse)
async def control_campaign(campaign_id: str, request: CampaignControlRequest):
    """
    캠페인 제어 (일시정지/재개/중지).

    Args:
        campaign_id: Campaign ID
        request: CampaignControlRequest (action: pause, resume, stop)

    Returns:
        CampaignControlResponse with success status
    """
    service = get_campaign_service()
    return await service.control_campaign(campaign_id, request)
