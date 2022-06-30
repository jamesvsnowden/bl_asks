
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Sequence, Tuple, Type, TYPE_CHECKING
from contextlib import suppress
from uuid import uuid4
from bpy.types import Context, Key, Object, Operator, PropertyGroup, MESH_MT_shape_key_context_menu
from bpy.props import CollectionProperty, PointerProperty
from bpy.utils import register_class, unregister_class
from bpy.app.handlers import load_post, persistent
from .types.component import Component
if TYPE_CHECKING:
    from bpy.types import FCurve, Menu, UILayout
    from .types.curve_component import KeyframePoint
    from .types.entity import Entity
    from .types.system import System

_namespaces = {}
_menu_items = []
COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}
COMPAT_OBJECTS = {'MESH', 'LATTICE', 'CURVE', 'SURFACE'}
SYM_AFIX_SEPRS = (".", " ", "-", "_")
SYM_AFIX_PAIRS = (
    ("l", "r"), ("r", "l"),
    ("L", "R"), ("R", "L"),
    ("left", "right"), ("right", "left"),
    ("Left", "Right"), ("Right", "Left"),
    ("LEFT", "RIGHT"), ("RIGHT", "LEFT"),
    ("RIGHT", "LEFT"), ("Left", "Right"),
    )
SYM_SFIX_LUT = {f'{a}{sep}': f'{b}{sep}' for a, b in SYM_AFIX_PAIRS for sep in SYM_AFIX_SEPRS}
SYM_PFIX_LUT = {f'{sep}{a}': f'{sep}{b}' for a, b in SYM_AFIX_PAIRS for sep in SYM_AFIX_SEPRS}


@persistent
def _on_file_load(_) -> None:
    import bpy
    for key in bpy.data.shape_keys:
        if key.is_property_set("asks"):
            for component in key.asks.components:
                component.__onfileload__()


@dataclass
class MenuItem:
    id: str
    text: str = ""
    icon: str = ""


def _draw_menu_items(menu: 'Menu', context:Context) -> None:
    layout = menu.layout
    for group in _menu_items.values():
        layout.separator()
        for item in group:
            layout.operator(item.id, text=item.label, icon=item.icon)


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


def _sympfix(name: str) -> str:
    return next((afix for afix in SYM_SFIX_LUT if name.startswith(afix)), "")


def _symsfix(name: str) -> str:
    return next((afix for afix in SYM_PFIX_LUT if name.endswith(afix)), "")


def split_symmetrical(name: str) -> Tuple[str, str, str]:
    """
    Splits the data block name into its symmetrical prefix, base name and symmetrical suffix.
    """
    assert isinstance(name, str)
    afix = _symsfix(name)
    if afix:
        return "", name[:-len(afix)], afix
    afix = _sympfix(name)
    if afix:
        return afix, name[len(afix)], ""
    return "", name, ""

class namespace:

    def __new__(cls: Type['namespace'], name: str) -> None:

        if not isinstance(name, str):
            raise TypeError()

        if name in _namespaces:
            return _namespaces[name]
        
        if not hasattr(Key, "ASKS"):
            from logging import getLogger
            from .types.reference import Reference
            from .types.component_entities import ComponentEntities
            from .types.processor_arguments import ProcessorArguments
            from .types.processor import Processor
            from .types.entity_processors import EntityProcessors
            from .types.entity_parameters import EntityParameters
            from .types.entity_operation import EntityOperation
            from .types.entity_operations import EntityOperations
            from .types.entity_draw_controller import EntityDrawController
            from .types.shape_component import ShapeComponent
            from .types.id_property_component import IDPropertyComponent
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

            classes = (
                Reference,
                ComponentEntities,
                ProcessorArguments,
                Processor,
                EntityProcessors,
                EntityParameters,
                EntityOperation,
                EntityOperations,
                EntityDrawController,
                ShapeComponent,
                IDPropertyComponent,
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
            )

            for cls_ in classes:
                register_class(cls_)

            System.CLASSES = classes
            Key.ASKS = System
            Key.asks = PointerProperty(
                name="ASKS",
                description="Advanced shape key system",
                type=System,
                options=set()
                )

            System.log = getLogger("asks")
            load_post.append(_on_file_load)
            MESH_MT_shape_key_context_menu.append(_draw_menu_items)

        return super(namespace, cls).__new__(cls)

    def __init__(self, name: str) -> None:
        self._name = name
        self._type = None
        self._menu_items = []
        self._components = {}
        self._processors = set()
        self._draw_funcs = set()
        _namespaces[name] = self

    def add_component(self, key: str, cls: Type['Component']) -> None:
        assert self._type is None
        self._components[key] = cls

    def add_processor(self, func: Callable) -> None:
        assert self._type is None
        func.asks_ns = self._name
        func.asks_id = str(uuid4())
        self._processors.add(func)

    def add_draw_handler(self, func: Callable) -> None:
        assert self._type is None
        func.asks_ns = self._name
        func.asks_id = str(uuid4())
        self._draw_funcs.add(func)

    def add_context_menu_item(self,
                              cls: Type[Operator],
                              text: Optional[str]=None,
                              icon: Optional[str]='NONE') -> None:
        if not issubclass(cls, Operator):
            raise TypeError()
        if text is None:
            text = cls.bl_label
        self._menu_items.append((MenuItem(cls.bl_idname, text=text, icon=icon), cls))

    def register(self) -> None:
        assert self._type is None

        data = {}
        asks = self._asks
        name = self._name
        menu = self._menu

        for key, cls in self._components.items():
            cls._users = getattr(cls, "_users", 0) + 1
            prop = f'{key}_components'
            asks.components__internal__[f'{name}.{key}'] = prop
            with suppress(ValueError): register_class(cls)
            data[prop] = CollectionProperty(type=cls, options={'HIDDEN'})

        for func in self._processors:
            asks.processors__internal__[func.asks_id] = func

        for func in self._draw_funcs:
            asks.draw_funcs__internal__[func.asks_id] = func

        if menu:
            items = []
            for item, cls in menu:
                items.append(item)
                with suppress(ValueError): register_class(cls)
                cls._users = getattr(cls, "_users", 0) + 1
            _menu_items[name] = items

        cls = self._type = type(name, (PropertyGroup,), {"__annotations__": data})
        register_class(cls)
        setattr(Key, name, cls)

    def unregister(self) -> None:
        asks = self._asks
        name = self._name
        menu = self._menu_items

        for key, cls in self._components.items():
            prop = f'{key}_components'
            with suppress(KeyError): del asks.components__internal__[prop]
            count = cls._users = getattr(cls, "_users", 1) - 1
            if count <= 0:
                with suppress(ValueError): unregister_class(cls)

        for func in self._processors:
            with suppress(KeyError): del asks.processors__internal__[func.asks_id]

        for func in self._draw_funcs:
            with suppress(KeyError): del asks.draw_funcs__internal__[func.asks_id]

        with suppress(KeyError): del _menu_items[name]
        for _, cls in menu:
            cls._users = getattr(cls, "_users", 1) - 1
            if cls._users <= 0:
                with suppress(ValueError): unregister_class(cls)

        cls = self._type
        if cls:
            with suppress(ValueError): unregister_class(cls)
            with suppress(AttributeError): delattr(Key, name)

        self._type = None
        self._components.clear()
        self._processors.clear()
        self._draw_funcs.clear()
        self._menu_items.clear()
        with suppress(KeyError): del _namespaces[name]

        if not _namespaces and hasattr(Key, "ASKS"):
            cls = Key.ASKS
            delattr(Key, "ASKS")

            if hasattr(cls, "CLASSES"):
                for cls_ in reversed(cls.CLASSES):
                    with suppress(ValueError): unregister_class(cls_)
                cls.CLASSES = tuple()
            
            with suppress(AttributeError): delattr(Key, "asks")
            with suppress(ValueError): unregister_class(cls)

            load_post.remove(_on_file_load)
            MESH_MT_shape_key_context_menu.remove(_draw_menu_items)
