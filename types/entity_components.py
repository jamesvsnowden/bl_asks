

from typing import Optional, TYPE_CHECKING, Set
from bpy.types import PropertyGroup
from .system_struct import SystemStruct
from .component import Component
from .reference_collection import ReferenceCollection
if TYPE_CHECKING:
    from .processor_arguments import ProcessorArguments
    from .processor import Processor
    from .entity import Entity


class EntityComponents(ReferenceCollection[Component], SystemStruct, PropertyGroup):

    @property
    def entity(self) -> 'Entity':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    def attach(self, component: Component, name: Optional[str]="", tags: Optional[Set[str]]=None) -> None:

        if not isinstance(component, Component):
            raise TypeError((f'{self.__class__.__name__}.attach(component, name="", tags=None): '
                             f'Expected component to be Component, '
                             f'not {component.__class__.__name__}'))

        system = self.system
        entity = self.entity

        if component.system != system:
            raise ValueError((f'{self.__class__.__name__}.attach(component, name="", tags=None): '
                              f'{component} does not belong to the same system as {entity}'))

        if component in entity.components:
            raise ValueError((f'{self.__class__.__name__}.attach(component, name="", tags=None): '
                              f'{component} is already attached to {entity}'))

        entity.components.collection__internal__.add().__init__(component, name=name, tags=tags)
        component.entities.collection__internal__.add().__init__(entity, tags=tags)

        processes = []
        if tags:
            for processor in entity.processors:
                proc_tags = processor.tags
                if proc_tags and proc_tags.issubset(tags):
                    processor.arguments.collection__internal__.add().__init__(component)
                    processes.append(processor)

        component.__onattached__(entity)

        for processor in processes:
            processor()

    def detach(self, component: Component) -> None:
        
        if not isinstance(component, Component):
            raise TypeError((f'{self.__class__.__name__}.detach(component): '
                             f'Expected component to be Component, '
                             f'not {component.__class__.__name__}'))

        system = self.system
        entity = self.entity
        cindex = self.find(component)

        if cindex == -1:
            raise ValueError((f'{self.__class__.__name__}.detach(component): '
                              f'{component} is not a component of {entity}'))

        processes = []
        tags = component.tags
        if tags:
            processor: 'Processor'
            arguments: 'ProcessorArguments'

            for processor in entity.processors:
                proc_tags = processor.tags
                if proc_tags and proc_tags.issubset(tags):
                    arguments = processor.arguments
                    arg_index = arguments.find(component)
                    if arg_index != -1:
                        arguments.collection__internal__.remove(arg_index)
                        processes.append(processor)

        entity.components.components__internal__.remove(cindex)

        eindex = component.entities.find(entity)
        if eindex != -1:
            component.entities.collection__internal__.remove(eindex)

        component.__ondetached__(entity)

        if component.disposable and len(component.entities) == 0:
            system.components.remove(component)

        for processor in processes:
            processor()
