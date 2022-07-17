
from typing import Any, Dict, Iterator, Union
from itertools import chain
from uuid import uuid4
from bpy.types import PropertyGroup
from .system_struct import SystemStruct
from .component import Component
from .entity import Entity


class SystemComponents(SystemStruct, PropertyGroup):

    def __call__(self, key: Union[str, Entity]) -> Iterator[Component]:
        if isinstance(key, Entity):
            return iter(key.components)
        if isinstance(key, str):
            path = self.system.components__internal__.get(key)
            if not path:
                raise ValueError()
            try:
                data = self.id_data.path_resolve(path)
            except ValueError:
                raise RuntimeError()
            else:
                return iter(data)
        raise TypeError((f'{self.__class__.__name__}(key): '
                         f'Expected key to be Entity or str, not {key.__class__.__name__}'))

    def __contains__(self, component: Component) -> bool:
        return isinstance(component, Component) and component.system == self.system

    def __iter__(self) -> Iterator[Component]:
        return chain(*[self(key) for key in self.system.components__internal__.keys()])

    def create(self, type: str, **properties: Dict[str, Any]) -> Component:
        path = self.system.components__internal__.get(type)
        if not path:
            raise ValueError((f'{self.__class__.__name__}.create(type, **properties): '
                              f'type "{type}" if not a recognized component type.'))
        try:
            data = self.id_data.path_resolve(path)
        except ValueError:
            raise RuntimeError((f'{self.__class__.__name__}.create(type, **properties): '
                                f'Failed to resolve component collection at path: "{path}"'))
        else:
            component = data.add()
            component["type"] = type
            component["name"] = f'ASKS_{uuid4()}'
            component["path"] = f'{path}["{component.name}"]'
            component.__init__(**properties)
            return component

    def delete(self, component: Component) -> None:
        pass