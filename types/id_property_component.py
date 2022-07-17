
from typing import Any, Dict, Optional, Sequence, Union, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, FloatProperty, StringProperty
from rna_prop_ui import rna_idprop_ui_create
from .component import Component
if TYPE_CHECKING:
    from bpy.types import UILayout


def id_property_component_ui_as_dict(component: 'IDPropertyComponent') -> Dict[str, Any]:
    return component.id_data.id_properties_ui(component.name).as_dict()


def id_property_component_default_get(component: 'IDPropertyComponent') -> float:
    return id_property_component_ui_as_dict().get("default", component.get("default", 0.0))


def id_property_component_default_set(component: 'IDPropertyComponent', value: float) -> None:
    component.update(default=value)


def id_property_component_description_get(component: 'IDPropertyComponent') -> str:
    return id_property_component_ui_as_dict().get("description", component.get("description", ""))


def id_property_component_description_set(component: 'IDPropertyComponent', value: str) -> None:
    component.update(description=value)


def id_property_component_min_get(component: 'IDPropertyComponent') -> float:
    return id_property_component_ui_as_dict(component).get("min", component.get("min", -100000.))


def id_property_component_min_set(component: 'IDPropertyComponent', value: float) -> None:
    component.update(min=value)


def id_property_component_max_get(component: 'IDPropertyComponent') -> float:
    return id_property_component_ui_as_dict(component).get("max", component.get("max", 100000.))


def id_property_component_max_set(component: 'IDPropertyComponent', value: float) -> None:
    component.update(max=value)


def id_property_component_soft_min_get(component: 'IDPropertyComponent') -> float:
    return id_property_component_ui_as_dict(component).get("soft_min", component.get("soft_min", -100000.))


def id_property_component_soft_min_set(component: 'IDPropertyComponent', value: float) -> None:
    component.update(soft_min=value)


def id_property_component_soft_max_get(component: 'IDPropertyComponent') -> float:
    return id_property_component_ui_as_dict(component).get("soft_max", component.get("soft_max", 100000.))


def id_property_component_soft_max_set(component: 'IDPropertyComponent', value: float) -> None:
    component.update(soft_max=value)


class IDPropertyComponent(Component, PropertyGroup):

    @property
    def data_path(self) -> str:
        return f'["{self.name}"]'

    default: FloatProperty(
        name="Default",
        get=id_property_component_default_get,
        set=id_property_component_default_set,
        options=set()
        )

    description: StringProperty(
        name="Description",
        get=lambda self: self.as_dict().get("description", self.get("description", "")),
        set=lambda self, value: self.update(description=value),
        options=set()
        )

    min: FloatProperty(
        name="Min",
        get=id_property_component_min_get,
        set=id_property_component_min_set,
        options=set()
        )

    max: FloatProperty(
        name="Max",
        get=id_property_component_max_get,
        set=id_property_component_max_set,
        options=set()
        )

    soft_min: FloatProperty(
        name="Soft Min",
        get=id_property_component_soft_min_get,
        set=id_property_component_soft_min_set,
        options=set()
        )

    soft_max: FloatProperty(
        name="Soft Max",
        get=id_property_component_soft_max_get,
        set=id_property_component_soft_max_set,
        options=set()
        )

    use_slider: BoolProperty(
        name="Slider",
        default=True,
        options=set()
        )

    def __init__(self, **properties: Dict[str, Any]) -> None:
        super().__init__(**properties)
        settings = {}
        for key in ("min", "max", "soft_min", "soft_max", "default", "description"):
            if key in properties:
                settings[key] = properties[key]
        rna_idprop_ui_create(self.id_data, self.name, **settings)

    def as_dict(self) -> Dict[str, Any]:
        return self.id_data.id_properties_ui(self.name).as_dict()

    def draw(self, layout: 'UILayout', label: Optional[str]=None) -> None:
        text = self.label if label is None else label
        layout.prop(self.id_data, self.data_path, text=text, slider=self.use_slider)

    def update(self,
               value: Optional[Union[float, Sequence[float]]]=None,
               **options: Dict[str, Any]) -> None:

        if value is not None:
            self.id_data[self.name] = value

        if options:
            for key, value in options.items():
                self[key] = value
            self.id_data.id_properties_ui(self.name).update(**options)
        self.process()