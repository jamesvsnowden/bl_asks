
from typing import Iterator, List, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from .entity import Entity


class EntityChildren:

    def __init__(self, entity: 'Entity') -> None:
        self._entity = entity

    def __contains__(self, key: 'Entity') -> bool:
        return any(x == key for x in self)

    def __iter__(self) -> Iterator['Entity']:
        owner = self._entity
        items = owner.system.entities.collection__internal__
        index = owner.index + 1
        depth = owner.depth + 1
        count = len(items)
        while index < count:
            x = items[index]
            d = x.depth
            if d <  depth: break
            if d == depth: yield x
            index += 1

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __bool__(self) -> bool:
        return any(self)

    def __getitem__(self, key: Union[int, slice]) -> Union['Entity', List['Entity']]:
        return list(self)[key]

    def append(self, entity: 'Entity') -> None:
        pass

    def find(self, entity: 'Entity') -> int:
        return next((i for i, x in enumerate(self) if x == entity), -1)

    def insert(self, index: int, entity: 'Entity') -> None:
        pass

    def move(self, from_index: int, to_index: int) -> None:
        pass

    def remove(self, entity: 'Entity') -> None:
        pass