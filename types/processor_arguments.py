
from typing import TYPE_CHECKING
from bpy.types import PropertyGroup
from .system_struct import SystemStruct
from .reference_collection import ReferenceCollection
if TYPE_CHECKING:
    from .component import Component

class ProcessorArguments(ReferenceCollection['Component'], SystemStruct, PropertyGroup):

    pass
