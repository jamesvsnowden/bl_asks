
from typing import Any,Iterator, List, Optional, Union
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty
from .system_struct import SystemStruct
from .entity_operation import EntityOperation


class EntityOperations(SystemStruct, PropertyGroup):

    collection__internal__: CollectionProperty(
        type=EntityOperation,
        options=set()
        )

    def __contains__(self, key: Union[str, EntityOperation]) -> bool:
        if isinstance(key, str): return key in self.collection__internal__
        if isinstance(key, EntityOperation): return any(x == key for x in self.collection__internal__)
        raise TypeError()

    def __getitem__(self, key: Union[str, int, slice]) -> Union[EntityOperation, List[EntityOperation]]:
        return self.collection__internal__[key]

    def __iter__(self) -> Iterator[EntityOperation]:
        return iter(self.collection__internal__)

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def find(self, key: Union[str, EntityOperation]) -> int:
        if isinstance(key, str): return self.collection__internal__.find(key)
        if isinstance(key, EntityOperation): return next((i for i, x in self if x == key), -1)
        raise TypeError()

    def get(self, name: str, default: Optional[Any]=None) -> Any:
        return self.collection__internal__.get(name, default)

    def items(self) -> Iterator[str, EntityOperation]:
        return self.collection__internal__.items()

    def keys(self) -> Iterator[str]:
        return self.collection__internal__.keys()

    def new(self, name: str, icon: Optional[int]=0, text: Optional[str]="") -> EntityOperation:
        if name in self.collection__internal__:
            raise ValueError()
        operation = self.collection__internal__.add()
        operation.__init__(name, icon, text)
        return operation

    def remove(self, operation: EntityOperation) -> None:
        if not isinstance(operation, EntityOperation):
            raise TypeError()
        index = self.find(operation)
        if index == -1:
            raise ValueError()
        self.collection__internal__.remove(index)
