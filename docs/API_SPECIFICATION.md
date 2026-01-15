# CareOn Hub - API 명세서 (API Specification)

> 통합 API 전체 엔드포인트 명세

**작성일:** 2026-01-16  
**버전:** 1.0.0  
**Base URL:** `http://localhost:8000`  
**인증:** X-API-Key Header

---

## 목차

1. [인증](#authentication)
2. [Personas API](#personas-api) - 15개 엔드포인트
3. [Campaigns API](#campaigns-api) - 8개 엔드포인트  
4. [Traffic API](#traffic-api) - 4개 엔드포인트
5. [Devices API](#devices-api) - 6개 엔드포인트
6. [Monitoring API](#monitoring-api) - 4개 엔드포인트
7. [기존 서비스 매핑](#legacy-service-mapping)
8. [에러 응답](#error-responses)

---

## Authentication

모든 API는 `X-API-Key` 헤더로 인증합니다.

```bash
X-API-Key: careon-hub-2026
```

**Example:**
```bash
curl -H "X-API-Key: careon-hub-2026" \
  http://localhost:8000/api/personas
```

**에러 응답 (401 Unauthorized):**
```json
{
  "detail": "Invalid API Key"
}
```

---

## Personas API

**기존 매핑:** `persona-manager:5002/`

페르소나 관리 및 Soul Swap 실행 API입니다.

### GET /api/personas

페르소나 목록 조회 (페이지네이션)

**Query Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| status | string | No | all | `idle`, `active`, `cooling_down`, `banned`, `retired` |
| min_trust_score | integer | No | 0 | 최소 신뢰도 점수 |
| location_label | string | No | null | 위치 라벨 필터 |
| tags | string[] | No | [] | 태그 필터 (comma separated) |
| limit | integer | No | 50 | 페이지 크기 (1-100) |
| offset | integer | No | 0 | 페이지 오프셋 |

**Response: 200 OK**
```json
{
  "items": [
    {
      "id": "uuid-string",
      "name": "직장인_30대_강남",
      "tags": ["explorer", "deep_reader"],
      "status": "idle",
      "trust_score": 15,
      "total_sessions": 120,
      "successful_sessions": 118,
      "success_rate": 0.983,
      "last_active_at": "2026-01-15T14:30:00Z",
      "cooldown_until": null,
      "device_config": {
        "android_id": "1a2b3c4d5e6f7890",
        "model": "SM-G960N"
      },
      "location": {
        "lat": 37.4979,
        "lng": 127.0276,
        "label": "강남역"
      }
    }
  ],
  "total": 1000,
  "limit": 50,
  "offset": 0
}
```

**Example:**
```bash
curl -H "X-API-Key: careon-hub-2026" \
  "http://localhost:8000/api/personas?status=idle&limit=10"
```

---

### GET /api/personas/{persona_id}

페르소나 상세 조회

**Path Parameters:**
- `persona_id: UUID` - 페르소나 ID

**Response: 200 OK**
```json
{
  "id": "uuid",
  "name": "직장인_30대_강남",
  "tags": ["explorer"],
  "device_config": {
    "android_id": "1a2b3c4d5e6f7890",
    "imei": "123456789012345",
    "model": "SM-G960N",
    "manufacturer": "samsung",
    "sdk_version": 33
  },
  "location": {
    "lat": 37.4979,
    "lng": 127.0276,
    "label": "강남역",
    "accuracy": 10.0
  },
  "behavior_profile": {
    "scroll_speed": "medium",
    "dwell_time_multiplier": 1.2,
    "active_hours": [9, 10, 11, 14, 15, 16, 19, 20]
  },
  "naver_identifiers": {
    "nnb_cookie": "...",
    "last_user_agent": "..."
  },
  "soul_file_path": "/sdcard/personas/persona_001/naver_v3.tar.gz",
  "soul_version": 3,
  "soul_size_bytes": 15728640,
  "soul_last_backup": "2026-01-15T18:00:00Z",
  "trust_score": 15,
  "status": "idle",
  "total_sessions": 120,
  "successful_sessions": 118,
  "total_pageviews": 450,
  "total_dwell_time": 54000,
  "avg_session_duration": 450,
  "last_active_at": "2026-01-15T14:30:00Z",
  "cooldown_until": null,
  "created_at": "2025-12-01T00:00:00Z",
  "updated_at": "2026-01-15T18:00:00Z"
}
```

**Response: 404 Not Found**
```json
{
  "detail": "Persona not found"
}
```

**Example:**
```bash
curl -H "X-API-Key: careon-hub-2026" \
  http://localhost:8000/api/personas/uuid-string
```

---

### POST /api/personas

페르소나 생성

**Request Body:**
```json
{
  "name": "대학생_20대_홍대",
  "tags": ["explorer", "quick_reader"],
  "device_config": {
    "android_id": "fedcba9876543210",
    "model": "SM-G973N",
    "manufacturer": "samsung",
    "sdk_version": 33
  },
  "location": {
    "lat": 37.5563,
    "lng": 126.9236,
    "label": "홍대입구역",
    "accuracy": 10.0
  },
  "behavior_profile": {
    "scroll_speed": "fast",
    "dwell_time_multiplier": 0.8
  }
}
```

**Response: 201 Created**
```json
{
  "id": "new-uuid",
  "name": "대학생_20대_홍대",
  "status": "idle",
  "trust_score": 0,
  "created_at": "2026-01-16T02:40:00Z"
}
```

---

### PUT /api/personas/{persona_id}

페르소나 업데이트

**Request Body:**
```json
{
  "name": "대학생_20대_홍대_수정",
  "tags": ["explorer", "deep_reader"],
  "location": {
    "lat": 37.5563,
    "lng": 126.9236,
    "label": "홍대입구역"
  }
}
```

**Response: 200 OK**
```json
{
  "id": "uuid",
  "name": "대학생_20대_홍대_수정",
  "updated_at": "2026-01-16T02:41:00Z"
}
```

---

### DELETE /api/personas/{persona_id}

페르소나 삭제

**Response: 204 No Content**

---

### POST /api/personas/{persona_id}/ban

페르소나 차단

**Request Body:**
```json
{
  "reason": "로그인 만료로 인한 연속 실패"
}
```

**Response: 200 OK**
```json
{
  "id": "uuid",
  "status": "banned",
  "ban_reason": "로그인 만료로 인한 연속 실패",
  "updated_at": "2026-01-16T02:42:00Z"
}
```

---

### POST /api/personas/{persona_id}/unban

페르소나 차단 해제

**Response: 200 OK**
```json
{
  "id": "uuid",
  "status": "idle",
  "ban_reason": null,
  "cooldown_until": "2026-01-16T03:42:00Z",
  "updated_at": "2026-01-16T02:42:00Z"
}
```

---

### GET /api/personas/{persona_id}/soul

Soul 파일 정보 조회

**Response: 200 OK**
```json
{
  "persona_id": "uuid",
  "soul_file_path": "/sdcard/personas/persona_001/naver_v3.tar.gz",
  "soul_version": 3,
  "soul_size_bytes": 15728640,
  "soul_last_backup": "2026-01-15T18:00:00Z",
  "available_versions": [
    {
      "version": 3,
      "file_path": "/sdcard/personas/persona_001/naver_v3.tar.gz",
      "size_bytes": 15728640,
      "created_at": "2026-01-15T18:00:00Z"
    },
    {
      "version": 2,
      "file_path": "/sdcard/personas/persona_001/naver_v2.tar.gz",
      "size_bytes": 15200000,
      "created_at": "2026-01-14T12:00:00Z"
    }
  ]
}
```

---

### POST /api/personas/sessions/start

세션 시작 (페르소나 선택)

**Request Body:**
```json
{
  "campaign_id": "campaign-uuid",
  "target_location": "강남역",
  "min_trust_score": 10
}
```

**Response: 200 OK**
```json
{
  "session_id": "session-uuid",
  "persona_id": "persona-uuid",
  "persona_name": "직장인_30대_강남",
  "status": "active",
  "device_serial": "R3CW60BHSAT",
  "started_at": "2026-01-16T02:45:00Z"
}
```

---

### POST /api/personas/sessions/{session_id}/complete

세션 완료

**Request Body:**
```json
{
  "success": true,
  "duration_sec": 180,
  "scroll_count": 8,
  "scroll_depth": 0.85,
  "interactions": 3,
  "phase_timings": {
    "cleanup_ms": 2000,
    "hardware_masking_ms": 1500,
    "soul_restore_ms": 8000,
    "app_launch_ms": 5000,
    "traffic_execution_ms": 160000,
    "soul_backup_ms": 10000
  }
}
```

**Response: 200 OK**
```json
{
  "session_id": "session-uuid",
  "persona_id": "persona-uuid",
  "success": true,
  "duration_sec": 180,
  "persona_new_status": "idle",
  "persona_new_trust_score": 16,
  "cooldown_until": "2026-01-16T03:15:00Z",
  "completed_at": "2026-01-16T02:48:00Z"
}
```

---

### POST /api/personas/sessions/{session_id}/abort

세션 중단

**Query Parameters:**
- `error_type: string` - 에러 유형 (`ui_not_found`, `timeout`, `network`, `app_crash`, `captcha`, `login_expired`)
- `error_message: string` - 에러 메시지

**Response: 200 OK**
```json
{
  "session_id": "session-uuid",
  "status": "aborted",
  "error_type": "ui_not_found",
  "error_message": "블로그 탭을 찾을 수 없음",
  "aborted_at": "2026-01-16T02:46:00Z"
}
```

---

### GET /api/personas/sessions

세션 목록 조회

**Query Parameters:**
| Name | Type | Required | Default |
|------|------|----------|---------|
| persona_id | UUID | No | null |
| campaign_id | UUID | No | null |
| success | boolean | No | null |
| limit | integer | No | 50 |
| offset | integer | No | 0 |

**Response: 200 OK**
```json
{
  "items": [
    {
      "id": "session-uuid",
      "persona_id": "persona-uuid",
      "persona_name": "직장인_30대_강남",
      "campaign_id": "campaign-uuid",
      "success": true,
      "duration_sec": 180,
      "scroll_count": 8,
      "started_at": "2026-01-16T02:45:00Z",
      "completed_at": "2026-01-16T02:48:00Z"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

---

### GET /api/personas/sessions/{session_id}

세션 상세 조회

**Response: 200 OK**
```json
{
  "id": "session-uuid",
  "persona_id": "persona-uuid",
  "persona_name": "직장인_30대_강남",
  "campaign_id": "campaign-uuid",
  "device_serial": "R3CW60BHSAT",
  "ip_address": "123.456.78.90",
  "ip_provider": "kt",
  "mission": {
    "type": "campaign_workflow",
    "target_keyword": "CCTV 설치",
    "target_url": "https://blog.naver.com/post/12345",
    "min_dwell_time": 120,
    "ai_check_required": true
  },
  "success": true,
  "duration_sec": 180,
  "scroll_count": 8,
  "scroll_depth": 0.85,
  "interactions": 3,
  "phase_timings": {
    "cleanup_ms": 2000,
    "hardware_masking_ms": 1500,
    "soul_restore_ms": 8000
  },
  "error_type": null,
  "error_message": null,
  "started_at": "2026-01-16T02:45:00Z",
  "completed_at": "2026-01-16T02:48:00Z"
}
```

---

### GET /api/personas/sessions/current/status

현재 활성 세션 상태 조회

**Response: 200 OK (활성 세션 있음)**
```json
{
  "is_active": true,
  "session_id": "session-uuid",
  "persona_id": "persona-uuid",
  "persona_name": "직장인_30대_강남",
  "started_at": "2026-01-16T02:45:00Z",
  "elapsed_sec": 120
}
```

**Response: 200 OK (활성 세션 없음)**
```json
{
  "is_active": false,
  "session_id": null
}
```

---

## Campaigns API

**기존 매핑:** `ai-project:8000/campaigns`

캠페인 관리 및 실행 API입니다.

### GET /api/campaigns

캠페인 목록 조회

**Query Parameters:**
- `status: string` - 상태 필터 (`draft`, `active`, `paused`, `completed`)

**Response: 200 OK**
```json
{
  "items": [
    {
      "id": "campaign-uuid",
      "name": "CCTV 설치 블로그 트래픽",
      "status": "active",
      "target_keyword": "CCTV 설치",
      "target_blog_url": "https://blog.naver.com/user/12345",
      "daily_quota": 100,
      "executed_today": 45,
      "total_executions": 1200,
      "success_rate": 0.95,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 5
}
```

---

### GET /api/campaigns/{campaign_id}

캠페인 상세 조회

**Response: 200 OK**
```json
{
  "id": "campaign-uuid",
  "name": "CCTV 설치 블로그 트래픽",
  "status": "active",
  "targets": [
    {
      "keyword": "CCTV 설치",
      "blog_title": "초보자도 쉽게! CCTV 설치 가이드",
      "blog_url": "https://blog.naver.com/user/12345",
      "blogger_name": "보안전문가",
      "target_clicks": 100,
      "target_dwell_time": 120,
      "success_count": 45
    }
  ],
  "daily_quota": 100,
  "executed_today": 45,
  "total_executions": 1200,
  "successful_executions": 1140,
  "success_rate": 0.95,
  "assigned_personas": ["persona-uuid-1", "persona-uuid-2"],
  "assigned_devices": ["R3CW60BHSAT"],
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-16T02:00:00Z"
}
```

---

### POST /api/campaigns/{campaign_id}/control

캠페인 제어 (시작, 일시정지, 재개, 중지)

**Request Body:**
```json
{
  "action": "start"
}
```

**Actions:**
- `start` - 캠페인 시작
- `pause` - 일시정지
- `resume` - 재개
- `stop` - 완전 중지

**Response: 200 OK**
```json
{
  "campaign_id": "campaign-uuid",
  "previous_status": "draft",
  "new_status": "active",
  "message": "Campaign started successfully"
}
```

---

### GET /api/campaigns/{campaign_id}/stats

캠페인 통계 조회

**Query Parameters:**
- `days: integer` - 통계 기간 (1-90일, 기본값: 7)

**Response: 200 OK**
```json
{
  "campaign_id": "campaign-uuid",
  "period": {
    "start_date": "2026-01-10",
    "end_date": "2026-01-16",
    "days": 7
  },
  "total_executions": 350,
  "successful_executions": 333,
  "success_rate": 0.951,
  "total_dwell_time": 42000,
  "avg_dwell_time": 120,
  "unique_personas_used": 45,
  "unique_ips_used": 38,
  "daily_stats": [
    {
      "date": "2026-01-16",
      "executions": 45,
      "successful": 43,
      "success_rate": 0.956,
      "avg_dwell_time": 125
    }
  ]
}
```

---

## Traffic API

**기존 매핑:** `ai-project:8000/traffic`

트래픽 실행 API입니다.

### POST /api/traffic/execute

트래픽 실행 (Pipeline 모드)

**Request Body:**
```json
{
  "campaign_id": "campaign-uuid",
  "persona_id": "persona-uuid",
  "device_serial": "R3CW60BHSAT"
}
```

**Response: 202 Accepted**
```json
{
  "execution_id": "execution-uuid",
  "status": "queued",
  "message": "Traffic execution queued"
}
```

---

### POST /api/traffic/execute-ai

트래픽 실행 (AI 모드 - 동적 UI 탐지)

**Request Body:**
```json
{
  "campaign_id": "campaign-uuid",
  "keyword": "CCTV 설치",
  "blog_title": "초보자도 쉽게! CCTV 설치 가이드",
  "blogger_name": "보안전문가",
  "blog_url": "https://blog.naver.com/user/12345",
  "device_serial": "R3CW60BHSAT"
}
```

**Response: 200 OK**
```json
{
  "execution_id": "execution-uuid",
  "success": true,
  "persona_id": "persona-uuid",
  "session_id": "session-uuid",
  "duration_sec": 180,
  "scroll_count": 8,
  "scroll_depth": 0.85,
  "dwell_time": 165,
  "completed_at": "2026-01-16T02:50:00Z"
}
```

---

### POST /api/traffic/batch

배치 트래픽 실행

**Request Body:**
```json
{
  "campaign_id": "campaign-uuid",
  "count": 5
}
```

**Response: 202 Accepted**
```json
{
  "batch_id": "batch-uuid",
  "count": 5,
  "status": "queued",
  "estimated_duration_sec": 900
}
```

---

### GET /api/traffic/logs/{campaign_id}

캠페인 트래픽 로그 조회

**Query Parameters:**
- `limit: integer` - 로그 개수 (1-100, 기본값: 20)

**Response: 200 OK**
```json
{
  "campaign_id": "campaign-uuid",
  "logs": [
    {
      "execution_id": "execution-uuid",
      "persona_id": "persona-uuid",
      "persona_name": "직장인_30대_강남",
      "success": true,
      "duration_sec": 180,
      "scroll_count": 8,
      "error_type": null,
      "executed_at": "2026-01-16T02:48:00Z"
    }
  ],
  "total": 150,
  "limit": 20
}
```

---

## Devices API

**기존 매핑:** `ai-project:8000/status/devices`

ADB 디바이스 관리 API입니다.

### GET /api/devices

디바이스 목록 조회

**Response: 200 OK**
```json
{
  "devices": [
    {
      "serial": "R3CW60BHSAT",
      "status": "online",
      "model": "SM-G960N",
      "manufacturer": "samsung",
      "sdk_version": 33,
      "screen_width": 1080,
      "screen_height": 2400,
      "battery_level": 85,
      "last_seen": "2026-01-16T02:50:00Z"
    }
  ],
  "total": 1,
  "online": 1,
  "offline": 0
}
```

---

### GET /api/devices/{device_serial}

디바이스 상세 조회

**Response: 200 OK**
```json
{
  "serial": "R3CW60BHSAT",
  "status": "online",
  "model": "SM-G960N",
  "manufacturer": "samsung",
  "sdk_version": 33,
  "android_version": "13",
  "screen_width": 1080,
  "screen_height": 2400,
  "battery_level": 85,
  "battery_temperature": 28.5,
  "cpu_usage": 15.3,
  "memory_available": 2048,
  "storage_available": 10240,
  "current_app": "com.nhn.android.search",
  "last_seen": "2026-01-16T02:50:00Z"
}
```

---

### POST /api/devices/{device_serial}/reboot

디바이스 재부팅

**Response: 200 OK**
```json
{
  "serial": "R3CW60BHSAT",
  "action": "reboot",
  "status": "rebooting",
  "message": "Device reboot initiated"
}
```

---

### POST /api/devices/{device_serial}/screenshot

스크린샷 캡처

**Response: 200 OK**
```json
{
  "serial": "R3CW60BHSAT",
  "screenshot_url": "/api/devices/R3CW60BHSAT/screenshots/2026-01-16_02-50-00.png",
  "size_bytes": 524288,
  "captured_at": "2026-01-16T02:50:00Z"
}
```

---

### GET /api/devices/{device_serial}/ui

UI 계층 조회

**Response: 200 OK**
```json
{
  "serial": "R3CW60BHSAT",
  "current_activity": "com.nhn.android.search/.activity.MainActivity",
  "ui_elements": [
    {
      "resource_id": "com.nhn.android.search:id/search_box",
      "text": "검색어를 입력하세요",
      "clickable": true,
      "bounds": {
        "left": 100,
        "top": 200,
        "right": 980,
        "bottom": 350
      }
    }
  ],
  "captured_at": "2026-01-16T02:50:00Z"
}
```

---

### POST /api/devices/{device_serial}/actions

디바이스 액션 실행

**Request Body:**
```json
{
  "action": "tap",
  "x": 540,
  "y": 275
}
```

**Actions:**
- `tap` - 탭 (x, y 필요)
- `swipe` - 스와이프 (start_x, start_y, end_x, end_y 필요)
- `input` - 텍스트 입력 (text 필요)
- `back` - 뒤로가기
- `home` - 홈

**Response: 200 OK**
```json
{
  "serial": "R3CW60BHSAT",
  "action": "tap",
  "success": true,
  "duration_ms": 120
}
```

---

## Monitoring API

**기존 매핑:** 신규 (통합 모니터링)

시스템 모니터링 및 로그 조회 API입니다.

### GET /api/monitoring/logs

실행 로그 조회

**Query Parameters:**
- `limit: integer` - 로그 개수 (1-100, 기본값: 100)
- `level: string` - 로그 레벨 (`info`, `warning`, `error`)

**Response: 200 OK**
```json
{
  "logs": [
    {
      "timestamp": "2026-01-16T02:50:00Z",
      "level": "info",
      "service": "persona-service",
      "message": "Session completed successfully",
      "session_id": "session-uuid",
      "persona_id": "persona-uuid"
    }
  ],
  "total": 1500,
  "limit": 100
}
```

---

### GET /api/monitoring/stats

시스템 통계

**Response: 200 OK**
```json
{
  "personas": {
    "total": 1000,
    "idle": 850,
    "active": 5,
    "cooling_down": 140,
    "banned": 5,
    "avg_trust_score": 12.5
  },
  "campaigns": {
    "total": 5,
    "active": 2,
    "paused": 1,
    "draft": 1,
    "completed": 1
  },
  "devices": {
    "total": 1,
    "online": 1,
    "offline": 0
  },
  "traffic": {
    "today_executions": 45,
    "today_success_rate": 0.956,
    "active_sessions": 1
  },
  "timestamp": "2026-01-16T02:50:00Z"
}
```

---

### GET /api/monitoring/health

시스템 헬스 체크

**Response: 200 OK**
```json
{
  "status": "healthy",
  "components": {
    "database": "connected",
    "adb": "connected",
    "portal": "available"
  },
  "uptime_sec": 86400,
  "timestamp": "2026-01-16T02:50:00Z"
}
```

---

### GET /api/monitoring/metrics

시스템 메트릭

**Response: 200 OK**
```json
{
  "cpu_usage": 15.3,
  "memory_usage": 45.2,
  "disk_usage": 62.1,
  "active_connections": 3,
  "request_rate_per_min": 120,
  "avg_response_time_ms": 250,
  "timestamp": "2026-01-16T02:50:00Z"
}
```

---

## Legacy Service Mapping

기존 3개 서비스 → CareOn Hub 매핑표입니다.

### persona-manager (5002) → CareOn Hub

| 기존 | 통합 | 변경사항 |
|------|------|---------|
| GET /health | GET /api/monitoring/health | 경로 변경 |
| GET /stats | GET /api/monitoring/stats | 경로 변경, 응답 구조 확장 |
| GET /personas | GET /api/personas | 경로 변경 |
| GET /personas/{id} | GET /api/personas/{id} | 동일 |
| POST /personas | POST /api/personas | 동일 |
| PUT /personas/{id} | PUT /api/personas/{id} | 동일 |
| DELETE /personas/{id} | DELETE /api/personas/{id} | 동일 |
| POST /personas/{id}/ban | POST /api/personas/{id}/ban | 동일 |
| POST /personas/{id}/unban | POST /api/personas/{id}/unban | 동일 |
| GET /personas/{id}/soul | GET /api/personas/{id}/soul | 동일 |
| POST /sessions/start | POST /api/personas/sessions/start | 경로 변경 |
| POST /sessions/{id}/complete | POST /api/personas/sessions/{id}/complete | 경로 변경 |
| POST /sessions/{id}/abort | POST /api/personas/sessions/{id}/abort | 경로 변경 |
| GET /sessions | GET /api/personas/sessions | 경로 변경 |
| GET /sessions/{id} | GET /api/personas/sessions/{id} | 경로 변경 |
| GET /sessions/current/status | GET /api/personas/sessions/current/status | 경로 변경 |

### ai-project (8000) → CareOn Hub

| 기존 | 통합 | 변경사항 |
|------|------|---------|
| GET /health | GET /api/monitoring/health | 경로 변경 |
| GET / | GET / | 동일 |
| GET /campaigns | GET /api/campaigns | 경로 변경 |
| GET /campaigns/{id} | GET /api/campaigns/{id} | 경로 변경 |
| POST /campaigns/{id}/control | POST /api/campaigns/{id}/control | 경로 변경 |
| GET /campaigns/{id}/stats | GET /api/campaigns/{id}/stats | 경로 변경 |
| POST /traffic/execute | POST /api/traffic/execute | 경로 변경 |
| POST /traffic/execute-ai | POST /api/traffic/execute-ai | 경로 변경 |
| POST /traffic/batch | POST /api/traffic/batch | 경로 변경 |
| GET /traffic/logs/{id} | GET /api/traffic/logs/{id} | 경로 변경 |
| GET /status/devices | GET /api/devices | 경로 변경 |
| GET /status/personas | 통합됨 | /api/monitoring/stats에 포함 |
| GET /status/engine | 통합됨 | /api/monitoring/stats에 포함 |

### blog-writer (5001) → CareOn Hub

blog-writer는 독립 서비스로 유지되며, CareOn Hub는 트래픽 실행만 담당합니다.

---

## Error Responses

### 400 Bad Request

잘못된 요청 파라미터

```json
{
  "detail": [
    {
      "loc": ["body", "keyword"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 401 Unauthorized

인증 실패

```json
{
  "detail": "Invalid API Key"
}
```

### 404 Not Found

리소스 없음

```json
{
  "detail": "Persona not found"
}
```

### 409 Conflict

리소스 충돌

```json
{
  "detail": "Persona is currently active in another session"
}
```

### 500 Internal Server Error

서버 내부 오류

```json
{
  "detail": "Internal server error",
  "error_id": "error-uuid"
}
```

---

*마지막 업데이트: 2026-01-16*  
*총 엔드포인트: 37개*  
*참조: Explore Agent af8aa55 분석 결과*
