"""
PortalClient - DroidRun Portal APK 클라이언트

DroidRun Portal APK와 통신하여 정확한 UI 요소 정보를 획득합니다.
Portal은 Content Provider를 통해 UI 트리를 제공합니다.

Components:
- PortalClient: Content Provider 통신
- UIElement: UI 요소 데이터 구조
- ElementFinder: 요소 검색 헬퍼

테스트 결과 (Galaxy Tab S9+):
- Portal APK 설치: 성공 (v0.4.7)
- 접근성 서비스 활성화: 성공
- UI 트리 수신: 정상

Author: Naver AI Evolution System
Created: 2025-12-15
"""

from .client import PortalClient, PortalConfig
from .element import UIElement, UITree, Bounds
from .finder import ElementFinder

__all__ = [
    "PortalClient",
    "PortalConfig",
    "UIElement",
    "UITree",
    "Bounds",
    "ElementFinder",
]

__version__ = "0.1.0"
