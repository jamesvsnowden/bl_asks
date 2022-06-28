
from typing import Optional, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import FloatProperty
from .component import Component
if TYPE_CHECKING:
    from bpy.types import UILayout


def value_component_value_update(component: 'ValueComponent', _) -> None:
    component.process()


class ValueComponent(Component, PropertyGroup):

    SYSTEM_PATH = "value_components__internal__"
    asks_idname = "asks.value"

    value: FloatProperty(
        name="Value",
        min=0.0,
        max=10.0,
        soft_min=0.0,
        soft_max=1.0,
        default=0.0,
        options=set(),
        update=value_component_value_update
        )

    def draw(self, layout: 'UILayout', label: Optional[str]=None) -> None:
        text = self.label if label is None else label
        layout.prop(self, "value", text=text)
