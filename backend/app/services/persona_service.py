"""Persona management service for CareOn Hub."""
import asyncio
import time
from typing import Optional, List
from datetime import datetime

from app.database.supabase import get_supabase_client
# Soul Swap imports (optional - requires ADB device and setup)
try:
    from app.core.soul_swap.soul.soul_manager import SoulManager
    from app.core.soul_swap.soul.app_data_paths import NAVER_APP
    from app.core.soul_swap.identity.device_identity import DeviceIdentityManager
    SOUL_SWAP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Soul Swap modules not available: {e}")
    SOUL_SWAP_AVAILABLE = False
    SoulManager = None
    DeviceIdentityManager = None
    NAVER_APP = None

from app.models.persona import (
    PersonaResponse,
    PersonaListResponse,
    PersonaUpdate,
    PersonaCreate,
    SoulSwapRequest,
    SoulSwapResponse,
    SessionStartRequest,
    SessionStartResponse,
    BanPersonaRequest,
    UnbanPersonaRequest
)


class PersonaService:
    """페르소나 관리 서비스."""

    def __init__(self):
        """Initialize persona service."""
        self.supabase = get_supabase_client()

        # Initialize Soul Swap components if available
        if SOUL_SWAP_AVAILABLE:
            self.soul_manager = SoulManager()
            self.identity_manager = DeviceIdentityManager()
        else:
            self.soul_manager = None
            self.identity_manager = None

    async def list_personas(
        self,
        status: Optional[str] = None,
        min_trust_score: int = 0,
        limit: int = 50,
        offset: int = 0
    ) -> PersonaListResponse:
        """
        페르소나 목록 조회 (페이지네이션).

        Args:
            status: 상태 필터 (idle, active, cooling_down, banned, all)
            min_trust_score: 최소 신뢰도 점수
            limit: 페이지 크기
            offset: 페이지 오프셋

        Returns:
            PersonaListResponse with paginated results
        """
        result = await self.supabase.list_personas(
            status=status,
            min_trust_score=min_trust_score,
            limit=limit,
            offset=offset
        )

        # Convert to Pydantic models
        personas = [PersonaResponse(**p) for p in result['items']]

        return PersonaListResponse(
            items=personas,
            total=result['total'],
            limit=result['limit'],
            offset=result['offset']
        )

    async def get_persona(self, persona_id: str) -> PersonaResponse:
        """
        페르소나 단일 조회.

        Args:
            persona_id: Persona UUID

        Returns:
            PersonaResponse object

        Raises:
            ValueError: If persona not found
        """
        persona_data = await self.supabase.get_persona(persona_id)
        return PersonaResponse(**persona_data)

    async def create_persona(self, request: PersonaCreate) -> PersonaResponse:
        """
        페르소나 생성.

        Args:
            request: PersonaCreate request

        Returns:
            Created PersonaResponse
        """
        persona_data = request.dict()
        created = await self.supabase.create_persona(persona_data)
        return PersonaResponse(**created)

    async def update_persona(
        self,
        persona_id: str,
        updates: PersonaUpdate
    ) -> PersonaResponse:
        """
        페르소나 업데이트.

        Args:
            persona_id: Persona UUID
            updates: PersonaUpdate request

        Returns:
            Updated PersonaResponse
        """
        update_data = updates.dict(exclude_unset=True)
        updated = await self.supabase.update_persona(persona_id, update_data)
        return PersonaResponse(**updated)

    async def execute_soul_swap(
        self,
        request: SoulSwapRequest
    ) -> SoulSwapResponse:
        """
        Soul Swap Phase 1-4 실행.

        Phase 1: Cleanup (force-stop, pm clear)
        Phase 2: Identity Masking (ANDROID_ID, GPS)
        Phase 3: Restore (tar.gz 백업 복원)
        Phase 4: Launch (앱 실행)

        Args:
            request: SoulSwapRequest

        Returns:
            SoulSwapResponse with success status and timing
        """
        if not SOUL_SWAP_AVAILABLE:
            return SoulSwapResponse(
                persona_id=request.persona_id,
                success=False,
                phase_completed=0,
                duration_seconds=0.0,
                error_message="Soul Swap modules not available (missing dependencies)"
            )

        start_time = time.time()

        try:
            # Get persona data
            persona_data = await self.supabase.get_persona(request.persona_id)
            persona_name = persona_data['name']
            device_config = persona_data.get('device_config', {})
            location = persona_data.get('location')

            # Phase 1: Cleanup
            print(f"[Soul Swap Phase 1] Cleanup apps for {persona_name}")
            await self.soul_manager.cleanup(NAVER_APP)
            # Note: Only using NAVER_APP for now (can add more apps later)

            # Phase 2: Identity Masking
            print(f"[Soul Swap Phase 2] Apply identity for {persona_name}")
            android_id = device_config.get('android_id')
            if android_id:
                await self.identity_manager.apply_identity(
                    android_id=android_id,
                    location=location
                )

            # Phase 3: Restore
            print(f"[Soul Swap Phase 3] Restore app data for {persona_name}")

            # Define backup paths
            backup_base = f"data/personas/{persona_name}"

            # Restore Naver app (default: naver_search)
            if 'naver_search' in request.apps or 'naver' in request.apps:
                await self.soul_manager.restore(
                    NAVER_APP,
                    backup_path=f"{backup_base}/naver.tar.gz"
                )

            # Note: Only using NAVER_APP for now (can add more apps later)

            # Phase 4: Launch
            print(f"[Soul Swap Phase 4] Launch app for {persona_name}")
            await self.soul_manager.launch_app(NAVER_APP)

            # Wait for app initialization
            await asyncio.sleep(5)

            duration = time.time() - start_time

            return SoulSwapResponse(
                persona_id=request.persona_id,
                success=True,
                phase_completed=4,  # Phase 5 is done after session
                duration_seconds=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"[Soul Swap Error] {str(e)}")
            return SoulSwapResponse(
                persona_id=request.persona_id,
                success=False,
                phase_completed=0,
                duration_seconds=duration,
                error_message=str(e)
            )

    async def backup_persona(self, persona_id: str) -> SoulSwapResponse:
        """
        Soul Swap Phase 5: Backup.

        세션 종료 후 앱 데이터를 백업합니다.

        Args:
            persona_id: Persona UUID

        Returns:
            SoulSwapResponse
        """
        if not SOUL_SWAP_AVAILABLE:
            return SoulSwapResponse(
                persona_id=persona_id,
                success=False,
                phase_completed=0,
                duration_seconds=0.0,
                error_message="Soul Swap modules not available (missing dependencies)"
            )

        start_time = time.time()

        try:
            # Get persona data
            persona_data = await self.supabase.get_persona(persona_id)
            persona_name = persona_data['name']

            print(f"[Soul Swap Phase 5] Backup app data for {persona_name}")

            # Define backup paths
            backup_base = f"data/personas/{persona_name}"

            # Backup Naver app
            await self.soul_manager.backup(
                NAVER_APP,
                backup_path=f"{backup_base}/naver.tar.gz"
            )

            # Note: Only using NAVER_APP for now (can add more apps later)

            duration = time.time() - start_time

            return SoulSwapResponse(
                persona_id=persona_id,
                success=True,
                phase_completed=5,
                duration_seconds=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"[Soul Swap Backup Error] {str(e)}")
            return SoulSwapResponse(
                persona_id=persona_id,
                success=False,
                phase_completed=4,
                duration_seconds=duration,
                error_message=str(e)
            )

    async def start_session(
        self,
        request: SessionStartRequest
    ) -> SessionStartResponse:
        """
        세션 시작 (세션 레코드 생성).

        Args:
            request: SessionStartRequest

        Returns:
            SessionStartResponse with session_id
        """
        session_data = {
            'persona_id': request.persona_id,
            'campaign_id': request.campaign_id,
            'status': 'running',
            'started_at': datetime.utcnow().isoformat()
        }

        created = await self.supabase.create_session(session_data)

        return SessionStartResponse(
            session_id=created['id'],
            persona_id=request.persona_id,
            campaign_id=request.campaign_id,
            started_at=datetime.fromisoformat(created['started_at'].replace('Z', '+00:00'))
        )

    async def complete_session(
        self,
        session_id: str,
        success: bool,
        failure_reason: Optional[str] = None
    ) -> None:
        """
        세션 완료 처리.

        Args:
            session_id: Session UUID
            success: 세션 성공 여부
            failure_reason: 실패 사유 (실패 시)
        """
        updates = {
            'status': 'completed' if success else 'failed',
            'completed_at': datetime.utcnow().isoformat()
        }

        if not success and failure_reason:
            updates['error_message'] = failure_reason

        await self.supabase.update_session(session_id, updates)

    async def ban_persona(self, request: BanPersonaRequest) -> PersonaResponse:
        """
        페르소나 수동 밴 처리.

        Args:
            request: BanPersonaRequest

        Returns:
            Updated PersonaResponse
        """
        await self.supabase.ban_persona(
            request.persona_id,
            request.reason
        )

        # Return updated persona
        return await self.get_persona(request.persona_id)

    async def unban_persona(self, request: UnbanPersonaRequest) -> PersonaResponse:
        """
        페르소나 밴 해제.

        Args:
            request: UnbanPersonaRequest

        Returns:
            Updated PersonaResponse
        """
        await self.supabase.unban_persona(request.persona_id)

        # Return updated persona
        return await self.get_persona(request.persona_id)

    async def get_sessions_by_persona(
        self,
        persona_id: str,
        limit: int = 10
    ) -> List[dict]:
        """
        특정 페르소나의 세션 이력 조회.

        Args:
            persona_id: Persona UUID
            limit: 조회할 세션 수

        Returns:
            List of session data
        """
        return await self.supabase.get_sessions_by_persona(persona_id, limit)

    async def get_sessions_by_campaign(
        self,
        campaign_id: str,
        status: Optional[str] = None
    ) -> List[dict]:
        """
        특정 캠페인의 세션 이력 조회.

        Args:
            campaign_id: Campaign ID
            status: 세션 상태 필터

        Returns:
            List of session data
        """
        return await self.supabase.get_sessions_by_campaign(campaign_id, status)


def get_persona_service() -> PersonaService:
    """
    Get PersonaService instance (for dependency injection).

    Returns:
        PersonaService instance
    """
    return PersonaService()
