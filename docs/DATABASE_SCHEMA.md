# CareOn Hub - Database Schema Documentation

> Supabase 데이터베이스 완전 명세서

**작성일**: 2026-01-16
**Supabase 프로젝트**: pkehcfbjotctvneordob.supabase.co
**데이터베이스**: PostgreSQL 15

---

## 목차

1. [개요](#개요)
2. [테이블 구조](#테이블-구조)
   - [personas](#personas-테이블)
   - [persona_sessions](#persona_sessions-테이블)
3. [인덱스](#인덱스)
4. [RPC 함수](#rpc-함수)
5. [Row Level Security (RLS)](#row-level-security-rls)
6. [트리거](#트리거)
7. [JSONB 필드 구조](#jsonb-필드-구조)
8. [데이터 관계도](#데이터-관계도)

---

## 개요

CareOn Hub는 Supabase PostgreSQL 데이터베이스를 사용하여 1,000개의 가상 페르소나와 세션 이력을 관리합니다.

**핵심 테이블**:
- `personas`: 페르소나 기본 정보 및 상태 관리 (29개 컬럼)
- `persona_sessions`: 세션 실행 이력 및 통계 (18개 컬럼)

**접근 방식**:
- REST API: `https://pkehcfbjotctvneordob.supabase.co/rest/v1/`
- PostgreSQL 직접 연결 (필요시)
- RPC 함수를 통한 복잡한 비즈니스 로직 실행

---

## 테이블 구조

### personas 테이블

**목적**: 1,000개의 가상 페르소나 프로필 및 상태 관리

#### 컬럼 정의

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 페르소나 고유 ID |
| `name` | VARCHAR(100) | NOT NULL | - | 페르소나 이름 (예: "직장인_30대_강남") |
| `device_config` | JSONB | NOT NULL | `'{}'::jsonb` | 디바이스 설정 (ANDROID_ID, IMEI 등) |
| `trust_score` | INTEGER | CHECK >= 0 | `0` | 신뢰도 점수 (세션 성공률 기반) |
| `status` | VARCHAR(20) | NOT NULL | `'idle'` | 현재 상태: idle, active, cooling_down, banned, retired |
| `last_used_at` | TIMESTAMP WITH TIME ZONE | - | `NULL` | 마지막 사용 시간 |
| `cooldown_until` | TIMESTAMP WITH TIME ZONE | - | `NULL` | 쿨다운 종료 시간 |
| `total_sessions` | INTEGER | CHECK >= 0 | `0` | 총 실행 세션 수 |
| `successful_sessions` | INTEGER | CHECK >= 0 | `0` | 성공한 세션 수 |
| `failed_sessions` | INTEGER | CHECK >= 0 | `0` | 실패한 세션 수 |
| `total_traffic_volume` | INTEGER | CHECK >= 0 | `0` | 총 트래픽 볼륨 (클릭 수) |
| `average_session_duration` | INTEGER | CHECK >= 0 | `0` | 평균 세션 지속 시간 (초) |
| `last_failure_reason` | TEXT | - | `NULL` | 마지막 실패 사유 |
| `consecutive_failures` | INTEGER | CHECK >= 0 | `0` | 연속 실패 횟수 (3회 이상 시 자동 banned) |
| `banned_at` | TIMESTAMP WITH TIME ZONE | - | `NULL` | 밴 처리 시간 |
| `banned_reason` | TEXT | - | `NULL` | 밴 사유 |
| `behavior_profile` | JSONB | NOT NULL | `'{}'::jsonb` | 행동 프로필 (타이핑 속도, 스크롤 패턴 등) |
| `location` | JSONB | - | `NULL` | GPS 위치 정보 (위도, 경도, 정확도) |
| `network_info` | JSONB | - | `NULL` | 네트워크 정보 (IP 대역, ISP) |
| `mission` | JSONB | - | `NULL` | 현재 할당된 미션 정보 |
| `mission_assigned_at` | TIMESTAMP WITH TIME ZONE | - | `NULL` | 미션 할당 시간 |
| `tags` | TEXT[] | - | `'{}'` | 태그 배열 (예: ["VIP", "고신뢰도"]) |
| `notes` | TEXT | - | `NULL` | 관리자 메모 |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | `now()` | 생성 시간 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | `now()` | 마지막 수정 시간 |
| `retired_at` | TIMESTAMP WITH TIME ZONE | - | `NULL` | 은퇴 처리 시간 |
| `retirement_reason` | TEXT | - | `NULL` | 은퇴 사유 |
| `metadata` | JSONB | - | `NULL` | 추가 메타데이터 |
| `performance_score` | NUMERIC(5,2) | CHECK >= 0 AND <= 100 | `0.00` | 성능 점수 (0~100) |

#### 제약 조건

**PRIMARY KEY**:
```sql
CONSTRAINT personas_pkey PRIMARY KEY (id)
```

**CHECK 제약**:
```sql
CONSTRAINT personas_trust_score_check CHECK (trust_score >= 0)
CONSTRAINT personas_total_sessions_check CHECK (total_sessions >= 0)
CONSTRAINT personas_successful_sessions_check CHECK (successful_sessions >= 0)
CONSTRAINT personas_failed_sessions_check CHECK (failed_sessions >= 0)
CONSTRAINT personas_total_traffic_volume_check CHECK (total_traffic_volume >= 0)
CONSTRAINT personas_average_session_duration_check CHECK (average_session_duration >= 0)
CONSTRAINT personas_consecutive_failures_check CHECK (consecutive_failures >= 0)
CONSTRAINT personas_performance_score_check CHECK (performance_score >= 0 AND performance_score <= 100)
```

**UNIQUE 제약**:
```sql
CONSTRAINT personas_name_unique UNIQUE (name)
```

#### 인덱스

| Index Name | Columns | Type | Purpose |
|-----------|---------|------|---------|
| `idx_personas_status` | `status` | B-tree | Status 필터링 최적화 (idle, active 등) |
| `idx_personas_trust_score` | `trust_score DESC` | B-tree | 고신뢰도 페르소나 검색 |
| `idx_personas_cooldown` | `cooldown_until` | B-tree | 쿨다운 만료 체크 |
| `idx_personas_last_used` | `last_used_at DESC` | B-tree | 최근 사용 이력 정렬 |
| `idx_personas_performance` | `performance_score DESC` | B-tree | 성능 순위 정렬 |
| `idx_personas_selection` | `status, cooldown_until, trust_score DESC` | B-tree (Composite) | **가용 페르소나 선택 최적화** (가장 중요) |
| `idx_personas_tags` | `tags` | GIN | 태그 배열 검색 최적화 |
| `idx_personas_device_config` | `device_config` | GIN | JSONB 필드 검색 최적화 |

**인덱스 사용 예시**:
```sql
-- idx_personas_selection 사용
SELECT * FROM personas
WHERE status = 'idle'
  AND (cooldown_until IS NULL OR cooldown_until < now())
ORDER BY trust_score DESC
LIMIT 1;

-- idx_personas_tags 사용
SELECT * FROM personas
WHERE tags @> ARRAY['VIP'];
```

#### 트리거

**updated_at 자동 갱신**:
```sql
CREATE TRIGGER update_personas_updated_at
BEFORE UPDATE ON personas
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

---

### persona_sessions 테이블

**목적**: 페르소나별 세션 실행 이력 및 통계 기록

#### 컬럼 정의

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | 세션 고유 ID |
| `persona_id` | UUID | NOT NULL, FOREIGN KEY | - | 페르소나 ID (personas.id 참조) |
| `campaign_id` | VARCHAR(100) | - | `NULL` | 캠페인 ID |
| `status` | VARCHAR(20) | NOT NULL | `'pending'` | 세션 상태: pending, running, completed, failed, cancelled |
| `started_at` | TIMESTAMP WITH TIME ZONE | - | `NULL` | 세션 시작 시간 |
| `completed_at` | TIMESTAMP WITH TIME ZONE | - | `NULL` | 세션 종료 시간 |
| `duration_seconds` | INTEGER | CHECK >= 0 | `0` | 세션 지속 시간 (초) |
| `traffic_volume` | INTEGER | CHECK >= 0 | `0` | 트래픽 볼륨 (클릭 수) |
| `conversions` | INTEGER | CHECK >= 0 | `0` | 전환 수 (목표 달성 횟수) |
| `error_message` | TEXT | - | `NULL` | 에러 메시지 (실패 시) |
| `execution_log` | JSONB | - | `NULL` | 실행 로그 (단계별 기록) |
| `metadata` | JSONB | - | `NULL` | 추가 메타데이터 |
| `device_info` | JSONB | - | `NULL` | 실행 당시 디바이스 정보 스냅샷 |
| `network_info` | JSONB | - | `NULL` | 실행 당시 네트워크 정보 |
| `soul_swap_phase` | VARCHAR(50) | - | `NULL` | Soul Swap 단계 (cleanup, restore, launch, backup) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | `now()` | 생성 시간 |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | `now()` | 마지막 수정 시간 |
| `retry_count` | INTEGER | CHECK >= 0 | `0` | 재시도 횟수 |

#### 제약 조건

**PRIMARY KEY**:
```sql
CONSTRAINT persona_sessions_pkey PRIMARY KEY (id)
```

**FOREIGN KEY**:
```sql
CONSTRAINT persona_sessions_persona_id_fkey
FOREIGN KEY (persona_id) REFERENCES personas(id)
ON DELETE CASCADE
```

**CHECK 제약**:
```sql
CONSTRAINT persona_sessions_duration_seconds_check CHECK (duration_seconds >= 0)
CONSTRAINT persona_sessions_traffic_volume_check CHECK (traffic_volume >= 0)
CONSTRAINT persona_sessions_conversions_check CHECK (conversions >= 0)
CONSTRAINT persona_sessions_retry_count_check CHECK (retry_count >= 0)
```

#### 인덱스

| Index Name | Columns | Type | Purpose |
|-----------|---------|------|---------|
| `idx_sessions_persona_id` | `persona_id` | B-tree | 페르소나별 세션 조회 |
| `idx_sessions_campaign_id` | `campaign_id` | B-tree | 캠페인별 세션 조회 |
| `idx_sessions_status` | `status` | B-tree | Status 필터링 |
| `idx_sessions_started_at` | `started_at DESC` | B-tree | 시간순 정렬 |
| `idx_sessions_completed_at` | `completed_at DESC` | B-tree | 완료 시간 정렬 |
| `idx_sessions_execution_log` | `execution_log` | GIN | JSONB 필드 검색 |

**인덱스 사용 예시**:
```sql
-- 특정 페르소나의 최근 세션 조회
SELECT * FROM persona_sessions
WHERE persona_id = 'uuid-here'
ORDER BY started_at DESC
LIMIT 10;

-- 특정 캠페인의 성공률 계산
SELECT
  campaign_id,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE status = 'completed') as successful
FROM persona_sessions
WHERE campaign_id = 'campaign-123'
GROUP BY campaign_id;
```

#### 트리거

**updated_at 자동 갱신**:
```sql
CREATE TRIGGER update_persona_sessions_updated_at
BEFORE UPDATE ON persona_sessions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

---

## RPC 함수

Supabase RPC 함수를 통해 복잡한 비즈니스 로직을 서버 사이드에서 실행합니다.

### select_available_persona()

**목적**: 가용한 최적 페르소나 자동 선택 (원자적 트랜잭션)

**시그니처**:
```sql
select_available_persona(
  campaign_id_param VARCHAR(100) DEFAULT NULL,
  min_trust_score_param INTEGER DEFAULT 0
) RETURNS UUID
```

**로직**:
1. 가용 조건 필터링:
   - `status = 'idle'`
   - `cooldown_until IS NULL OR cooldown_until < now()`
   - `trust_score >= min_trust_score_param`
2. 신뢰도 점수 내림차순 정렬
3. 첫 번째 페르소나 선택 (FOR UPDATE SKIP LOCKED)
4. 선택된 페르소나 상태 변경:
   - `status = 'active'`
   - `last_used_at = now()`
   - `mission = {"campaign_id": campaign_id_param}`
   - `mission_assigned_at = now()`
5. UUID 반환

**사용 예시**:
```sql
SELECT select_available_persona('campaign-123', 10);
-- 반환: 'f7b3c8d2-1234-5678-9abc-def012345678'
```

**Python 호출**:
```python
result = supabase.rpc('select_available_persona', {
    'campaign_id_param': 'campaign-123',
    'min_trust_score_param': 10
}).execute()
persona_id = result.data  # UUID
```

---

### checkin_persona()

**목적**: 세션 종료 후 페르소나 상태 복원 (쿨다운 설정)

**시그니처**:
```sql
checkin_persona(
  persona_id_param UUID,
  session_id_param UUID,
  success BOOLEAN,
  failure_reason_param TEXT DEFAULT NULL,
  cooldown_minutes INTEGER DEFAULT 30
) RETURNS VOID
```

**로직**:
1. 세션 상태 업데이트:
   - `status = 'completed' OR 'failed'`
   - `completed_at = now()`
   - `error_message = failure_reason_param` (실패 시)
2. 페르소나 통계 업데이트:
   - `total_sessions += 1`
   - `successful_sessions += 1` (성공 시)
   - `failed_sessions += 1` (실패 시)
   - `consecutive_failures` 증가/리셋
3. 페르소나 상태 변경:
   - 성공: `status = 'cooling_down'`, `cooldown_until = now() + cooldown_minutes`
   - 실패: `last_failure_reason = failure_reason_param`
   - 3회 연속 실패: `status = 'banned'`, `banned_at = now()`, `banned_reason = '3회 연속 실패'`
4. `trust_score` 재계산:
   - 성공률 기반: `trust_score = (successful_sessions * 100) / total_sessions`

**사용 예시**:
```sql
-- 성공 체크인
CALL checkin_persona(
  'f7b3c8d2-1234-5678-9abc-def012345678',
  'session-uuid',
  TRUE,
  NULL,
  30
);

-- 실패 체크인
CALL checkin_persona(
  'f7b3c8d2-1234-5678-9abc-def012345678',
  'session-uuid',
  FALSE,
  'ADB connection lost',
  60
);
```

**Python 호출**:
```python
supabase.rpc('checkin_persona', {
    'persona_id_param': persona_id,
    'session_id_param': session_id,
    'success': True,
    'failure_reason_param': None,
    'cooldown_minutes': 30
}).execute()
```

---

### get_persona_stats()

**목적**: 페르소나 통계 조회 (집계 데이터)

**시그니처**:
```sql
get_persona_stats(
  persona_id_param UUID
) RETURNS TABLE (
  total_sessions INTEGER,
  successful_sessions INTEGER,
  failed_sessions INTEGER,
  success_rate NUMERIC(5,2),
  average_duration INTEGER,
  total_traffic INTEGER,
  total_conversions INTEGER
)
```

**로직**:
1. `personas` 테이블에서 기본 통계 조회
2. `persona_sessions` 테이블에서 집계:
   - 평균 세션 지속 시간
   - 총 트래픽 볼륨
   - 총 전환 수
3. 성공률 계산: `(successful_sessions * 100.0) / NULLIF(total_sessions, 0)`

**사용 예시**:
```sql
SELECT * FROM get_persona_stats('f7b3c8d2-1234-5678-9abc-def012345678');
```

**반환 예시**:
```json
{
  "total_sessions": 150,
  "successful_sessions": 145,
  "failed_sessions": 5,
  "success_rate": 96.67,
  "average_duration": 180,
  "total_traffic": 4500,
  "total_conversions": 120
}
```

---

### ban_persona()

**목적**: 페르소나 수동 밴 처리

**시그니처**:
```sql
ban_persona(
  persona_id_param UUID,
  reason_param TEXT
) RETURNS VOID
```

**로직**:
1. 페르소나 상태 변경:
   - `status = 'banned'`
   - `banned_at = now()`
   - `banned_reason = reason_param`
2. 활성 세션 있으면 취소:
   - `UPDATE persona_sessions SET status = 'cancelled' WHERE persona_id = persona_id_param AND status = 'running'`

**사용 예시**:
```sql
CALL ban_persona(
  'f7b3c8d2-1234-5678-9abc-def012345678',
  '의심스러운 활동 패턴 감지'
);
```

---

### unban_persona()

**목적**: 페르소나 밴 해제

**시그니처**:
```sql
unban_persona(
  persona_id_param UUID
) RETURNS VOID
```

**로직**:
1. 페르소나 상태 변경:
   - `status = 'idle'`
   - `banned_at = NULL`
   - `banned_reason = NULL`
   - `consecutive_failures = 0`
   - `last_failure_reason = NULL`

**사용 예시**:
```sql
CALL unban_persona('f7b3c8d2-1234-5678-9abc-def012345678');
```

---

## Row Level Security (RLS)

Supabase는 Row Level Security를 사용하여 테이블 접근을 제어합니다.

### personas 테이블 RLS 정책

**정책 1: service_role 전체 접근**
```sql
CREATE POLICY "service_role_full_access"
ON personas
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
```

**정책 2: authenticated 읽기 전용**
```sql
CREATE POLICY "authenticated_read_only"
ON personas
FOR SELECT
TO authenticated
USING (true);
```

**정책 3: anon 제한적 읽기**
```sql
CREATE POLICY "anon_limited_read"
ON personas
FOR SELECT
TO anon
USING (
  status IN ('idle', 'cooling_down')
  AND banned_at IS NULL
);
```

**적용**:
```sql
ALTER TABLE personas ENABLE ROW LEVEL SECURITY;
```

---

### persona_sessions 테이블 RLS 정책

**정책 1: service_role 전체 접근**
```sql
CREATE POLICY "service_role_full_access"
ON persona_sessions
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
```

**정책 2: authenticated 읽기 전용**
```sql
CREATE POLICY "authenticated_read_only"
ON persona_sessions
FOR SELECT
TO authenticated
USING (true);
```

**정책 3: anon 접근 불가**
```sql
-- 익명 사용자는 세션 이력 조회 불가 (정책 없음)
```

**적용**:
```sql
ALTER TABLE persona_sessions ENABLE ROW LEVEL SECURITY;
```

---

## JSONB 필드 구조

### device_config (personas 테이블)

**목적**: 디바이스 고유 식별자 및 설정

**필드**:
```json
{
  "android_id": "16-hex-char-string",
  "imei": "15-digit-string",
  "serial": "device-serial-number",
  "model": "SM-G960N",
  "manufacturer": "samsung",
  "brand": "samsung",
  "device": "starlte",
  "product": "starltexx",
  "sdk_version": 33,
  "android_version": "13",
  "build_fingerprint": "samsung/starltexx/starlte:13/TP1A.220624.014/G960NKSU9HWL1:user/release-keys",
  "security_patch": "2023-12-01",
  "screen_width": 1440,
  "screen_height": 2960,
  "density": 560
}
```

**예시 조회**:
```sql
SELECT
  id,
  name,
  device_config->>'model' as model,
  device_config->>'android_id' as android_id
FROM personas
WHERE device_config->>'manufacturer' = 'samsung';
```

---

### behavior_profile (personas 테이블)

**목적**: 페르소나별 행동 패턴 정의 (사람처럼 행동)

**필드**:
```json
{
  "typing_speed": {
    "wpm": 45,
    "error_rate": 0.03,
    "pause_probability": 0.15
  },
  "scroll_pattern": {
    "speed_range": [500, 1500],
    "pause_probability": 0.2,
    "back_scroll_probability": 0.1
  },
  "click_pattern": {
    "delay_range": [300, 800],
    "double_click_probability": 0.05,
    "misclick_probability": 0.02
  },
  "read_time_multiplier": 1.2,
  "interest_decay_rate": 0.15,
  "multitasking_probability": 0.1
}
```

**사용 예시**:
```python
# BehaviorInjector에서 행동 프로필 로드
behavior = persona['behavior_profile']
typing_speed = behavior['typing_speed']['wpm']
error_rate = behavior['typing_speed']['error_rate']
```

---

### location (personas 테이블)

**목적**: 페르소나 위치 정보 (GPS 스푸핑용)

**필드**:
```json
{
  "latitude": 37.497942,
  "longitude": 127.027621,
  "altitude": 38.5,
  "accuracy": 15.0,
  "provider": "gps",
  "address": "서울특별시 강남구 역삼동",
  "region": "서울",
  "district": "강남구"
}
```

---

### network_info (personas 테이블)

**목적**: 네트워크 환경 정보

**필드**:
```json
{
  "ip_range": "211.xxx.xxx.xxx/24",
  "isp": "SK Broadband",
  "connection_type": "wifi",
  "wifi_ssid": "HomeNetwork_5G",
  "mobile_carrier": "SKT",
  "mobile_network_type": "5G"
}
```

---

### mission (personas 테이블)

**목적**: 현재 할당된 미션 정보

**필드**:
```json
{
  "campaign_id": "campaign-123",
  "campaign_name": "CCTV 설치 키워드 부스팅",
  "target_url": "https://blog.naver.com/...",
  "keywords": ["CCTV 설치", "보안카메라"],
  "actions": [
    {"type": "search", "keyword": "CCTV 설치"},
    {"type": "click", "target": "blog_link"},
    {"type": "read", "duration": 120},
    {"type": "scroll", "count": 3}
  ],
  "assigned_at": "2026-01-16T12:34:56Z"
}
```

---

### execution_log (persona_sessions 테이블)

**목적**: 세션 실행 단계별 로그

**필드**:
```json
{
  "steps": [
    {
      "timestamp": "2026-01-16T12:35:00Z",
      "phase": "soul_swap_cleanup",
      "status": "success",
      "duration_ms": 2500
    },
    {
      "timestamp": "2026-01-16T12:35:03Z",
      "phase": "soul_swap_restore",
      "status": "success",
      "duration_ms": 8000,
      "details": {
        "apps_restored": ["com.nhn.android.search", "com.nhn.android.nfc"]
      }
    },
    {
      "timestamp": "2026-01-16T12:35:15Z",
      "phase": "traffic_execution",
      "status": "success",
      "duration_ms": 125000,
      "details": {
        "searches": 1,
        "clicks": 1,
        "scrolls": 5,
        "read_time": 120
      }
    },
    {
      "timestamp": "2026-01-16T12:37:20Z",
      "phase": "soul_swap_backup",
      "status": "success",
      "duration_ms": 5000
    }
  ],
  "summary": {
    "total_duration_ms": 140500,
    "phases_completed": 4,
    "phases_failed": 0
  }
}
```

**조회 예시**:
```sql
SELECT
  id,
  status,
  execution_log->'summary'->>'total_duration_ms' as duration_ms,
  execution_log->'summary'->>'phases_completed' as phases_completed
FROM persona_sessions
WHERE campaign_id = 'campaign-123'
  AND status = 'completed';
```

---

### device_info (persona_sessions 테이블)

**목적**: 실행 당시 디바이스 상태 스냅샷

**필드**:
```json
{
  "battery_level": 85,
  "battery_charging": false,
  "screen_brightness": 150,
  "wifi_connected": true,
  "mobile_data": false,
  "airplane_mode": false,
  "location_enabled": true,
  "timestamp": "2026-01-16T12:35:00Z"
}
```

---

## 데이터 관계도

```
┌─────────────────────────────────────────┐
│            personas                     │
│  (1,000 rows)                           │
├─────────────────────────────────────────┤
│ id (PK)                    UUID         │
│ name                       VARCHAR(100) │
│ device_config              JSONB        │
│ trust_score                INTEGER      │
│ status                     VARCHAR(20)  │
│ last_used_at               TIMESTAMPTZ  │
│ cooldown_until             TIMESTAMPTZ  │
│ total_sessions             INTEGER      │
│ successful_sessions        INTEGER      │
│ failed_sessions            INTEGER      │
│ behavior_profile           JSONB        │
│ location                   JSONB        │
│ mission                    JSONB        │
│ ...                                     │
└───────────┬─────────────────────────────┘
            │
            │ 1:N
            │
┌───────────▼─────────────────────────────┐
│      persona_sessions                   │
│  (수만~수십만 rows)                      │
├─────────────────────────────────────────┤
│ id (PK)                    UUID         │
│ persona_id (FK)            UUID         │
│ campaign_id                VARCHAR(100) │
│ status                     VARCHAR(20)  │
│ started_at                 TIMESTAMPTZ  │
│ completed_at               TIMESTAMPTZ  │
│ duration_seconds           INTEGER      │
│ traffic_volume             INTEGER      │
│ conversions                INTEGER      │
│ execution_log              JSONB        │
│ device_info                JSONB        │
│ ...                                     │
└─────────────────────────────────────────┘
```

**관계**:
- 1개 페르소나 → N개 세션 (1:N)
- 외래키: `persona_sessions.persona_id → personas.id` (ON DELETE CASCADE)

**데이터 흐름**:
1. 캠페인 시작 → `select_available_persona()` 호출
2. 페르소나 선택 → `personas.status = 'active'`
3. 세션 생성 → `persona_sessions` 레코드 INSERT
4. 트래픽 실행 → `execution_log` 업데이트
5. 세션 종료 → `checkin_persona()` 호출
6. 통계 업데이트 → `personas.successful_sessions++`, `status = 'cooling_down'`

---

## 마이그레이션 SQL

### 초기 테이블 생성

```sql
-- personas 테이블
CREATE TABLE personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    device_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    trust_score INTEGER DEFAULT 0 CHECK (trust_score >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'idle',
    last_used_at TIMESTAMP WITH TIME ZONE,
    cooldown_until TIMESTAMP WITH TIME ZONE,
    total_sessions INTEGER DEFAULT 0 CHECK (total_sessions >= 0),
    successful_sessions INTEGER DEFAULT 0 CHECK (successful_sessions >= 0),
    failed_sessions INTEGER DEFAULT 0 CHECK (failed_sessions >= 0),
    total_traffic_volume INTEGER DEFAULT 0 CHECK (total_traffic_volume >= 0),
    average_session_duration INTEGER DEFAULT 0 CHECK (average_session_duration >= 0),
    last_failure_reason TEXT,
    consecutive_failures INTEGER DEFAULT 0 CHECK (consecutive_failures >= 0),
    banned_at TIMESTAMP WITH TIME ZONE,
    banned_reason TEXT,
    behavior_profile JSONB NOT NULL DEFAULT '{}'::jsonb,
    location JSONB,
    network_info JSONB,
    mission JSONB,
    mission_assigned_at TIMESTAMP WITH TIME ZONE,
    tags TEXT[] DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    retired_at TIMESTAMP WITH TIME ZONE,
    retirement_reason TEXT,
    metadata JSONB,
    performance_score NUMERIC(5,2) DEFAULT 0.00 CHECK (performance_score >= 0 AND performance_score <= 100)
);

-- persona_sessions 테이블
CREATE TABLE persona_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    campaign_id VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER DEFAULT 0 CHECK (duration_seconds >= 0),
    traffic_volume INTEGER DEFAULT 0 CHECK (traffic_volume >= 0),
    conversions INTEGER DEFAULT 0 CHECK (conversions >= 0),
    error_message TEXT,
    execution_log JSONB,
    metadata JSONB,
    device_info JSONB,
    network_info JSONB,
    soul_swap_phase VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0)
);
```

### 인덱스 생성

```sql
-- personas 인덱스
CREATE INDEX idx_personas_status ON personas(status);
CREATE INDEX idx_personas_trust_score ON personas(trust_score DESC);
CREATE INDEX idx_personas_cooldown ON personas(cooldown_until);
CREATE INDEX idx_personas_last_used ON personas(last_used_at DESC);
CREATE INDEX idx_personas_performance ON personas(performance_score DESC);
CREATE INDEX idx_personas_selection ON personas(status, cooldown_until, trust_score DESC);
CREATE INDEX idx_personas_tags ON personas USING GIN(tags);
CREATE INDEX idx_personas_device_config ON personas USING GIN(device_config);

-- persona_sessions 인덱스
CREATE INDEX idx_sessions_persona_id ON persona_sessions(persona_id);
CREATE INDEX idx_sessions_campaign_id ON persona_sessions(campaign_id);
CREATE INDEX idx_sessions_status ON persona_sessions(status);
CREATE INDEX idx_sessions_started_at ON persona_sessions(started_at DESC);
CREATE INDEX idx_sessions_completed_at ON persona_sessions(completed_at DESC);
CREATE INDEX idx_sessions_execution_log ON persona_sessions USING GIN(execution_log);
```

### 트리거 함수 생성

```sql
-- updated_at 자동 갱신 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- personas 트리거
CREATE TRIGGER update_personas_updated_at
BEFORE UPDATE ON personas
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- persona_sessions 트리거
CREATE TRIGGER update_persona_sessions_updated_at
BEFORE UPDATE ON persona_sessions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

---

## Python 사용 예시

### Supabase 클라이언트 초기화

```python
from supabase import create_client, Client

supabase: Client = create_client(
    supabase_url="https://pkehcfbjotctvneordob.supabase.co",
    supabase_key="your-service-role-key"
)
```

### 페르소나 조회

```python
# 가용 페르소나 목록
response = supabase.table('personas') \
    .select('*') \
    .eq('status', 'idle') \
    .gte('trust_score', 10) \
    .order('trust_score', desc=True) \
    .limit(10) \
    .execute()

personas = response.data
```

### 페르소나 선택 (RPC)

```python
# 원자적 선택
result = supabase.rpc('select_available_persona', {
    'campaign_id_param': 'campaign-123',
    'min_trust_score_param': 10
}).execute()

persona_id = result.data  # UUID
```

### 세션 생성

```python
session_data = {
    'persona_id': persona_id,
    'campaign_id': 'campaign-123',
    'status': 'running',
    'started_at': 'now()'
}

response = supabase.table('persona_sessions') \
    .insert(session_data) \
    .execute()

session_id = response.data[0]['id']
```

### 세션 체크인 (RPC)

```python
supabase.rpc('checkin_persona', {
    'persona_id_param': persona_id,
    'session_id_param': session_id,
    'success': True,
    'failure_reason_param': None,
    'cooldown_minutes': 30
}).execute()
```

### 통계 조회

```python
# 페르소나 통계
stats = supabase.rpc('get_persona_stats', {
    'persona_id_param': persona_id
}).execute()

print(f"성공률: {stats.data['success_rate']}%")
print(f"총 세션: {stats.data['total_sessions']}")
```

---

*마지막 업데이트: 2026-01-16*
*프로젝트: CareOn Hub v1.0.0*
