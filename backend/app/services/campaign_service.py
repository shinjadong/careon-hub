"""Campaign management service for CareOn Hub."""
import asyncio
import uuid
from typing import Optional, List
from datetime import datetime

from app.database.supabase import get_supabase_client
from app.services.persona_service import PersonaService
from app.services.device_service import DeviceService

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
from app.models.persona import SoulSwapRequest


class CampaignService:
    """캠페인 관리 서비스."""

    def __init__(self):
        """Initialize campaign service."""
        self.supabase = get_supabase_client()
        self.persona_service = PersonaService()
        self.device_service = DeviceService()

        # In-memory campaign storage (temporary - should use database)
        self._campaigns = {}
        self._running_campaigns = {}

    async def list_campaigns(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> CampaignListResponse:
        """
        캠페인 목록 조회 (임시 구현).

        Args:
            status: 상태 필터 (active, paused, completed)
            limit: 페이지 크기
            offset: 페이지 오프셋

        Returns:
            CampaignListResponse
        """
        # TODO: Replace with database query
        campaigns = list(self._campaigns.values())

        # Filter by status
        if status:
            campaigns = [c for c in campaigns if c.get('status') == status]

        # Pagination
        total = len(campaigns)
        paginated = campaigns[offset:offset + limit]

        # Convert to CampaignResponse
        campaign_responses = []
        for c in paginated:
            campaign_responses.append(CampaignResponse(
                id=c['id'],
                name=c['name'],
                description=c.get('description'),
                keyword=c['keyword'],
                target_blog_url=c['target_blog_url'],
                read_time_seconds=c.get('read_time_seconds', 120),
                status=c.get('status', 'active'),
                total_executions=c.get('total_executions', 0),
                successful_executions=c.get('successful_executions', 0),
                failed_executions=c.get('failed_executions', 0),
                created_at=c.get('created_at', datetime.utcnow()),
                updated_at=c.get('updated_at', datetime.utcnow())
            ))

        return CampaignListResponse(
            items=campaign_responses,
            total=total,
            limit=limit,
            offset=offset
        )

    async def get_campaign(self, campaign_id: str) -> CampaignResponse:
        """
        캠페인 단일 조회.

        Args:
            campaign_id: Campaign ID

        Returns:
            CampaignResponse

        Raises:
            ValueError: If campaign not found
        """
        campaign = self._campaigns.get(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        return CampaignResponse(
            id=campaign['id'],
            name=campaign['name'],
            description=campaign.get('description'),
            keyword=campaign['keyword'],
            target_blog_url=campaign['target_blog_url'],
            read_time_seconds=campaign.get('read_time_seconds', 120),
            status=campaign.get('status', 'active'),
            total_executions=campaign.get('total_executions', 0),
            successful_executions=campaign.get('successful_executions', 0),
            failed_executions=campaign.get('failed_executions', 0),
            created_at=campaign.get('created_at', datetime.utcnow()),
            updated_at=campaign.get('updated_at', datetime.utcnow())
        )

    async def create_campaign(self, request: CampaignCreate) -> CampaignResponse:
        """
        캠페인 생성.

        Args:
            request: CampaignCreate request

        Returns:
            Created CampaignResponse
        """
        campaign_id = str(uuid.uuid4())

        campaign_data = {
            'id': campaign_id,
            'name': request.name,
            'description': request.description,
            'keyword': request.keyword,
            'target_blog_url': request.target_blog_url,
            'read_time_seconds': request.read_time_seconds,
            'status': 'active',
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        self._campaigns[campaign_id] = campaign_data

        return await self.get_campaign(campaign_id)

    async def update_campaign(
        self,
        campaign_id: str,
        updates: CampaignUpdate
    ) -> CampaignResponse:
        """
        캠페인 업데이트.

        Args:
            campaign_id: Campaign ID
            updates: CampaignUpdate request

        Returns:
            Updated CampaignResponse
        """
        campaign = self._campaigns.get(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Apply updates
        update_data = updates.dict(exclude_unset=True)
        campaign.update(update_data)
        campaign['updated_at'] = datetime.utcnow()

        return await self.get_campaign(campaign_id)

    async def execute_campaign(
        self,
        request: CampaignExecuteRequest
    ) -> CampaignExecuteResponse:
        """
        캠페인 실행 (전체 워크플로우).

        Workflow:
        1. 가용 페르소나 선택 (Supabase RPC)
        2. Soul Swap 실행 (Phase 1-4)
        3. 세션 레코드 생성
        4. Traffic 실행 (백그라운드)
        5. Soul Swap Backup (Phase 5)
        6. 체크인

        Args:
            request: CampaignExecuteRequest

        Returns:
            CampaignExecuteResponse with execution_id and status
        """
        execution_id = str(uuid.uuid4())
        personas_assigned = []

        try:
            # Get campaign config
            campaign = self._campaigns.get(request.campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {request.campaign_id} not found")

            # Step 1: Select available persona (via Supabase RPC)
            print(f"[Campaign Execute] Selecting persona for {request.campaign_id}")
            persona_id = await self.supabase.select_available_persona(
                campaign_id=request.campaign_id,
                min_trust_score=request.min_trust_score
            )
            personas_assigned.append(persona_id)

            # Step 2: Execute Soul Swap (Phase 1-4)
            print(f"[Campaign Execute] Soul Swap for persona {persona_id}")
            swap_request = SoulSwapRequest(persona_id=persona_id)
            swap_result = await self.persona_service.execute_soul_swap(swap_request)

            if not swap_result.success:
                print(f"[Campaign Execute] Soul Swap failed: {swap_result.error_message}")
                # Mark execution as failed
                campaign['total_executions'] = campaign.get('total_executions', 0) + 1
                campaign['failed_executions'] = campaign.get('failed_executions', 0) + 1

                return CampaignExecuteResponse(
                    campaign_id=request.campaign_id,
                    execution_id=execution_id,
                    personas_assigned=personas_assigned,
                    status='failed',
                    started_at=datetime.utcnow()
                )

            # Step 3: Create session record
            print(f"[Campaign Execute] Creating session record")
            from app.models.persona import SessionStartRequest
            session_request = SessionStartRequest(
                persona_id=persona_id,
                campaign_id=request.campaign_id
            )
            session_response = await self.persona_service.start_session(session_request)
            session_id = session_response.session_id

            # Step 4: Execute traffic workflow (background)
            print(f"[Campaign Execute] Starting traffic workflow (background)")
            asyncio.create_task(
                self._execute_traffic_workflow(
                    persona_id=persona_id,
                    session_id=session_id,
                    campaign_id=request.campaign_id,
                    campaign_config=campaign
                )
            )

            # Track running campaign
            self._running_campaigns[execution_id] = {
                'campaign_id': request.campaign_id,
                'execution_id': execution_id,
                'persona_id': persona_id,
                'session_id': session_id,
                'status': 'running',
                'started_at': datetime.utcnow()
            }

            # Update campaign stats
            campaign['total_executions'] = campaign.get('total_executions', 0) + 1

            return CampaignExecuteResponse(
                campaign_id=request.campaign_id,
                execution_id=execution_id,
                personas_assigned=personas_assigned,
                status='running',
                started_at=datetime.utcnow()
            )

        except Exception as e:
            print(f"[Campaign Execute Error] {str(e)}")

            # Update failure count
            if request.campaign_id in self._campaigns:
                campaign = self._campaigns[request.campaign_id]
                campaign['total_executions'] = campaign.get('total_executions', 0) + 1
                campaign['failed_executions'] = campaign.get('failed_executions', 0) + 1

            return CampaignExecuteResponse(
                campaign_id=request.campaign_id,
                execution_id=execution_id,
                personas_assigned=personas_assigned,
                status='failed',
                started_at=datetime.utcnow()
            )

    async def _execute_traffic_workflow(
        self,
        persona_id: str,
        session_id: str,
        campaign_id: str,
        campaign_config: dict
    ):
        """
        트래픽 워크플로우 실행 (백그라운드 태스크).

        Args:
            persona_id: Persona UUID
            session_id: Session UUID
            campaign_id: Campaign ID
            campaign_config: Campaign configuration
        """
        success = False
        failure_reason = None

        try:
            print(f"[Traffic Workflow] Starting for campaign {campaign_id}")

            # Simulate traffic execution
            # TODO: Replace with actual Traffic Pipeline integration
            keyword = campaign_config['keyword']
            target_url = campaign_config['target_blog_url']
            read_time = campaign_config.get('read_time_seconds', 120)

            print(f"[Traffic Workflow] Keyword: {keyword}")
            print(f"[Traffic Workflow] Target: {target_url}")
            print(f"[Traffic Workflow] Read time: {read_time}s")

            # Simulate work
            await asyncio.sleep(5)  # Simulate traffic execution

            success = True
            print(f"[Traffic Workflow] Completed successfully")

        except Exception as e:
            success = False
            failure_reason = str(e)
            print(f"[Traffic Workflow Error] {failure_reason}")

        finally:
            # Step 5: Soul Swap Backup (Phase 5)
            print(f"[Traffic Workflow] Backing up persona {persona_id}")
            try:
                await self.persona_service.backup_persona(persona_id)
            except Exception as e:
                print(f"[Traffic Workflow] Backup failed: {e}")

            # Step 6: Complete session and checkin
            print(f"[Traffic Workflow] Completing session {session_id}")
            try:
                await self.persona_service.complete_session(
                    session_id=session_id,
                    success=success,
                    failure_reason=failure_reason
                )

                # Checkin persona (via Supabase RPC)
                await self.supabase.checkin_persona(
                    persona_id=persona_id,
                    session_id=session_id,
                    success=success,
                    failure_reason=failure_reason,
                    cooldown_minutes=30
                )

                # Update campaign stats
                campaign = self._campaigns.get(campaign_id)
                if campaign:
                    if success:
                        campaign['successful_executions'] = campaign.get('successful_executions', 0) + 1
                    else:
                        campaign['failed_executions'] = campaign.get('failed_executions', 0) + 1

                print(f"[Traffic Workflow] Checkin completed")

            except Exception as e:
                print(f"[Traffic Workflow] Checkin failed: {e}")

    async def get_campaign_stats(
        self,
        campaign_id: str
    ) -> CampaignStatsResponse:
        """
        캠페인 통계 조회.

        Args:
            campaign_id: Campaign ID

        Returns:
            CampaignStatsResponse

        Raises:
            ValueError: If campaign not found
        """
        campaign = self._campaigns.get(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Get sessions from Supabase
        sessions = await self.supabase.get_sessions_by_campaign(campaign_id)

        total = len(sessions)
        successful = len([s for s in sessions if s.get('status') == 'completed'])
        failed = len([s for s in sessions if s.get('status') == 'failed'])

        # Calculate average duration
        durations = [s.get('duration_seconds', 0) for s in sessions if s.get('duration_seconds')]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Calculate success rate
        success_rate = (successful / total * 100) if total > 0 else 0

        # Calculate traffic volume (sum of all traffic_volume)
        total_traffic = sum([s.get('traffic_volume', 0) for s in sessions])

        return CampaignStatsResponse(
            campaign_id=campaign_id,
            total_executions=campaign.get('total_executions', 0),
            successful_executions=campaign.get('successful_executions', 0),
            failed_executions=campaign.get('failed_executions', 0),
            average_duration_seconds=avg_duration,
            total_traffic_volume=total_traffic,
            success_rate=success_rate
        )

    async def control_campaign(
        self,
        campaign_id: str,
        request: CampaignControlRequest
    ) -> CampaignControlResponse:
        """
        캠페인 제어 (일시정지/재개/중지).

        Args:
            campaign_id: Campaign ID
            request: CampaignControlRequest

        Returns:
            CampaignControlResponse
        """
        campaign = self._campaigns.get(campaign_id)
        if not campaign:
            return CampaignControlResponse(
                campaign_id=campaign_id,
                action=request.action,
                success=False,
                message=f"Campaign {campaign_id} not found"
            )

        action = request.action

        if action == 'pause':
            campaign['status'] = 'paused'
            message = f"Campaign {campaign_id} paused"

        elif action == 'resume':
            campaign['status'] = 'active'
            message = f"Campaign {campaign_id} resumed"

        elif action == 'stop':
            campaign['status'] = 'completed'
            message = f"Campaign {campaign_id} stopped"

        else:
            return CampaignControlResponse(
                campaign_id=campaign_id,
                action=action,
                success=False,
                message=f"Invalid action: {action}"
            )

        campaign['updated_at'] = datetime.utcnow()

        return CampaignControlResponse(
            campaign_id=campaign_id,
            action=action,
            success=True,
            message=message
        )


def get_campaign_service() -> CampaignService:
    """
    Get CampaignService instance (for dependency injection).

    Returns:
        CampaignService instance
    """
    return CampaignService()
