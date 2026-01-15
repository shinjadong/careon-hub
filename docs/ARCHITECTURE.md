# CareOn Hub - System Architecture

> 시스템 아키텍처 설계 문서

**작성일**: 2026-01-16
**버전**: 1.0.0
**프로젝트**: CareOn Hub - 통합 CCTV 트래픽 관리 시스템

---

## 목차

1. [시스템 개요](#시스템-개요)
2. [전체 아키텍처](#전체-아키텍처)
3. [레이어 구조](#레이어-구조)
4. [모듈 통합 전략](#모듈-통합-전략)
5. [데이터 플로우](#데이터-플로우)
6. [보안 및 인증](#보안-및-인증)
7. [배포 아키텍처](#배포-아키텍처)
8. [확장성 전략](#확장성-전략)

---

## 시스템 개요

### 프로젝트 목표

**CareOn Hub**는 기존 3개의 분산된 마이크로서비스를 하나의 통합 플랫폼으로 재구축한 시스템입니다.

**통합 전**:
```
persona-manager (5002) ─┐
ai-project (8000)       ├─→ 복잡한 서비스 간 통신
blog-writer (5001)      ─┘    독립적 배포, 복잡한 관리
```

**통합 후**:
```
CareOn Hub (8000)
├─ FastAPI 백엔드 (통합 API)
└─ React 프론트엔드 (5173)
   → 단일 진입점, 간소화된 관리
```

### 핵심 특징

- **단일 백엔드**: FastAPI 기반 통합 API 서버
- **웹 UI**: React + TypeScript 관리 대시보드
- **모듈 통합**: Soul Swap, ADB Tools, Traffic Pipeline, Portal Client
- **실시간 모니터링**: WebSocket 기반 상태 업데이트
- **확장 가능**: 마이크로서비스 분리 준비 완료

---

## 전체 아키텍처

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         사용자 (관리자)                               │
└────────────────┬───────────────────────────────────────────────────┘
                 │
                 │ HTTPS
                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                    React Frontend (포트 5173)                       │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐    │
│  │  Dashboard   │  Campaigns   │  Personas    │   Devices    │    │
│  └──────────────┴──────────────┴──────────────┴──────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  TanStack Query (캐싱) + Axios (HTTP 클라이언트)              │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ REST API + WebSocket
                          ▼
┌────────────────────────────────────────────────────────────────────┐
│                FastAPI Backend (포트 8000)                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                      API Layer                                │ │
│  │  ┌──────────┬──────────┬──────────┬──────────┬───────────┐  │ │
│  │  │campaigns │ personas │ devices  │ traffic  │monitoring │  │ │
│  │  │   .py    │   .py    │   .py    │   .py    │    .py    │  │ │
│  │  └──────────┴──────────┴──────────┴──────────┴───────────┘  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Service Layer                              │ │
│  │  ┌────────────────┬───────────────┬─────────────────────┐   │ │
│  │  │CampaignService │PersonaService │   DeviceService     │   │ │
│  │  │                │               │                     │   │ │
│  │  │ 캠페인 관리     │ 페르소나 관리  │   디바이스 제어      │   │ │
│  │  │ 워크플로우      │ Soul Swap     │   ADB 명령 실행      │   │ │
│  │  └────────────────┴───────────────┴─────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                  Core Business Logic                          │ │
│  │  ┌───────────┬──────────┬──────────────┬─────────────────┐  │ │
│  │  │soul_swap/ │  adb/    │  traffic/    │    portal/      │  │ │
│  │  │           │          │              │                 │  │ │
│  │  │ Phase 1-5 │Enhanced  │Naver Session │DroidRun Portal  │  │ │
│  │  │ Soul Swap │ADB Tools │Pipeline      │UI Detection     │  │ │
│  │  └───────────┴──────────┴──────────────┴─────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────┬──────────────────────────────┬───────────────────┘
                  │                              │
                  ▼                              ▼
┌─────────────────────────────────┐   ┌──────────────────────────────┐
│   Supabase (PostgreSQL)         │   │   External Systems           │
│  ┌──────────────────────────┐   │   │  ┌────────────────────────┐ │
│  │ personas                 │   │   │  │ ADB 연결 디바이스       │ │
│  │ persona_sessions         │   │   │  │ (Android 폰/태블릿)    │ │
│  │                          │   │   │  └────────────────────────┘ │
│  │ RPC Functions:           │   │   │                              │
│  │ - select_available_      │   │   │  ┌────────────────────────┐ │
│  │   persona()              │   │   │  │ DroidRun Portal APK    │ │
│  │ - checkin_persona()      │   │   │  │ (UI 요소 탐지)         │ │
│  │ - get_persona_stats()    │   │   │  └────────────────────────┘ │
│  └──────────────────────────┘   │   │                              │
└─────────────────────────────────┘   └──────────────────────────────┘
```

### 기술 스택

| 레이어 | 기술 |
|--------|------|
| **Frontend** | React 18, TypeScript, Vite, TanStack Query, Axios, React Router |
| **Backend** | Python 3.13, FastAPI, Uvicorn, Pydantic |
| **Database** | Supabase (PostgreSQL 15) |
| **Device Control** | adbutils, subprocess |
| **External Integration** | DroidRun Portal (APK) |
| **Deployment** | systemd, Linux |

---

## 레이어 구조

### 1. API Layer (FastAPI Routers)

**위치**: `backend/app/api/`

**역할**: HTTP 엔드포인트 정의 및 요청/응답 처리

**파일 구조**:
```
app/api/
├── __init__.py
├── campaigns.py        # 캠페인 API (8개 엔드포인트)
├── personas.py         # 페르소나 API (15개 엔드포인트)
├── devices.py          # 디바이스 API (6개 엔드포인트)
├── traffic.py          # 트래픽 API (4개 엔드포인트)
└── monitoring.py       # 모니터링 API (4개 엔드포인트)
```

**책임**:
- Request validation (Pydantic 모델)
- Response serialization
- 에러 핸들링
- API 문서 자동 생성 (OpenAPI)

**예시 코드**:
```python
# app/api/campaigns.py
from fastapi import APIRouter, Depends
from app.services.campaign_service import CampaignService
from app.models.campaign import CampaignResponse, CampaignExecuteRequest

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

@router.post("/{campaign_id}/execute")
async def execute_campaign(
    campaign_id: str,
    request: CampaignExecuteRequest,
    service: CampaignService = Depends()
) -> CampaignResponse:
    """캠페인 실행"""
    return await service.execute_campaign(campaign_id, request)
```

---

### 2. Service Layer

**위치**: `backend/app/services/`

**역할**: 비즈니스 로직 구현 및 워크플로우 오케스트레이션

**파일 구조**:
```
app/services/
├── __init__.py
├── campaign_service.py    # 캠페인 관리
├── persona_service.py     # 페르소나 관리 + Soul Swap
├── device_service.py      # 디바이스 제어
└── monitoring_service.py  # 로그 및 통계
```

**책임**:
- 복잡한 비즈니스 로직 구현
- 여러 Core 모듈 조합
- Supabase 데이터베이스 연동
- 트랜잭션 관리

**의존성 주입 패턴**:
```python
# app/services/campaign_service.py
from app.database.supabase import get_supabase_client
from app.core.soul_swap.soul import SoulManager
from app.core.traffic.pipeline import NaverSessionPipeline

class CampaignService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.soul_manager = SoulManager()
        self.pipeline = NaverSessionPipeline()

    async def execute_campaign(self, campaign_id: str, request: CampaignExecuteRequest):
        # 1. 페르소나 선택
        persona_id = await self.select_persona(campaign_id)

        # 2. Soul Swap 실행
        await self.soul_manager.swap(persona_id)

        # 3. 트래픽 실행
        result = await self.pipeline.run_campaign_workflow(campaign_id)

        # 4. 결과 기록
        await self.record_session(persona_id, result)

        return result
```

---

### 3. Core Business Logic

**위치**: `backend/app/core/`

**역할**: 재사용 가능한 핵심 비즈니스 로직 (도메인 로직)

**파일 구조**:
```
app/core/
├── soul_swap/              # Soul Swap 프로토콜
│   ├── soul/
│   │   ├── soul_manager.py       # Phase 1, 3, 4, 5
│   │   ├── cookie_manager.py     # 쿠키 백업/복원
│   │   └── app_data_paths.py     # 앱별 데이터 경로
│   ├── identity/
│   │   └── device_identity.py    # Phase 2 (ANDROID_ID, GPS)
│   └── __init__.py
│
├── adb/                    # Android 디바이스 제어
│   ├── adb_enhanced.py           # EnhancedAdbTools
│   ├── behavior_injector.py      # 사람처럼 행동
│   ├── device_session_manager.py # 세션 관리
│   ├── engagement_simulator.py   # 사용자 참여 시뮬레이션
│   └── __init__.py
│
├── traffic/                # 트래픽 파이프라인
│   ├── pipeline.py               # NaverSessionPipeline
│   └── __init__.py
│
└── portal/                 # DroidRun Portal 연동
    ├── client.py                 # PortalClient
    ├── element.py                # UIElement
    ├── finder.py                 # ElementFinder
    └── __init__.py
```

**모듈별 역할**:

#### soul_swap 모듈
- **Phase 1 (cleanup)**: 앱 초기화 (force-stop, pm clear)
- **Phase 2 (identity)**: 디바이스 ID 변경 (ANDROID_ID, GPS)
- **Phase 3 (restore)**: tar.gz 백업 복원
- **Phase 4 (launch)**: 앱 실행 및 초기화 대기
- **Phase 5 (backup)**: 앱 데이터 백업

#### adb 모듈
- **EnhancedAdbTools**: 베지어 곡선 기반 스와이프, 오타 포함 타이핑
- **BehaviorInjector**: 행동 프로필 기반 자동화
- **DeviceSessionManager**: 디바이스 세션 관리
- **EngagementSimulator**: 체류 시간, 스크롤 패턴 시뮬레이션

#### traffic 모듈
- **NaverSessionPipeline**: 검색 → 블로그 진입 → 읽기 워크플로우
- Portal 연동으로 정확한 UI 요소 탐지

#### portal 모듈
- **PortalClient**: DroidRun Portal APK HTTP API 클라이언트
- **UIElement**: 화면 요소 표현 (bounds, text, resource_id)
- **ElementFinder**: XPath, text, resource_id 기반 검색

---

### 4. Database Layer

**위치**: `backend/app/database/`

**역할**: Supabase 클라이언트 래퍼

**파일 구조**:
```
app/database/
├── __init__.py
└── supabase.py           # SupabaseClient 싱글톤
```

**책임**:
- Supabase 연결 관리
- 테이블 CRUD 래퍼
- RPC 함수 호출
- 연결 풀 관리

**예시 코드**:
```python
# app/database/supabase.py
from supabase import create_client, Client
from app.config import get_settings

class SupabaseClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            settings = get_settings()
            cls._instance = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
        return cls._instance

    async def select_available_persona(self, campaign_id: str, min_trust_score: int = 0):
        """RPC: 가용 페르소나 선택"""
        result = self._instance.rpc('select_available_persona', {
            'campaign_id_param': campaign_id,
            'min_trust_score_param': min_trust_score
        }).execute()
        return result.data

def get_supabase_client() -> SupabaseClient:
    return SupabaseClient()
```

---

### 5. Model Layer (Pydantic)

**위치**: `backend/app/models/`

**역할**: Request/Response 데이터 모델 정의

**파일 구조**:
```
app/models/
├── __init__.py
├── common.py             # 공통 모델 (PaginationParams, ErrorResponse)
├── campaign.py           # 캠페인 모델
├── persona.py            # 페르소나 모델
└── device.py             # 디바이스 모델
```

**예시 코드**:
```python
# app/models/persona.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PersonaBase(BaseModel):
    name: str = Field(..., max_length=100)
    device_config: dict
    behavior_profile: dict = {}
    location: Optional[dict] = None

class PersonaCreate(PersonaBase):
    pass

class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    trust_score: Optional[int] = None
    status: Optional[str] = None

class PersonaResponse(PersonaBase):
    id: str
    trust_score: int
    status: str
    total_sessions: int
    successful_sessions: int
    created_at: datetime
    updated_at: datetime
```

---

## 모듈 통합 전략

### Soul Swap 통합 (PersonaService)

**통합 방식**: PersonaService가 SoulManager를 조합하여 5단계 프로토콜 실행

```python
# app/services/persona_service.py
class PersonaService:
    async def execute_soul_swap(self, persona_id: str):
        persona = await self.supabase.get_persona(persona_id)

        # Phase 1: Cleanup
        await self.soul_manager.cleanup(NAVER_SEARCH_APP)
        await self.soul_manager.cleanup(NAVER_BLOG_APP)

        # Phase 2: Identity Masking
        await self.identity_manager.apply_identity(
            android_id=persona['device_config']['android_id'],
            location=persona['location']
        )

        # Phase 3: Restore
        await self.soul_manager.restore(
            NAVER_SEARCH_APP,
            backup_path=f"data/personas/{persona['name']}/naver_search.tar.gz"
        )
        await self.soul_manager.restore(
            NAVER_BLOG_APP,
            backup_path=f"data/personas/{persona['name']}/naver_blog.tar.gz"
        )

        # Phase 4: Launch
        await self.soul_manager.launch_app(NAVER_SEARCH_APP)

        # Phase 5는 세션 종료 시 호출
```

**데이터 흐름**:
```
PersonaService
    ↓
SoulManager (Phase 1, 3, 4, 5)
    ↓
adb shell commands
    ↓
Android Device
```

---

### ADB Tools 통합 (DeviceService + TrafficService)

**통합 방식**: DeviceService는 단순 명령, TrafficService는 행동 시뮬레이션

```python
# app/services/device_service.py
class DeviceService:
    def __init__(self):
        self.adb = EnhancedAdbTools()

    async def list_devices(self):
        """연결된 디바이스 목록"""
        return self.adb.list_devices()

    async def reboot_device(self, device_id: str):
        """디바이스 재부팅"""
        return self.adb.reboot(device_id)

# app/services/campaign_service.py (TrafficService 포함)
class CampaignService:
    async def execute_traffic(self, persona_id: str, campaign_config: dict):
        # Behavior 프로필 로드
        persona = await self.get_persona(persona_id)

        # BehaviorInjector로 사람처럼 행동
        injector = BehaviorInjector(
            adb_tools=self.adb,
            behavior_profile=persona['behavior_profile']
        )

        # 검색어 입력 (오타 포함, 불규칙한 속도)
        await injector.type_like_human("CCTV 설치")

        # 스크롤 (베지어 곡선, 불규칙한 속도)
        await injector.scroll_like_human(direction="down", count=3)

        # 클릭 (약간의 위치 오차)
        await injector.tap_like_human(x=500, y=800)
```

**데이터 흐름**:
```
CampaignService
    ↓
BehaviorInjector (행동 프로필)
    ↓
EnhancedAdbTools (베지어 곡선, 오타 주입)
    ↓
adb input commands
    ↓
Android Device
```

---

### Traffic Pipeline 통합 (CampaignService)

**통합 방식**: CampaignService가 NaverSessionPipeline을 호출하여 전체 워크플로우 실행

```python
# app/services/campaign_service.py
class CampaignService:
    async def execute_campaign(self, campaign_id: str, request: CampaignExecuteRequest):
        # 1. 페르소나 선택 및 Soul Swap
        persona_id = await self.select_and_swap_persona(campaign_id)

        # 2. Traffic Pipeline 실행
        pipeline = NaverSessionPipeline(
            adb_tools=self.adb,
            portal_client=self.portal,
            persona_profile=persona
        )

        result = await pipeline.run_campaign_workflow(
            keyword=request.keyword,
            target_blog_url=request.target_blog_url,
            read_time_seconds=request.read_time_seconds
        )

        # 3. 결과 기록
        await self.record_session(persona_id, result)

        # 4. Soul Swap Phase 5 (Backup)
        await self.soul_manager.backup_all_apps(persona_id)

        return result
```

**파이프라인 단계**:
```
1. Naver 검색 앱 실행
2. 검색어 입력 + 검색
3. 블로그 링크 탐지 (Portal)
4. 블로그 클릭
5. 콘텐츠 읽기 (스크롤 + 체류)
6. 앱 종료
```

---

### Portal 통합 (TrafficService)

**통합 방식**: PortalClient를 사용하여 정확한 UI 요소 탐지

```python
# app/services/campaign_service.py (또는 TrafficService)
class CampaignService:
    async def find_blog_link(self, keyword: str):
        # DroidRun Portal로 UI 트리 가져오기
        ui_tree = await self.portal.get_ui_tree()

        # 블로그 링크 찾기
        blog_link = self.portal.find_by_text(
            ui_tree,
            text_pattern=r"blog\.naver\.com",
            type="android.widget.TextView"
        )

        if blog_link:
            # 좌표로 클릭
            await self.adb.tap(
                x=blog_link.center_x,
                y=blog_link.center_y
            )
        else:
            raise ValueError("블로그 링크를 찾을 수 없습니다")
```

**Portal API 호출 흐름**:
```
CampaignService
    ↓
PortalClient.get_ui_tree()
    ↓
HTTP GET http://localhost:9999/ui_tree
    ↓
DroidRun Portal APK (Android)
    ↓
UI 계층 구조 JSON 반환
    ↓
ElementFinder로 요소 검색
    ↓
좌표 반환 → ADB tap
```

---

## 데이터 플로우

### 1. 캠페인 실행 플로우

**전체 과정**: 사용자가 웹 UI에서 "캠페인 실행" 버튼 클릭 → 트래픽 완료까지

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                              │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        │ 1. POST /api/campaigns/123/execute
                        │    { keyword: "CCTV 설치", target_url: "..." }
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                             │
│  campaigns.py → CampaignService.execute_campaign()                  │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        │ 2. Service Layer 진입
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CampaignService                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Step 1: 페르소나 선택 (원자적 트랜잭션)                          │  │
│  │   - Supabase RPC: select_available_persona()                 │  │
│  │   - 조건: status='idle', cooldown 만료, trust_score >= 10    │  │
│  │   - 반환: persona_id (UUID)                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                        │                                             │
│                        ▼                                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Step 2: Soul Swap 실행 (PersonaService 위임)                  │  │
│  │   Phase 1: Cleanup (force-stop, pm clear)                    │  │
│  │   Phase 2: Identity (ANDROID_ID, GPS 변경)                   │  │
│  │   Phase 3: Restore (tar.gz 복원)                              │  │
│  │   Phase 4: Launch (앱 실행)                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                        │                                             │
│                        ▼                                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Step 3: 세션 레코드 생성                                        │  │
│  │   - persona_sessions 테이블 INSERT                            │  │
│  │   - status: 'running', started_at: now()                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                        │                                             │
│                        ▼                                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Step 4: Traffic Pipeline 실행                                  │  │
│  │   NaverSessionPipeline.run_campaign_workflow()                │  │
│  │     ├─ 검색 앱 실행                                            │  │
│  │     ├─ 검색어 입력 (BehaviorInjector: 오타, 불규칙 속도)       │  │
│  │     ├─ 검색 실행                                               │  │
│  │     ├─ Portal로 블로그 링크 탐지                                │  │
│  │     ├─ 블로그 클릭                                             │  │
│  │     ├─ 콘텐츠 읽기 (스크롤 3-5회, 체류 120초)                  │  │
│  │     └─ 앱 종료                                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                        │                                             │
│                        ▼                                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Step 5: Soul Swap Phase 5 (Backup)                            │  │
│  │   - 앱 데이터 tar.gz 백업                                       │  │
│  │   - data/personas/{name}/naver_search.tar.gz                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                        │                                             │
│                        ▼                                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Step 6: 세션 체크인 (Supabase RPC)                             │  │
│  │   checkin_persona(persona_id, session_id, success=True)       │  │
│  │     ├─ 세션 상태: 'completed', completed_at: now()            │  │
│  │     ├─ 페르소나 통계 업데이트: successful_sessions++          │  │
│  │     ├─ trust_score 재계산                                      │  │
│  │     └─ 페르소나 상태: 'cooling_down' (30분)                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        │ 7. Response 반환
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Frontend (React)                                │
│  실시간 상태 업데이트 (WebSocket 또는 Polling)                        │
│    - 캠페인 진행 상황                                                 │
│    - 세션 로그                                                        │
│    - 성공/실패 결과                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

**예상 소요 시간**:
- Step 1 (페르소나 선택): 0.1초
- Step 2 (Soul Swap Phase 1-4): 15초
- Step 3 (세션 생성): 0.1초
- Step 4 (Traffic 실행): 120-180초
- Step 5 (Backup): 5초
- Step 6 (체크인): 0.1초
- **총**: 약 2.5-3.5분

---

### 2. Soul Swap 5단계 프로세스

```
┌────────────────────────────────────────────────────────────────────┐
│ Phase 1: Cleanup (초기화)                                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ for app in [NAVER_SEARCH, NAVER_BLOG]:                       │ │
│  │   adb shell am force-stop {app.package}                      │ │
│  │   adb shell pm clear {app.package}                           │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  결과: 앱 데이터 완전 삭제, 로그인 세션 제거                          │
└────────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│ Phase 2: Identity Masking (디바이스 ID 변경)                        │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ adb shell settings put secure android_id {new_android_id}    │ │
│  │ adb shell setprop gsm.sim.operator.numeric {mcc_mnc}         │ │
│  │ adb shell setprop ro.build.fingerprint {fingerprint}         │ │
│  │ adb shell settings put secure location_providers_allowed gps │ │
│  │ adb shell "echo {lat},{lon} > /data/local/tmp/mock_gps.txt"  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  결과: 새 페르소나의 디바이스 정체성 부여                              │
└────────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│ Phase 3: Restore (백업 복원)                                         │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ for app in [NAVER_SEARCH, NAVER_BLOG]:                       │ │
│  │   backup_path = f"data/personas/{name}/{app.name}.tar.gz"    │ │
│  │   adb push {backup_path} /data/local/tmp/restore.tar.gz      │ │
│  │   adb shell tar -xzf /data/local/tmp/restore.tar.gz          │ │
│  │       -C /data/data/{app.package}                            │ │
│  │   adb shell chown -R {app.uid}:{app.uid}                     │ │
│  │       /data/data/{app.package}                               │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  결과: 페르소나의 이전 앱 데이터 (로그인, 쿠키, 히스토리) 복원         │
└────────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│ Phase 4: Launch (앱 실행)                                            │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ adb shell monkey -p {app.package} -c                          │ │
│  │     android.intent.category.LAUNCHER 1                        │ │
│  │ await asyncio.sleep(5)  # 초기화 대기                          │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  결과: 페르소나 정체성으로 앱 실행, 트래픽 준비 완료                   │
└────────────────────────────────────────────────────────────────────┘
                         │
                         │ [트래픽 실행 ...]
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│ Phase 5: Backup (세션 종료 후)                                       │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ for app in [NAVER_SEARCH, NAVER_BLOG]:                       │ │
│  │   adb shell am force-stop {app.package}                      │ │
│  │   adb shell tar -czf /data/local/tmp/backup.tar.gz           │ │
│  │       -C /data/data {app.package}                            │ │
│  │   adb pull /data/local/tmp/backup.tar.gz                     │ │
│  │       data/personas/{name}/{app.name}.tar.gz                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  결과: 업데이트된 앱 상태 백업 (쿠키, 히스토리 포함)                   │
└────────────────────────────────────────────────────────────────────┘
```

**중요 사항**:
- Phase 2는 Phase 1과 3 사이에 실행 (디바이스 ID 먼저 변경)
- Phase 3는 root 권한 필요 (`/data/data/` 접근)
- Phase 5는 세션 성공/실패 관계없이 항상 실행 (상태 보존)

---

### 3. 트래픽 세션 실행 플로우

```
┌────────────────────────────────────────────────────────────────────┐
│             NaverSessionPipeline.run_campaign_workflow()            │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│ Step 1: 네이버 검색 앱 실행                                           │
│   adb shell monkey -p com.nhn.android.search ...                   │
│   await asyncio.sleep(3)                                           │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│ Step 2: Portal로 검색창 탐지                                          │
│   ui_tree = portal.get_ui_tree()                                   │
│   search_box = portal.find_by_resource_id(                         │
│       ui_tree, "com.nhn.android.search:id/search_input"            │
│   )                                                                │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│ Step 3: 검색어 입력 (BehaviorInjector)                               │
│   behavior_injector.type_like_human(                               │
│       text="CCTV 설치",                                             │
│       typing_speed_wpm=45,  # 분당 45단어                           │
│       error_rate=0.03       # 3% 오타 확률                          │
│   )                                                                │
│   실제 입력: "CCT V 설치" (오타) → 백스페이스 → "CCTV 설치"           │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│ Step 4: 검색 실행 (엔터 키)                                           │
│   adb shell input keyevent KEYCODE_ENTER                           │
│   await asyncio.sleep(2)  # 결과 로딩 대기                          │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│ Step 5: Portal로 블로그 링크 탐지                                     │
│   ui_tree = portal.get_ui_tree()                                   │
│   blog_links = portal.find_by_text(                                │
│       ui_tree,                                                     │
│       text_pattern=r"blog\.naver\.com",                            │
│       type="android.widget.TextView"                               │
│   )                                                                │
│   target_link = blog_links[0]  # 첫 번째 결과                       │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│ Step 6: 블로그 링크 클릭 (약간의 오차)                                 │
│   behavior_injector.tap_like_human(                                │
│       x=target_link.center_x,                                      │
│       y=target_link.center_y,                                      │
│       offset_range=5  # ±5px 랜덤 오프셋                            │
│   )                                                                │
│   await asyncio.sleep(5)  # 블로그 페이지 로딩                       │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│ Step 7: 콘텐츠 읽기 시뮬레이션                                         │
│   EngagementSimulator.simulate_reading(                            │
│       duration_seconds=120,                                        │
│       scroll_count=3-5 (랜덤),                                      │
│       pause_probability=0.2,                                       │
│       back_scroll_probability=0.1                                  │
│   )                                                                │
│                                                                    │
│   실제 행동:                                                         │
│     - 스크롤 다운 (베지어 곡선, 500-1500ms 속도)                      │
│     - 랜덤 정지 (2-5초)                                              │
│     - 다시 스크롤                                                    │
│     - 가끔 위로 스크롤 (20% 확률)                                     │
│     - 총 120초 체류                                                  │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────────┐
│ Step 8: 앱 종료 및 정리                                               │
│   adb shell am force-stop com.nhn.android.search                   │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
                    [세션 완료]
```

---

## 보안 및 인증

### 1. API 인증

**방식**: HTTP Header 기반 API Key 인증

```python
# app/main.py
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    settings = get_settings()
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

# API 엔드포인트에 적용
@router.post("/api/campaigns/{id}/execute")
async def execute_campaign(
    campaign_id: str,
    api_key: str = Depends(verify_api_key)
):
    ...
```

**환경변수**:
```bash
API_KEY=careon-hub-2026
```

**Frontend 사용**:
```typescript
// frontend/src/services/api.ts
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'X-API-Key': 'careon-hub-2026'
  }
});
```

---

### 2. Supabase Row Level Security (RLS)

**정책 계층**:

1. **service_role** (백엔드 전용):
   - 모든 테이블 전체 접근 (READ/WRITE/DELETE)
   - 환경변수: `SUPABASE_SERVICE_KEY`

2. **authenticated** (인증된 사용자):
   - personas: 읽기 전용
   - persona_sessions: 읽기 전용

3. **anon** (익명 사용자):
   - personas: 제한적 읽기 (status='idle', 'cooling_down' 만)
   - persona_sessions: 접근 불가

**환경변수**:
```bash
SUPABASE_URL=https://pkehcfbjotctvneordob.supabase.co
SUPABASE_ANON_KEY=eyJ... (제한적 권한)
SUPABASE_SERVICE_KEY=eyJ... (전체 권한)
```

**백엔드에서는 SERVICE_KEY 사용**:
```python
supabase = create_client(
    settings.supabase_url,
    settings.supabase_service_key  # service_role
)
```

---

### 3. 환경변수 관리

**위치**: `/home/tlswkehd/projects/careon-hub/backend/.env`

**민감 정보**:
```bash
SUPABASE_SERVICE_KEY=eyJ...        # 전체 권한 키
API_KEY=careon-hub-2026            # API 인증 키
```

**Git 보안**:
```bash
# .gitignore
.env
.env.local
*.key
*.pem
```

---

### 4. CORS 설정

**개발 환경**:
```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**프로덕션 환경**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://careon-hub.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key"],
)
```

---

## 배포 아키텍처

### systemd 서비스 구성

**파일**: `/etc/systemd/system/careon-hub.service`

```ini
[Unit]
Description=CareOn Hub - Unified Traffic Management System
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

**명령어**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable careon-hub
sudo systemctl start careon-hub
sudo systemctl status careon-hub
```

---

### 프론트엔드 배포 (Nginx)

**빌드**:
```bash
cd frontend
npm run build
# → dist/ 디렉토리 생성
```

**Nginx 설정**: `/etc/nginx/sites-available/careon-hub`

```nginx
server {
    listen 80;
    server_name careon-hub.example.com;

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

---

## 확장성 전략

### 1. 수평 확장 (Horizontal Scaling)

**현재 아키텍처**: 단일 서버 (Monolith)

**확장 방안**:
```
Load Balancer (Nginx)
    ↓
┌───────┬───────┬───────┐
│ App 1 │ App 2 │ App 3 │ (FastAPI 인스턴스)
└───────┴───────┴───────┘
    ↓
Supabase (공유 DB)
```

**필요 변경사항**:
- Supabase 연결 풀 관리
- Stateless 설계 (세션 상태는 DB에 저장)
- Redis로 캐싱 (페르소나 목록, 디바이스 상태)

---

### 2. 마이크로서비스 분리 (향후)

**분리 후보**:
```
API Gateway (FastAPI)
    ↓
┌────────────┬────────────┬────────────┐
│ Persona    │ Campaign   │ Device     │
│ Service    │ Service    │ Service    │
└────────────┴────────────┴────────────┘
    ↓
Supabase (공유) 또는 개별 DB
```

**분리 기준**:
- Persona Service: 페르소나 관리 + Soul Swap
- Campaign Service: 캠페인 실행 + Traffic Pipeline
- Device Service: ADB 디바이스 제어

---

### 3. 디바이스 풀 관리

**현재**: 단일 서버에 여러 디바이스 연결

**확장**:
```
┌──────────────┐
│ Device Pool  │
│  Manager     │
└──────┬───────┘
       │
   ┌───┴────┬────────┬────────┐
   │ Node 1 │ Node 2 │ Node 3 │
   │ 10개   │ 10개   │ 10개   │
   └────────┴────────┴────────┘
      총 30개 디바이스
```

**필요 변경사항**:
- Redis로 디바이스 가용성 관리
- gRPC 또는 HTTP API로 Node 간 통신
- 디바이스 헬스 체크 자동화

---

*마지막 업데이트: 2026-01-16*
*프로젝트: CareOn Hub v1.0.0*
