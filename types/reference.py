
from typing import Iterable, Optional, TYPE_CHECKING, Set
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, StringProperty
from .system_struct import SystemStruct
if TYPE_CHECKING:
    from .system_object import SystemObject

class Reference(SystemStruct, PropertyGroup):

    path: StringProperty(
        name="Path",
        get=lambda self: self.get("path", ""),
        options={'HIDDEN'}
        )

    tags__internal__: CollectionProperty(
        name="Tags",
        type=PropertyGroup,
        options={'HIDDEN'}
        )

    @property
    def tags(self) -> Set[str]:
        return set(self.tags__internal__.keys())

    def __bool__(self) -> bool:
        return bool(self.path)

    def __call__(self) -> 'SystemObject':
        return self.id_data.path_resolve(self.path)

    def __init__(self,
                 data: 'SystemObject',
                 name: Optional[str]="",
                 tags: Optional[Iterable[str]]=None) -> None:
        self["name"] = name
        self["path"] = data.path
        if tags:
            for tag in set(tags):
                self.tags__internal__.add()["name"] = tag
