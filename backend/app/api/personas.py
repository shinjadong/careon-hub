"""Persona management API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.services.persona_service import get_persona_service
from app.models.persona import (
    PersonaResponse,
    PersonaListResponse,
    PersonaCreate,
    PersonaUpdate,
    SoulSwapRequest,
    SoulSwapResponse,
    SessionStartRequest,
    SessionStartResponse,
    BanPersonaRequest,
    UnbanPersonaRequest
)

router = APIRouter(prefix="/api/personas", tags=["personas"])


@router.get("/", response_model=PersonaListResponse)
async def list_personas(
    status: Optional[str] = Query(None, description="상태 필터 (idle, active, cooling_down, banned, all)"),
    min_trust_score: int = Query(0, ge=0, description="최소 신뢰도 점수"),
    limit: int = Query(50, ge=1, le=100, description="페이지 크기"),
    offset: int = Query(0, ge=0, description="페이지 오프셋")
):
    """
    페르소나 목록 조회 (페이지네이션).

    Returns:
        PersonaListResponse with paginated results
    """
    service = get_persona_service()
    return await service.list_personas(
        status=status,
        min_trust_score=min_trust_score,
        limit=limit,
        offset=offset
    )


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(persona_id: str):
    """
    페르소나 단일 조회.

    Args:
        persona_id: Persona UUID

    Returns:
        PersonaResponse object

    Raises:
        HTTPException: If persona not found
    """
    service = get_persona_service()

    try:
        return await service.get_persona(persona_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/", response_model=PersonaResponse)
async def create_persona(request: PersonaCreate):
    """
    페르소나 생성.

    Args:
        request: PersonaCreate request

    Returns:
        Created PersonaResponse
    """
    service = get_persona_service()

    try:
        return await service.create_persona(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create persona: {str(e)}")


@router.patch("/{persona_id}", response_model=PersonaResponse)
async def update_persona(persona_id: str, updates: PersonaUpdate):
    """
    페르소나 업데이트.

    Args:
        persona_id: Persona UUID
        updates: PersonaUpdate request

    Returns:
        Updated PersonaResponse
    """
    service = get_persona_service()

    try:
        return await service.update_persona(persona_id, updates)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.post("/soul-swap", response_model=SoulSwapResponse)
async def execute_soul_swap(request: SoulSwapRequest):
    """
    Soul Swap 실행 (Phase 1-4).

    Phase 1: Cleanup (force-stop, pm clear)
    Phase 2: Identity Masking (ANDROID_ID, GPS)
    Phase 3: Restore (tar.gz 백업 복원)
    Phase 4: Launch (앱 실행)

    Args:
        request: SoulSwapRequest

    Returns:
        SoulSwapResponse with execution results
    """
    service = get_persona_service()
    return await service.execute_soul_swap(request)


@router.post("/{persona_id}/backup", response_model=SoulSwapResponse)
async def backup_persona(persona_id: str):
    """
    페르소나 백업 (Soul Swap Phase 5).

    세션 종료 후 앱 데이터를 백업합니다.

    Args:
        persona_id: Persona UUID

    Returns:
        SoulSwapResponse
    """
    service = get_persona_service()
    return await service.backup_persona(persona_id)


@router.post("/sessions/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    """
    세션 시작 (세션 레코드 생성).

    Args:
        request: SessionStartRequest

    Returns:
        SessionStartResponse with session_id
    """
    service = get_persona_service()
    return await service.start_session(request)


@router.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: str,
    success: bool = Query(..., description="세션 성공 여부"),
    failure_reason: Optional[str] = Query(None, description="실패 사유")
):
    """
    세션 완료 처리.

    Args:
        session_id: Session UUID
        success: 세션 성공 여부
        failure_reason: 실패 사유 (실패 시)

    Returns:
        Success message
    """
    service = get_persona_service()
    await service.complete_session(session_id, success, failure_reason)

    return {
        "success": True,
        "message": "Session completed",
        "session_id": session_id
    }


@router.get("/{persona_id}/sessions")
async def get_persona_sessions(
    persona_id: str,
    limit: int = Query(10, ge=1, le=100, description="조회할 세션 수")
):
    """
    특정 페르소나의 세션 이력 조회.

    Args:
        persona_id: Persona UUID
        limit: 조회할 세션 수

    Returns:
        List of session data
    """
    service = get_persona_service()
    sessions = await service.get_sessions_by_persona(persona_id, limit)

    return {
        "persona_id": persona_id,
        "sessions": sessions,
        "total": len(sessions)
    }


@router.post("/ban", response_model=PersonaResponse)
async def ban_persona(request: BanPersonaRequest):
    """
    페르소나 수동 밴 처리.

    Args:
        request: BanPersonaRequest

    Returns:
        Updated PersonaResponse
    """
    service = get_persona_service()
    return await service.ban_persona(request)


@router.post("/unban", response_model=PersonaResponse)
async def unban_persona(request: UnbanPersonaRequest):
    """
    페르소나 밴 해제.

    Args:
        request: UnbanPersonaRequest

    Returns:
        Updated PersonaResponse
    """
    service = get_persona_service()
    return await service.unban_persona(request)
