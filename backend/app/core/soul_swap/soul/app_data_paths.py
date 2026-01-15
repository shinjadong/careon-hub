"""
앱 데이터 경로 및 설정
영혼 스왑 대상 앱의 경로 정의
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class AppConfig:
    """앱 설정"""
    package: str
    data_path: str
    launch_activity: str
    critical_files: List[str] = field(default_factory=list)
    exclude_from_backup: List[str] = field(default_factory=list)


# 네이버 앱
NAVER_APP = AppConfig(
    package="com.nhn.android.search",
    data_path="/data/data/com.nhn.android.search",
    launch_activity=".ui.SplashActivity",
    critical_files=[
        "shared_prefs/cookies.xml",
        "shared_prefs/NID_SES.xml",
        "shared_prefs/NNB.xml",  # 50년 쿠키 (매우 중요!)
        "shared_prefs/login_prefs.xml",
    ],
    exclude_from_backup=[
        "cache/*",
        "code_cache/*",
        "no_backup/*",
    ]
)

# Chrome
CHROME_APP = AppConfig(
    package="com.android.chrome",
    data_path="/data/data/com.android.chrome",
    launch_activity="com.google.android.apps.chrome.Main",
    critical_files=[
        "app_chrome/Default/Cookies",
        "app_chrome/Default/Login Data",
        "app_chrome/Default/Web Data",
    ],
    exclude_from_backup=[
        "cache/*",
        "app_chrome/Default/Cache/*",
        "app_chrome/Default/Code Cache/*",
    ]
)

# 네이버 지도
NAVER_MAP_APP = AppConfig(
    package="com.nhn.android.nmap",
    data_path="/data/data/com.nhn.android.nmap",
    launch_activity=".MainActivity",
    critical_files=[
        "shared_prefs/",
    ],
    exclude_from_backup=[
        "cache/*",
        "code_cache/*",
    ]
)

# 앱 설정 레지스트리
APP_CONFIGS = {
    "naver": NAVER_APP,
    "chrome": CHROME_APP,
    "naver_map": NAVER_MAP_APP,
}


def get_app_config(app_name: str) -> AppConfig:
    """앱 설정 조회"""
    config = APP_CONFIGS.get(app_name.lower())
    if not config:
        raise ValueError(f"Unknown app: {app_name}. Available: {list(APP_CONFIGS.keys())}")
    return config


# 영혼 파일 저장 기본 경로
SOUL_STORAGE_BASE = "/sdcard/personas"

# 백업 유지 개수
MAX_BACKUP_VERSIONS = 3
