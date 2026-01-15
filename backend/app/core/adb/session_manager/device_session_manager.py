"""
DeviceSessionManager - 세션 리셋 및 IP 회전 관리자

핑거프린트 실험 결과 기반 구현:
- IP 변경: 비행기 모드 토글
- 쿠키 삭제: pm clear로 Chrome 데이터 초기화
- 세션 쿨다운: 30분 이상 대기

Author: Naver AI Evolution System
Created: 2025-12-15
"""

import asyncio
import subprocess
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger("naver_evolution.session_manager")


# =============================================================================
# Data Classes & Enums
# =============================================================================

class SessionState(Enum):
    """세션 상태"""
    IDLE = "idle"                    # 대기 중
    ACTIVE = "active"                # 활성 세션
    COOLING_DOWN = "cooling_down"    # 쿨다운 중
    RESETTING = "resetting"          # 리셋 중
    ERROR = "error"                  # 오류 상태


@dataclass
class SessionConfig:
    """세션 관리 설정"""
    # 디바이스 설정
    device_serial: Optional[str] = None

    # 브라우저 설정
    browser_package: str = "com.android.chrome"

    # 세션 제한
    max_pageviews_per_session: int = 5
    dwell_time_min_sec: int = 120      # 최소 체류시간 (2분)
    dwell_time_max_sec: int = 180      # 최대 체류시간 (3분)

    # 쿨다운 설정
    cooldown_minutes: int = 30

    # IP 회전 설정
    airplane_mode_wait_sec: int = 5     # 비행기 모드 대기 시간
    ip_change_verify: bool = True       # IP 변경 확인 여부

    # 타임아웃
    command_timeout_sec: int = 30


@dataclass
class SessionResetResult:
    """세션 리셋 결과"""
    success: bool
    old_ip: Optional[str] = None
    new_ip: Optional[str] = None
    ip_changed: bool = False
    cookies_cleared: bool = False
    duration_sec: float = 0.0
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SessionInfo:
    """현재 세션 정보"""
    session_id: str
    state: SessionState
    start_time: datetime
    pageview_count: int = 0
    last_activity: Optional[datetime] = None
    current_ip: Optional[str] = None


# =============================================================================
# DeviceSessionManager Class
# =============================================================================

class DeviceSessionManager:
    """
    디바이스 세션 관리자

    핑거프린트 실험 결과 기반:
    - NNB 쿠키 삭제로 새 사용자 생성
    - 비행기 모드로 IP 변경
    - 30분 쿨다운으로 재방문 제한 회피

    사용 예시:
        manager = DeviceSessionManager()

        # 새 세션 시작 (IP 변경 + 쿠키 삭제)
        result = await manager.create_new_identity()

        # 세션 활동
        await manager.record_pageview()

        # 쿨다운 대기
        await manager.wait_cooldown()
    """

    def __init__(self, config: SessionConfig = None):
        self.config = config or SessionConfig()
        self.current_session: Optional[SessionInfo] = None
        self.session_history: List[SessionInfo] = []
        self._session_counter = 0

    # =========================================================================
    # ADB 명령 실행
    # =========================================================================

    def _run_adb(self, *args, timeout: int = None) -> str:
        """ADB 명령 실행"""
        cmd = ["adb"]
        if self.config.device_serial:
            cmd.extend(["-s", self.config.device_serial])
        cmd.extend(args)

        timeout = timeout or self.config.command_timeout_sec

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode != 0:
                logger.warning(f"ADB command failed: {result.stderr}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"ADB command timed out: {' '.join(cmd)}")
            return ""
        except Exception as e:
            logger.error(f"ADB command error: {e}")
            return ""

    # =========================================================================
    # IP 관리
    # =========================================================================

    async def get_current_ip(self) -> Optional[str]:
        """현재 IP 주소 확인"""
        # 방법 1: curl 사용
        result = self._run_adb("shell", "curl", "-s", "ifconfig.me", timeout=10)
        if result and "." in result:
            return result.strip()

        # 방법 2: 네트워크 인터페이스 확인
        result = self._run_adb("shell", "ip", "addr", "show", "rmnet0")
        if result:
            # inet 라인에서 IP 추출
            for line in result.split("\n"):
                if "inet " in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        ip = parts[1].split("/")[0]
                        return ip

        return None

    async def toggle_airplane_mode(self, enable: bool) -> bool:
        """
        비행기 모드 토글

        참고: Android 16+에서는 브로드캐스트 권한이 제한됨
        대안으로 cmd connectivity 사용
        """
        mode = "1" if enable else "0"

        # 비행기 모드 설정
        self._run_adb("shell", "settings", "put", "global", "airplane_mode_on", mode)

        # 방법 1: cmd connectivity (Android 11+)
        if enable:
            self._run_adb("shell", "cmd", "connectivity", "airplane-mode", "enable")
        else:
            self._run_adb("shell", "cmd", "connectivity", "airplane-mode", "disable")

        # 상태 확인
        await asyncio.sleep(1)
        result = self._run_adb("shell", "settings", "get", "global", "airplane_mode_on")

        return result.strip() == mode

    async def toggle_mobile_data(self, enable: bool) -> bool:
        """모바일 데이터 토글 (IP 변경 대안)"""
        if enable:
            self._run_adb("shell", "svc", "data", "enable")
        else:
            self._run_adb("shell", "svc", "data", "disable")

        await asyncio.sleep(2)
        return True

    async def rotate_ip(self) -> tuple[bool, Optional[str], Optional[str]]:
        """
        IP 회전

        방법 1: 비행기 모드 (권한 있으면)
        방법 2: 모바일 데이터 OFF/ON

        Returns:
            (성공여부, 이전IP, 새IP)
        """
        old_ip = await self.get_current_ip()
        logger.info(f"Current IP: {old_ip}")

        # 방법 1: 비행기 모드 시도
        logger.info("Trying airplane mode...")
        airplane_success = await self.toggle_airplane_mode(True)
        await asyncio.sleep(self.config.airplane_mode_wait_sec)
        await self.toggle_airplane_mode(False)

        # 비행기 모드 실패시 모바일 데이터 토글
        if not airplane_success:
            logger.info("Airplane mode failed, trying mobile data toggle...")
            await self.toggle_mobile_data(False)
            await asyncio.sleep(3)
            await self.toggle_mobile_data(True)

        # 네트워크 연결 대기
        await asyncio.sleep(10)

        # 새 IP 확인
        new_ip = await self.get_current_ip()
        logger.info(f"New IP: {new_ip}")

        ip_changed = old_ip != new_ip and new_ip is not None

        return ip_changed, old_ip, new_ip

    # =========================================================================
    # 쿠키/데이터 관리
    # =========================================================================

    async def clear_browser_data(self) -> bool:
        """브라우저 데이터 전체 삭제 (쿠키, 캐시, 로컬 스토리지)"""
        package = self.config.browser_package

        logger.info(f"Clearing browser data: {package}")

        # pm clear로 앱 데이터 전체 삭제
        result = self._run_adb("shell", "pm", "clear", package)

        success = "Success" in result
        if success:
            logger.info("Browser data cleared successfully")
        else:
            logger.warning(f"Failed to clear browser data: {result}")

        return success

    async def clear_specific_data(self) -> bool:
        """특정 데이터만 삭제 (쿠키, 로컬 스토리지)"""
        package = self.config.browser_package

        # Chrome 캐시/쿠키 경로
        paths = [
            f"/data/data/{package}/app_chrome/Default/Cookies",
            f"/data/data/{package}/app_chrome/Default/Local Storage",
            f"/data/data/{package}/cache",
        ]

        for path in paths:
            self._run_adb("shell", "rm", "-rf", path)

        return True

    # =========================================================================
    # 세션 관리
    # =========================================================================

    async def create_new_identity(self) -> SessionResetResult:
        """
        새로운 사용자 ID 생성

        1. 비행기 모드로 IP 변경
        2. Chrome 데이터 삭제로 NNB 쿠키 초기화

        Returns:
            SessionResetResult
        """
        start_time = time.time()

        if self.current_session:
            self.current_session.state = SessionState.RESETTING

        try:
            # 1. IP 회전
            ip_changed, old_ip, new_ip = await self.rotate_ip()

            if self.config.ip_change_verify and not ip_changed:
                logger.warning("IP did not change, but continuing...")

            # 2. 브라우저 데이터 삭제
            cookies_cleared = await self.clear_browser_data()

            # 3. 새 세션 생성
            self._session_counter += 1
            session_id = f"session_{self._session_counter}_{int(time.time())}"

            self.current_session = SessionInfo(
                session_id=session_id,
                state=SessionState.ACTIVE,
                start_time=datetime.now(),
                current_ip=new_ip
            )

            duration = time.time() - start_time

            return SessionResetResult(
                success=True,
                old_ip=old_ip,
                new_ip=new_ip,
                ip_changed=ip_changed,
                cookies_cleared=cookies_cleared,
                duration_sec=duration
            )

        except Exception as e:
            logger.error(f"Failed to create new identity: {e}")
            if self.current_session:
                self.current_session.state = SessionState.ERROR

            return SessionResetResult(
                success=False,
                error_message=str(e),
                duration_sec=time.time() - start_time
            )

    async def record_pageview(self) -> bool:
        """페이지뷰 기록"""
        if not self.current_session:
            logger.warning("No active session")
            return False

        self.current_session.pageview_count += 1
        self.current_session.last_activity = datetime.now()

        # 최대 페이지뷰 초과 확인
        if self.current_session.pageview_count >= self.config.max_pageviews_per_session:
            logger.info(f"Max pageviews reached: {self.current_session.pageview_count}")
            self.current_session.state = SessionState.COOLING_DOWN
            return False

        return True

    async def wait_cooldown(self, minutes: int = None) -> None:
        """쿨다운 대기"""
        minutes = minutes or self.config.cooldown_minutes

        if self.current_session:
            self.current_session.state = SessionState.COOLING_DOWN

        logger.info(f"Waiting cooldown: {minutes} minutes")

        # 1분 단위로 로그 출력
        for i in range(minutes):
            await asyncio.sleep(60)
            remaining = minutes - i - 1
            if remaining > 0 and remaining % 5 == 0:
                logger.info(f"Cooldown remaining: {remaining} minutes")

        if self.current_session:
            self.session_history.append(self.current_session)
            self.current_session = None

    def get_session_stats(self) -> Dict[str, Any]:
        """세션 통계"""
        total_sessions = len(self.session_history)
        total_pageviews = sum(s.pageview_count for s in self.session_history)

        if self.current_session:
            total_sessions += 1
            total_pageviews += self.current_session.pageview_count

        return {
            "total_sessions": total_sessions,
            "total_pageviews": total_pageviews,
            "current_session": self.current_session.session_id if self.current_session else None,
            "current_state": self.current_session.state.value if self.current_session else "idle",
        }

    # =========================================================================
    # 디바이스 상태 확인
    # =========================================================================

    async def check_device_connected(self) -> bool:
        """디바이스 연결 확인"""
        result = self._run_adb("devices")
        lines = result.strip().split("\n")[1:]

        for line in lines:
            if "device" in line and "unauthorized" not in line:
                if self.config.device_serial:
                    if self.config.device_serial in line:
                        return True
                else:
                    return True

        return False

    async def get_network_type(self) -> str:
        """현재 네트워크 타입 확인 (LTE/5G/WiFi)"""
        # 모바일 데이터 상태
        result = self._run_adb("shell", "settings", "get", "global", "mobile_data")
        mobile_data = result.strip() == "1"

        # WiFi 상태
        result = self._run_adb("shell", "settings", "get", "global", "wifi_on")
        wifi_on = result.strip() == "1"

        if wifi_on:
            return "WiFi"
        elif mobile_data:
            # 상세 네트워크 타입 확인
            result = self._run_adb("shell", "getprop", "gsm.network.type")
            return result.strip() or "Mobile"
        else:
            return "Disconnected"

    async def ensure_mobile_data(self) -> bool:
        """모바일 데이터 사용 확인 (WiFi 끄기)"""
        # WiFi 끄기
        self._run_adb("shell", "svc", "wifi", "disable")
        await asyncio.sleep(2)

        # 모바일 데이터 켜기
        self._run_adb("shell", "svc", "data", "enable")
        await asyncio.sleep(2)

        network_type = await self.get_network_type()
        return network_type != "WiFi" and network_type != "Disconnected"


# =============================================================================
# Quick Session Reset (동기 버전)
# =============================================================================

def quick_session_reset(device_serial: str = None) -> SessionResetResult:
    """
    빠른 세션 리셋 (동기 함수)

    사용 예시:
        result = quick_session_reset()
        if result.success:
            print(f"New IP: {result.new_ip}")
    """
    import asyncio

    manager = DeviceSessionManager(SessionConfig(device_serial=device_serial))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(manager.create_new_identity())
        return result
    finally:
        loop.close()
