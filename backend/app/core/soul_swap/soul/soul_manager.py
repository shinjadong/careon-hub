"""
Soul Manager
앱 데이터(영혼) 백업 및 복원 관리
"""

import asyncio
import subprocess
import re
import os
from typing import Optional, Dict, Any
from datetime import datetime

from .app_data_paths import (
    AppConfig,
    NAVER_APP,
    SOUL_STORAGE_BASE,
    MAX_BACKUP_VERSIONS,
)


class SoulManager:
    """영혼(앱 데이터) 관리자"""

    def __init__(self, device_serial: Optional[str] = None):
        """
        Args:
            device_serial: ADB 디바이스 시리얼 (None이면 기본 디바이스)
        """
        self._serial = device_serial
        self._soul_base = SOUL_STORAGE_BASE

    async def _shell(self, command: str, timeout: int = 30) -> str:
        """ADB 쉘 명령 실행"""
        adb_cmd = ["adb"]
        if self._serial:
            adb_cmd.extend(["-s", self._serial])
        adb_cmd.extend(["shell", command])

        try:
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: subprocess.run(
                        adb_cmd,
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )
                ),
                timeout=timeout + 5
            )
            if result.returncode != 0 and result.stderr:
                raise RuntimeError(f"ADB error: {result.stderr}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Command timed out: {command}")

    async def cleanup(self, app: AppConfig = None) -> bool:
        """
        Phase 1: 앱 데이터 초기화 (Clean-Up)

        Args:
            app: 앱 설정 (기본: 네이버)

        Returns:
            성공 여부
        """
        app = app or NAVER_APP

        # 앱 강제 종료
        await self._shell(f"am force-stop {app.package}")
        await asyncio.sleep(0.5)

        # 데이터 초기화
        result = await self._shell(f"pm clear {app.package}")

        return "Success" in result

    async def restore(
        self,
        persona_id: str,
        soul_file: Optional[str] = None,
        app: AppConfig = None
    ) -> bool:
        """
        Phase 3: 영혼 복원 (Soul Restore)

        Args:
            persona_id: 페르소나 ID
            soul_file: 영혼 파일 경로 (None이면 최신 버전)
            app: 앱 설정 (기본: 네이버)

        Returns:
            성공 여부
        """
        app = app or NAVER_APP

        # 영혼 파일 경로 결정
        if not soul_file:
            soul_file = await self._get_latest_soul_file(persona_id)
            if not soul_file:
                raise FileNotFoundError(f"No soul file found for persona: {persona_id}")

        # 파일 존재 확인
        exists = await self._shell(f"test -f {soul_file} && echo 'exists'")
        if "exists" not in exists:
            raise FileNotFoundError(f"Soul file not found: {soul_file}")

        # 1. 앱 초기화 (pm clear)
        await self.cleanup(app)

        # 2. tar.gz 압축 해제 (루트 권한 필요)
        await self._shell(
            f"su -c 'tar -xzf {soul_file} -C {app.data_path}/'",
            timeout=60
        )

        # 3. 권한 복구 (chown) (루트 권한 필요)
        uid = await self._get_app_uid(app.package)
        await self._shell(f"su -c 'chown -R u0_a{uid}:u0_a{uid} {app.data_path}/'")

        return True

    async def backup(
        self,
        persona_id: str,
        app: AppConfig = None
    ) -> Dict[str, Any]:
        """
        Phase 5: 영혼 백업 (Memory Backup)

        Args:
            persona_id: 페르소나 ID
            app: 앱 설정 (기본: 네이버)

        Returns:
            백업 정보 (file_path, version, size_bytes)
        """
        app = app or NAVER_APP
        soul_path = f"{self._soul_base}/{persona_id}"

        # 디렉토리 생성
        await self._shell(f"mkdir -p {soul_path}")

        # 다음 버전 번호 결정
        version = await self._get_next_version(persona_id)
        backup_file = f"{soul_path}/backup_v{version}.tar.gz"

        # 백업 생성 (exclude 옵션 적용)
        exclude_opts = " ".join(f"--exclude='{e}'" for e in app.exclude_from_backup)
        await self._shell(
            f"tar -czf {backup_file} {exclude_opts} -C {app.data_path}/ .",
            timeout=120
        )

        # 파일 크기 확인
        size_result = await self._shell(f"stat -c %s {backup_file}")
        size_bytes = int(size_result) if size_result.isdigit() else 0

        # 오래된 백업 정리
        await self._cleanup_old_backups(persona_id)

        return {
            "file_path": backup_file,
            "version": version,
            "size_bytes": size_bytes,
            "backup_at": datetime.now().isoformat()
        }

    async def launch_app(self, app: AppConfig = None) -> bool:
        """
        Phase 4: 앱 실행

        Args:
            app: 앱 설정 (기본: 네이버)

        Returns:
            성공 여부
        """
        app = app or NAVER_APP

        # 앱 실행
        result = await self._shell(
            f"am start -n {app.package}/{app.launch_activity}"
        )

        return "Error" not in result

    async def verify_login_state(self, app: AppConfig = None) -> bool:
        """
        로그인 상태 확인 (쿠키 파일 존재 여부)

        Args:
            app: 앱 설정 (기본: 네이버)

        Returns:
            로그인 상태 추정 (쿠키 파일 존재 여부)
        """
        app = app or NAVER_APP

        # 핵심 쿠키 파일 확인
        for critical_file in app.critical_files:
            full_path = f"{app.data_path}/{critical_file}"
            exists = await self._shell(f"test -f {full_path} && echo 'exists'")
            if "exists" not in exists:
                return False

        return True

    async def _get_app_uid(self, package: str) -> int:
        """앱의 UID 조회 (u0_a{n}의 n 값)"""
        # Android 15+: cmd package list packages -U 사용
        result = await self._shell(f"cmd package list packages -U | grep {package}")

        match = re.search(r'uid:(\d+)', result)
        if match:
            full_uid = int(match.group(1))
            # uid:10281 → 281
            return full_uid - 10000

        # fallback: dumpsys 방식
        result = await self._shell(f"dumpsys package {package} | grep userId")
        match = re.search(r'userId=(\d+)', result)
        if match:
            full_uid = int(match.group(1))
            return full_uid - 10000

        raise ValueError(f"UID not found for {package}")

    async def _get_latest_soul_file(self, persona_id: str) -> Optional[str]:
        """최신 영혼 파일 경로 조회"""
        soul_path = f"{self._soul_base}/{persona_id}"

        # 파일 목록 조회 (최신순)
        result = await self._shell(
            f"ls -t {soul_path}/backup_v*.tar.gz 2>/dev/null | head -1"
        )

        return result if result else None

    async def _get_next_version(self, persona_id: str) -> int:
        """다음 백업 버전 번호"""
        soul_path = f"{self._soul_base}/{persona_id}"

        result = await self._shell(
            f"ls {soul_path}/backup_v*.tar.gz 2>/dev/null | wc -l"
        )

        try:
            current_count = int(result.strip())
            return current_count + 1
        except ValueError:
            return 1

    async def _cleanup_old_backups(
        self,
        persona_id: str,
        keep: int = MAX_BACKUP_VERSIONS
    ) -> None:
        """오래된 백업 파일 정리"""
        soul_path = f"{self._soul_base}/{persona_id}"

        # 오래된 파일 삭제 (최신 keep개 제외)
        await self._shell(
            f"ls -t {soul_path}/backup_v*.tar.gz 2>/dev/null | "
            f"tail -n +{keep + 1} | xargs -r rm -f"
        )

    async def get_soul_info(self, persona_id: str) -> Dict[str, Any]:
        """페르소나의 영혼 파일 정보 조회"""
        soul_path = f"{self._soul_base}/{persona_id}"

        # 파일 목록
        files_result = await self._shell(
            f"ls -la {soul_path}/backup_v*.tar.gz 2>/dev/null"
        )

        if not files_result or "No such file" in files_result:
            return {
                "exists": False,
                "versions": [],
                "latest": None
            }

        # 파일 파싱
        versions = []
        for line in files_result.split('\n'):
            if 'backup_v' in line:
                parts = line.split()
                if len(parts) >= 5:
                    size = int(parts[4]) if parts[4].isdigit() else 0
                    filename = parts[-1]
                    version_match = re.search(r'backup_v(\d+)', filename)
                    version = int(version_match.group(1)) if version_match else 0
                    versions.append({
                        "version": version,
                        "file": filename,
                        "size_bytes": size
                    })

        versions.sort(key=lambda x: x["version"], reverse=True)

        return {
            "exists": len(versions) > 0,
            "versions": versions,
            "latest": versions[0] if versions else None
        }
