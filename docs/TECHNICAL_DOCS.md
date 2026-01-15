# CareOn Hub - 기술 문서 (Technical Documentation)

> 복사된 핵심 모듈의 완전한 기술 명세

**작성일:** 2026-01-16  
**대상:** 개발자  
**목적:** 복사된 4개 핵심 모듈(soul_swap, adb, traffic, portal)의 완전한 API 레퍼런스

---

## 목차

1. [Soul Swap 모듈](#1-soul-swap-module)
2. [ADB 모듈](#2-adb-module)
3. [Traffic 모듈](#3-traffic-module)
4. [Portal 모듈](#4-portal-module)
5. [통합 가이드](#5-integration-guide)

---

## 1. Soul Swap Module

**위치:** `/home/tlswkehd/projects/careon-hub/backend/app/core/soul_swap/`

**목적:** 앱 데이터 백업/복원 및 디바이스 Identity 변경

### 1.1 모듈 구조

```
soul_swap/
├── soul/
│   ├── __init__.py
│   ├── app_data_paths.py      # 앱 설정 상수
│   ├── soul_manager.py         # 백업/복원 관리
│   └── cookie_manager.py       # 쿠키 추출/검증
└── identity/
    ├── __init__.py
    └── device_identity.py      # ANDROID_ID, GPS 제어
```

### 1.2 app_data_paths.py

#### AppConfig (dataclass)

타겟 앱의 설정 정보를 정의합니다.

**필드:**
- `package: str` - 앱 패키지명 (예: com.nhn.android.search)
- `data_path: str` - 앱 데이터 디렉토리 경로 (예: /data/data/com.nhn.android.search)
- `launch_activity: str` - 앱 메인 액티비티 (예: .activity.MainActivity)
- `critical_files: List[str]` - 로그인 확인용 필수 파일 경로
- `exclude_from_backup: List[str]` - 백업 제외 파일/디렉토리 (예: cache/)

**사전 정의된 앱:**
```python
NAVER_APP = AppConfig(
    package="com.nhn.android.search",
    data_path="/data/data/com.nhn.android.search",
    launch_activity=".activity.MainActivity",
    critical_files=[
        "shared_prefs/com.nhn.android.search_preferences.xml",
        "app_webview/Cookies"
    ],
    exclude_from_backup=["cache/", "code_cache/", "files/image_manager_disk_cache/"]
)

CHROME_APP = AppConfig(
    package="com.android.chrome",
    data_path="/data/data/com.android.chrome",
    launch_activity="com.google.android.apps.chrome.Main",
    critical_files=["app_chrome/Default/Cookies"],
    exclude_from_backup=["cache/"]
)

NAVER_MAP_APP = AppConfig(...)
```

**상수:**
- `SOUL_STORAGE_BASE: str = "/sdcard/personas"` - 백업 저장 루트 경로
- `MAX_BACKUP_VERSIONS: int = 3` - 최대 유지 백업 버전

---

### 1.3 soul_manager.py

#### SoulManager Class

앱 데이터 백업/복원을 관리하는 핵심 클래스입니다.

**초기화:**
```python
from app.core.soul_swap.soul import SoulManager

manager = SoulManager()
```

#### Methods

##### async cleanup(app: AppConfig) -> None

**목적:** Phase 1 - 앱 초기화 (강제 종료 + 데이터 초기화)

**파라미터:**
- `app: AppConfig` - 타겟 앱 설정

**동작:**
1. `am force-stop {package}` - 앱 강제 종료
2. `pm clear {package}` - 앱 데이터 완전 삭제 (shared_prefs, databases, files 모두)

**예외:**
- `subprocess.CalledProcessError` - ADB 명령 실패

**사용 예제:**
```python
from app.core.soul_swap.soul import SoulManager, NAVER_APP

manager = SoulManager()
await manager.cleanup(NAVER_APP)
print("✓ Naver 앱 초기화 완료")
```

---

##### async restore(persona_id: str, soul_file: str, app: AppConfig) -> None

**목적:** Phase 3 - tar.gz 백업 파일로부터 앱 데이터 복원

**파라미터:**
- `persona_id: str` - 페르소나 ID
- `soul_file: str` - 백업 파일 경로 (예: /sdcard/personas/persona_001/naver_v3.tar.gz)
- `app: AppConfig` - 타겟 앱 설정

**동작:**
1. tar.gz 파일을 `/data/data/{package}/`로 추출
2. 파일 소유권을 앱 UID로 변경 (`chown`)
3. 권한 복원 (`chmod`)

**예외:**
- `FileNotFoundError` - 백업 파일이 없음
- `subprocess.CalledProcessError` - 추출 또는 권한 변경 실패

**사용 예제:**
```python
persona_id = "persona_001"
soul_file = f"/sdcard/personas/{persona_id}/naver_v3.tar.gz"

await manager.restore(persona_id, soul_file, NAVER_APP)
print("✓ Naver 앱 데이터 복원 완료")
```

---

##### async backup(persona_id: str, app: AppConfig) -> str

**목적:** Phase 5 - 현재 앱 데이터를 tar.gz로 백업

**파라미터:**
- `persona_id: str` - 페르소나 ID  
- `app: AppConfig` - 타겟 앱 설정

**반환:**
- `str` - 생성된 백업 파일 경로

**동작:**
1. 다음 버전 번호 계산 (`v1`, `v2`, `v3`)
2. exclude 패턴을 제외하고 tar.gz 생성
3. 최대 백업 버전 초과 시 오래된 백업 삭제 (MAX_BACKUP_VERSIONS)

**사용 예제:**
```python
backup_file = await manager.backup("persona_001", NAVER_APP)
print(f"✓ 백업 완료: {backup_file}")
# 출력: /sdcard/personas/persona_001/naver_v1.tar.gz
```

---

##### async launch_app(app: AppConfig) -> None

**목적:** Phase 4 - 앱 실행

**파라미터:**
- `app: AppConfig` - 실행할 앱 설정

**동작:**
- `am start -n {package}/{activity}` - 앱 메인 액티비티 실행

**사용 예제:**
```python
await manager.launch_app(NAVER_APP)
await asyncio.sleep(5)  # 앱 초기화 대기
```

---

##### async verify_login_state(app: AppConfig) -> bool

**목적:** 로그인 상태 확인 (critical_files 존재 여부 체크)

**파라미터:**
- `app: AppConfig` - 확인할 앱 설정

**반환:**
- `bool` - 모든 critical_files가 존재하면 True

**사용 예제:**
```python
is_logged_in = await manager.verify_login_state(NAVER_APP)
if is_logged_in:
    print("✓ 로그인 상태 확인됨")
else:
    print("✗ 로그인 필요")
```

---

##### get_soul_info(persona_id: str, app: AppConfig) -> Dict

**목적:** 백업 파일 메타데이터 조회

**파라미터:**
- `persona_id: str` - 페르소나 ID
- `app: AppConfig` - 앱 설정

**반환:**
- `Dict` - 백업 파일 정보
  - `latest_version: int` - 최신 버전 번호
  - `latest_file: str` - 최신 백업 파일 경로
  - `file_size: int` - 파일 크기 (bytes)
  - `modified_time: datetime` - 수정 시각

**사용 예제:**
```python
info = await manager.get_soul_info("persona_001", NAVER_APP)
print(f"최신 백업: {info['latest_file']} ({info['file_size']} bytes)")
```

---

### 1.4 cookie_manager.py

#### CookieManager Class

Naver 앱의 쿠키를 추출하고 검증합니다.

**초기화:**
```python
from app.core.soul_swap.soul import CookieManager

cookie_mgr = CookieManager()
```

#### Methods

##### async extract_naver_cookies() -> Dict[str, str]

**목적:** Naver 앱에서 NNB, NID_SES, NID_AUT 쿠키 추출

**반환:**
- `Dict[str, str]` - 쿠키 딕셔너리
  - `"NNB"`: 50년 유효한 디바이스 식별자
  - `"NID_AUT"`: 로그인 인증 토큰 (2주 유효)
  - `"NID_SES"`: 세션 식별자 (1일 유효)
  - `"IV"`: 세션 UUID

**동작:**
1. SharedPreferences XML 파일 읽기
2. XML 파싱하여 쿠키 값 추출
3. 디코딩 및 정리

**사용 예제:**
```python
cookies = await cookie_mgr.extract_naver_cookies()
print(f"NNB: {cookies.get('NNB')}")
print(f"NID_AUT: {cookies.get('NID_AUT')}")
```

---

##### async validate_cookies(cookies: Dict[str, str]) -> Dict[str, bool]

**목적:** 추출한 쿠키의 유효성 검증

**파라미터:**
- `cookies: Dict[str, str]` - 쿠키 딕셔너리

**반환:**
- `Dict[str, bool]` - 쿠키별 유효성
  - `"NNB": bool`
  - `"NID_AUT": bool`  
  - `"NID_SES": bool`

**검증 조건:**
- 쿠키 값이 존재하는가
- 길이가 적절한가 (NNB: 16자, NID_AUT: 64자+)
- 형식이 올바른가

**사용 예제:**
```python
cookies = await cookie_mgr.extract_naver_cookies()
validation = await cookie_mgr.validate_cookies(cookies)

if validation["NID_AUT"]:
    print("✓ 로그인 상태 유효")
else:
    print("✗ 재로그인 필요")
```

---

### 1.5 device_identity.py

#### DeviceIdentityManager Class

디바이스 하드웨어 ID와 GPS 위치를 제어합니다.

**초기화:**
```python
from app.core.soul_swap.identity import DeviceIdentityManager

identity_mgr = DeviceIdentityManager()
```

#### Methods

##### async apply_identity(device_config: Dict) -> None

**목적:** Phase 2 - 디바이스 identity 적용 (ANDROID_ID + GPS)

**파라미터:**
- `device_config: Dict` - 디바이스 설정 딕셔너리
  - `android_id: str` - 16자리 hex 문자열 (예: "1234567890abcdef")
  - `location: Dict` - 위치 정보
    - `lat: float` - 위도
    - `lng: float` - 경도
    - `accuracy: float` - 정확도 (미터)
    - `altitude: float` - 고도 (미터)

**동작:**
1. ANDROID_ID 변경 (`settings put secure android_id`)
2. GPS 위치 설정 (FakeGPS broadcast)

**사용 예제:**
```python
device_config = {
    "android_id": "1a2b3c4d5e6f7890",
    "location": {
        "lat": 37.4979,
        "lng": 127.0276,
        "accuracy": 10.0,
        "altitude": 50.0
    }
}

await identity_mgr.apply_identity(device_config)
print("✓ 디바이스 identity 적용 완료")
```

---

##### async set_android_id(android_id: str) -> None

**목적:** ANDROID_ID 변경

**파라미터:**
- `android_id: str` - 16자리 hex 문자열

**동작:**
- `settings put secure android_id {value}` 실행
- 시스템 재부팅 없이 즉시 적용

**예외:**
- `ValueError` - android_id 형식이 잘못됨 (16자리 hex 아님)

**사용 예제:**
```python
new_id = "fedcba0987654321"
await identity_mgr.set_android_id(new_id)

# 확인
current_id = await identity_mgr.get_android_id()
assert current_id == new_id
```

---

##### async set_gps_location(lat: float, lng: float, accuracy: float = 10.0, altitude: float = 0.0) -> None

**목적:** GPS 위치 설정 (FakeGPS 앱 필요)

**파라미터:**
- `lat: float` - 위도 (-90 ~ 90)
- `lng: float` - 경도 (-180 ~ 180)
- `accuracy: float` - 정확도 (기본값: 10.0 미터)
- `altitude: float` - 고도 (기본값: 0.0 미터)

**동작:**
- FakeGPS 앱에 broadcast 전송
- `am broadcast -a com.droidrun.fakegps.SET_LOCATION`

**사용 예제:**
```python
# 강남역 좌표
await identity_mgr.set_gps_location(
    lat=37.4979,
    lng=127.0276,
    accuracy=5.0
)
```

---

##### async get_current_location() -> Dict

**목적:** 현재 GPS 위치 조회

**반환:**
- `Dict` - 현재 위치 정보
  - `lat: float`
  - `lng: float`
  - `accuracy: float`
  - `provider: str` - "gps" 또는 "network"

**사용 예제:**
```python
location = await identity_mgr.get_current_location()
print(f"현재 위치: {location['lat']}, {location['lng']}")
```

---

## 2. ADB Module

**위치:** `/home/tlswkehd/projects/careon-hub/backend/app/core/adb/`

**목적:** 인간 행동 시뮬레이션을 포함한 ADB 디바이스 제어

### 2.1 모듈 구조

```
adb/
├── device_tools/
│   ├── __init__.py
│   ├── adb_enhanced.py         # 핵심 ADB 제어
│   └── behavior_injector.py    # 인간 행동 생성
└── session_manager/
    ├── __init__.py
    ├── device_session_manager.py   # 세션 관리, IP 로테이션
    └── engagement_simulator.py     # 블로그 방문 시뮬레이션
```

### 2.2 adb_enhanced.py

#### EnhancedAdbTools Class

**목적:** 인간 행동 시뮬레이션 기능을 포함한 ADB 인터페이스

**초기화:**
```python
from app.core.adb.device_tools import EnhancedAdbTools, AdbConfig

config = AdbConfig(
    serial="R3CW60BHSAT",  # 디바이스 시리얼 (None이면 자동 감지)
    action_interval_min_ms=300,  # 액션 간 최소 딜레이
    action_interval_max_ms=800,  # 액션 간 최대 딜레이
    screen_width=1080,
    screen_height=2400
)

tools = EnhancedAdbTools(config)
await tools.connect()
```

**Factory Functions:**
```python
# 추천: 스텔스 모드 (자연스러운 인간 행동)
tools = create_stealth_tools(serial=None)

# 빠른 모드 (짧은 딜레이, 여전히 인간처럼)
tools = create_fast_tools(serial=None)
```

#### Connection Methods

##### async connect(serial: Optional[str] = None) -> bool

**목적:** ADB 디바이스 연결

**파라미터:**
- `serial: Optional[str]` - 디바이스 시리얼 (None이면 자동 감지)

**반환:**
- `bool` - 연결 성공 여부

**사용 예제:**
```python
success = await tools.connect("R3CW60BHSAT")
if success:
    print("✓ 디바이스 연결 성공")
```

---

#### Tap & Click Methods

##### async tap(x: int, y: int, duration_ms: int = 100) -> ActionResult

**목적:** 화면 특정 좌표 탭 (인간처럼 jitter 포함)

**파라미터:**
- `x: int` - X 좌표 (픽셀)
- `y: int` - Y 좌표 (픽셀)
- `duration_ms: int` - 탭 지속 시간 (기본값: 100ms)

**반환:**
- `ActionResult` - 실행 결과
  - `success: bool`
  - `message: str`
  - `action_type: str` = "tap"
  - `duration_ms: int`
  - `details: Dict`

**특징:**
- ±15px jitter 자동 적용 (인간 손가락 부정확성 시뮬레이션)
- Bezier curve 기반 압력 변화 (시작 0.3 → 피크 1.0 → 끝 0.2)

**사용 예제:**
```python
# 검색창 클릭
result = await tools.tap(x=540, y=200, duration_ms=120)
if result.success:
    print(f"✓ Tap 성공: {result.duration_ms}ms 소요")
```

---

##### async tap_by_index(index: int) -> ActionResult

**목적:** UI 계층에서 n번째 clickable 요소 탭

**파라미터:**
- `index: int` - 요소 인덱스 (0부터 시작)

**동작:**
1. UI 계층 덤프
2. clickable 요소 추출
3. index번째 요소의 중심 좌표 계산
4. tap() 호출

**사용 예제:**
```python
# 첫 번째 검색 결과 클릭
result = await tools.tap_by_index(0)
```

---

#### Swipe Methods

##### async swipe(start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 500, use_curved_path: bool = True) -> ActionResult

**목적:** 화면 스와이프 (곡선 경로 + 손떨림 시뮬레이션)

**파라미터:**
- `start_x, start_y: int` - 시작 좌표
- `end_x, end_y: int` - 끝 좌표
- `duration_ms: int` - 스와이프 지속 시간
- `use_curved_path: bool` - 곡선 경로 사용 여부 (기본값: True)

**동작:**
- Bezier curve로 자연스러운 경로 생성
- Perlin noise로 손떨림 추가
- motionevent DOWN → MOVE(여러 포인트) → UP 시뮬레이션

**사용 예제:**
```python
# 위로 스크롤
result = await tools.swipe(
    start_x=540, start_y=1500,
    end_x=540, end_y=500,
    duration_ms=600,
    use_curved_path=True
)
```

---

##### async scroll_down(distance: int = 500) -> ActionResult

**목적:** 아래로 스크롤

**파라미터:**
- `distance: int` - 스크롤 거리 (픽셀, 기본값: 500)

**사용 예제:**
```python
await tools.scroll_down(distance=800)
```

##### async scroll_up(distance: int = 500) -> ActionResult

**목적:** 위로 스크롤

---

#### Text Input Methods

##### async input_text(text: str, clear: bool = True) -> ActionResult

**목적:** 텍스트 입력 (인간 타이핑 시뮬레이션)

**파라미터:**
- `text: str` - 입력할 텍스트
- `clear: bool` - 입력 전 기존 텍스트 삭제 (기본값: True)

**특징:**
- 글자당 50~500ms 랜덤 딜레이
- 8% 확률로 오타 + 백스페이스 수정
- 단어 사이에 150ms 추가 딜레이
- QWERTY 키보드 인접 키 오타 시뮬레이션

**사용 예제:**
```python
await tools.input_text("CCTV 설치 비용", clear=True)
# 실제 입력: "CCTV 설{backspace}설치 비용"
```

---

#### App Control Methods

##### async start_app(package: str, activity: str) -> ActionResult

**목적:** 앱 실행

**파라미터:**
- `package: str` - 패키지명
- `activity: str` - 액티비티명

**사용 예제:**
```python
await tools.start_app(
    package="com.nhn.android.search",
    activity=".activity.MainActivity"
)
```

##### async stop_app(package: str) -> ActionResult

**목적:** 앱 강제 종료

##### async open_url(url: str, package: str = "com.android.chrome") -> ActionResult

**목적:** 브라우저로 URL 열기

**사용 예제:**
```python
await tools.open_url("https://blog.naver.com/post/12345")
```

---

#### Utility Methods

##### async take_screenshot() -> bytes

**목적:** 스크린샷 캡처

**반환:**
- `bytes` - PNG 이미지 데이터

**사용 예제:**
```python
screenshot_data = await tools.take_screenshot()
with open("screenshot.png", "wb") as f:
    f.write(screenshot_data)
```

##### async get_ui_hierarchy() -> str

**목적:** UI 계층 XML 덤프

**반환:**
- `str` - UI 계층 XML 문자열

---

### 2.3 behavior_injector.py

#### BehaviorInjector Class

**목적:** 인간 행동 패턴 생성 (Bezier curve, 오타, 스크롤 패턴)

**초기화:**
```python
from app.core.adb.device_tools import BehaviorInjector, BehaviorConfig

config = BehaviorConfig(
    typing_delay_ms=(50, 500),
    typing_error_rate=0.08,
    tap_offset_px=15,
    scroll_pause_probability=0.15
)

injector = BehaviorInjector(config)
```

**Factory Functions:**
```python
injector = create_stealth_injector()  # 권장
injector = create_fast_injector()     # 빠른 테스트용
```

#### Methods

##### generate_bezier_curve(start: Tuple, end: Tuple, control_point_count: int, sample_count: int) -> List[TouchPoint]

**목적:** Bezier curve 경로 생성

**반환:**
- `List[TouchPoint]` - 터치 포인트 리스트
  - `x, y: int` - 좌표
  - `pressure: float` - 압력 (0.0~1.0)
  - `timestamp: float` - 정규화된 타임스탬프 (0.0~1.0)

**사용 예제:**
```python
path = injector.generate_bezier_curve(
    start=(100, 100),
    end=(500, 500),
    control_point_count=2,
    sample_count=15
)

for point in path:
    # motionevent로 전송
    print(f"({point.x}, {point.y}) - pressure: {point.pressure}")
```

---

##### generate_human_typing(text: str, error_rate: float) -> List[TypingEvent]

**목적:** 인간 타이핑 이벤트 생성 (오타 포함)

**반환:**
- `List[TypingEvent]` - 타이핑 이벤트 리스트
  - `char: str` - 입력할 문자
  - `delay_ms: int` - 이전 문자 후 딜레이
  - `is_correction: bool` - 백스페이스 수정 여부

**사용 예제:**
```python
events = injector.generate_human_typing("hello", error_rate=0.1)

for event in events:
    if event.is_correction:
        await tools.press_key("KEYCODE_DEL")
    else:
        await tools.input_text(event.char, clear=False)
    await asyncio.sleep(event.delay_ms / 1000)
```

---

## 3. Traffic Module

**위치:** `/home/tlswkehd/projects/careon-hub/backend/app/core/traffic/`

**목적:** 통합 트래픽 세션 워크플로우 오케스트레이션

### 3.1 모듈 구조

```
traffic/
└── pipeline/
    └── __init__.py     # NaverSessionPipeline 클래스
```

### 3.2 NaverSessionPipeline Class

**목적:** Naver 검색 → 블로그 진입 → 콘텐츠 읽기 전체 플로우 자동화

**초기화:**
```python
from app.core.traffic.pipeline import NaverSessionPipeline, PipelineConfig

config = PipelineConfig(
    device_serial="R3CW60BHSAT",
    screen_width=1080,
    screen_height=2400,
    max_pageviews_per_session=5,
    cooldown_minutes=30,
    dwell_time_base_min_sec=90,
    dwell_time_base_max_sec=180,
    scroll_count_range=(4, 10),
    use_portal=True
)

pipeline = NaverSessionPipeline(config)
```

#### Methods

##### async run_campaign_workflow(keyword: str, target_blog_title: str, target_blogger: str, target_date: str, target_url: str, persona_id: Optional[str] = None) -> SessionResult

**목적:** 실제 사용자처럼 Naver 검색 → 블로그 탭 클릭 → 특정 포스트 찾기 → 읽기 전체 플로우

**파라미터:**
- `keyword: str` - 검색 키워드
- `target_blog_title: str` - 타겟 블로그 포스트 제목
- `target_blogger: str` - 블로거 닉네임
- `target_date: str` - 포스트 날짜
- `target_url: str` - 타겟 URL
- `persona_id: Optional[str]` - 페르소나 ID

**반환:**
- `SessionResult` - 세션 실행 결과
  - `persona_id: str`
  - `persona_name: str`
  - `visits: List[VisitResult]`
  - `total_dwell_time: int` - 총 체류 시간 (초)
  - `total_scrolls: int` - 총 스크롤 횟수
  - `duration_sec: int` - 세션 전체 소요 시간

**워크플로우:**
1. Naver 앱 실행
2. 검색창에 키워드 입력
3. 검색 결과 스크롤
4. "블로그" 탭 클릭 (Portal 사용)
5. 타겟 포스트 찾기 (제목, 블로거, 날짜 매칭)
6. 포스트 클릭 → 진입
7. 3단계 읽기 (아래로 → 위로 → 다시 아래로)
8. 공유 버튼 클릭 → URL 복사

**사용 예제:**
```python
result = await pipeline.run_campaign_workflow(
    keyword="CCTV 설치",
    target_blog_title="초보자도 쉽게! CCTV 설치 가이드",
    target_blogger="보안전문가",
    target_date="2026.01.15",
    target_url="https://blog.naver.com/user/12345",
    persona_id="persona_001"
)

print(f"✓ 세션 완료: {result.total_dwell_time}초 체류, {result.total_scrolls}회 스크롤")
```

---

##### async visit_url(url: str) -> VisitResult

**목적:** URL 직접 방문 + 읽기 시뮬레이션

**파라미터:**
- `url: str` - 방문할 URL

**반환:**
- `VisitResult` - 방문 결과
  - `success: bool`
  - `url: str`
  - `domain: str`
  - `dwell_time: int` - 체류 시간 (초)
  - `scroll_count: int` - 스크롤 횟수
  - `scroll_depth: float` - 스크롤 깊이 (0.0~1.0)
  - `actions: List[str]` - 수행한 액션 리스트

**사용 예제:**
```python
result = await pipeline.visit_url("https://blog.naver.com/post/12345")
print(f"방문 완료: {result.dwell_time}초 체류, 스크롤 깊이 {result.scroll_depth:.1%}")
```

---

## 4. Portal Module

**위치:** `/home/tlswkehd/projects/careon-hub/backend/app/core/portal/`

**목적:** DroidRun Portal APK를 통한 정확한 UI 요소 탐지

### 4.1 모듈 구조

```
portal/
└── portal_client/
    ├── __init__.py
    ├── client.py       # PortalClient
    ├── element.py      # UIElement, Bounds
    └── finder.py       # ElementFinder
```

### 4.2 PortalClient Class

**초기화:**
```python
from app.core.portal.portal_client import PortalClient, PortalConfig

config = PortalConfig(
    device_serial="R3CW60BHSAT",
    timeout_sec=10,
    retry_count=3,
    cache_ttl_sec=0.5
)

portal = PortalClient(config)
```

#### Methods

##### async get_ui_tree() -> UITree

**목적:** 현재 화면의 UI 계층 트리 조회

**반환:**
- `UITree` - UI 계층 트리 객체

**사용 예제:**
```python
tree = await portal.get_ui_tree()

# 클릭 가능한 요소 찾기
clickable = tree.clickable_elements
print(f"{len(clickable)}개 클릭 가능 요소 발견")
```

---

##### async find_by_text(text: str, exact: bool = False) -> Optional[UIElement]

**목적:** 텍스트로 UI 요소 찾기

**파라미터:**
- `text: str` - 검색할 텍스트
- `exact: bool` - 정확히 일치 여부 (기본값: False, 부분 일치)

**반환:**
- `Optional[UIElement]` - 찾은 요소 (없으면 None)

**사용 예제:**
```python
# "검색" 버튼 찾기
search_btn = await portal.find_by_text("검색", exact=False)
if search_btn:
    x, y = search_btn.center
    await tools.tap(x, y)
```

---

### 4.3 UIElement Class

**필드:**
- `resource_id: str` - Android 리소스 ID
- `text: str` - 표시 텍스트
- `clickable: bool` - 클릭 가능 여부
- `enabled: bool` - 활성화 여부
- `bounds: Bounds` - 화면 좌표 범위
- `children: List[UIElement]` - 자식 요소

**속성:**
- `center: Tuple[int, int]` - 중심 좌표 (x, y)

**사용 예제:**
```python
element = tree.find(text_contains="블로그")
if element:
    print(f"요소: {element.text}")
    print(f"위치: {element.bounds.left}, {element.bounds.top}")
    print(f"중심: {element.center}")
```

---

### 4.4 ElementFinder Class

고수준 요소 검색 헬퍼입니다.

**초기화:**
```python
from app.core.portal.portal_client import ElementFinder

finder = ElementFinder(portal_client)
```

#### Methods

##### async find_search_box() -> Optional[UIElement]

**목적:** 검색 입력창 찾기

##### async find_blog_item_by_title(title: str) -> Optional[UIElement]

**목적:** 블로그 검색 결과에서 제목으로 포스트 찾기

**사용 예제:**
```python
post = await finder.find_blog_item_by_title("CCTV 설치 가이드")
if post:
    x, y = post.center
    await tools.tap(x, y)
```

---

## 5. Integration Guide

### 5.1 모듈 간 통합 예제

#### 전체 Soul Swap + Traffic 워크플로우

```python
from app.core.soul_swap.soul import SoulManager, NAVER_APP
from app.core.soul_swap.identity import DeviceIdentityManager
from app.core.adb.device_tools import create_stealth_tools
from app.core.traffic.pipeline import NaverSessionPipeline

# 1. 초기화
soul_mgr = SoulManager()
identity_mgr = DeviceIdentityManager()
tools = create_stealth_tools()
pipeline = NaverSessionPipeline(...)

# 2. Phase 1: Cleanup
await soul_mgr.cleanup(NAVER_APP)

# 3. Phase 2: Identity Masking
device_config = {
    "android_id": "fedcba9876543210",
    "location": {"lat": 37.4979, "lng": 127.0276, "accuracy": 10.0}
}
await identity_mgr.apply_identity(device_config)

# 4. Phase 3: Restore
soul_file = "/sdcard/personas/persona_001/naver_v3.tar.gz"
await soul_mgr.restore("persona_001", soul_file, NAVER_APP)

# 5. Phase 4: Launch & Execute
await soul_mgr.launch_app(NAVER_APP)
await asyncio.sleep(5)

result = await pipeline.run_campaign_workflow(
    keyword="CCTV 설치",
    target_blog_title="...",
    target_blogger="...",
    target_date="2026.01.15",
    target_url="https://...",
    persona_id="persona_001"
)

# 6. Phase 5: Backup
backup_file = await soul_mgr.backup("persona_001", NAVER_APP)
print(f"✓ 백업 완료: {backup_file}")
```

---

### 5.2 Import 경로 변경 가이드

기존 import 경로를 CareOn Hub 경로로 변경:

**Before (persona-manager):**
```python
from src.soul.manager import SoulManager
from src.identity.device_identity import DeviceIdentityManager
```

**After (CareOn Hub):**
```python
from app.core.soul_swap.soul.soul_manager import SoulManager
from app.core.soul_swap.identity.device_identity import DeviceIdentityManager
```

**Before (ai-project):**
```python
from src.shared.device_tools.adb_enhanced import EnhancedAdbTools
from src.shared.pipeline import NaverSessionPipeline
from src.shared.portal_client import PortalClient
```

**After (CareOn Hub):**
```python
from app.core.adb.device_tools.adb_enhanced import EnhancedAdbTools
from app.core.traffic.pipeline import NaverSessionPipeline
from app.core.portal.portal_client.client import PortalClient
```

---

### 5.3 환경변수 요구사항

모든 모듈이 필요로 하는 환경변수:

```bash
# Supabase
SUPABASE_URL=https://pkehcfbjotctvneordob.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

# API
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=careon-hub-2026

# DeepSeek (선택, blog-writer 통합 시)
DEEPSEEK_API_KEY=sk-...
```

---

### 5.4 의존성 요구사항

모든 모듈이 의존하는 Python 패키지:

```txt
# requirements.txt (이미 설치됨)
adbutils>=1.2.0
aiohttp>=3.9.0
asyncio
subprocess (built-in)
xml.etree.ElementTree (built-in)
```

---

## 부록

### A. 데이터 클래스 정의

#### ActionResult
```python
@dataclass
class ActionResult:
    success: bool
    message: str
    action_type: str  # "tap", "swipe", "input", etc.
    duration_ms: int
    details: Dict[str, Any]
```

#### SessionResult
```python
@dataclass
class SessionResult:
    persona_id: str
    persona_name: str
    visits: List[VisitResult]
    total_dwell_time: int
    total_scrolls: int
    duration_sec: int
```

#### VisitResult
```python
@dataclass
class VisitResult:
    success: bool
    url: str
    domain: str
    dwell_time: int
    scroll_count: int
    scroll_depth: float
    actions: List[str]
```

---

*마지막 업데이트: 2026-01-16*  
*참조: Explore Agent a8263a2 분석 결과*
