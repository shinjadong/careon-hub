"""
Device Identity Manager
ANDROID_ID 및 GPS 위치 변조 관리
"""

import asyncio
import subprocess
import re
from typing import Optional, Dict, Any

from ..models import DeviceConfig, Location


class DeviceIdentityManager:
    """디바이스 식별자 관리자"""

    # FakeGPS 앱 브로드캐스트 액션
    FAKEGPS_ACTION = "com.fakegps.SET_LOCATION"

    def __init__(self, device_serial: Optional[str] = None):
        """
        Args:
            device_serial: ADB 디바이스 시리얼 (None이면 기본 디바이스)
        """
        self._serial = device_serial

    async def _shell(self, command: str, timeout: int = 10) -> str:
        """ADB 쉘 명령 실행"""
        adb_cmd = ["adb"]
        if self._serial:
            adb_cmd.extend(["-s", self._serial])
        adb_cmd.extend(["shell", command])

        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                adb_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
        )
        return result.stdout.strip()

    async def apply_identity(self, device_config: DeviceConfig) -> bool:
        """
        Phase 2: 디바이스 식별자 적용 (Hardware Masking)

        Args:
            device_config: 디바이스 설정

        Returns:
            성공 여부
        """
        success = True

        # ANDROID_ID 변경 (필수)
        if device_config.android_id:
            result = await self.set_android_id(device_config.android_id)
            success = success and result

        return success

    async def apply_location(self, location: Location) -> bool:
        """
        GPS 위치 적용

        Args:
            location: 위치 정보

        Returns:
            성공 여부
        """
        return await self.set_gps_location(
            lat=location.lat,
            lng=location.lng,
            accuracy=location.accuracy,
            altitude=location.altitude
        )

    async def set_android_id(self, android_id: str) -> bool:
        """
        ANDROID_ID 변경

        Args:
            android_id: 새 ANDROID_ID (16자리 hex)

        Returns:
            성공 여부

        Note:
            루팅된 기기에서만 동작합니다.
        """
        # 유효성 검사
        if not android_id or len(android_id) != 16:
            raise ValueError(f"Invalid android_id: must be 16 hex chars, got {android_id}")

        # settings put secure android_id
        await self._shell(f"settings put secure android_id {android_id}")

        # 적용 확인
        current = await self.get_android_id()
        return current == android_id

    async def get_android_id(self) -> str:
        """현재 ANDROID_ID 조회"""
        result = await self._shell("settings get secure android_id")
        return result.strip()

    async def set_gps_location(
        self,
        lat: float,
        lng: float,
        accuracy: float = 10.0,
        altitude: float = 0.0
    ) -> bool:
        """
        GPS 위치 변조 (FakeGPS 앱 사용)

        Args:
            lat: 위도
            lng: 경도
            accuracy: 정확도 (미터)
            altitude: 고도 (미터)

        Returns:
            성공 여부

        Note:
            FakeGPS 앱이 설치되어 있어야 합니다.
            대안: Xposed/Magisk 모듈 사용
        """
        # FakeGPS 브로드캐스트
        cmd = (
            f"am broadcast -a {self.FAKEGPS_ACTION} "
            f"--ef lat {lat} "
            f"--ef lng {lng} "
            f"--ef accuracy {accuracy} "
            f"--ef altitude {altitude}"
        )

        result = await self._shell(cmd)
        return "Broadcast completed" in result

    async def get_current_location(self) -> Optional[Dict[str, float]]:
        """
        현재 GPS 위치 조회

        Returns:
            위치 정보 또는 None
        """
        # dumpsys location을 통한 위치 조회
        result = await self._shell(
            "dumpsys location | grep -A2 'last location'"
        )

        if not result:
            return None

        # 위도/경도 파싱
        lat_match = re.search(r'lat=([\d.-]+)', result)
        lng_match = re.search(r'lng=([\d.-]+)', result)

        if lat_match and lng_match:
            return {
                "lat": float(lat_match.group(1)),
                "lng": float(lng_match.group(1))
            }

        return None

    async def get_device_info(self) -> Dict[str, Any]:
        """
        현재 디바이스 정보 조회

        Returns:
            디바이스 정보
        """
        info = {}

        # ANDROID_ID
        info["android_id"] = await self.get_android_id()

        # 모델명
        info["model"] = await self._shell("getprop ro.product.model")

        # 제조사
        info["manufacturer"] = await self._shell("getprop ro.product.manufacturer")

        # SDK 버전
        sdk = await self._shell("getprop ro.build.version.sdk")
        info["sdk_version"] = int(sdk) if sdk.isdigit() else None

        # 빌드 핑거프린트
        info["build_fingerprint"] = await self._shell("getprop ro.build.fingerprint")

        # 시리얼
        info["serial"] = await self._shell("getprop ro.serialno")

        return info

    async def verify_identity(self, device_config: DeviceConfig) -> Dict[str, bool]:
        """
        현재 디바이스 식별자가 설정과 일치하는지 확인

        Args:
            device_config: 기대하는 디바이스 설정

        Returns:
            각 식별자별 일치 여부
        """
        current = await self.get_device_info()

        result = {
            "android_id_match": current.get("android_id") == device_config.android_id,
        }

        return result


class LocationProvider:
    """위치 프로바이더 설정 도우미"""

    def __init__(self, device_serial: Optional[str] = None):
        self._serial = device_serial

    async def _shell(self, command: str) -> str:
        adb_cmd = ["adb"]
        if self._serial:
            adb_cmd.extend(["-s", self._serial])
        adb_cmd.extend(["shell", command])

        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(adb_cmd, capture_output=True, text=True)
        )
        return result.stdout.strip()

    async def enable_mock_location(self, app_package: str = "com.fakegps") -> bool:
        """
        모의 위치 앱 허용

        Args:
            app_package: FakeGPS 앱 패키지명

        Returns:
            성공 여부
        """
        # 개발자 옵션 → 모의 위치 앱 선택
        await self._shell(
            f"settings put secure mock_location 1"
        )
        await self._shell(
            f"appops set {app_package} android:mock_location allow"
        )
        return True

    async def disable_mock_location(self) -> bool:
        """모의 위치 비활성화"""
        await self._shell("settings put secure mock_location 0")
        return True
