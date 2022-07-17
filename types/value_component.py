
from typing import Any, Dict, Optional, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import FloatProperty
from .component import Component
if TYPE_CHECKING:
    from bpy.types import UILayout


def value_component_value_update(component: 'ValueComponent', _) -> None:
    component.process()
    mirror = component.mirror
    if mirror:
        try:
            symtarget = mirror()
        except ValueError:
            component.system.log.warning(f'{component} mirror {mirror} not found.')
        else:
            symtarget["value"] = component.value
            symtarget.process()


class ValueComponent(Component, PropertyGroup):

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

    def __properties__(self) -> Dict[str, Any]:
        return dict(super().__properties__(), value=self.value)
