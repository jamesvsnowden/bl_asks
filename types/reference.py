
from typing import Optional, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import StringProperty
from .system_struct import SystemStruct
if TYPE_CHECKING:
    from .system_object import SystemObject

class Reference(SystemStruct, PropertyGroup):

    path: StringProperty(
        name="Path",
        get=lambda self: self.get("path", ""),
        options={'HIDDEN'}
        )

    def __call__(self) -> 'SystemObject':
        return self.system.path_resolve(self.path)

    def __init__(self, object: 'SystemObject', name: Optional[str]="") -> None:
        self["name"] = name
        self["path"] = object.system_path

    def __init__(self, name: str, object: 'SystemObject') -> None:
        self["name"] = name
        self["path"] = object.system_path
