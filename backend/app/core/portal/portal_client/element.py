"""
UIElement - UI 요소 데이터 구조

DroidRun Portal에서 반환하는 UI 트리 구조를 표현합니다.

Author: Naver AI Evolution System
Created: 2025-12-15
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple


@dataclass
class Bounds:
    """
    UI 요소의 경계 영역

    Android의 bounds 형식: [left,top][right,bottom]
    """
    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0

    @property
    def width(self) -> int:
        """너비"""
        return self.right - self.left

    @property
    def height(self) -> int:
        """높이"""
        return self.bottom - self.top

    @property
    def center_x(self) -> int:
        """중심 X 좌표"""
        return (self.left + self.right) // 2

    @property
    def center_y(self) -> int:
        """중심 Y 좌표"""
        return (self.top + self.bottom) // 2

    @property
    def center(self) -> Tuple[int, int]:
        """중심 좌표 (x, y)"""
        return (self.center_x, self.center_y)

    def contains(self, x: int, y: int) -> bool:
        """좌표가 영역 안에 있는지"""
        return self.left <= x <= self.right and self.top <= y <= self.bottom

    def to_dict(self) -> Dict[str, int]:
        """딕셔너리로 변환"""
        return {
            "left": self.left,
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom
        }

    @classmethod
    def from_string(cls, bounds_str: str) -> "Bounds":
        """
        문자열에서 파싱

        형식: "[left,top][right,bottom]" 또는 "left,top,right,bottom"
        """
        if not bounds_str:
            return cls()

        # [left,top][right,bottom] 형식
        match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
        if len(match) == 2:
            left, top = int(match[0][0]), int(match[0][1])
            right, bottom = int(match[1][0]), int(match[1][1])
            return cls(left, top, right, bottom)

        # left,top,right,bottom 형식
        parts = bounds_str.replace('[', '').replace(']', '').split(',')
        if len(parts) == 4:
            return cls(
                int(parts[0].strip()), int(parts[1].strip()),
                int(parts[2].strip()), int(parts[3].strip())
            )

        return cls()

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "Bounds":
        """딕셔너리에서 생성"""
        return cls(
            left=data.get("left", 0),
            top=data.get("top", 0),
            right=data.get("right", 0),
            bottom=data.get("bottom", 0)
        )


@dataclass
class UIElement:
    """
    UI 요소

    DroidRun Portal에서 반환하는 UI 요소 정보를 표현합니다.
    """

    # === 기본 정보 ===
    index: int = 0
    text: str = ""
    resource_id: str = ""
    class_name: str = ""
    package: str = ""
    content_desc: str = ""

    # === 상태 ===
    checkable: bool = False
    checked: bool = False
    clickable: bool = False
    enabled: bool = True
    focusable: bool = False
    focused: bool = False
    scrollable: bool = False
    long_clickable: bool = False
    password: bool = False
    selected: bool = False
    visible_to_user: bool = True

    # === 영역 ===
    bounds: Bounds = field(default_factory=Bounds)

    # === 자식 요소 ===
    children: List["UIElement"] = field(default_factory=list)

    # === 원본 데이터 ===
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def center(self) -> Tuple[int, int]:
        """중심 좌표"""
        return self.bounds.center

    @property
    def has_text(self) -> bool:
        """텍스트가 있는지"""
        return bool(self.text.strip())

    @property
    def is_interactive(self) -> bool:
        """상호작용 가능한지"""
        return self.clickable or self.long_clickable or self.scrollable

    def contains_text(self, text: str, case_sensitive: bool = False) -> bool:
        """텍스트 포함 여부"""
        if not text:
            return False

        element_text = self.text
        search_text = text

        if not case_sensitive:
            element_text = element_text.lower()
            search_text = search_text.lower()

        return search_text in element_text

    def matches(self, **criteria) -> bool:
        """
        조건 매칭

        Args:
            text: 정확한 텍스트 매칭
            text_contains: 텍스트 포함
            resource_id: 리소스 ID
            class_name: 클래스명
            clickable: 클릭 가능 여부
            scrollable: 스크롤 가능 여부
            enabled: 활성화 여부
        """
        for key, value in criteria.items():
            if value is None:
                continue

            if key == "text":
                if self.text != value:
                    return False
            elif key == "text_contains":
                if not self.contains_text(value):
                    return False
            elif key == "text_contains_case":
                if not self.contains_text(value, case_sensitive=True):
                    return False
            elif key == "resource_id":
                if value not in self.resource_id:
                    return False
            elif key == "resource_id_exact":
                if self.resource_id != value:
                    return False
            elif key == "class_name":
                if value not in self.class_name:
                    return False
            elif key == "class_name_exact":
                if self.class_name != value:
                    return False
            elif key == "content_desc":
                if value not in self.content_desc:
                    return False
            elif key == "clickable":
                if self.clickable != value:
                    return False
            elif key == "scrollable":
                if self.scrollable != value:
                    return False
            elif key == "enabled":
                if self.enabled != value:
                    return False
            elif key == "visible":
                if self.visible_to_user != value:
                    return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "index": self.index,
            "text": self.text,
            "resource_id": self.resource_id,
            "class_name": self.class_name,
            "package": self.package,
            "content_desc": self.content_desc,
            "checkable": self.checkable,
            "checked": self.checked,
            "clickable": self.clickable,
            "enabled": self.enabled,
            "focusable": self.focusable,
            "focused": self.focused,
            "scrollable": self.scrollable,
            "long_clickable": self.long_clickable,
            "password": self.password,
            "selected": self.selected,
            "visible_to_user": self.visible_to_user,
            "bounds": self.bounds.to_dict(),
            "children": [child.to_dict() for child in self.children]
        }

    # className 기반 clickable 추론을 위한 상수
    CLICKABLE_CLASSES = {
        'Button', 'ImageButton', 'CheckBox', 'RadioButton', 'Switch',
        'ToggleButton', 'EditText', 'Spinner', 'SeekBar', 'RatingBar',
        'android.widget.Button', 'android.widget.ImageButton',
        'android.widget.CheckBox', 'android.widget.RadioButton',
        'android.widget.Switch', 'android.widget.EditText',
        'android.widget.Spinner', 'android.view.View',
    }

    SCROLLABLE_CLASSES = {
        'ScrollView', 'HorizontalScrollView', 'ListView', 'RecyclerView',
        'GridView', 'NestedScrollView', 'ViewPager', 'WebView',
        'android.widget.ScrollView', 'android.widget.ListView',
        'androidx.recyclerview.widget.RecyclerView',
    }

    @classmethod
    def _infer_clickable(cls, class_name: str, resource_id: str, text: str, bounds_valid: bool) -> bool:
        """className, resourceId, text 기반으로 clickable 추론"""
        # 클래스명 체크
        simple_class = class_name.split('.')[-1] if class_name else ''
        if simple_class in cls.CLICKABLE_CLASSES or class_name in cls.CLICKABLE_CLASSES:
            return True

        # WebView 내의 View는 대부분 클릭 가능
        if simple_class == 'View' and bounds_valid:
            return True

        # resourceId에 button, btn, click 등 포함
        rid_lower = resource_id.lower()
        if any(kw in rid_lower for kw in ['button', 'btn', 'click', 'tab', 'link', 'item']):
            return True

        # 텍스트가 있고 bounds가 유효하면 클릭 가능으로 추론 (보수적)
        if text and bounds_valid and simple_class in ['TextView', 'ImageView']:
            return True

        return False

    @classmethod
    def _infer_scrollable(cls, class_name: str) -> bool:
        """className 기반으로 scrollable 추론"""
        simple_class = class_name.split('.')[-1] if class_name else ''
        return simple_class in cls.SCROLLABLE_CLASSES or class_name in cls.SCROLLABLE_CLASSES

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UIElement":
        """딕셔너리에서 생성"""
        bounds_data = data.get("bounds", {})
        if isinstance(bounds_data, str):
            bounds = Bounds.from_string(bounds_data)
        elif isinstance(bounds_data, dict):
            bounds = Bounds.from_dict(bounds_data)
        else:
            bounds = Bounds()

        children = [
            cls.from_dict(child)
            for child in data.get("children", [])
        ]

        # Portal 형식 호환: resourceId -> resource_id, className -> class_name
        resource_id = data.get("resource-id", data.get("resource_id", data.get("resourceId", "")))
        class_name = data.get("class", data.get("class_name", data.get("className", "")))
        text = data.get("text", "")

        # bounds 유효성 체크
        bounds_valid = bounds.width > 0 and bounds.height > 0

        # clickable/scrollable 추론 (데이터에 없으면)
        clickable = data.get("clickable")
        if clickable is None:
            clickable = cls._infer_clickable(class_name, resource_id, text, bounds_valid)
        elif isinstance(clickable, str):
            clickable = clickable.lower() == 'true'

        scrollable = data.get("scrollable")
        if scrollable is None:
            scrollable = cls._infer_scrollable(class_name)
        elif isinstance(scrollable, str):
            scrollable = scrollable.lower() == 'true'

        return cls(
            index=data.get("index", 0),
            text=text,
            resource_id=resource_id,
            class_name=class_name,
            package=data.get("package", ""),
            content_desc=data.get("content-desc", data.get("content_desc", "")),
            checkable=data.get("checkable", False),
            checked=data.get("checked", False),
            clickable=clickable,
            enabled=data.get("enabled", True),
            focusable=data.get("focusable", False),
            focused=data.get("focused", False),
            scrollable=scrollable,
            long_clickable=data.get("long-clickable", data.get("long_clickable", False)),
            password=data.get("password", False),
            selected=data.get("selected", False),
            visible_to_user=data.get("visible-to-user", data.get("visible_to_user", True)),
            bounds=bounds,
            children=children,
            raw_data=data
        )

    def __repr__(self) -> str:
        text_preview = self.text[:20] + "..." if len(self.text) > 20 else self.text
        return f"UIElement(text='{text_preview}', class='{self.class_name.split('.')[-1]}', clickable={self.clickable})"


class UITree:
    """
    UI 트리

    전체 UI 계층 구조를 관리하고 검색 기능을 제공합니다.
    """

    def __init__(self, root: UIElement = None):
        self.root = root
        self._all_elements: List[UIElement] = []

        if root:
            self._flatten(root)

    def _flatten(self, element: UIElement):
        """재귀적으로 모든 요소를 평탄화"""
        self._all_elements.append(element)
        for child in element.children:
            self._flatten(child)

    @property
    def all_elements(self) -> List[UIElement]:
        """모든 요소 목록"""
        return self._all_elements

    @property
    def clickable_elements(self) -> List[UIElement]:
        """클릭 가능한 요소 목록"""
        return [e for e in self._all_elements if e.clickable]

    @property
    def interactive_elements(self) -> List[UIElement]:
        """상호작용 가능한 요소 목록"""
        return [e for e in self._all_elements if e.is_interactive]

    @property
    def text_elements(self) -> List[UIElement]:
        """텍스트가 있는 요소 목록"""
        return [e for e in self._all_elements if e.has_text]

    def find(self, **criteria) -> Optional[UIElement]:
        """
        조건에 맞는 첫 번째 요소 검색

        Args:
            **criteria: UIElement.matches()에 전달할 조건

        Returns:
            첫 번째 매칭 요소 또는 None
        """
        for element in self._all_elements:
            if element.matches(**criteria):
                return element
        return None

    def find_all(self, **criteria) -> List[UIElement]:
        """
        조건에 맞는 모든 요소 검색

        Args:
            **criteria: UIElement.matches()에 전달할 조건

        Returns:
            매칭되는 모든 요소 목록
        """
        return [e for e in self._all_elements if e.matches(**criteria)]

    def find_by_text(self, text: str, exact: bool = False) -> Optional[UIElement]:
        """텍스트로 요소 검색"""
        if exact:
            return self.find(text=text)
        return self.find(text_contains=text)

    def find_all_by_text(self, text: str, exact: bool = False) -> List[UIElement]:
        """텍스트로 모든 요소 검색"""
        if exact:
            return self.find_all(text=text)
        return self.find_all(text_contains=text)

    def find_by_resource_id(self, resource_id: str) -> Optional[UIElement]:
        """리소스 ID로 요소 검색"""
        return self.find(resource_id=resource_id)

    def find_at_position(self, x: int, y: int) -> Optional[UIElement]:
        """특정 좌표에 있는 요소 검색 (가장 작은 영역)"""
        candidates = [
            e for e in self._all_elements
            if e.bounds.contains(x, y)
        ]

        if not candidates:
            return None

        # 가장 작은 영역의 요소 반환
        return min(candidates, key=lambda e: e.bounds.width * e.bounds.height)

    def get_scrollable_containers(self) -> List[UIElement]:
        """스크롤 가능한 컨테이너 목록"""
        return [e for e in self._all_elements if e.scrollable]

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "root": self.root.to_dict() if self.root else None,
            "total_elements": len(self._all_elements),
            "clickable_count": len(self.clickable_elements),
            "interactive_count": len(self.interactive_elements)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UITree":
        """딕셔너리에서 생성"""
        # Portal 형식: {"a11y_tree": [...], "phone_state": {...}}
        if "a11y_tree" in data:
            a11y_tree = data["a11y_tree"]
            if isinstance(a11y_tree, list) and a11y_tree:
                # 리스트의 첫 번째 요소가 루트
                root = UIElement.from_dict(a11y_tree[0])
                return cls(root)

        root_data = data.get("root") or data.get("hierarchy") or data
        if root_data:
            root = UIElement.from_dict(root_data)
            return cls(root)
        return cls()

    @classmethod
    def from_json(cls, json_str: str) -> "UITree":
        """JSON 문자열에서 생성"""
        import json
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError:
            return cls()

    def __len__(self) -> int:
        return len(self._all_elements)

    def __repr__(self) -> str:
        return f"UITree(elements={len(self)}, clickable={len(self.clickable_elements)})"
