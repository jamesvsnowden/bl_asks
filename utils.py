
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Set, Tuple, Type, TYPE_CHECKING
from contextlib import suppress
from uuid import uuid4
from bpy.types import Context, Key, Object, Operator, PropertyGroup, MESH_MT_shape_key_context_menu
from bpy.props import BoolProperty, CollectionProperty, PointerProperty, StringProperty
from bpy.utils import register_class, unregister_class
from bpy.app.handlers import load_post, persistent
from .types.component import Component
if TYPE_CHECKING:
    from bpy.types import FCurve, Menu
    from .types.curve_component import KeyframePoint

_namespaces = {}
_menu_items = {}
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


def _ensure_entities(key: Key) -> None:
    entities = key.asks.entities
    for shape in key.key_blocks:
        if shape not in entities:
            entities.create(shape)


@persistent
def _on_file_load(_) -> None:
    import bpy
    for key in bpy.data.shape_keys:
        _ensure_entities(key)
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
            layout.operator(item.id, text=item.text, icon=item.icon)


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


def split_symmetrical(name: str) -> Tuple[str, str, str]:
    """
    Splits the data block name into its symmetrical prefix, base name and symmetrical suffix.
    """
    assert isinstance(name, str)
    afix = next((x for x in SYM_SFIX_LUT if name.startswith(x)), "")
    if afix:
        return "", name[:-len(afix)], afix
    afix = next((x for x in SYM_PFIX_LUT if name.endswith(x)), "")
    if afix:
        return afix, name[len(afix)], ""
    return "", name, ""


def symmetrical_target(name: str) -> str:
    """
    Returns the name of the symmetrical data block if the name is symmetrical,
    otherwise returns an emptpy string.
    """
    afix = next((afix for afix in SYM_PFIX_LUT if name.endswith(afix)), "")
    if afix:
        return f'{name[:-len(afix)]}{SYM_PFIX_LUT[afix]}'
    afix = next((afix for afix in SYM_SFIX_LUT if name.startswith(afix)), "")
    if afix:
        return f'{SYM_SFIX_LUT[afix]}{name[len(afix):]}'
    return ""


def entity_clone(object: Object, entity: Entity, options: Set[str]) -> Entity:
    name = entity.shape.value
    if 'MIRROR' in options:
        

def subtree_clone(object: Object,
                  subtree: EntitySubtree,
                  options: Set[str]) -> EntitySubtree:
    for entity in subtree:
        name = entity.shape.value
        if mirror:
            name = symmetrical_target(name) or name
        shape = object.shape_key_add(name=name, from_mix=False)

# Duplicate
# Duplicate & Mirror (Topological=True|False, Link=True|False)

# each component has
# - SYMMETRICAL option
# - symmetry_target reference
# - mirroring__internal__ flag to prevent recursion
# - optional draw_symmetry_options function
# - optional __onsymmetry__ function to handle updating the symmetry target

# components with the SYMMETRICAL option are copied rather than linked


def clone_shape_key(object: Object,
                    shape: ShapeKey,
                    mirror: Optional[bool]=False) -> ShapeKey:

    if mirror:
        name = symmetrical_target(shape.name) or f'{shape.name}_copy'
    else:
        name = f'{shape.name}_copy'

    clone = object.shape_key_add(name=name, from_mix=False)

    data = [vert.co.copy() for vert in shape.data]
    if mirror:
        scale = Vector((-1.0, 1.0, 1.0))
        for vec in data:
            vec *= scale

    for vert, vec in zip(clone.data, data):
        vert.co = vec

    clone.slider_min = shape.slider_min
    clone.slider_max = shape.slider_max
    clone.value = shape.value

    grp = shape.vertex_group
    if grp:
        if mirror:
            grp = symmetrical_target(grp) or grp
        clone.vertex_group = grp

    rel = shape.relative_key
    if rel:
        if mirror:
            tgt = symmetrical_target(rel.name)
            if tgt:
                rel = shape.id_data.key_blocks.get(tgt, rel)
        clone.relative_key = rel

    return clone



class ASKS_OT_shape_key_add(Operator):

    bl_idname = "asks.shape_key_add"
    bl_label = "New Shape Key"
    bl_options = {'INTERNAL', 'UNDO'}

    from_mix: BoolProperty(
        name="From Mix",
        default=False,
        options=set()
        )

    name: StringProperty(
        name="Name",
        default="Key",
        options=set()
        )

    @classmethod
    def poll(cls, context: Context) -> bool:
        if validate_context(context):
            object = context.object
            return object is not None and supports_shape_keys(object)

    def invoke(self, context: Context, _) -> Set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "name")
        layout.prop(self, "from_mix")

    def execute(self, context: Context) -> Set[str]:
        shape = context.object.shape_key_add(name=self.name, from_mix=self.from_mix)
        key = shape.id_data
        system = key.asks
        entities = system.entities
        entity = entities.create(shape)

        active = entities.active
        if active:
            index = active.index + len(active.subtree)
            entity["index"] = index
            entity["depth"] = active.depth
            entities.collection__internal__.move(len(entities)-1, index)
            for item in entities[index+1:]:
                item["index"] = item.index + 1
            # TODO move shape to correct index ?

        return {'FINISHED'}


class ASKS_OT_shape_key_remove(Operator):

    bl_idname = "asks.shape_key_remove"
    bl_label = "Remove Shape Key"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        if validate_context(context):
            object = context.object
            if object is not None and supports_shape_keys(object):
                key = object.data.shape_keys
                return key is not None and key.asks.entities.active is not None

    def execute(self, context: Context) -> Set[str]:
        return {'FINISHED'}



class ASKS_OT_shape_key_duplicate(Operator):

    bl_idname = "asks.shape_key_duplicate"
    bl_label = "Duplicate Shape Key"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        if validate_context(context):
            object = context.object
            if object is not None and supports_shape_keys(object):
                return object.active_shape_key is not None

    def execute(self, context: Context) -> Set[str]:
        object = context.object

        shape = object.active_shapekey
        clone = object.shape_key_add(name=f'{shape.name}_copy', from_mix=False)

        clone.relative_key = shape.relative_key
        clone.vertex_group = shape.vertex_group
        clone.slider_min = shape.slider_min
        clone.slider_max = shape.slider_max
        clone.value = shape.value

        for source, target in zip(shape.data, clone.data):
            target.co = source.co

        # foreach entity in subtree
        # - clone entity (duplicating shape & props)
        # - create references to components
        # foreach entity in new subtree
        # - if _copy exists

        key = shape.id_data
        if key.is_property_set("asks"):
            system = key.asks
            entity = system.entities.get(shape)
            if entity:
                eclone = system.entities.create(clone)
                ctable = {}

                for item in entity.subtree:
                    copy = 

                # Duplicate components
                for ref in entity.components.collection__internal__:
                    com = ref()
                    cpy = system.components.create(com.type, **com.__properties__())
                    eclone.components.attach(cpy)
                    ctable[com.name] = cpy
                
                for srcproc in entity.processors:
                    tgtproc = eclone.processors.collection__internal__.add()
                    tgtproc["name"] = srcproc.name
                    tgtproc.entity.__init__(eclone)
                    tgtproc["handler__internal__"] = srcproc.handler__internal__

                eclone.init()


        return {'FINISHED'}



class ASKS_OT_duplicate_and_mirror(Operator):

    bl_idname = "asks.duplicate_and_mirror"
    bl_label = "Duplicate & Mirror"
    bl_options = {'INTERNAL', 'UNDO'}

    topological: BoolProperty(
        name="Topological",
        default=False,
        options=set()
        )

    link: BoolProperty(
        name="Link",
        default=True,
        options=set()
        )

    @classmethod
    def poll(cls, context: Context) -> bool:
        if validate_context(context):
            object = context.object
            if object is not None and supports_shape_keys(object):
                shapekey = object.active_shape_key
                if shapekey is not None:
                    name = symmetrical_target(shapekey.name)
                    return bool(name) and name not in shapekey.id_data.key_blocks

    def invoke(self, context: Context, event: 'Event') -> Set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "topological")

        shapekey = context.object.active_shape_key
        key = shapekey.id_data
        if key.is_property_set("asks") and shapekey in key.asks.entities:
            layout.prop(self, "link")

    def execute(self, context: Context) -> Set[str]:
        object = context.object
        shape = object.active_shape_key

        subtree = []
        
        # duplicate shape key(s)

        # recursively mirror shapes


        return {'FINISHED'}




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
        name = self._name
        menu = self._menu_items

        for key, cls in self._components.items():
            cls._users = getattr(cls, "_users", 0) + 1
            Key.ASKS.components__internal__[f'{name}.{key}'] = f'{name}.{key}_components'
            with suppress(ValueError): register_class(cls)
            data[f'{key}_components'] = CollectionProperty(type=cls, options={'HIDDEN'})

        for func in self._processors:
            Key.ASKS.processors__internal__[func.asks_id] = func

        for func in self._draw_funcs:
            Key.ASKS.draw_funcs__internal__[func.asks_id] = func

        if menu:
            items = []
            for item, cls in menu:
                items.append(item)
                with suppress(ValueError): register_class(cls)
                cls._users = getattr(cls, "_users", 0) + 1
            _menu_items[name] = items

        cls = self._type = type(name, (PropertyGroup,), {"__annotations__": data})
        register_class(cls)
        setattr(Key, name, PointerProperty(type=cls, options={'HIDDEN'}))

    def unregister(self) -> None:
        name = self._name
        menu = self._menu_items

        for key, cls in self._components.items():
            prop = f'{key}_components'
            with suppress(KeyError): del Key.ASKS.components__internal__[prop]
            count = cls._users = getattr(cls, "_users", 1) - 1
            if count <= 0:
                with suppress(ValueError): unregister_class(cls)

        for func in self._processors:
            with suppress(KeyError): del Key.ASKS.processors__internal__[func.asks_id]

        for func in self._draw_funcs:
            with suppress(KeyError): del Key.ASKS.draw_funcs__internal__[func.asks_id]

        with suppress(KeyError): del _menu_items[name]
        for _, cls in menu:
            cls._users = getattr(cls, "_users", 1) - 1
            if cls._users <= 0:
                with suppress(ValueError): unregister_class(cls)

        cls = self._type
        if cls:
            with suppress(AttributeError): delattr(Key, name)
            with suppress(ValueError): unregister_class(cls)

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
            # with suppress(ValueError): unregister_class(cls)

            load_post.remove(_on_file_load)
            MESH_MT_shape_key_context_menu.remove(_draw_menu_items)
