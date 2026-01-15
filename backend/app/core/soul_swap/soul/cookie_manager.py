"""
Cookie Manager
앱 쿠키 추출 및 검증
"""

import asyncio
import subprocess
import re
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta


class CookieManager:
    """앱 쿠키 관리자"""

    def __init__(self, device_serial: Optional[str] = None):
        self._serial = device_serial

    async def _shell(self, command: str) -> str:
        """ADB 쉘 명령 실행"""
        adb_cmd = ["adb"]
        if self._serial:
            adb_cmd.extend(["-s", self._serial])
        adb_cmd.extend(["shell", command])

        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(adb_cmd, capture_output=True, text=True)
        )
        return result.stdout.strip()

    async def extract_naver_cookies(self) -> Dict[str, Any]:
        """
        네이버 앱 쿠키 추출

        Returns:
            추출된 쿠키 정보
        """
        cookies = {}
        naver_prefs = "/data/data/com.nhn.android.search/shared_prefs"

        # NNB 쿠키 (50년 만료, 디바이스 식별)
        nnb = await self._extract_pref_value(f"{naver_prefs}/NNB.xml", "NNB")
        if nnb:
            cookies["nnb_cookie"] = nnb

        # NID_SES 쿠키 (세션)
        nid = await self._extract_pref_value(f"{naver_prefs}/NID_SES.xml", "NID_SES")
        if nid:
            cookies["nid_cookie"] = nid

        # NID_AUT 쿠키 (로그인 상태)
        nid_aut = await self._extract_pref_value(f"{naver_prefs}/NID_AUT.xml", "NID_AUT")
        if nid_aut:
            cookies["nid_aut_cookie"] = nid_aut

        return cookies

    async def _extract_pref_value(self, pref_file: str, key: str) -> Optional[str]:
        """SharedPreferences XML에서 값 추출"""
        try:
            content = await self._shell(f"cat {pref_file} 2>/dev/null")
            if not content or "No such file" in content:
                return None

            # XML 파싱
            root = ET.fromstring(content)

            # string 태그에서 검색
            for string_elem in root.findall(".//string"):
                if string_elem.get("name") == key:
                    return string_elem.text

            # map 형태인 경우
            for map_elem in root.findall(".//map"):
                for entry in map_elem:
                    if entry.get("name") == key:
                        return entry.get("value") or entry.text

            return None

        except (ET.ParseError, Exception):
            return None

    async def validate_cookies(self, cookies: Dict[str, Any]) -> Dict[str, Any]:
        """
        쿠키 유효성 검증

        Returns:
            검증 결과
        """
        result = {
            "valid": False,
            "has_nnb": False,
            "has_session": False,
            "warnings": []
        }

        # NNB 쿠키 (필수)
        if cookies.get("nnb_cookie"):
            result["has_nnb"] = True
        else:
            result["warnings"].append("NNB cookie missing (device identifier)")

        # 세션 쿠키
        if cookies.get("nid_cookie") or cookies.get("nid_aut_cookie"):
            result["has_session"] = True
        else:
            result["warnings"].append("Session cookie missing (may need re-login)")

        # 최소 NNB는 있어야 함
        result["valid"] = result["has_nnb"]

        return result

    async def get_cookie_stats(self) -> Dict[str, Any]:
        """쿠키 파일 상태 조회"""
        naver_prefs = "/data/data/com.nhn.android.search/shared_prefs"

        stats = {
            "files": {},
            "total_size": 0
        }

        # 주요 쿠키 파일들 확인
        cookie_files = [
            "NNB.xml",
            "NID_SES.xml",
            "NID_AUT.xml",
            "cookies.xml",
        ]

        for filename in cookie_files:
            file_path = f"{naver_prefs}/{filename}"
            result = await self._shell(f"stat -c '%s %Y' {file_path} 2>/dev/null")

            if result and "No such file" not in result:
                parts = result.split()
                if len(parts) >= 2:
                    size = int(parts[0])
                    mtime = int(parts[1])
                    stats["files"][filename] = {
                        "exists": True,
                        "size_bytes": size,
                        "modified_at": datetime.fromtimestamp(mtime).isoformat()
                    }
                    stats["total_size"] += size
            else:
                stats["files"][filename] = {"exists": False}

        return stats


# 네이버 쿠키 분석 결과 (참고용)
NAVER_COOKIE_INFO = {
    "NNB": {
        "description": "디바이스 고유 식별자",
        "expiry": "50년",
        "risk": "높음 - 변경 시 새 사용자로 인식",
        "format": "13자리 영숫자 (예: N42LJ2QRSQ7GS)"
    },
    "NID_AUT": {
        "description": "로그인 인증 토큰",
        "expiry": "세션 또는 2주",
        "risk": "중간 - 만료 시 재로그인 필요"
    },
    "NID_SES": {
        "description": "세션 식별자",
        "expiry": "세션",
        "risk": "낮음 - 자동 갱신"
    },
    "IV": {
        "description": "세션 UUID",
        "expiry": "요청별",
        "risk": "낮음 - 매 요청마다 변경"
    }
}
