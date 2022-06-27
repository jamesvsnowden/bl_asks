
from typing import Iterator, List, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from .entity import Entity

class EntitySubtree:

    def __init__(self, entity: 'Entity') -> None:
        self._entity = entity

    def __contains__(self, entity: 'Entity') -> bool:
        return any(x == entity for x in self)

    def __len__(self) -> int:
        owner = self._entity
        index = owner.index + 1
        depth = owner.depth
        count = 1
        items = owner.system.entities.collection__internal__
        limit = len(items)
        while index < limit:
            if items[index].depth <= depth: break
            count += 1
            index += 1
        return count

    def __iter__(self) -> Iterator['Entity']:
        owner = self._entity
        index = owner.index + 1
        depth = owner.depth
        items = owner.system.entities.collection__internal__
        limit = len(items)
        yield owner
        while index < limit:
            item = items[index]
            if item.depth <= depth: break
            yield item
            index += 1

    def __getitem__(self, key: Union[int, slice]) -> Union['Entity', List['Entity']]:
        return list(self)[key]
