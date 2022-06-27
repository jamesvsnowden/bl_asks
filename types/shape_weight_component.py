
from typing import Optional, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import FloatProperty
from .component import Component
if TYPE_CHECKING:
    from bpy.types import UILayout


class ShapeWeightComponent(Component, PropertyGroup):

    SYSTEM_PATH = "shape_weight_components__internal__"

    value: FloatProperty(
        name="Value",
        min=0.0,
        max=10.0,
        soft_min=0.0,
        soft_max=1.0,
        default=0.0,
        options=set(),
        update=lambda self, _: self.process()
        )

    def draw(self, layout: 'UILayout', label: Optional[str]=None) -> None:
        text = self.label if label is None else label
        layout.prop(self, "value", text=text, icon=self.icon)
