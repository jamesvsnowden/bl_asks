
from typing import Callable, Dict, Set, Tuple, Type, Union, TYPE_CHECKING
from inspect import isclass
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, CollectionProperty, PointerProperty, StringProperty
from .system_struct import SystemStruct
from .reference import Reference
from .processor_arguments import ProcessorArguments
if TYPE_CHECKING:
    from .component import Component
    from .entity import Entity

class Processor(SystemStruct, PropertyGroup):

    arguments: PointerProperty(
        type=ProcessorArguments,
        options=set()
        )

    entity: PointerProperty(
        type=Reference,
        options=set()
        )

    handler__internal__: StringProperty(options={'HIDDEN'})

    init: BoolProperty(
        get=lambda self: self.get("is_init_function", False),
        options=set()
        )

    @property
    def handler(self) -> Callable:
        return self.system.processors__internal__[self.handler__internal__]

    tags__internal__: CollectionProperty(type=PropertyGroup, options={'HIDDEN'})

    @property
    def tags(self) -> Set[str]:
        return set(self.tags__internal__)

    def __init__(self,
                 entity: 'Entity',
                 handler: Callable,
                 *args: Union[Tuple[Set[str]], Tuple['Component', ...]],
                 **kwargs: Dict[str, Union[str, 'Component']]) -> None:
        self["name"] = kwargs.pop("name", "")
        self["init"] = kwargs.pop("init", False)
        self.entity.__init__(entity)
        self.handler__internal__ = handler.asks_id

        arguments = self.arguments.collection__internal__

        if len(args) == 1 and isinstance(args[0], set):
            tags = args[0]
            for tag in tags:
                self.tags__internal__.add().name = tag
            for component in entity.components(tags):
                arguments.add().__init__(component)
        else:
            for component in args:
                arguments.add().__init__(component)
            for name, component in kwargs.items():
                arguments.add().__init__(component, name)

    def __call__(self) -> None:
        args = []
        kwds = {}
        for name, reference in self.arguments.items(dereference=False):
            try:
                value = reference()
            except ValueError:
                value = None
            if name:
                kwds[name] = value
            else:
                args.append(value)
        self.handler(self.entity(), *args, **kwds)