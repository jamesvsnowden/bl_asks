
from typing import Optional
from bpy.types import PropertyGroup
from bpy.props import FloatProperty
from .component import Component


def range_component_min_get(component: 'RangeComponent') -> float:
    return component.get("min", 0.0)


def range_component_min_set(component: 'RangeComponent', value: float) -> None:
    value = min(value, component.max)
    if component.min != value:
        component["min"] = value
        component.process()


def range_component_max_get(component: 'RangeComponent') -> float:
    return component.get("max", 1.0)


def range_component_max_set(component: 'RangeComponent', value: float) -> None:
    value = max(value, component.min)
    if component.max != value:
        component["max"] = value
        component.process()


class RangeComponent(Component, PropertyGroup):

    SYSTEM_PATH = "range_components__internal__"
    asks_idname = "asks.range"

    min: FloatProperty(
        min=-10.0,
        max=9.999,
        get=range_component_min_get,
        set=range_component_min_set,
        options=set(),
        )

    max: FloatProperty(
        min=-9.999,
        max=10.0,
        get=range_component_max_get,
        set=range_component_max_set,
        options=set()
        )

    def draw(self, layout: 'UILayout', label: Optional[str]=None) -> None:
        if label is None: label = self.label
        col = layout.column(heading=label, align=True)
        col.prop(self, "min", text=""),
        col.prop(self, "max", text="")
