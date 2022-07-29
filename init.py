
from typing import Dict, Iterator, List, Optional, Union
from uuid import uuid4
from bpy.types import PropertyGroup, ShapeKey
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, PointerProperty, StringProperty
from bpy import msgbus
from rna_prop_ui import rna_idprop_ui_create


def _id(self) -> str:
    id_ = self.get("identifier", "")
    if not id_:
        id_ = str(uuid4())
        self["identifier"] = id_
    return id_


class Identifiable:

    identifier: StringProperty(
        name="Identifier",
        get=_id,
        options={'HIDDEN'}
        )


class SystemObject:

    @property
    def system(self) -> 'System':
        return self.id_data.asks


class MessageBroker(Identifiable, SystemObject):

    @property
    def message_bus_key(self) -> object:
        return self.system.internal__.key_mapping.setdefault(self.identifier, object())


class Point(PropertyGroup):

    pass


class Points(PropertyGroup):

    internal__: CollectionProperty(type=Point)


class Curve(PropertyGroup):

    points: PointerProperty(type=Points)


class Range(PropertyGroup):

    min: FloatProperty()

    max: FloatProperty()


class Ranges(PropertyGroup):

    x: PointerProperty(type=Range)

    y: PointerProperty(type=Range)


class Interpolation(PropertyGroup):

    curve: PointerProperty(type=Curve)

    range: PointerProperty(type=Ranges)


class Target(MessageBroker, PropertyGroup):
    pass


class Targets(PropertyGroup):

    internal__: CollectionProperty(type=Target)


class Variable(PropertyGroup):
    
    targets: PointerProperty(type=Targets)


class Variables(PropertyGroup):

    internal__: CollectionProperty(type=Variable)


class Parameter(PropertyGroup):
    # could be a reference to an id property or a shape key value
    pass


class Parameters(PropertyGroup):

    internal__: CollectionProperty(type=Parameter)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[Parameter, List[Parameter]]:
        return self.internal__[key]

    def __iter__(self) -> Iterator[Parameter]:
        return iter(self.internal__)

    def __len__(self) -> int:
        return len(self.internal__)


def weight_driver_expression_get(self) -> str:
    pass

def weight_driver_expression_set(self, value: str) -> None:
    pass


class WeightDriver(SystemObject, PropertyGroup):

    @property
    def data_path(self) -> str:
        path = f'["{self.name}"]'
        return f'key_blocks{path}.value' if self.get("type", 0) else path

    enabled: BoolProperty(
        name="Enabled",
        get=lambda self: self.get("enabled", False),
        options={'HIDDEN'}
        )

    expression: StringProperty(
        name="Expression",
        get=weight_driver_expression_get,
        set=weight_driver_expression_set,
        options=set()
        )

    interpolation: PointerProperty(
        name="Interpolation",
        type=Interpolation,
        options=set()
        )

    name: StringProperty(
        name="Name",
        get=lambda self: self.get("name", ""),
        options=set()
        )

    parameters: PointerProperty(
        name="Parameters",
        type=Parameters,
        options=set()
        )
   
    type: EnumProperty(
        name="Type",
        items=[
            ('INPUT', "Input", ""),
            ('VALUE', "Value", ""),
            ],
        get=lambda self: self.get("type", 0),
        options={'HIDDEN'}
        )
    
    variables: PointerProperty(
        name="Variables",
        type=Variables,
        options=set()
        )

    def __init__(self, type: str, name: str) -> None:
        self["name"] = name
        self["type"] = ('INPUT', 'VALUE').index(type)
        self["enabled"] = True

    def update(self) -> None:
        if self.enabled:
            drivers = self.id_data.animation_data_create().drivers
            path = self.data_path
            fcurve = drivers.find(path)
            if fcurve is None:
                fcurve = drivers.new(path)
            driver = fcurve.driver
            variables = driver.variables
            for variable in reversed(tuple(variables)):
                variables.remove()


def on_shape_key_name_update(node: 'Node') -> None:
    shape = node.shape_key
    if shape:
        for key in ("input", "value"):
            if node.is_property_set(key):
                driver: WeightDriver = getattr(node, key)
                if driver.enabled:
                    driver["name"] = shape.name


class Node(MessageBroker, PropertyGroup):
    
    input: PointerProperty(
        name="Input",
        type=WeightDriver,
        options=set()
        )

    @property
    def shape_key(self) -> Optional[ShapeKey]:
        return self.id_data.key_blocks.get(self.name)

    @property
    def is_valid(self) -> bool:
        return self.shape_key is not None

    value: PointerProperty(
        name="Value",
        type=WeightDriver,
        options=set()
        )

    def __load__(self) -> None:
        shape = self.shape_key
        if shape:
            msgbus.subscribe_rna(owner=self.message_bus_key,
                                 key=shape.path_resolve("name", False),
                                 notify=on_shape_key_name_update,
                                 args=(self,))



class Nodes(PropertyGroup):

    internal__: CollectionProperty(type=Node)


class SystemInternals(PropertyGroup):

    key_mapping: Dict[str, object] = {}


class System(PropertyGroup):

    internal__: PointerProperty(type=SystemInternals)

    nodes: PointerProperty(type=Nodes)