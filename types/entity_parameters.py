
from bpy.types import PropertyGroup
from .system_struct import SystemStruct
from .reference_collection import ReferenceCollection
from .id_property_component import IDPropertyComponent

class EntityParameters(ReferenceCollection[IDPropertyComponent], SystemStruct, PropertyGroup):

    pass
