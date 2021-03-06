
from typing import Any, Dict, Optional, TYPE_CHECKING
from bpy.props import BoolProperty, PointerProperty, StringProperty
from .system_object import SystemObject
from .reference import Reference
from .component_entities import ComponentEntities
if TYPE_CHECKING:
    from bpy.types import UILayout
    from .entity import Entity

class Component(SystemObject):

    asks_options = set()

    disposable: BoolProperty(
        default=False,
        options=set()
        )

    entities: PointerProperty(
        name="Entities",
        type=ComponentEntities,
        options=set()
        )

    hide: BoolProperty(
        name="Hide",
        default=False,
        options=set()
        )

    label: StringProperty(
        name="Label",
        default="",
        options=set()
        )

    mirror: PointerProperty(
        name="Mirror",
        type=Reference,
        options=set()
        )

    mirroring__internal__: BoolProperty(
        get=lambda self: self.get("mirroring__internal__", False),
        options={'HIDDEN'}
        )

    type: StringProperty(
        name="Type",
        get=lambda self: self.get("type", ""),
        options={'HIDDEN'}
        )

    def draw(self, layout: 'UILayout', label: Optional[str]=None) -> None:
        pass

    # draw_symmetry_options(layout: 'UILayout') -> None

    def duplicate(self, mirror: bool) -> 'Component':
        return self.system.components.create(self.type, **self.__properties__(mirror))

    def process(self) -> None:
        for entity in self.entities:
            for process in entity.processors(self):
                process()

    def __init__(self, **properties: Dict[str, Any]) -> None:
        for key, value in properties.items():
            self[key] = value

    def __onfileload__(self) -> None:
        pass

    def __onattached__(self, entity: 'Entity') -> None:
        pass

    def __ondetached__(self, entity: 'Entity') -> None:
        pass

    def __ondisposed__(self) -> None:
        pass

    def __onsymmetry__(self, symtarget: 'Component') -> None:
        pass

    def __properties__(self, mirror: bool) -> Dict[str, Any]:
        return {
            "hide": self.hide,
            "disposable": self.disposable,
            "label": self.label
            }

    def __str__(self) -> str:
        return f'{self.__class__.__name__}@{self.path}'
