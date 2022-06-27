
from bpy.types import PropertyGroup
from bpy.props import PointerProperty
from .system_components import SystemComponents
from .system_entities import SystemEntities

class System(PropertyGroup):

    draw_funcs__internal__ = {}
    components__internal__ = {}
    processors__internal__ = {}
    log = None

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
