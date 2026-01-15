"""
Soul Manager 모듈
앱 데이터(영혼) 백업 및 복원 관리
"""

from .app_data_paths import (
    AppConfig,
    NAVER_APP,
    CHROME_APP,
    NAVER_MAP_APP,
    APP_CONFIGS,
    get_app_config,
    SOUL_STORAGE_BASE,
    MAX_BACKUP_VERSIONS,
)

from .soul_manager import SoulManager

from .cookie_manager import (
    CookieManager,
    NAVER_COOKIE_INFO,
)

__all__ = [
    # App Configs
    "AppConfig",
    "NAVER_APP",
    "CHROME_APP",
    "NAVER_MAP_APP",
    "APP_CONFIGS",
    "get_app_config",
    "SOUL_STORAGE_BASE",
    "MAX_BACKUP_VERSIONS",
    # Soul Manager
    "SoulManager",
    # Cookie Manager
    "CookieManager",
    "NAVER_COOKIE_INFO",
]
