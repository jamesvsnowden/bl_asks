
from typing import Any, Dict, Optional, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, StringProperty
from .component import Component
if TYPE_CHECKING:
    from bpy.types import UILayout


def range_component_min_get(component: 'RangeComponent') -> float:
    return component.get("min", 0.0)


def range_component_min_set(component: 'RangeComponent', value: float) -> None:
    range_component_max_modify(component, value)
    range_component_max_mirror(component, value)


def range_component_min_modify(component: 'RangeComponent', value: float) -> None:
    value = min(value, component.max)
    if component.min != value:
        component["min"] = value
        component.process()


def range_component_min_mirror(component: 'RangeComponent', value: float) -> None:
    mirror = component.mirror
    if mirror:
        try:
            symtarget = mirror()
        except ValueError:
            component.system.log.warning(f'{component} mirror {mirror} not found.')
        else:
            range_component_min_modify(symtarget, value)


def range_component_max_get(component: 'RangeComponent') -> float:
    return component.get("max", 1.0)


def range_component_max_set(component: 'RangeComponent', value: float) -> None:
    range_component_max_modify(component, value)
    range_component_max_mirror(component, value)


def range_component_max_modify(component: 'RangeComponent', value: float) -> None:
    value = max(value, component.min)
    if component.max != value:
        component["max"] = value
        component.process()


def range_component_max_mirror(component: 'RangeComponent', value: float) -> None:
    mirror = component.mirror
    if mirror:
        try:
            symtarget = mirror()
        except ValueError:
            component.system.log.warning(f'{component} mirror {mirror} not found.')
        else:
            range_component_max_modify(symtarget, value)


class RangeComponent(Component, PropertyGroup):

    label_min: StringProperty(
        default="Min",
        options=set()
        )

    label_max: StringProperty(
        default="Max",
        options=set()
        )

    min: FloatProperty(
        min=-10.0,
        max=9.999,
        precision=3,
        get=range_component_min_get,
        set=range_component_min_set,
        options=set(),
        )

    max: FloatProperty(
        min=-9.999,
        max=10.0,
        precision=3,
        get=range_component_max_get,
        set=range_component_max_set,
        options=set()
        )

    def draw(self, layout: 'UILayout', label: Optional[str]=None) -> None:
        if label is None: label = self.label
        col = layout.column(align=True)
        col.prop(self, "min", text=f'{label + " " if label else ""}{self.label_min}')
        col.prop(self, "max", text=self.label_max)

    def __onsymmetry__(self, symtarget: 'Component') -> None:
        symtarget["min"] = self.min
        symtarget["max"] = self.max
        symtarget.process()

    def __properties__(self) -> Dict[str, Any]:
        return dict(
            super().__properties__(),
            label_min=self.label_min,
            label_max=self.label_max,
            min=self.min,
            max=self.max
            )
