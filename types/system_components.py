
from typing import Any, Dict, Iterator, Type, Union
from itertools import chain
from bpy.types import PropertyGroup
from .system_struct import SystemStruct
from .component import Component
from .entity import Entity


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

    def create(self, type: str, **properties: Dict[str, Any]) -> Component:
        cls = self.system.components__internal__.get(type)
        if cls is None:
            raise KeyError()
        try:
            collection = self.system.path_resolve(cls.SYSTEM_PATH)
        except ValueError:
            raise TypeError()
        else:
            component = collection.add()
            component.__init__(**properties)
            return component

    def delete(self, component: Component) -> None:
        pass