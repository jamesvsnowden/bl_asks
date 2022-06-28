
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Type, Union, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty
from .system_struct import SystemStruct
from .processor import Processor
if TYPE_CHECKING:
    from .component import Component

class EntityProcessors(SystemStruct, PropertyGroup):

    collection__internal__: CollectionProperty(
        type=Processor,
        options={'HIDDEN'}
        )

    def __call__(self, component: 'Component') -> Iterator[Processor]:
        for processor in self.collection__internal__:
            if component in processor.arguments:
                yield processor

    def __contains__(self, key: Union[str, Processor]) -> bool:
        if isinstance(key, str): return key in self.collection__internal__
        if isinstance(key, Processor): return any(x == key for x in self)
        raise TypeError()

    def __getitem__(self, key: Union[str, int, slice]) -> Union[Processor, List[Processor]]:
        return self.collection__internal__[key]

    def __iter__(self) -> Iterator[Processor]:
        return iter(self.collection__internal__)

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def find(self, key: Union[str, Processor]) -> int:
        if isinstance(key, str): return self.collection__internal__.find(key)
        if isinstance(key, Processor): return next((i for i, x in enumerate(self) if x == key), -1)
        raise TypeError()

    def get(self, name: str, default: Optional[Any]=None) -> Any:
        return self.collection__internal__.get(name, default)

    def items(self) -> Iterator[Tuple[str, Processor]]:
        return self.collection__internal__.items()

    def keys(self) -> Iterator[str]:
        return self.collection__internal__.keys()

    def assign(self,
               handler: Callable,
               *args: Union[Tuple[Type['Component']], Tuple['Component', ...]],
               **kwargs: Dict[str, 'Component']) -> Processor:

        if not callable(handler):
            raise TypeError()

        if not getattr(handler, 'ASKS_ID', ""):
            raise ValueError()

        path: str = self.path_from_id()
        entity = self.id_data.path_resolve(path.rpartition(".")[0])

        processor = self.collection__internal__.add()
        processor.__init__(entity, handler, *args, **kwargs)

        return processor

    def remove(self, processor: Processor) -> None:
        if not isinstance(processor, Processor):
            raise TypeError()
        index = self.find(processor)
        if index == -1:
            raise ValueError()
        self.collection__internal__.remove(index)

    def values(self) -> Iterator[Processor]:
        return self.collection__internal__.values()