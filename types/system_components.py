
from typing import Any, Dict, Iterator, Type, TypeVar, Union
from itertools import chain
from bpy.types import PropertyGroup
from .system_struct import SystemStruct
from .component import Component
from .entity import Entity

T = TypeVar("T", bound=Component)

class SystemComponents(SystemStruct, PropertyGroup):

    def __call__(self, key: Union[Type[Component], Entity]) -> Iterator[Component]:
        if isinstance(key, Entity):
            return iter(key.components)
        if issubclass(key, Component):
            try:
                collection = self.system.path_resolve(key.SYSTEM_PATH)
            except ValueError():
                raise TypeError()
            else:
                return iter(collection)
        raise TypeError()

    def __contains__(self, component: Component) -> bool:
        return isinstance(component, Component) and component.system == self.system

    def __iter__(self) -> Iterator[Component]:
        system = self.system
        return chain(*[getattr(system, k) for k in system.components__internal__.keys()])

    def create(self, type: Type[T], **properties: Dict[str, Any]) -> T:
        if not issubclass(type, Component):
            raise TypeError()
        try:
            collection = self.system.path_resolve(type.SYSTEM_PATH)
        except ValueError:
            raise TypeError()
        else:
            component: T = collection.add()
            component.__init__(**properties)
            return component

    def delete(self, component: Component) -> None:
        pass