
from typing import Callable, Sequence, Type, TYPE_CHECKING
from uuid import uuid4
from bpy.types import Context, Key, Object
from bpy.app.handlers import persistent
from .types.component import Component
if TYPE_CHECKING:
    from bpy.types import FCurve, UILayout
    from .types.curve_component import KeyframePoint
    from .types.entity import Entity
    from .types.system import System

COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}
COMPAT_OBJECTS = {'MESH', 'LATTICE', 'CURVE', 'SURFACE'}


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
        from .types.entity_parameters import EntityParameters
        from .types.entity_operation import EntityOperation
        from .types.entity_operations import EntityOperations
        from .types.shape_component import ShapeComponent
        from .types.value_component import ValueComponent
        from .types.id_property_component import IDPropertyComponent
        from .types.range_component import RangeComponent
        from .types.curve_component import (CurveComponentPoint,
                                            CurveComponentPoints,
                                            CurveComponent)
        from .types.curve_mapping_manager import (ASKS_OT_curve_point_handle_type_set,
                                                  ASKS_OT_curve_point_remove,
                                                  ASKS_OT_curve_reload,
                                                  CurveMappingManager)
        from .types.entity_components import EntityComponents
        from .types.entity import Entity
        from .types.entity_settings_panel import EntitySettingsPanel
        from .types.system_components import SystemComponents
        from .types.system_entities import SystemEntities
        from .types.system import System

        for cls in (
                Reference,
                ComponentEntities,
                ProcessorArguments,
                Processor,
                EntityProcessors,
                EntityParameters,
                EntityOperation,
                EntityOperations,
                ShapeComponent,
                ValueComponent,
                IDPropertyComponent,
                RangeComponent,
                CurveComponentPoint,
                CurveComponentPoints,
                CurveComponent,
                ASKS_OT_curve_point_handle_type_set,
                ASKS_OT_curve_point_remove,
                ASKS_OT_curve_reload,
                CurveMappingManager,
                EntityComponents,
                Entity,
                EntitySettingsPanel,
                SystemComponents,
                SystemEntities,
                System
            ):
            register_class(cls)

        for cls in (
                ShapeComponent,
                IDPropertyComponent,
                ValueComponent,
                CurveComponent,
                RangeComponent,
                ):
            System.components__internal__[cls.asks_idname] = cls
            setattr(System, cls.SYSTEM_PATH, CollectionProperty(type=cls, options={'HIDDEN'}))

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


def validate_context(context: Context) -> bool:
    return context.engine in COMPAT_ENGINES


def supports_shape_keys(object: Object) -> bool:
    return object.type in COMPAT_OBJECTS


def set_keyframe_points(fcurve: 'FCurve', points: Sequence['KeyframePoint']) -> None:

    frames = fcurve.keyframe_points
    length = len(frames)
    target = len(points)

    while length > target:
        frames.remove(frames[-1])
        length -= 1

    for index, point in enumerate(points):

        if index < length:
            frame = frames[index]
        else:
            frame = frames.insert(point.co[0], point.co[1])
            length += 1

        frame.interpolation = point.interpolation
        frame.easing = point.easing
        frame.co = point.co
        frame.handle_left_type = point.handle_left_type
        frame.handle_right_type = point.handle_right_type
        frame.handle_left = point.handle_left
        frame.handle_right = point.handle_right


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
        asks.components__internal__[cls.asks_idname] = cls
        setattr(asks, path, bpy.props.CollectionProperty(type=cls, options={'HIDDEN'}))


def register_draw_handler(handler: Callable[['UILayout', 'Entity'], None]) -> None:
    if not callable(handler):
        raise TypeError()

    key = getattr(handler, "ASKS_ID", "")
    if not key:
        key = f'ASKS_{uuid4()}'
        handler.ASKS_ID = key
        _registered_system().draw_funcs__internal__[key] = handler


def register_processor(function: Callable) -> None:
    if not callable(function):
        raise TypeError()

    key = getattr(function, "ASKS_ID", "")
    if not key:
        key = f'ASKS_{uuid4()}'
        function.ASKS_ID = key
        _registered_system().processors__internal__[key] = function