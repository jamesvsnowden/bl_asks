
from typing import Optional, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import IntProperty, StringProperty
from .system_struct import SystemStruct
if TYPE_CHECKING:
    from bpy.types import UILayout
    from .system_object import SystemObject


def entity_operation_name_get(operation: 'EntityOperation') -> str:
    return operation.get("name", "")


def entity_operation_name_set(operation: 'EntityOperation', value: str) -> None:
    raise AttributeError(f'{operation.__class__.__name__}.name is read-only')


class EntityOperation(SystemStruct, PropertyGroup):

    name: StringProperty(
        name="Name",
        get=entity_operation_name_get,
        set=entity_operation_name_set,
        options=set()
        )

    icon: IntProperty(
        name="Icon",
        default=0,
        options=set()
        )

    text: StringProperty(
        name="Text",
        default="",
        options=set()
        )

    def __init__(self,
                 name: str,
                 icon: Optional[int]=0,
                 text: Optional[str]="") -> None:
        self["name"] = name
        self["icon"] = icon
        self["text"] = text

    def draw(self, layout: 'UILayout', object: 'SystemObject') -> None:
        layout.operator(self.name, text=self.text, icon_value=self.icon)
