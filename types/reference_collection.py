

from typing import Any, Generic, Iterator, List, Optional, Tuple, Type, TypeVar, Union
from bpy.props import CollectionProperty
from .system_object import SystemObject
from .reference import Reference

T = TypeVar("T", bound=SystemObject)

class ReferenceCollection(Generic[T]):

    collection__internal__: CollectionProperty(
        type=Reference,
        options={'HIDDEN'}
        )

    def __call__(self, type: Type[T]) -> Iterator[T]:
        return filter(lambda x: isinstance(x, type), self)

    def __contains__(self, key: Union[str, T, Type[T]]) -> bool:
        if isinstance(key, str): return key in self.collection__internal__
        if isinstance(key, T): return any(x == key for x in self)
        if issubclass(key, T): return any(isinstance(x, key) for x in self)
        raise TypeError()

    def __iter__(self) -> Iterator[T]:
        return map(Reference.__call__, self.collection__internal__)

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[T, List[T]]:
        if isinstance(key, (str, int)):
            return self.collection__internal__[key]()
        elif isinstance(key, slice):
            return map(Reference.__call__, self.collection__internal__[key])
        else:
            raise TypeError()

    def __bool__(self) -> bool:
        return len(self) > 0

    def find(self, key: Union[str, T]) -> int:
        if isinstance(key, str): return self.collection__internal__.find(key)
        if isinstance(key, T): return next((i for i, x in enumerate(self) if x == key), -1)
        raise TypeError()

    def get(self, name: str, default: Optional[Any]=None) -> Any:
        reference = self.collection__internal__.get(name)
        return default if reference is None else reference()

    def items(self) -> Iterator[Tuple[str, T]]:
        for name, reference in self.collection__internal__:
            yield name, reference()

    def keys(self) -> Iterator[str]:
        return self.collection__internal__.keys()

    def values(self) -> Iterator[T]:
        return iter(self)
