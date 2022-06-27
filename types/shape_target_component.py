
from typing import Any, Dict, Optional, TYPE_CHECKING
from uuid import uuid4
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, StringProperty
from bpy.msgbus import clear_by_owner, subscribe_rna
from .component import Component
if TYPE_CHECKING:
    from bpy.types import ShapeKey, UILayout

def shapekey_name_subscriber(component: 'ShapeTargetComponent', shapekey: 'ShapeKey') -> None:
    system = component.system
    syskey = component.system.entities.reverselut__internal___.get(component.value)

    if syskey:
        syskey["name"] = shapekey.name
    else:
        system.log.error()

    component["value"] = shapekey.name

    if not component.lock__internal__:
        component["lock__internal__"] = True
        try:
            component.process()
        finally: component["lock__internal__"] = False


def shape_target_component_value_get(component: 'ShapeTargetComponent') -> str:
    return component.get("value", "")


def shape_target_component_value_set(component: 'ShapeTargetComponent', value: str) -> None:
    shapekey = component.id_data.key_blocks.get(component.value)
    if shapekey:
        shapekey.name = value
        component["value"] = shapekey.name
    else:
        component["value"] = value


class ShapeTargetComponent(Component, PropertyGroup):

    SYSTEM_PATH = "shape_target_components__internal__"
    _owners: Dict[str, object] = {}

    owner__internal__: StringProperty(
        default="",
        options={'HIDDEN'}
        )

    lock__internal__: BoolProperty(
        get=lambda self: self.get("lock__internal__", False),
        options={'HIDDEN'}
        )

    value: StringProperty(
        name="Name",
        description="Unique shape key name",
        get=lambda self: self.get("value", ""),
        options=set()
        )

    def draw(self, layout: 'UILayout', label: Optional[str]=None) -> None:
        if label is None: label = self.label
        layout.prop(self, "value", text=label, icon=self.icon)

    def __init__(self, **kwargs: Dict[str, Any]) -> None:
        super.__init__(**kwargs)
        self.disposable = True
        self.hide = True
        self.label = "Name"
        self.__onfileload__()

    def __onfileload__(self) -> None:
        shape = self.id_data.key_blocks.get(self.value)
        if shape:
            key = str(uuid4())
            obj = object()
            self._owners[key] = obj
            self.owner__internal__ = key
            subscribe_rna(key=shape.path_resolve("name", False),
                          owner=obj,
                          notify=shapekey_name_subscriber,
                          args=(self, shape),
                          options={'PERSISTENT'})

    def __ondisposed__(self) -> None:
        key = self.owner__internal__
        obj = self._owners.get(key)
        if obj is not None:
            del self._owners[key]
            clear_by_owner(obj)
