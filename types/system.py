
from bpy.types import PropertyGroup
from bpy.props import PointerProperty
from .curve_mapping_manager import CurveMappingManager
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

    curve_mapping_manager: PointerProperty(
        name="Curve Mapping Manager",
        type=CurveMappingManager,
        options=set()
        )

    entities: PointerProperty(
        name="Entities",
        type=SystemEntities,
        options=set()
        )
