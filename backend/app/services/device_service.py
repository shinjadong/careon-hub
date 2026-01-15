"""Device management service for CareOn Hub."""
import asyncio
import subprocess
from typing import List, Optional
from app.models.device import (
    DeviceInfo,
    DeviceStatus,
    DeviceAction,
    DeviceActionResponse,
    DeviceListResponse
)


class DeviceService:
    """디바이스 관리 서비스 (ADB 기반)."""

    def __init__(self):
        """Initialize device service."""
        pass

    async def _run_adb_command(
        self,
        command: List[str],
        timeout: int = 10
    ) -> str:
        """
        Run ADB command and return output.

        Args:
            command: ADB command as list (e.g., ['adb', 'devices'])
            timeout: Command timeout in seconds

        Returns:
            Command output string

        Raises:
            subprocess.CalledProcessError: If command fails
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    process.returncode,
                    command,
                    stdout,
                    stderr
                )

            return stdout.decode('utf-8').strip()

        except asyncio.TimeoutError:
            process.kill()
            raise TimeoutError(f"ADB command timed out after {timeout}s")

    async def _run_adb_device_command(
        self,
        device_id: str,
        command: str,
        timeout: int = 10
    ) -> str:
        """
        Run ADB shell command on specific device.

        Args:
            device_id: Device serial number
            command: Shell command to execute
            timeout: Command timeout

        Returns:
            Command output
        """
        cmd = ['adb', '-s', device_id, 'shell', command]
        return await self._run_adb_command(cmd, timeout)

    async def list_devices(self) -> List[DeviceInfo]:
        """
        연결된 디바이스 목록 조회.

        Returns:
            List of DeviceInfo objects
        """
        # Get device list from adb devices
        output = await self._run_adb_command(['adb', 'devices'])

        lines = output.split('\n')[1:]  # Skip "List of devices attached"
        device_ids = []

        for line in lines:
            line = line.strip()
            if line and '\t' in line:
                device_id, status = line.split('\t')
                if status == 'device':  # Only connected devices
                    device_ids.append(device_id)

        # Get detailed info for each device
        devices = []
        for device_id in device_ids:
            try:
                info = await self.get_device_info(device_id)
                devices.append(info)
            except Exception as e:
                # If device becomes unavailable, skip it
                print(f"Warning: Failed to get info for {device_id}: {e}")
                continue

        return devices

    async def get_device_info(self, device_id: str) -> DeviceInfo:
        """
        디바이스 상세 정보 조회.

        Args:
            device_id: Device serial number

        Returns:
            DeviceInfo object
        """
        # Get device properties
        model = await self._run_adb_device_command(
            device_id,
            "getprop ro.product.model"
        )

        manufacturer = await self._run_adb_device_command(
            device_id,
            "getprop ro.product.manufacturer"
        )

        android_version = await self._run_adb_device_command(
            device_id,
            "getprop ro.build.version.release"
        )

        sdk_version_str = await self._run_adb_device_command(
            device_id,
            "getprop ro.build.version.sdk"
        )
        sdk_version = int(sdk_version_str) if sdk_version_str.isdigit() else None

        # Get battery level
        battery_level = await self._get_battery_level(device_id)

        return DeviceInfo(
            device_id=device_id,
            model=model.strip(),
            manufacturer=manufacturer.strip(),
            android_version=android_version.strip(),
            status='connected',
            battery_level=battery_level,
            sdk_version=sdk_version
        )

    async def _get_battery_level(self, device_id: str) -> Optional[int]:
        """
        배터리 레벨 조회 (private helper).

        Args:
            device_id: Device serial number

        Returns:
            Battery level (0-100) or None if unavailable
        """
        try:
            output = await self._run_adb_device_command(
                device_id,
                "dumpsys battery | grep level"
            )

            # Parse "level: 85" format
            if ':' in output:
                level_str = output.split(':')[1].strip()
                return int(level_str)

            return None

        except Exception:
            return None

    async def reboot_device(self, device_id: str) -> DeviceActionResponse:
        """
        디바이스 재부팅.

        Args:
            device_id: Device serial number

        Returns:
            DeviceActionResponse with success status
        """
        try:
            await self._run_adb_command(
                ['adb', '-s', device_id, 'reboot'],
                timeout=5
            )

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
                message=f'재부팅 실패: {str(e)}'
            )

    async def take_screenshot(
        self,
        device_id: str,
        save_path: str = "/tmp/screenshot.png"
    ) -> DeviceActionResponse:
        """
        스크린샷 촬영.

        Args:
            device_id: Device serial number
            save_path: Local file path to save screenshot

        Returns:
            DeviceActionResponse with file path
        """
        try:
            # Take screenshot on device
            await self._run_adb_device_command(
                device_id,
                "screencap -p /sdcard/screenshot.png"
            )

            # Pull screenshot to local
            await self._run_adb_command([
                'adb', '-s', device_id,
                'pull', '/sdcard/screenshot.png', save_path
            ])

            # Clean up device screenshot
            await self._run_adb_device_command(
                device_id,
                "rm /sdcard/screenshot.png"
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
                message=f'스크린샷 실패: {str(e)}'
            )

    async def get_device_status(self, device_id: str) -> DeviceStatus:
        """
        디바이스 연결 상태 확인.

        Args:
            device_id: Device serial number

        Returns:
            DeviceStatus object
        """
        try:
            # Try to get a simple property to check connection
            await self._run_adb_device_command(
                device_id,
                "getprop ro.build.version.sdk",
                timeout=3
            )

            return DeviceStatus(
                device_id=device_id,
                is_connected=True,
                last_seen=__import__('datetime').datetime.utcnow()
            )

        except Exception:
            return DeviceStatus(
                device_id=device_id,
                is_connected=False,
                last_seen=__import__('datetime').datetime.utcnow()
            )

    async def clear_app_data(
        self,
        device_id: str,
        package_name: str
    ) -> DeviceActionResponse:
        """
        앱 데이터 초기화 (pm clear).

        Args:
            device_id: Device serial number
            package_name: App package name

        Returns:
            DeviceActionResponse
        """
        try:
            output = await self._run_adb_device_command(
                device_id,
                f"pm clear {package_name}"
            )

            success = 'Success' in output

            return DeviceActionResponse(
                device_id=device_id,
                action='clear_app_data',
                success=success,
                message=f'{package_name} 데이터 초기화 {"성공" if success else "실패"}',
                data={'package': package_name, 'output': output}
            )

        except Exception as e:
            return DeviceActionResponse(
                device_id=device_id,
                action='clear_app_data',
                success=False,
                message=f'데이터 초기화 실패: {str(e)}',
                data={'package': package_name}
            )

    async def force_stop_app(
        self,
        device_id: str,
        package_name: str
    ) -> DeviceActionResponse:
        """
        앱 강제 종료.

        Args:
            device_id: Device serial number
            package_name: App package name

        Returns:
            DeviceActionResponse
        """
        try:
            await self._run_adb_device_command(
                device_id,
                f"am force-stop {package_name}"
            )

            return DeviceActionResponse(
                device_id=device_id,
                action='force_stop',
                success=True,
                message=f'{package_name} 강제 종료 완료',
                data={'package': package_name}
            )

        except Exception as e:
            return DeviceActionResponse(
                device_id=device_id,
                action='force_stop',
                success=False,
                message=f'강제 종료 실패: {str(e)}',
                data={'package': package_name}
            )


def get_device_service() -> DeviceService:
    """
    Get DeviceService instance (for dependency injection).

    Returns:
        DeviceService instance
    """
    return DeviceService()
