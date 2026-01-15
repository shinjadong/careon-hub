"""
PortalClient - DroidRun Portal Content Provider 클라이언트

DroidRun Portal APK의 Content Provider를 통해 UI 트리를 획득합니다.

Content Provider URIs:
- content://com.droidrun.portal/version - 버전 확인
- content://com.droidrun.portal/state - UI 상태 (트리)

테스트 결과 (Galaxy Tab S9+):
- adb shell "content query --uri content://com.droidrun.portal/version"
- 결과: {"status":"success","data":"0.4.7"}

Author: Naver AI Evolution System
Created: 2025-12-15
"""

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

from .element import UIElement, UITree, Bounds

logger = logging.getLogger("naver_evolution.portal_client")


# Portal Content Provider URI
PORTAL_PACKAGE = "com.droidrun.portal"
PORTAL_AUTHORITY = "com.droidrun.portal"
PORTAL_ACCESSIBILITY_SERVICE = f"{PORTAL_PACKAGE}/{PORTAL_PACKAGE}.service.DroidrunAccessibilityService"


@dataclass
class PortalConfig:
    """Portal 클라이언트 설정"""
    device_serial: Optional[str] = None
    timeout_sec: int = 10
    retry_count: int = 3
    cache_ttl_sec: float = 0.5  # UI 캐시 유효 시간


@dataclass
class PortalResponse:
    """Portal 응답"""
    success: bool
    status: str = ""
    data: Any = None
    error_message: Optional[str] = None
    raw: str = ""


class PortalClient:
    """
    DroidRun Portal Content Provider 클라이언트

    Portal APK와 통신하여 정확한 UI 트리를 획득합니다.

    사용 예시:
        client = PortalClient()

        # Portal 상태 확인
        if await client.is_running():
            # UI 트리 획득
            tree = await client.get_ui_tree()

            # 요소 검색
            element = tree.find(text_contains="검색")

            if element:
                # 요소 탭
                await tools.tap(*element.center)
    """

    def __init__(self, config: PortalConfig = None):
        """
        Args:
            config: Portal 클라이언트 설정
        """
        self.config = config or PortalConfig()
        self._ui_cache: Optional[UITree] = None
        self._cache_time: float = 0

    # =========================================================================
    # ADB Commands
    # =========================================================================

    def _run_adb(self, *args, timeout: int = None) -> Tuple[bool, str]:
        """ADB 명령 실행"""
        cmd = ["adb"]
        if self.config.device_serial:
            cmd.extend(["-s", self.config.device_serial])
        cmd.extend(args)

        timeout = timeout or self.config.timeout_sec

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout
            )

            output = result.stdout.strip() if result.stdout else ""
            if result.returncode != 0:
                error = result.stderr.strip() or output
                return (False, error)

            return (True, output)

        except subprocess.TimeoutExpired:
            logger.error(f"ADB command timeout: {' '.join(cmd)}")
            return (False, "Command timeout")
        except Exception as e:
            logger.error(f"ADB command error: {e}")
            return (False, str(e))

    def _query_content_provider(self, path: str) -> PortalResponse:
        """
        Content Provider 쿼리

        Args:
            path: URI 경로 (예: "/version", "/state")

        Returns:
            PortalResponse
        """
        uri = f"content://{PORTAL_AUTHORITY}{path}"

        success, output = self._run_adb(
            "shell", "content", "query", "--uri", uri
        )

        if not success:
            return PortalResponse(
                success=False,
                error_message=output,
                raw=output
            )

        # 응답 파싱
        try:
            # Content Provider 출력 형식 처리
            # Row: 0 _data={"status":"success",...}
            if "result=" in output or "_data=" in output:
                json_start = output.find('{')
                json_end = output.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = output[json_start:json_end]
                    data = json.loads(json_str)
                    inner_data = data.get("data")
                    # data가 JSON 문자열이면 추가 파싱
                    if isinstance(inner_data, str) and inner_data.startswith('{'):
                        try:
                            inner_data = json.loads(inner_data)
                        except:
                            pass
                    return PortalResponse(
                        success=data.get("status") == "success",
                        status=data.get("status", ""),
                        data=inner_data,
                        raw=output
                    )

            # 직접 JSON 형식
            if output.startswith('{'):
                data = json.loads(output)
                return PortalResponse(
                    success=data.get("status") == "success",
                    status=data.get("status", ""),
                    data=data.get("data"),
                    raw=output
                )

            return PortalResponse(
                success=True,
                data=output,
                raw=output
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Portal response: {e}")
            return PortalResponse(
                success=False,
                error_message=f"JSON parse error: {e}",
                raw=output
            )

    # =========================================================================
    # Portal Status
    # =========================================================================

    async def get_version(self) -> Optional[str]:
        """
        Portal 버전 확인

        Returns:
            버전 문자열 (예: "0.4.7") 또는 None
        """
        response = self._query_content_provider("/version")

        if response.success and response.data:
            version = str(response.data)
            logger.debug(f"Portal version: {version}")
            return version

        return None

    async def is_running(self) -> bool:
        """
        Portal이 실행 중인지 확인

        Returns:
            실행 여부
        """
        version = await self.get_version()
        return version is not None

    async def is_installed(self) -> bool:
        """
        Portal APK 설치 여부 확인

        Returns:
            설치 여부
        """
        success, output = self._run_adb(
            "shell", "pm", "list", "packages", PORTAL_PACKAGE
        )

        return success and PORTAL_PACKAGE in output

    async def is_accessibility_enabled(self) -> bool:
        """
        Portal 접근성 서비스 활성화 여부 확인

        Returns:
            활성화 여부
        """
        success, output = self._run_adb(
            "shell", "settings", "get", "secure", "enabled_accessibility_services"
        )

        if success:
            return PORTAL_ACCESSIBILITY_SERVICE in output

        return False

    # =========================================================================
    # Accessibility Service
    # =========================================================================

    async def enable_accessibility(self) -> bool:
        """
        Portal 접근성 서비스 활성화

        Returns:
            활성화 성공 여부
        """
        logger.info("Enabling Portal accessibility service...")

        # 현재 활성화된 서비스 확인
        success, current = self._run_adb(
            "shell", "settings", "get", "secure", "enabled_accessibility_services"
        )

        if PORTAL_ACCESSIBILITY_SERVICE in current:
            logger.info("Portal accessibility already enabled")
            return True

        # 서비스 추가
        if current and current != "null":
            new_value = f"{current}:{PORTAL_ACCESSIBILITY_SERVICE}"
        else:
            new_value = PORTAL_ACCESSIBILITY_SERVICE

        self._run_adb(
            "shell", "settings", "put", "secure",
            "enabled_accessibility_services", new_value
        )

        # 접근성 전체 활성화
        self._run_adb(
            "shell", "settings", "put", "secure", "accessibility_enabled", "1"
        )

        await asyncio.sleep(1)

        # 확인
        enabled = await self.is_accessibility_enabled()
        if enabled:
            logger.info("Portal accessibility enabled successfully")
        else:
            logger.warning("Failed to enable Portal accessibility")

        return enabled

    # =========================================================================
    # UI Tree
    # =========================================================================

    async def get_ui_tree(self, use_cache: bool = True) -> UITree:
        """
        UI 트리 획득

        Args:
            use_cache: 캐시 사용 여부

        Returns:
            UITree 객체
        """
        import time

        # 캐시 확인
        if use_cache and self._ui_cache:
            if time.time() - self._cache_time < self.config.cache_ttl_sec:
                return self._ui_cache

        # Portal에서 UI 상태 획득
        response = self._query_content_provider("/state")

        if not response.success:
            logger.warning(f"Failed to get UI tree: {response.error_message}")
            return UITree()

        # UI 트리 파싱
        try:
            if isinstance(response.data, dict):
                tree = UITree.from_dict(response.data)
            elif isinstance(response.data, str):
                tree = UITree.from_json(response.data)
            else:
                tree = UITree()

            # 캐시 업데이트
            self._ui_cache = tree
            self._cache_time = time.time()

            logger.debug(f"UI tree retrieved: {tree}")
            return tree

        except Exception as e:
            logger.error(f"Failed to parse UI tree: {e}")
            return UITree()

    async def get_ui_state(self) -> Dict[str, Any]:
        """
        원시 UI 상태 획득

        Returns:
            UI 상태 딕셔너리
        """
        response = self._query_content_provider("/state")

        if response.success:
            return response.data if isinstance(response.data, dict) else {}

        return {}

    def clear_cache(self):
        """UI 캐시 초기화"""
        self._ui_cache = None
        self._cache_time = 0

    # =========================================================================
    # Element Finding (Shortcuts)
    # =========================================================================

    async def find_element(self, **criteria) -> Optional[UIElement]:
        """
        조건에 맞는 요소 검색

        Args:
            **criteria: 검색 조건 (text, text_contains, resource_id, clickable 등)

        Returns:
            첫 번째 매칭 요소 또는 None
        """
        tree = await self.get_ui_tree()
        return tree.find(**criteria)

    async def find_elements(self, **criteria) -> List[UIElement]:
        """
        조건에 맞는 모든 요소 검색

        Args:
            **criteria: 검색 조건

        Returns:
            매칭되는 모든 요소 목록
        """
        tree = await self.get_ui_tree()
        return tree.find_all(**criteria)

    async def find_by_text(self, text: str, exact: bool = False) -> Optional[UIElement]:
        """텍스트로 요소 검색"""
        tree = await self.get_ui_tree()
        return tree.find_by_text(text, exact)

    async def find_clickable_elements(self) -> List[UIElement]:
        """클릭 가능한 모든 요소"""
        tree = await self.get_ui_tree()
        return tree.clickable_elements

    async def find_scrollable_containers(self) -> List[UIElement]:
        """스크롤 가능한 컨테이너"""
        tree = await self.get_ui_tree()
        return tree.get_scrollable_containers()

    # =========================================================================
    # Screenshot
    # =========================================================================

    async def get_screenshot(self) -> Optional[bytes]:
        """
        스크린샷 획득

        Portal을 통한 스크린샷 (일반 ADB 스크린샷과 동일)

        Returns:
            PNG 이미지 바이트 또는 None
        """
        cmd = ["adb"]
        if self.config.device_serial:
            cmd.extend(["-s", self.config.device_serial])
        cmd.extend(["exec-out", "screencap", "-p"])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10
            )

            if result.returncode == 0:
                return result.stdout

        except Exception as e:
            logger.error(f"Screenshot failed: {e}")

        return None

    # =========================================================================
    # Portal Management
    # =========================================================================

    async def start_portal(self) -> bool:
        """Portal 앱 시작"""
        success, _ = self._run_adb(
            "shell", "am", "start",
            "-n", f"{PORTAL_PACKAGE}/.MainActivity"
        )

        if success:
            await asyncio.sleep(2)
            return await self.is_running()

        return False

    async def stop_portal(self) -> bool:
        """Portal 앱 종료"""
        success, _ = self._run_adb(
            "shell", "am", "force-stop", PORTAL_PACKAGE
        )
        return success

    async def setup(self) -> bool:
        """
        Portal 초기 설정

        1. 설치 확인
        2. 앱 시작
        3. 접근성 활성화
        4. 동작 확인

        Returns:
            설정 성공 여부
        """
        logger.info("Setting up Portal...")

        # 1. 설치 확인
        if not await self.is_installed():
            logger.error("Portal APK not installed")
            return False

        # 2. 접근성 활성화
        if not await self.is_accessibility_enabled():
            if not await self.enable_accessibility():
                logger.error("Failed to enable accessibility")
                return False

        # 3. 앱 시작 (이미 실행 중이면 스킵)
        if not await self.is_running():
            if not await self.start_portal():
                logger.warning("Failed to start Portal, but continuing...")

        # 4. 동작 확인
        await asyncio.sleep(1)
        if await self.is_running():
            version = await self.get_version()
            logger.info(f"Portal setup complete (v{version})")
            return True

        logger.warning("Portal setup completed but may not be fully functional")
        return True

    async def get_status(self) -> Dict[str, Any]:
        """
        Portal 상태 정보

        Returns:
            상태 딕셔너리
        """
        is_installed = await self.is_installed()
        is_running = await self.is_running() if is_installed else False
        version = await self.get_version() if is_running else None
        accessibility = await self.is_accessibility_enabled() if is_installed else False

        return {
            "installed": is_installed,
            "running": is_running,
            "version": version,
            "accessibility_enabled": accessibility,
            "ready": is_running and accessibility
        }
