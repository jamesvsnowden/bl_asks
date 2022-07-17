
from typing import Any, Dict, Optional, TYPE_CHECKING
from uuid import uuid4
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, StringProperty
from .component import Component
if TYPE_CHECKING:
    from bpy.types import Driver, FCurve, ShapeKey, UILayout

# Add Container & ContainerEntities


class ShapeKeyNameComponent(Component, PropertyGroup):

    def __init__(self, data: 'ShapeKey', path: str) -> None:
        self["path"] = path


class ShapeKeyValueComponent(Component, PropertyGroup):

    @property
    def data_path(self) -> str:
        return f'key_blocks["{self.name}"].value'

    def driver(self, ensure: Optional[bool]=True) -> Optional['Driver']:
        fcurve = self.fcurve(ensure)
        if fcurve is not None:
            return fcurve.driver

    def fcurve(self, ensure: Optional[bool]=True) -> Optional['FCurve']:
        animdata = self.id_data.animation_data
        if animdata is None:
            if not ensure:
                return
            animdata = self.id_data.animation_data_create()
        datapath = self.data_path
        fcurve = animdata.drivers.find(datapath)
        if fcurve is None:
            fcurve = animdata.drivers.new(datapath)
        return fcurve

    def __init__(self, data: 'ShapeKey', path: str) -> None:
        self["name"] = data.name
        self["path"] = path




def shapekey_name_subscriber(component: 'ShapeComponent', shapekey: 'ShapeKey') -> None:
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


def shape_target_component_value_get(component: 'ShapeComponent') -> str:
    return component.get("value", "")


def shape_target_component_value_set(component: 'ShapeComponent', value: str) -> None:
    shapekey = component.resolve()
    if shapekey:
        shapekey.name = value
        component["value"] = shapekey.name
    else:
        component["value"] = value


class ShapeComponent(Component, PropertyGroup):

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

    def draw(self,
             layout: 'UILayout',
             label: Optional[str]=None,
             icon: Optional[str]="SHAPEKEY_DATA") -> None:

        if label is None:
            label = self.label
        layout.prop(self, "value", text=label, icon=icon)

    def resolve(self) -> Optional['ShapeKey']:
        return self.id_data.key_blocks.get(self.value)

    def __init__(self, **kwargs: Dict[str, Any]) -> None:
        super().__init__(**kwargs)
        self.disposable = True
        self.hide = True
        self.label = "Name"
        self.__onfileload__()

    def __onfileload__(self) -> None:
        shapekey = self.resolve()
        if shapekey:
            from bpy import msgbus
            key = str(uuid4())
            obj = object()
            self._owners[key] = obj
            self.owner__internal__ = key
            msgbus.subscribe_rna(key=shapekey.path_resolve("name", False),
                                 owner=obj,
                                 notify=shapekey_name_subscriber,
                                 args=(self, shapekey),
                                 options={'PERSISTENT'})

    def __ondisposed__(self) -> None:
        key = self.owner__internal__
        obj = self._owners.get(key)
        if obj is not None:
            from bpy import msgbus
            del self._owners[key]
            msgbus.clear_by_owner(obj)
