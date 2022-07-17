
from typing import Any, Dict, Iterator, List, Optional, Union
from bpy.types import PropertyGroup, ShapeKey
from bpy.props import CollectionProperty, IntProperty
from .system_struct import SystemStruct
from .reference import Reference
from .entity import Entity

class SystemEntities(SystemStruct, PropertyGroup):

    reverselut__internal__: CollectionProperty(
        type=Reference,
        options={'HIDDEN'}
        )

    collection__internal__: CollectionProperty(
        type=Entity,
        options={'HIDDEN'}
        )

    active_index: IntProperty(
        name="Shape Key",
        min=0,
        default=0,
        options=set()
        )

    @property
    def active(self) -> Optional[Entity]:
        index = self.active_index
        if index < len(self):
            return self.collection__internal__[index]

    def __contains__(self, key: Union[str, ShapeKey]) -> bool:
        if isinstance(key, ShapeKey):
            key = key.name
        if isinstance(key, str):
            return key in self.reverselut__internal__
        raise TypeError()

    def __getitem__(self, key: Union[str, ShapeKey, int, slice]) -> Union[Entity, List[Entity]]:
        if isinstance(key, ShapeKey):
            key = key.name
        if isinstance(key, str):
            return self.reverselut__internal__[key]()
        if isinstance(key, (int, slice)):
            return self.collection__internal__[key]
        raise TypeError()

    def __iter__(self) -> Iterator['Entity']:
        return iter(self.collection__internal__)

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def ensure(self, shapekey: ShapeKey) -> Entity:
        return self.get(shapekey) or self.create(shapekey)

    def get(self, key: Union[str, ShapeKey], default: Optional[Any]=None) -> Any:
        if isinstance(key, ShapeKey):
            key = key.name
        if isinstance(key, str):
            ref = self.reverselut__internal__.get(key)
            return default if ref is None else ref() or default
        raise TypeError()

    def create(self, shapekey: ShapeKey, **properties: Dict[str, Any]) -> Entity:
        if not isinstance(shapekey, ShapeKey):
            raise TypeError()
        if shapekey.id_data != self.id_data:
            raise ValueError()
        if shapekey in self:
            raise ValueError()
        entity = self.collection__internal__.add()
        entity.__init__(shapekey, **properties)
        entity["index"] = len(self) - 1
        entity["depth"] = 0
        self.reverselut__internal__.add().__init__(entity, name=shapekey.name)
        return entity

    def delete(self, entity: Entity) -> None:
        pass