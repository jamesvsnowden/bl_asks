
from typing import Callable, Dict, Tuple, Type, Union, TYPE_CHECKING
from inspect import isclass
from bpy.types import PropertyGroup
from bpy.props import PointerProperty, StringProperty
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

    @property
    def handler(self) -> Callable:
        return self.system.handlers__internal__[self.handler__internal__]

    type__internal__: StringProperty(options={'HIDDEN'})

    def __init__(self,
                 entity: 'Entity',
                 handler: Callable,
                 *args: Union[Tuple[Type[Component]], Tuple[Component, ...]],
                 **kwargs: Dict[str, Component]) -> None:
        self["name"] = kwargs.pop("name", "")
        self.entity.__init__(entity)
        self.handler__internal__ = handler.ASKS_ID

        arguments = self.arguments.collection__internal__

        if len(args) == 1 and isclass(args[0]):
            cls = args[0]
            key = cls.SYSTEM_PATH
            self.type__internal__ = key
            for component in entity.components(cls):
                arguments.add().__init__(component)
        else:
            for component in args:
                arguments.add().__init__(component)
            for name, component in kwargs.items():
                arguments.add().__init__(component, name)

    def process(self) -> None:
        args = []
        kwds = {}
        for name, component in self.arguments.items():
            if name:
                kwds[name] = component
            else:
                args.append(component)
        self.handler(self.entity(), *args, **kwds)