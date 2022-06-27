
from typing import Callable, Dict, TYPE_CHECKING, Type
from bpy.types import PropertyGroup
from bpy.props import PointerProperty
from .system_components import SystemComponents
from .system_entities import SystemEntities
if TYPE_CHECKING:
    from logging import Logger
    from bpy.types import UILayout
    from .component import Component
    from .entity import Entity

class System(PropertyGroup):

    draw_funcs__internal__: Dict[str, Callable[['UILayout', 'Entity'], None]] = {}
    components__internal__: Dict[str, Type['Component']] = {}
    processors__internal__: Dict[str, Callable] = {}
    log: 'Logger' = None

    components: PointerProperty(
        name="Components",
        type=SystemComponents,
        options=set()
        )

    entities: PointerProperty(
        name="Entities",
        type=SystemEntities,
        options=set()
        )
