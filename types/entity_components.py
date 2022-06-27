

from typing import Optional, TYPE_CHECKING
from bpy.types import PropertyGroup
from .system_struct import SystemStruct
from .component import Component
from .reference_collection import ReferenceCollection
if TYPE_CHECKING:
    from .entity import Entity


class EntityComponents(ReferenceCollection[Component], SystemStruct, PropertyGroup):

    @property
    def entity(self) -> 'Entity':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    def attach(self, component: Component, name: Optional[str]="") -> None:
        system = self.system
        entity = self.entity

        if not isinstance(component, Component):
            system.log.error(f'{component} is not a Component')
            return

        if component.system != system:
            system.log.error(f'{component} does not belong to the same system as {entity}')
            return

        if component in entity.components:
            system.log.warning(f'{component} is already attached to {entity}')
            return

        entity.components.collection__internal__.add().__init__(component, name)
        component.entities.collection__internal__.add().__init__(entity)

        key = component.SYSTEM_PATH
        processes = []
        for processor in entity.processors:
            if processor.type__internal__ == key:
                processor.arguments.collection__internal__.add().__init__(component)
                processes.append(processor)

        component.__onattached__(entity)

        for processor in processes:
            processor()

    def detach(self, component: Component) -> None:
        system = self.system
        entity = self.entity

        index = entity.components.find(component)
        
        if index == -1:
            system.log.warning(f'{component} is not attached to {entity}')
            return

        processes = []

        for processor in entity.processors:
            index = processor.arguments.find(component)
            if index != -1:
                processor.arguments.collection__internal__.remove(index)
                if component.SYSTEM_PATH == processor.type__internal__:
                    processes.append(processor)

        entity.components.components__internal__.remove(index)

        index = component.entities.find(entity)
        if index != -1:
            component.entities.collection__internal__.remove(index)

        component.__ondetached__(entity)

        if component.disposable and len(component.entities) == 0:
            system.components.remove(component)

        for processor in processes:
            processor()
