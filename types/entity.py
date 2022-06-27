
from typing import Any, Callable, Dict, Iterator, Optional, Type, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import IntProperty, PointerProperty, StringProperty
from .system_object import SystemObject
from .reference import Reference
from .entity_components import EntityComponents
from .entity_parameters import EntityParameters
from .id_property_component import IDPropertyComponent
from .shape_target_component import ShapeTargetComponent
from .entity_processors import EntityProcessors
from .entity_subtree import EntitySubtree
from .entity_children import EntityChildren
if TYPE_CHECKING:
    from bpy.types import Driver, FCurve, ShapeKey, UILayout
    from .component import Component


class Entity(SystemObject, PropertyGroup):

    SYSTEM_PATH = "entities.collection__internal__"

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

    drawhandler__internal__: StringProperty(
        default="",
        options={'HIDDEN'}
        )

    @property
    def draw_handler(self) -> Optional[Callable[['UILayout', 'Entity'], None]]:
        name = self.draw_funcs__internal__
        if name:
            return self.system.drawhandlers__internal__.get(name)

    @draw_handler.setter
    def draw_handler(self, handler: Callable[['UILayout', 'Entity'], None]):
        if not callable(handler):
            raise TypeError()
        name = getattr(handler, "ASKS_ID", "")
        if not name or name not in self.system.drawhandlers__internal__:
            raise ValueError()
        self.draw_funcs__internal__ = name

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

    tag: StringProperty(
        name="Tag",
        default="",
        options=set()
        )

    parameters: PointerProperty(
        name="Parameters",
        type=EntityParameters,
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

    shape: PointerProperty(
        name="Shape",
        type=Reference,
        options=set()
        )

    @property
    def subtree(self) -> EntitySubtree:
        return EntitySubtree(self)

    def draw(self, layout: 'UILayout') -> None:
        handler = self.draw_handler
        if handler:
            handler(layout, self)
        else:
            component: 'Component'
            for component in self.components:
                if not component.hide:
                    component.draw(layout, self)

    def driver(self, ensure: Optional[bool]=True) -> Optional['Driver']:
        fcurve = self.fcurve(ensure)
        if fcurve is not None:
            return fcurve.driver

    def fcurve(self, ensure: Optional[bool]=True) -> Optional['FCurve']:
        animdata = self.id_data.animation_data
        if animdata is None:
            if not ensure: return
            animdata = self.id_data.animation_data_create()
        datapath = f'key_blocks["{self.shape().value}"].value'
        fcurve = animdata.drivers.find(datapath)
        if fcurve is None and ensure:
            fcurve = animdata.drivers.new(datapath)
        return fcurve

    def __init__(self, shapekey: 'ShapeKey', **properties: Dict[str, Any]) -> None:
        super().__init__()

        for key, value in properties.items():
            self[key] = value

        system = self.system

        target = system.create_component(ShapeTargetComponent, value=shapekey.name)
        target.entities.collection__internal__.add().__init__(self)
        self.shape.__init__(target, "shape")

        params = self.parameters.collection__internal__
        kwargs = dict(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=1.0)

        for _ in range(2):
            param = system.create_component(IDPropertyComponent, **kwargs)
            param.entities.collection__internal__.add().__init__(self)
            params.add().__init__(param)