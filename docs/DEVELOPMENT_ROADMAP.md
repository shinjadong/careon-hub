# CareOn Hub - Development Roadmap

> 단계별 개발 로드맵 및 구현 가이드

**작성일**: 2026-01-16
**버전**: 1.0.0
**프로젝트**: CareOn Hub

---

## 목차

1. [개발 철학](#개발-철학)
2. [Phase 개요](#phase-개요)
3. [Phase B: Supabase 클라이언트](#phase-b-supabase-클라이언트)
4. [Phase C: Pydantic 모델](#phase-c-pydantic-모델)
5. [Phase D: 서비스 계층](#phase-d-서비스-계층)
6. [Phase E: API 라우터](#phase-e-api-라우터)
7. [Phase F: 프론트엔드 페이지](#phase-f-프론트엔드-페이지)
8. [Phase G: 통합 테스트](#phase-g-통합-테스트)
9. [Phase H: 배포 준비](#phase-h-배포-준비)
10. [예상 일정](#예상-일정)

---

## 개발 철학

### 우선순위 원칙

1. **P0 (최우선)**: 독립적이고 테스트 용이한 기능
2. **P1 (높음)**: 시스템 핵심 기능
3. **P2 (중간)**: 복잡한 통합 기능
4. **P3 (낮음)**: 부가 기능 및 최적화

### 개발 순서 전략

1. **의존성 우선**: 다른 모듈이 의존하는 기반부터 구현
2. **단순 → 복잡**: 간단한 것부터 시작해 복잡도 증가
3. **독립성 우선**: 독립적으로 테스트 가능한 모듈 우선
4. **점진적 통합**: 각 Phase 완료 후 통합 테스트

### 검증 방법

- **단위 테스트**: pytest로 각 함수/메서드 검증
- **통합 테스트**: 실제 Supabase/ADB 연동 테스트
- **수동 테스트**: curl 또는 프론트엔드로 E2E 확인

---

## Phase 개요

```
Phase A: 문서화 (완료) ✅
    ↓
Phase B: Supabase 클라이언트 (30분)
    ↓
Phase C: Pydantic 모델 (45분)
    ↓
Phase D: 서비스 계층 (4.5시간)
    ├─ D.1: DeviceService (P0, 60분)
    ├─ D.2: PersonaService (P1, 90분)
    └─ D.3: CampaignService (P2, 120분)
    ↓
Phase E: API 라우터 (90분)
    ├─ devices.py (P0, 30분)
    ├─ personas.py (P1, 30분)
    └─ campaigns.py (P2, 30분)
    ↓
Phase F: 프론트엔드 페이지 (2시간)
    ├─ Devices.tsx (P0, 40분)
    ├─ Personas.tsx (P1, 40분)
    └─ Campaigns.tsx (P2, 40분)
    ↓
Phase G: 통합 테스트 (1시간)
    ↓
Phase H: 배포 준비 (1시간)

총 예상 시간: 약 10시간
```

---

## Phase B: Supabase 클라이언트

**우선순위**: **필수** (모든 서비스가 의존)
**예상 소요 시간**: 30분
**담당 파일**: `backend/app/database/supabase.py`

### 구현 목표

Supabase와 통신하는 클라이언트 클래스 구현 (싱글톤 패턴)

### 구현 내용

#### 1. SupabaseClient 클래스 (15분)

**기본 구조**:
```python
# app/database/supabase.py
from supabase import create_client, Client
from app.config import get_settings
from typing import Optional, List, Dict, Any

class SupabaseClient:
    _instance: Optional[Client] = None

    def __new__(cls):
        if cls._instance is None:
            settings = get_settings()
            cls._instance = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
        return cls._instance

    @property
    def client(self) -> Client:
        return self._instance
```

#### 2. Personas 테이블 래퍼 (10분)

```python
class SupabaseClient:
    # ... (기존 코드)

    async def list_personas(
        self,
        status: Optional[str] = None,
        min_trust_score: int = 0,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """페르소나 목록 조회 (페이지네이션)"""
        query = self.client.table('personas').select('*')

        if status and status != 'all':
            query = query.eq('status', status)

        if min_trust_score > 0:
            query = query.gte('trust_score', min_trust_score)

        # 카운트 조회
        count_response = query.execute()
        total = len(count_response.data)

        # 페이지네이션
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
        """페르소나 단일 조회"""
        response = self.client.table('personas') \
            .select('*') \
            .eq('id', persona_id) \
            .single() \
            .execute()
        return response.data

    async def update_persona(
        self,
        persona_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """페르소나 업데이트"""
        response = self.client.table('personas') \
            .update(updates) \
            .eq('id', persona_id) \
            .execute()
        return response.data[0]
```

#### 3. RPC 함수 래퍼 (5분)

```python
class SupabaseClient:
    # ... (기존 코드)

    async def select_available_persona(
        self,
        campaign_id: str,
        min_trust_score: int = 0
    ) -> str:
        """RPC: 가용 페르소나 원자적 선택"""
        result = self.client.rpc('select_available_persona', {
            'campaign_id_param': campaign_id,
            'min_trust_score_param': min_trust_score
        }).execute()
        return result.data  # UUID 반환

    async def checkin_persona(
        self,
        persona_id: str,
        session_id: str,
        success: bool,
        failure_reason: Optional[str] = None,
        cooldown_minutes: int = 30
    ) -> None:
        """RPC: 세션 종료 후 페르소나 체크인"""
        self.client.rpc('checkin_persona', {
            'persona_id_param': persona_id,
            'session_id_param': session_id,
            'success': success,
            'failure_reason_param': failure_reason,
            'cooldown_minutes': cooldown_minutes
        }).execute()

    async def get_persona_stats(self, persona_id: str) -> Dict[str, Any]:
        """RPC: 페르소나 통계 조회"""
        result = self.client.rpc('get_persona_stats', {
            'persona_id_param': persona_id
        }).execute()
        return result.data
```

#### 4. 싱글톤 getter 함수

```python
def get_supabase_client() -> SupabaseClient:
    """의존성 주입용 getter"""
    return SupabaseClient()
```

### 검증 방법

**단위 테스트**:
```python
# tests/test_supabase.py
import pytest
from app.database.supabase import get_supabase_client

@pytest.mark.asyncio
async def test_list_personas():
    client = get_supabase_client()
    result = await client.list_personas(status='idle', limit=10)

    assert 'items' in result
    assert isinstance(result['items'], list)
    assert result['limit'] == 10

@pytest.mark.asyncio
async def test_select_available_persona():
    client = get_supabase_client()
    persona_id = await client.select_available_persona(
        campaign_id='test-campaign',
        min_trust_score=5
    )

    assert persona_id is not None
    assert len(persona_id) == 36  # UUID 길이
```

**수동 테스트**:
```python
# scripts/test_supabase.py
import asyncio
from app.database.supabase import get_supabase_client

async def main():
    client = get_supabase_client()

    # 테스트 1: 페르소나 목록
    personas = await client.list_personas(status='idle', limit=5)
    print(f"✓ Found {len(personas['items'])} idle personas")

    # 테스트 2: 가용 페르소나 선택
    persona_id = await client.select_available_persona('test-campaign')
    print(f"✓ Selected persona: {persona_id}")

    # 테스트 3: 페르소나 정보 조회
    persona = await client.get_persona(persona_id)
    print(f"✓ Persona name: {persona['name']}")

if __name__ == '__main__':
    asyncio.run(main())
```

---

## Phase C: Pydantic 모델

**우선순위**: **필수** (API 라우터가 의존)
**예상 소요 시간**: 45분
**담당 파일**: `backend/app/models/`

### 구현 목표

Request/Response를 위한 Pydantic 모델 정의

### 구현 순서

#### C.1: Common 모델 (P0, 10분)

**파일**: `app/models/common.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

class PaginationParams(BaseModel):
    """페이지네이션 파라미터"""
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class PaginatedResponse(BaseModel):
    """페이지네이션 응답"""
    items: List[Any]
    total: int
    limit: int
    offset: int

class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthResponse(BaseModel):
    """헬스 체크 응답"""
    status: str
    service: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

---

#### C.2: Device 모델 (P0, 10분)

**파일**: `app/models/device.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class DeviceInfo(BaseModel):
    """디바이스 정보"""
    device_id: str
    model: str
    manufacturer: str
    android_version: str
    status: str  # connected, disconnected, offline
    battery_level: Optional[int] = None

class DeviceStatus(BaseModel):
    """디바이스 상태"""
    device_id: str
    is_connected: bool
    last_seen: datetime

class DeviceAction(BaseModel):
    """디바이스 액션 요청"""
    action: str  # reboot, screenshot, clear_cache
    parameters: Optional[Dict[str, Any]] = None

class DeviceActionResponse(BaseModel):
    """디바이스 액션 응답"""
    device_id: str
    action: str
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
```

---

#### C.3: Persona 모델 (P1, 15분)

**파일**: `app/models/persona.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class PersonaBase(BaseModel):
    """페르소나 기본 정보"""
    name: str = Field(..., max_length=100)
    device_config: Dict[str, Any]
    behavior_profile: Dict[str, Any] = Field(default_factory=dict)
    location: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)

class PersonaCreate(PersonaBase):
    """페르소나 생성 요청"""
    pass

class PersonaUpdate(BaseModel):
    """페르소나 업데이트 요청"""
    name: Optional[str] = None
    trust_score: Optional[int] = None
    status: Optional[str] = None
    behavior_profile: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

class PersonaResponse(PersonaBase):
    """페르소나 응답"""
    id: str
    trust_score: int
    status: str
    last_used_at: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    total_sessions: int
    successful_sessions: int
    failed_sessions: int
    performance_score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PersonaListResponse(BaseModel):
    """페르소나 목록 응답"""
    items: List[PersonaResponse]
    total: int
    limit: int
    offset: int

class SoulSwapRequest(BaseModel):
    """Soul Swap 요청"""
    persona_id: str
    apps: List[str] = Field(
        default=['naver_search', 'naver_blog'],
        description="백업/복원할 앱 목록"
    )

class SoulSwapResponse(BaseModel):
    """Soul Swap 응답"""
    persona_id: str
    success: bool
    phase_completed: int  # 1-5
    duration_seconds: float
    error_message: Optional[str] = None

class SessionStartRequest(BaseModel):
    """세션 시작 요청"""
    persona_id: str
    campaign_id: str

class SessionStartResponse(BaseModel):
    """세션 시작 응답"""
    session_id: str
    persona_id: str
    campaign_id: str
    started_at: datetime
```

---

#### C.4: Campaign 모델 (P2, 10분)

**파일**: `app/models/campaign.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CampaignBase(BaseModel):
    """캠페인 기본 정보"""
    name: str
    description: Optional[str] = None
    keyword: str
    target_blog_url: str
    read_time_seconds: int = Field(default=120, ge=30, le=600)

class CampaignCreate(CampaignBase):
    """캠페인 생성 요청"""
    pass

class CampaignUpdate(BaseModel):
    """캠페인 업데이트 요청"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # active, paused, completed

class CampaignResponse(CampaignBase):
    """캠페인 응답"""
    id: str
    status: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CampaignExecuteRequest(BaseModel):
    """캠페인 실행 요청"""
    campaign_id: str
    persona_count: int = Field(default=1, ge=1, le=10)
    min_trust_score: int = Field(default=0, ge=0)

class CampaignExecuteResponse(BaseModel):
    """캠페인 실행 응답"""
    campaign_id: str
    execution_id: str
    personas_assigned: List[str]
    status: str  # queued, running, completed, failed
    started_at: datetime

class CampaignStatsResponse(BaseModel):
    """캠페인 통계 응답"""
    campaign_id: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_duration_seconds: float
    total_traffic_volume: int
    success_rate: float
```

### 검증 방법

**단위 테스트**:
```python
# tests/test_models.py
from app.models.persona import PersonaResponse

def test_persona_response():
    data = {
        'id': 'uuid-here',
        'name': 'test_persona',
        'device_config': {'android_id': '1234567890abcdef'},
        'behavior_profile': {},
        'trust_score': 15,
        'status': 'idle',
        'total_sessions': 100,
        'successful_sessions': 95,
        'failed_sessions': 5,
        'performance_score': 95.0,
        'created_at': '2026-01-16T12:00:00Z',
        'updated_at': '2026-01-16T12:00:00Z'
    }

    persona = PersonaResponse(**data)
    assert persona.name == 'test_persona'
    assert persona.trust_score == 15
```

---

## Phase D: 서비스 계층

**우선순위**: **핵심** (비즈니스 로직 구현)
**예상 소요 시간**: 4.5시간

---

### D.1: DeviceService (P0, 60분)

**우선순위**: **P0 - 최우선**
**이유**: 독립적, ADB만 사용, 빠른 검증 가능

**파일**: `app/services/device_service.py`

#### 구현 내용 (40분)

```python
# app/services/device_service.py
from app.core.adb.adb_enhanced import EnhancedAdbTools
from app.models.device import (
    DeviceInfo, DeviceStatus, DeviceAction, DeviceActionResponse
)
from typing import List
import asyncio

class DeviceService:
    def __init__(self):
        self.adb = EnhancedAdbTools()

    async def list_devices(self) -> List[DeviceInfo]:
        """연결된 디바이스 목록"""
        devices = self.adb.list_devices()
        result = []

        for device_id in devices:
            info = await self.get_device_info(device_id)
            result.append(info)

        return result

    async def get_device_info(self, device_id: str) -> DeviceInfo:
        """디바이스 상세 정보"""
        # ADB 명령으로 디바이스 정보 조회
        model = await self.adb.shell(
            device_id,
            "getprop ro.product.model"
        )
        manufacturer = await self.adb.shell(
            device_id,
            "getprop ro.product.manufacturer"
        )
        android_version = await self.adb.shell(
            device_id,
            "getprop ro.build.version.release"
        )
        battery_level = await self._get_battery_level(device_id)

        return DeviceInfo(
            device_id=device_id,
            model=model.strip(),
            manufacturer=manufacturer.strip(),
            android_version=android_version.strip(),
            status='connected',
            battery_level=battery_level
        )

    async def reboot_device(self, device_id: str) -> DeviceActionResponse:
        """디바이스 재부팅"""
        try:
            await self.adb.shell(device_id, "reboot")
            return DeviceActionResponse(
                device_id=device_id,
                action='reboot',
                success=True,
                message='재부팅 명령 전송 완료'
            )
        except Exception as e:
            return DeviceActionResponse(
                device_id=device_id,
                action='reboot',
                success=False,
                message=str(e)
            )

    async def take_screenshot(
        self,
        device_id: str,
        save_path: str
    ) -> DeviceActionResponse:
        """스크린샷 촬영"""
        try:
            # 디바이스에서 스크린샷 촬영
            await self.adb.shell(
                device_id,
                "screencap -p /sdcard/screenshot.png"
            )

            # PC로 전송
            await self.adb.pull(
                device_id,
                "/sdcard/screenshot.png",
                save_path
            )

            return DeviceActionResponse(
                device_id=device_id,
                action='screenshot',
                success=True,
                message=f'스크린샷 저장: {save_path}',
                data={'file_path': save_path}
            )
        except Exception as e:
            return DeviceActionResponse(
                device_id=device_id,
                action='screenshot',
                success=False,
                message=str(e)
            )

    async def _get_battery_level(self, device_id: str) -> int:
        """배터리 레벨 조회"""
        output = await self.adb.shell(
            device_id,
            "dumpsys battery | grep level"
        )
        # "level: 85" 형식 파싱
        level = int(output.split(':')[1].strip())
        return level
```

#### 검증 (20분)

**단위 테스트**:
```python
# tests/test_device_service.py
import pytest
from app.services.device_service import DeviceService

@pytest.mark.asyncio
async def test_list_devices():
    service = DeviceService()
    devices = await service.list_devices()

    assert isinstance(devices, list)
    if len(devices) > 0:
        device = devices[0]
        assert device.device_id is not None
        assert device.model is not None

@pytest.mark.asyncio
async def test_get_device_info():
    service = DeviceService()
    devices = await service.list_devices()

    if len(devices) > 0:
        device_id = devices[0].device_id
        info = await service.get_device_info(device_id)

        assert info.device_id == device_id
        assert info.battery_level is not None
```

**수동 테스트**:
```bash
# 실제 ADB 디바이스 연결 필요
adb devices

python -c "
import asyncio
from app.services.device_service import DeviceService

async def main():
    service = DeviceService()
    devices = await service.list_devices()
    print(f'Found {len(devices)} devices')
    for d in devices:
        print(f'  - {d.model} ({d.device_id}): {d.battery_level}%')

asyncio.run(main())
"
```

---

### D.2: PersonaService (P1, 90분)

**우선순위**: **P1 - 높음**
**이유**: 시스템 핵심 기능 (Soul Swap)

**파일**: `app/services/persona_service.py`

#### 구현 내용 (60분)

```python
# app/services/persona_service.py
from app.database.supabase import get_supabase_client
from app.core.soul_swap.soul import SoulManager, NAVER_SEARCH_APP, NAVER_BLOG_APP
from app.core.soul_swap.identity import DeviceIdentityManager
from app.models.persona import (
    PersonaResponse, PersonaListResponse, PersonaUpdate,
    SoulSwapRequest, SoulSwapResponse
)
from typing import Optional, List
import asyncio
import time

class PersonaService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.soul_manager = SoulManager()
        self.identity_manager = DeviceIdentityManager()

    async def list_personas(
        self,
        status: Optional[str] = None,
        min_trust_score: int = 0,
        limit: int = 50,
        offset: int = 0
    ) -> PersonaListResponse:
        """페르소나 목록 조회"""
        result = await self.supabase.list_personas(
            status=status,
            min_trust_score=min_trust_score,
            limit=limit,
            offset=offset
        )

        personas = [PersonaResponse(**p) for p in result['items']]

        return PersonaListResponse(
            items=personas,
            total=result['total'],
            limit=result['limit'],
            offset=result['offset']
        )

    async def get_persona(self, persona_id: str) -> PersonaResponse:
        """페르소나 단일 조회"""
        persona = await self.supabase.get_persona(persona_id)
        return PersonaResponse(**persona)

    async def update_persona(
        self,
        persona_id: str,
        updates: PersonaUpdate
    ) -> PersonaResponse:
        """페르소나 업데이트"""
        updated = await self.supabase.update_persona(
            persona_id,
            updates.dict(exclude_unset=True)
        )
        return PersonaResponse(**updated)

    async def execute_soul_swap(
        self,
        request: SoulSwapRequest
    ) -> SoulSwapResponse:
        """Soul Swap 5단계 프로세스 실행"""
        start_time = time.time()

        try:
            persona = await self.supabase.get_persona(request.persona_id)

            # Phase 1: Cleanup
            await self.soul_manager.cleanup(NAVER_SEARCH_APP)
            await self.soul_manager.cleanup(NAVER_BLOG_APP)

            # Phase 2: Identity Masking
            device_config = persona['device_config']
            await self.identity_manager.apply_identity(
                android_id=device_config['android_id'],
                location=persona.get('location')
            )

            # Phase 3: Restore
            persona_name = persona['name']
            await self.soul_manager.restore(
                NAVER_SEARCH_APP,
                backup_path=f"data/personas/{persona_name}/naver_search.tar.gz"
            )
            await self.soul_manager.restore(
                NAVER_BLOG_APP,
                backup_path=f"data/personas/{persona_name}/naver_blog.tar.gz"
            )

            # Phase 4: Launch
            await self.soul_manager.launch_app(NAVER_SEARCH_APP)
            await asyncio.sleep(5)  # 초기화 대기

            duration = time.time() - start_time

            return SoulSwapResponse(
                persona_id=request.persona_id,
                success=True,
                phase_completed=4,  # Phase 5는 세션 종료 시
                duration_seconds=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            return SoulSwapResponse(
                persona_id=request.persona_id,
                success=False,
                phase_completed=0,
                duration_seconds=duration,
                error_message=str(e)
            )

    async def backup_persona(self, persona_id: str) -> SoulSwapResponse:
        """Soul Swap Phase 5: Backup"""
        start_time = time.time()

        try:
            persona = await self.supabase.get_persona(persona_id)
            persona_name = persona['name']

            # Backup all apps
            await self.soul_manager.backup(
                NAVER_SEARCH_APP,
                backup_path=f"data/personas/{persona_name}/naver_search.tar.gz"
            )
            await self.soul_manager.backup(
                NAVER_BLOG_APP,
                backup_path=f"data/personas/{persona_name}/naver_blog.tar.gz"
            )

            duration = time.time() - start_time

            return SoulSwapResponse(
                persona_id=persona_id,
                success=True,
                phase_completed=5,
                duration_seconds=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            return SoulSwapResponse(
                persona_id=persona_id,
                success=False,
                phase_completed=4,
                duration_seconds=duration,
                error_message=str(e)
            )
```

#### 검증 (30분)

**통합 테스트** (실제 ADB 디바이스 필요):
```python
# tests/integration/test_persona_service.py
import pytest
from app.services.persona_service import PersonaService
from app.models.persona import SoulSwapRequest

@pytest.mark.asyncio
async def test_soul_swap_full_cycle():
    service = PersonaService()

    # 1. 가용 페르소나 조회
    personas = await service.list_personas(status='idle', limit=1)
    assert len(personas.items) > 0

    persona_id = personas.items[0].id

    # 2. Soul Swap 실행 (Phase 1-4)
    swap_request = SoulSwapRequest(persona_id=persona_id)
    swap_result = await service.execute_soul_swap(swap_request)

    assert swap_result.success is True
    assert swap_result.phase_completed == 4
    print(f"✓ Soul Swap 완료: {swap_result.duration_seconds:.1f}초")

    # 3. Backup (Phase 5)
    backup_result = await service.backup_persona(persona_id)

    assert backup_result.success is True
    assert backup_result.phase_completed == 5
    print(f"✓ Backup 완료: {backup_result.duration_seconds:.1f}초")
```

---

### D.3: CampaignService (P2, 120분)

**우선순위**: **P2 - 중간**
**이유**: 가장 복잡한 통합 (PersonaService + DeviceService + Traffic Pipeline)

**파일**: `app/services/campaign_service.py`

#### 구현 내용 (80분)

```python
# app/services/campaign_service.py
from app.database.supabase import get_supabase_client
from app.services.persona_service import PersonaService
from app.core.traffic.pipeline import NaverSessionPipeline
from app.core.adb.adb_enhanced import EnhancedAdbTools
from app.core.portal.client import PortalClient
from app.models.campaign import (
    CampaignResponse, CampaignExecuteRequest, CampaignExecuteResponse,
    CampaignStatsResponse
)
from typing import List
import asyncio
import uuid
import time

class CampaignService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.persona_service = PersonaService()
        self.adb = EnhancedAdbTools()
        self.portal = PortalClient()

    async def execute_campaign(
        self,
        request: CampaignExecuteRequest
    ) -> CampaignExecuteResponse:
        """캠페인 실행 (전체 워크플로우)"""
        execution_id = str(uuid.uuid4())
        personas_assigned = []

        try:
            # Step 1: 페르소나 선택 (RPC)
            persona_id = await self.supabase.select_available_persona(
                campaign_id=request.campaign_id,
                min_trust_score=request.min_trust_score
            )
            personas_assigned.append(persona_id)

            # Step 2: Soul Swap 실행
            await self._execute_soul_swap(persona_id)

            # Step 3: 세션 레코드 생성
            session_id = await self._create_session(
                persona_id=persona_id,
                campaign_id=request.campaign_id,
                execution_id=execution_id
            )

            # Step 4: Traffic Pipeline 실행 (비동기)
            asyncio.create_task(
                self._execute_traffic_workflow(
                    persona_id=persona_id,
                    session_id=session_id,
                    campaign_id=request.campaign_id
                )
            )

            return CampaignExecuteResponse(
                campaign_id=request.campaign_id,
                execution_id=execution_id,
                personas_assigned=personas_assigned,
                status='running',
                started_at=datetime.utcnow()
            )

        except Exception as e:
            return CampaignExecuteResponse(
                campaign_id=request.campaign_id,
                execution_id=execution_id,
                personas_assigned=personas_assigned,
                status='failed',
                started_at=datetime.utcnow()
            )

    async def _execute_soul_swap(self, persona_id: str):
        """Soul Swap Phase 1-4"""
        from app.models.persona import SoulSwapRequest
        swap_request = SoulSwapRequest(persona_id=persona_id)
        result = await self.persona_service.execute_soul_swap(swap_request)

        if not result.success:
            raise Exception(f"Soul Swap failed: {result.error_message}")

    async def _create_session(
        self,
        persona_id: str,
        campaign_id: str,
        execution_id: str
    ) -> str:
        """세션 레코드 생성"""
        session_data = {
            'persona_id': persona_id,
            'campaign_id': campaign_id,
            'execution_id': execution_id,
            'status': 'running',
            'started_at': 'now()'
        }

        response = await self.supabase.client.table('persona_sessions') \
            .insert(session_data) \
            .execute()

        return response.data[0]['id']

    async def _execute_traffic_workflow(
        self,
        persona_id: str,
        session_id: str,
        campaign_id: str
    ):
        """트래픽 워크플로우 실행 (백그라운드)"""
        success = False
        failure_reason = None

        try:
            # 캠페인 설정 조회
            campaign = await self._get_campaign_config(campaign_id)

            # Pipeline 실행
            pipeline = NaverSessionPipeline(
                adb_tools=self.adb,
                portal_client=self.portal
            )

            result = await pipeline.run_campaign_workflow(
                keyword=campaign['keyword'],
                target_blog_url=campaign['target_blog_url'],
                read_time_seconds=campaign['read_time_seconds']
            )

            success = result['success']
            if not success:
                failure_reason = result.get('error')

        except Exception as e:
            success = False
            failure_reason = str(e)

        finally:
            # Soul Swap Phase 5: Backup
            await self.persona_service.backup_persona(persona_id)

            # 체크인
            await self.supabase.checkin_persona(
                persona_id=persona_id,
                session_id=session_id,
                success=success,
                failure_reason=failure_reason,
                cooldown_minutes=30
            )

    async def _get_campaign_config(self, campaign_id: str) -> dict:
        """캠페인 설정 조회 (임시 하드코딩)"""
        # TODO: 실제로는 campaigns 테이블에서 조회
        return {
            'keyword': 'CCTV 설치',
            'target_blog_url': 'https://blog.naver.com/...',
            'read_time_seconds': 120
        }

    async def get_campaign_stats(
        self,
        campaign_id: str
    ) -> CampaignStatsResponse:
        """캠페인 통계 조회"""
        # Supabase에서 세션 집계
        sessions = await self.supabase.client.table('persona_sessions') \
            .select('*') \
            .eq('campaign_id', campaign_id) \
            .execute()

        total = len(sessions.data)
        successful = len([s for s in sessions.data if s['status'] == 'completed'])
        failed = len([s for s in sessions.data if s['status'] == 'failed'])

        avg_duration = sum([
            s['duration_seconds'] for s in sessions.data
            if s.get('duration_seconds')
        ]) / max(total, 1)

        return CampaignStatsResponse(
            campaign_id=campaign_id,
            total_executions=total,
            successful_executions=successful,
            failed_executions=failed,
            average_duration_seconds=avg_duration,
            total_traffic_volume=0,  # TODO
            success_rate=successful / max(total, 1) * 100
        )
```

#### 검증 (40분)

**E2E 테스트** (실제 환경 필요):
```python
# tests/integration/test_campaign_e2e.py
import pytest
from app.services.campaign_service import CampaignService
from app.models.campaign import CampaignExecuteRequest

@pytest.mark.asyncio
async def test_campaign_full_execution():
    service = CampaignService()

    # 캠페인 실행
    request = CampaignExecuteRequest(
        campaign_id='test-campaign-123',
        persona_count=1,
        min_trust_score=5
    )

    result = await service.execute_campaign(request)

    assert result.status == 'running'
    assert len(result.personas_assigned) == 1

    print(f"✓ 캠페인 실행 시작: {result.execution_id}")
    print(f"✓ 할당된 페르소나: {result.personas_assigned[0]}")

    # 완료 대기 (최대 5분)
    for _ in range(60):
        stats = await service.get_campaign_stats('test-campaign-123')
        if stats.total_executions > 0:
            print(f"✓ 캠페인 완료: 성공률 {stats.success_rate:.1f}%")
            break
        await asyncio.sleep(5)
```

---

## Phase E: API 라우터

**예상 소요 시간**: 90분 (각 30분)

### E.1: devices.py (P0, 30분)

**파일**: `app/api/devices.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from app.services.device_service import DeviceService
from app.models.device import DeviceInfo, DeviceAction, DeviceActionResponse
from typing import List

router = APIRouter(prefix="/api/devices", tags=["devices"])

@router.get("/", response_model=List[DeviceInfo])
async def list_devices():
    """연결된 디바이스 목록"""
    service = DeviceService()
    return await service.list_devices()

@router.get("/{device_id}", response_model=DeviceInfo)
async def get_device(device_id: str):
    """디바이스 상세 정보"""
    service = DeviceService()
    try:
        return await service.get_device_info(device_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{device_id}/reboot", response_model=DeviceActionResponse)
async def reboot_device(device_id: str):
    """디바이스 재부팅"""
    service = DeviceService()
    return await service.reboot_device(device_id)

@router.post("/{device_id}/screenshot", response_model=DeviceActionResponse)
async def take_screenshot(device_id: str, save_path: str = "/tmp/screenshot.png"):
    """스크린샷 촬영"""
    service = DeviceService()
    return await service.take_screenshot(device_id, save_path)
```

**main.py에 등록**:
```python
# app/main.py
from app.api import devices

app.include_router(devices.router)
```

**검증**:
```bash
curl -H "X-API-Key: careon-hub-2026" http://localhost:8000/api/devices
```

---

### E.2: personas.py (P1, 30분)

**파일**: `app/api/personas.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.persona_service import PersonaService
from app.models.persona import (
    PersonaResponse, PersonaListResponse, PersonaUpdate,
    SoulSwapRequest, SoulSwapResponse
)
from typing import Optional

router = APIRouter(prefix="/api/personas", tags=["personas"])

@router.get("/", response_model=PersonaListResponse)
async def list_personas(
    status: Optional[str] = Query(None),
    min_trust_score: int = Query(0),
    limit: int = Query(50),
    offset: int = Query(0)
):
    """페르소나 목록 조회"""
    service = PersonaService()
    return await service.list_personas(
        status=status,
        min_trust_score=min_trust_score,
        limit=limit,
        offset=offset
    )

@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(persona_id: str):
    """페르소나 단일 조회"""
    service = PersonaService()
    try:
        return await service.get_persona(persona_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{persona_id}", response_model=PersonaResponse)
async def update_persona(persona_id: str, updates: PersonaUpdate):
    """페르소나 업데이트"""
    service = PersonaService()
    return await service.update_persona(persona_id, updates)

@router.post("/soul-swap", response_model=SoulSwapResponse)
async def execute_soul_swap(request: SoulSwapRequest):
    """Soul Swap 실행"""
    service = PersonaService()
    return await service.execute_soul_swap(request)
```

**검증**:
```bash
curl -H "X-API-Key: careon-hub-2026" \
  "http://localhost:8000/api/personas?status=idle&limit=10"
```

---

### E.3: campaigns.py (P2, 30분)

**파일**: `app/api/campaigns.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from app.services.campaign_service import CampaignService
from app.models.campaign import (
    CampaignExecuteRequest, CampaignExecuteResponse,
    CampaignStatsResponse
)

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

@router.post("/execute", response_model=CampaignExecuteResponse)
async def execute_campaign(request: CampaignExecuteRequest):
    """캠페인 실행"""
    service = CampaignService()
    return await service.execute_campaign(request)

@router.get("/{campaign_id}/stats", response_model=CampaignStatsResponse)
async def get_campaign_stats(campaign_id: str):
    """캠페인 통계 조회"""
    service = CampaignService()
    return await service.get_campaign_stats(campaign_id)
```

**검증**:
```bash
curl -X POST -H "X-API-Key: careon-hub-2026" \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "test", "persona_count": 1}' \
  http://localhost:8000/api/campaigns/execute
```

---

## Phase F: 프론트엔드 페이지

**예상 소요 시간**: 2시간

### F.1: Devices.tsx (P0, 40분)

**파일**: `frontend/src/pages/Devices.tsx`

```typescript
import { useQuery } from '@tanstack/react-query';
import { devicesApi } from '../services/api';

export default function Devices() {
  const { data: devices, isLoading } = useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesApi.list().then(res => res.data),
    refetchInterval: 10000 // 10초마다 갱신
  });

  if (isLoading) return <div>로딩 중...</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h2>연결된 디바이스</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th>Device ID</th>
            <th>Model</th>
            <th>Manufacturer</th>
            <th>Battery</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {devices?.map(device => (
            <tr key={device.device_id}>
              <td>{device.device_id}</td>
              <td>{device.model}</td>
              <td>{device.manufacturer}</td>
              <td>{device.battery_level}%</td>
              <td>{device.status}</td>
              <td>
                <button onClick={() => handleReboot(device.device_id)}>
                  재부팅
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

async function handleReboot(deviceId: string) {
  if (confirm('디바이스를 재부팅하시겠습니까?')) {
    await devicesApi.reboot(deviceId);
    alert('재부팅 명령 전송 완료');
  }
}
```

---

### F.2: Personas.tsx (P1, 40분)

**파일**: `frontend/src/pages/Personas.tsx`

```typescript
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { personasApi } from '../services/api';

export default function Personas() {
  const [status, setStatus] = useState('all');

  const { data, isLoading } = useQuery({
    queryKey: ['personas', status],
    queryFn: () => personasApi.list({ status, limit: 50 }).then(res => res.data)
  });

  if (isLoading) return <div>로딩 중...</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h2>페르소나 관리</h2>

      <div style={{ marginBottom: '20px' }}>
        <label>상태 필터: </label>
        <select value={status} onChange={e => setStatus(e.target.value)}>
          <option value="all">전체</option>
          <option value="idle">대기</option>
          <option value="active">활성</option>
          <option value="cooling_down">쿨다운</option>
          <option value="banned">밴</option>
        </select>
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th>이름</th>
            <th>신뢰도</th>
            <th>상태</th>
            <th>총 세션</th>
            <th>성공률</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {data?.items.map(persona => (
            <tr key={persona.id}>
              <td>{persona.name}</td>
              <td>{persona.trust_score}</td>
              <td>{persona.status}</td>
              <td>{persona.total_sessions}</td>
              <td>
                {persona.total_sessions > 0
                  ? (persona.successful_sessions / persona.total_sessions * 100).toFixed(1)
                  : 0}%
              </td>
              <td>
                <button onClick={() => handleSoulSwap(persona.id)}>
                  Soul Swap
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{ marginTop: '20px' }}>
        <p>총 {data?.total}개 페르소나</p>
      </div>
    </div>
  );
}

async function handleSoulSwap(personaId: string) {
  if (confirm('Soul Swap을 실행하시겠습니까?')) {
    const result = await personasApi.soulSwap({ persona_id: personaId });
    alert(`Soul Swap ${result.data.success ? '성공' : '실패'}`);
  }
}
```

---

### F.3: Campaigns.tsx (P2, 40분)

**파일**: `frontend/src/pages/Campaigns.tsx`

```typescript
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { campaignsApi } from '../services/api';

export default function Campaigns() {
  const [campaignId, setCampaignId] = useState('test-campaign');
  const [personaCount, setPersonaCount] = useState(1);

  const executeMutation = useMutation({
    mutationFn: (data: any) => campaignsApi.execute(data).then(res => res.data),
    onSuccess: (data) => {
      alert(`캠페인 실행 시작: ${data.execution_id}`);
    }
  });

  const handleExecute = () => {
    executeMutation.mutate({
      campaign_id: campaignId,
      persona_count: personaCount,
      min_trust_score: 5
    });
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>캠페인 관리</h2>

      <div style={{ marginBottom: '20px' }}>
        <label>캠페인 ID: </label>
        <input
          type="text"
          value={campaignId}
          onChange={e => setCampaignId(e.target.value)}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label>페르소나 수: </label>
        <input
          type="number"
          value={personaCount}
          onChange={e => setPersonaCount(parseInt(e.target.value))}
          min={1}
          max={10}
        />
      </div>

      <button
        onClick={handleExecute}
        disabled={executeMutation.isPending}
        style={{
          padding: '10px 20px',
          fontSize: '16px',
          backgroundColor: '#4CAF50',
          color: 'white',
          border: 'none',
          cursor: 'pointer'
        }}
      >
        {executeMutation.isPending ? '실행 중...' : '캠페인 실행'}
      </button>

      {executeMutation.isSuccess && (
        <div style={{ marginTop: '20px', color: 'green' }}>
          ✓ 캠페인 실행 시작됨
        </div>
      )}

      {executeMutation.isError && (
        <div style={{ marginTop: '20px', color: 'red' }}>
          ✗ 실행 실패: {executeMutation.error.message}
        </div>
      )}
    </div>
  );
}
```

**App.tsx에 라우트 추가**:
```typescript
// frontend/src/App.tsx
import Devices from './pages/Devices';
import Personas from './pages/Personas';
import Campaigns from './pages/Campaigns';

// ...
<Routes>
  <Route path="/" element={<Dashboard />} />
  <Route path="/devices" element={<Devices />} />
  <Route path="/personas" element={<Personas />} />
  <Route path="/campaigns" element={<Campaigns />} />
</Routes>
```

---

## Phase G: 통합 테스트

**예상 소요 시간**: 1시간

### E2E 테스트 시나리오

1. **디바이스 연결 확인** (5분)
   - 웹 UI `/devices` 접속
   - ADB 디바이스 목록 확인
   - 배터리 레벨 표시 확인

2. **페르소나 조회** (5분)
   - 웹 UI `/personas` 접속
   - 상태 필터링 (idle, active 등)
   - 통계 정보 확인

3. **Soul Swap 실행** (10분)
   - 페르소나 선택 → "Soul Swap" 버튼
   - Phase 1-4 완료 확인 (약 15초)
   - 디바이스에서 앱 실행 확인

4. **캠페인 실행** (30분)
   - 웹 UI `/campaigns` 접속
   - 캠페인 ID 입력 → "실행" 버튼
   - 백그라운드 실행 확인
   - 2-3분 대기 후 통계 확인

5. **에러 핸들링** (10분)
   - ADB 연결 해제 → 에러 메시지 확인
   - 잘못된 페르소나 ID → 404 확인
   - API Key 없이 요청 → 401 확인

---

## Phase H: 배포 준비

**예상 소요 시간**: 1시간

### H.1: systemd 서비스 설정 (30분)

**백엔드 서비스**:
```bash
sudo nano /etc/systemd/system/careon-hub.service
```

```ini
[Unit]
Description=CareOn Hub Backend
After=network.target

[Service]
Type=simple
User=tlswkehd
WorkingDirectory=/home/tlswkehd/projects/careon-hub/backend
Environment="PATH=/home/tlswkehd/projects/careon-hub/backend/.venv/bin"
ExecStart=/home/tlswkehd/projects/careon-hub/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable careon-hub
sudo systemctl start careon-hub
```

---

### H.2: 프론트엔드 빌드 및 Nginx 설정 (30분)

**빌드**:
```bash
cd frontend
npm run build
```

**Nginx 설정**:
```bash
sudo nano /etc/nginx/sites-available/careon-hub
```

```nginx
server {
    listen 80;
    server_name localhost;

    root /home/tlswkehd/projects/careon-hub/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/careon-hub /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 예상 일정

| Phase | 작업 | 소요 시간 | 누적 시간 |
|-------|------|-----------|-----------|
| A | 문서화 (5개 문서) | 2시간 | 2시간 |
| B | Supabase 클라이언트 | 30분 | 2.5시간 |
| C | Pydantic 모델 | 45분 | 3.25시간 |
| D.1 | DeviceService + API | 1.5시간 | 4.75시간 |
| D.2 | PersonaService + API | 2시간 | 6.75시간 |
| D.3 | CampaignService + API | 2.5시간 | 9.25시간 |
| E | API 라우터 통합 | (D에 포함) | 9.25시간 |
| F | 프론트엔드 페이지 | 2시간 | 11.25시간 |
| G | 통합 테스트 | 1시간 | 12.25시간 |
| H | 배포 준비 | 1시간 | 13.25시간 |
| **총계** | | **13.25시간** | |

**병렬 작업 가능**:
- Phase B + C 동시 진행 가능 (1인 기준 순차 진행)
- Phase D.1 완료 후 D.2 시작 (의존성)
- Phase F는 Phase E 완료 후 시작 (API 필요)

**실제 일정 예측** (1인 개발):
- 집중 작업 시: **2일** (하루 7시간 × 2일)
- 일반 작업 시: **3-4일** (하루 4-5시간)

---

*마지막 업데이트: 2026-01-16*
*프로젝트: CareOn Hub v1.0.0*
*상태: 문서화 완료, 개발 준비 완료*
