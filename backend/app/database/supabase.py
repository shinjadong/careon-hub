"""Supabase client wrapper for CareOn Hub."""
from supabase import create_client, Client
from app.config import get_settings
from typing import Optional, List, Dict, Any


class SupabaseClient:
    """Singleton Supabase client wrapper."""

    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            settings = get_settings()
            cls._client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
        return cls._instance

    @property
    def client(self) -> Client:
        """Get the underlying Supabase client."""
        return self.__class__._client

    # ========================================
    # Personas Table Methods
    # ========================================

    async def list_personas(
        self,
        status: Optional[str] = None,
        min_trust_score: int = 0,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        페르소나 목록 조회 (페이지네이션).

        Args:
            status: 상태 필터 (idle, active, cooling_down, banned, all)
            min_trust_score: 최소 신뢰도 점수
            limit: 페이지 크기
            offset: 페이지 오프셋

        Returns:
            Dict containing items, total, limit, offset
        """
        query = self.client.table('personas').select('*', count='exact')

        # Status 필터
        if status and status != 'all':
            query = query.eq('status', status)

        # Trust score 필터
        if min_trust_score > 0:
            query = query.gte('trust_score', min_trust_score)

        # Count 조회 (필터 적용된 상태에서)
        count_response = query.execute()
        total = count_response.count if hasattr(count_response, 'count') else len(count_response.data)

        # 페이지네이션 적용
        response = query.order('trust_score', desc=True) \
                        .range(offset, offset + limit - 1) \
                        .execute()

        return {
            'items': response.data,
            'total': total,
            'limit': limit,
            'offset': offset
        }

    async def get_persona(self, persona_id: str) -> Dict[str, Any]:
        """
        페르소나 단일 조회.

        Args:
            persona_id: 페르소나 UUID

        Returns:
            Persona data dictionary

        Raises:
            Exception: If persona not found
        """
        response = self.client.table('personas') \
            .select('*') \
            .eq('id', persona_id) \
            .single() \
            .execute()

        if not response.data:
            raise ValueError(f"Persona {persona_id} not found")

        return response.data

    async def update_persona(
        self,
        persona_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        페르소나 업데이트.

        Args:
            persona_id: 페르소나 UUID
            updates: 업데이트할 필드 딕셔너리

        Returns:
            Updated persona data
        """
        response = self.client.table('personas') \
            .update(updates) \
            .eq('id', persona_id) \
            .execute()

        if not response.data:
            raise ValueError(f"Failed to update persona {persona_id}")

        return response.data[0]

    async def create_persona(self, persona_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        페르소나 생성.

        Args:
            persona_data: 페르소나 데이터

        Returns:
            Created persona data
        """
        response = self.client.table('personas') \
            .insert(persona_data) \
            .execute()

        if not response.data:
            raise ValueError("Failed to create persona")

        return response.data[0]

    # ========================================
    # Persona Sessions Table Methods
    # ========================================

    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        세션 레코드 생성.

        Args:
            session_data: 세션 데이터

        Returns:
            Created session data
        """
        response = self.client.table('persona_sessions') \
            .insert(session_data) \
            .execute()

        if not response.data:
            raise ValueError("Failed to create session")

        return response.data[0]

    async def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        세션 업데이트.

        Args:
            session_id: 세션 UUID
            updates: 업데이트할 필드

        Returns:
            Updated session data
        """
        response = self.client.table('persona_sessions') \
            .update(updates) \
            .eq('id', session_id) \
            .execute()

        if not response.data:
            raise ValueError(f"Failed to update session {session_id}")

        return response.data[0]

    async def get_sessions_by_persona(
        self,
        persona_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        특정 페르소나의 세션 이력 조회.

        Args:
            persona_id: 페르소나 UUID
            limit: 조회할 세션 수

        Returns:
            List of session data
        """
        response = self.client.table('persona_sessions') \
            .select('*') \
            .eq('persona_id', persona_id) \
            .order('started_at', desc=True) \
            .limit(limit) \
            .execute()

        return response.data

    async def get_sessions_by_campaign(
        self,
        campaign_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        특정 캠페인의 세션 이력 조회.

        Args:
            campaign_id: 캠페인 ID
            status: 세션 상태 필터 (optional)

        Returns:
            List of session data
        """
        query = self.client.table('persona_sessions') \
            .select('*') \
            .eq('campaign_id', campaign_id)

        if status:
            query = query.eq('status', status)

        response = query.order('started_at', desc=True).execute()

        return response.data

    # ========================================
    # RPC Functions
    # ========================================

    async def select_available_persona(
        self,
        campaign_id: str,
        min_trust_score: int = 0
    ) -> str:
        """
        RPC: 가용 페르소나 원자적 선택.

        Supabase RPC 함수를 호출하여 원자적으로 가용한 페르소나를 선택하고
        상태를 'active'로 변경합니다.

        Args:
            campaign_id: 캠페인 ID
            min_trust_score: 최소 신뢰도 점수

        Returns:
            Selected persona UUID

        Raises:
            Exception: If no available persona found
        """
        result = self.client.rpc('select_available_persona', {
            'campaign_id_param': campaign_id,
            'min_trust_score_param': min_trust_score
        }).execute()

        if not result.data:
            raise ValueError(
                f"No available persona found with min_trust_score={min_trust_score}"
            )

        return result.data

    async def checkin_persona(
        self,
        persona_id: str,
        session_id: str,
        success: bool,
        failure_reason: Optional[str] = None,
        cooldown_minutes: int = 30
    ) -> None:
        """
        RPC: 세션 종료 후 페르소나 체크인.

        세션 상태를 업데이트하고 페르소나 통계를 갱신하며
        쿨다운을 설정합니다.

        Args:
            persona_id: 페르소나 UUID
            session_id: 세션 UUID
            success: 세션 성공 여부
            failure_reason: 실패 사유 (실패 시)
            cooldown_minutes: 쿨다운 시간 (분)
        """
        self.client.rpc('checkin_persona', {
            'persona_id_param': persona_id,
            'session_id_param': session_id,
            'success': success,
            'failure_reason_param': failure_reason,
            'cooldown_minutes': cooldown_minutes
        }).execute()

    async def get_persona_stats(self, persona_id: str) -> Dict[str, Any]:
        """
        RPC: 페르소나 통계 조회.

        Args:
            persona_id: 페르소나 UUID

        Returns:
            Statistics dictionary containing:
                - total_sessions
                - successful_sessions
                - failed_sessions
                - success_rate
                - average_duration
                - total_traffic
                - total_conversions
        """
        result = self.client.rpc('get_persona_stats', {
            'persona_id_param': persona_id
        }).execute()

        if not result.data:
            raise ValueError(f"Failed to get stats for persona {persona_id}")

        return result.data

    async def ban_persona(self, persona_id: str, reason: str) -> None:
        """
        RPC: 페르소나 수동 밴 처리.

        Args:
            persona_id: 페르소나 UUID
            reason: 밴 사유
        """
        self.client.rpc('ban_persona', {
            'persona_id_param': persona_id,
            'reason_param': reason
        }).execute()

    async def unban_persona(self, persona_id: str) -> None:
        """
        RPC: 페르소나 밴 해제.

        Args:
            persona_id: 페르소나 UUID
        """
        self.client.rpc('unban_persona', {
            'persona_id_param': persona_id
        }).execute()


def get_supabase_client() -> SupabaseClient:
    """
    Get the singleton Supabase client instance.

    Used for dependency injection in FastAPI endpoints.

    Returns:
        SupabaseClient instance
    """
    return SupabaseClient()
