
from ctypes import Union
from typing import Iterable, Iterator, Set, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty
from .system_struct import SystemStruct
if TYPE_CHECKING:
    from .component import Component
    from .processor import Processor


def component_tags_update(tags: 'ComponentTags') -> None:
    path: str = tags.path_from_id()
    component: 'Component' = tags.id_data.path_resolve(path.rpartition(".")[0])
    processor: 'Processor'
    data = set(tags)
    for entity in component.entities:
        for processor in entity.processors:
            query = processor.tags__internal__
            if len(query):
                args = processor.arguments
                index = args.find(component)
                if set(query).issubset(data):
                    if index == -1:
                        args.collection__internal__.add().__init__(component)
                elif index != -1:
                    args.collection__internal__.remove(index)


class ComponentTags(SystemStruct, PropertyGroup):

    collection__internal__: CollectionProperty(
        type=PropertyGroup,
        options={'HIDDEN'}
        )

    def __init__(self) -> 

    def __contains__(self, tag: str) -> bool:
        return tag in self.collection__internal__

    def __bool__(self) -> bool:
        return len(self) > 0

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __iter__(self) -> Iterator[str]:
        return self.collection__internal__.keys()

    def __eq__(self, other: Set[str]) -> bool:
        return set(self) == other

    def __le__(self, other: Set[str]) -> bool:
        return set(self) <= other

    def __lt__(self, other: Set[str]) -> bool:
        return set(self) < other

    def __ge__(self, other: Set[str]) -> bool:
        return set(self) >= other

    def __gt__(self, other: Set[str]) -> bool:
        return set(self) > other
