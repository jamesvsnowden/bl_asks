
from typing import Callable, Type, TYPE_CHECKING
from uuid import uuid4
from bpy.types import Key
from bpy.app.handlers import persistent
from .types.component import Component
if TYPE_CHECKING:
    from bpy.types import UILayout
    from .types.entity import Entity
    from .types.system import System


@persistent
def _on_file_load(_) -> None:
    import bpy
    for key in bpy.data.shape_keys:
        if key.is_property_set("asks"):
            for component in key.asks.components:
                component.__onfileload__()


def _registered_system() -> Type['System']:
    if not hasattr(Key, "ASKS"):

        from logging import getLogger
        from bpy.utils import register_class
        from bpy.props import CollectionProperty, PointerProperty
        from bpy.app.handlers import load_post
        from .types.reference import Reference
        from .types.component_entities import ComponentEntities
        from .types.processor_arguments import ProcessorArguments
        from .types.processor import Processor
        from .types.entity_processors import EntityProcessors
        from .types.entity_operation import EntityOperation
        from .types.entity_operations import EntityOperations
        from .types.shape_target_component import ShapeTargetComponent
        from .types.shape_weight_component import ShapeWeightComponent
        from .types.id_property_component import IDPropertyComponent
        from .types.entity_components import EntityComponents
        from .types.entity import Entity
        from .types.system_components import SystemComponents
        from .types.system_entities import SystemEntities

        for cls in (
                Reference,
                ComponentEntities,
                ProcessorArguments,
                Processor,
                EntityProcessors,
                EntityOperation,
                EntityOperations,
                ShapeTargetComponent,
                ShapeWeightComponent,
                IDPropertyComponent,
                EntityComponents,
                Entity,
                SystemComponents,
                SystemEntities
            ):
            register_class(cls)

        for cls in (
                ShapeTargetComponent,
                ShapeWeightComponent,
                IDPropertyComponent,
                ):
            path = cls.SYSTEM_PATH
            System.components__internal__[path] = cls
            setattr(System, path, CollectionProperty(type=cls, options={'HIDDEN'}))

        Key.ASKS = System
        Key.asks = PointerProperty(
            name="ASKS",
            description="Advanced shape key system",
            type=System,
            options=set()
            )

        System.log = getLogger("asks")
        load_post.append(_on_file_load)

    return Key.ASKS


def register_component(cls: Type[Component]) -> None:
    if not issubclass(cls, Component):
        raise TypeError()
    
    if not cls.SYSTEM_PATH:
        import re
        import bpy

        asks = _registered_system()
        path = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        path = f'{path}{"s" if path.endswith("_component") else "_components"}'
        path = f'{path}__internal__'

        bpy.utils.register_class(cls)
        cls.SYSTEM_PATH = path
        asks.components__internal__[path] = cls
        setattr(asks, path, bpy.props.CollectionProperty(type=cls, options={'HIDDEN'}))


def register_draw_handler(handler: Callable[['UILayout', 'Entity'], None]) -> None:
    if not callable(handler):
        raise TypeError()

    key = getattr(handler, "ASKS_ID", "")
    if not key:
        key = f'ASKS_{uuid4()}'
        handler.AKS_ID = key
        _registered_system().draw_funcs__internal__[key] = handler


def register_processor(function: Callable) -> None:
    if not callable(function):
        raise TypeError()

    key = getattr(function, "ASKS_ID", "")
    if not key:
        key = f'ASKS_{uuid4()}'
        function.ASKS_ID = key
        _registered_system().processors__internal__[key] = function