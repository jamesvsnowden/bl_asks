
from typing import Callable, Iterator, Optional, TYPE_CHECKING, Set
from uuid import uuid4
from bpy.types import PropertyGroup
from bpy.props import IntProperty, PointerProperty, StringProperty
from .system_object import SystemObject
from .shape_component import ShapeComponent
from .id_property_component import IDPropertyComponent
from .entity_components import EntityComponents
from .entity_processors import EntityProcessors
from .entity_subtree import EntitySubtree
from .entity_children import EntityChildren
from .entity_draw_controller import EntityDrawController
if TYPE_CHECKING:
    from bpy.types import Driver, FCurve, ShapeKey


class Entity(SystemObject, PropertyGroup):

    @property
    def ancestors(self) -> Iterator['Entity']:
        pass

    components: PointerProperty(
        name="Components",
        type=EntityComponents,
        options=set()
        )
    
    @property
    def children(self) -> EntityChildren:
        return EntityChildren(self)

    depth: IntProperty(
        name="Depth",
        get=lambda self: self.get("depth", 0),
        options={'HIDDEN'}
        )

    @property
    def descendants(self) -> Iterator['Entity']:
        subtree = iter(self.subtree)
        next(subtree)
        yield from subtree

    draw: PointerProperty(
        name="Draw",
        type=EntityDrawController,
        options=set()
        )

    icon: IntProperty(
        name="Icon",
        default=176,
        options=set()
        )

    index: IntProperty(
        name="Index",
        get=lambda self: self.get("index", 0),
        options={'HIDDEN'}
        )

    influence: PointerProperty(
        name="Influence",
        type=IDPropertyComponent,
        options=set()
        )

    @property
    def parent(self) -> Optional['Entity']:
        if self.depth:
            index = self.index
            if index > 0:
                items = self.system.entities.collection__internal__
                while index > 0:
                    item = items[index]

    processors: PointerProperty(
        name="EntityProcessors",
        type=EntityProcessors,
        options=set()
        )

    weight: PointerProperty(
        name="Weight",
        type=IDPropertyComponent,
        options=set()
        )

    shape: PointerProperty(
        name="Shape",
        type=ShapeComponent,
        options=set()
        )

    type: StringProperty(
        name="Type",
        get=lambda self: self.get("type", ""),
        options=set()
        )

    @property
    def subtree(self) -> EntitySubtree:
        return EntitySubtree(self)

    def driver(self, ensure: Optional[bool]=True) -> Optional['Driver']:
        fcurve = self.fcurve(ensure)
        if fcurve is not None:
            return fcurve.driver

    def fcurve(self, ensure: Optional[bool]=True) -> Optional['FCurve']:
        animdata = self.id_data.animation_data
        if animdata is None:
            if not ensure: return
            animdata = self.id_data.animation_data_create()
        datapath = f'key_blocks["{self.shape.value}"].value'
        fcurve = animdata.drivers.find(datapath)
        if fcurve is None and ensure:
            fcurve = animdata.drivers.new(datapath)
        return fcurve

    def __init__(self,
                 data: 'ShapeKey',
                 type: Optional[str]='NONE',
                 icon: Optional[int]=0,
                 draw: Optional[Callable]=None) -> None:

        self["name"] = f'ASKS_{uuid4()}'
        self["path"] = f'asks.entities.collection__internal__["{self.name}"]'
        self["type"] = type
        self["icon"] = icon
    
        self.draw.entity__internal__ = self.name
        if draw:
            self.draw.handler = draw

        self.shape.__init__(
            name=f'ASKS_{uuid4()}',
            path=f'{self.path}.shape',
            value=data.name
            )

        self.influence.__init__(
            name=f'ASKS_{uuid4()}',
            path=f'{self.path}.influence',
            min=0.0,
            max=1.0,
            soft_min=0.0,
            soft_max=1.0,
            default=1.0
            )

        self.weight.__init__(
            name=f'ASKS_{uuid4()}',
            path=f'{self.path}.weight',
            min=0.0,
            max=1.0,
            soft_min=0.0,
            soft_max=1.0,
            default=1.0
            )

        self.shape.entities.collection__internal__.add().__init__(self)
        self.influence.entities.collection__internal__.add().__init__(self)
        self.weight.entities.collection__internal__.add().__init__(self)
