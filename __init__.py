

# Nodes are GROUP or SHAPE, they have Curve and Value components

from contextlib import suppress
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Type, TypeVar, Union, TYPE_CHECKING
from uuid import uuid4
from bpy.types import Key, Menu, Object, Operator, Panel, PropertyGroup, ShapeKey, UIList
from bpy.props import CollectionProperty, IntProperty, PointerProperty, StringProperty
from rna_prop_ui import rna_idprop_ui_create
if TYPE_CHECKING:
    from bpy.types import ChannelDriverVariables, Context, Driver, DriverVariable, FCurve, UILayout


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
EventListener = Callable[['Controller', 'Event'], None]
TEvent = TypeVar('TEvent', bound=Type['Event'])


@dataclass(frozen=True)
class Event:
    pass


@dataclass(frozen=True)
class NameUpdateEvent(Event):
    value: str
    previous_value: str


@dataclass(frozen=True)
class ParentNameUpdateEvent(Event):
    value: str
    previous_value: str


@dataclass(frozen=True)
class SliderMinUpdateEvent(Event):
    value: float


@dataclass(frozen=True)
class SliderMaxUpdateEvent(Event):
    value: float



def event_listener(type: Type[Event]) -> Callable[[EventListener], EventListener]:
    def register_event_listener(listener: EventListener) -> EventListener:
        listener._type = type
        listener._guid = uuid4().hex
        _get_system()._listeners[listener._guid] = listener
        return listener
    return register_event_listener


@dataclass
class Action:
    operator: str
    label: str = ""
    icon: str = ''
    icon_value: int = 0
    description: str = ""

    def __init__(self, operator: Type[Operator], **options: Dict[str, Union[int, str]]) -> None:
        self.operator = operator.bl_idname
        self.label = options.get("label", operator.bl_label)
        self.icon = options.get("icon", 'NONE')
        self.icon_value = options.get("icon_value", 0)
        self.description = options.get("description", operator.bl_description)

class Variables:

    def __getitem__(self, key: Union[str, int]) -> 'DriverVariable':
        if isinstance(key, int):
            key += 2
        return self._data[key]

    def __init__(self, data: 'ChannelDriverVariables') -> None:
        self._data = data

    def __iter__(self) -> Iterator['DriverVariable']:
        return iter(self._data[2:])

    def __len__(self) -> int:
        return len(self._data) - 2

    def clear(self) -> None:
        data = self._data
        for item in reversed(data[2:]):
            data.remove(item)

    def get(self, key: Union[int, str]) -> Optional['DriverVariable']:
        data = self._data
        if isinstance(key, int):
            key += 2
            if key < len(data):
                return data[key]
        elif isinstance(key, str):
            return data.get(key)
        else:
            raise TypeError(f'Expected key to be int or str, not {key.__class__.__name__}')

    def new(self) -> 'DriverVariable':
        return self._data.new()

    def remove(self, variable: 'DriverVariable') -> None:
        self._data.remove(variable)


def _value_path(name: str) -> str:
    return f'key_blocks["{name}"].value'






class Controller:

    NAMESPACE = ''
    actions = tuple()

    def _init_driver(self, driver: 'Driver') -> None:
        name = self.get_node_name()
        vars = driver.variables

        for var in reversed(list(vars)):
            vars.remove(var)

        for key, path in [('_w', f'user["{name}"]'), ('__w', f'["{name}"]')]:
            var = var.new()
            var.type = 'SINGLE_PROP'
            var.name = key
            var.targets[0].id_type = 'KEY'
            var.targets[0].id = self.id_data
            var.targets[0].data_path = path

        driver.expression = "_w*__w"

    def _get_driver(self) -> 'Driver':
        fcurve = self._get_fcurve()
        driver = fcurve.driver
        if len(driver.variables) < 2:
            self._init_driver(driver)
        return driver

    def _get_fcurve(self) -> 'FCurve':
        animdata = self.id_data.animation_data_create()
        datapath = f'key_blocks["{self.get_node_name()}"].value'
        return animdata.drivers.find(datapath) or animdata.drivers.new(datapath)

    def __init__(self, node: 'Node') -> None:
        self["node_name"] = node.name
        self._init_driver(self._get_fcurve().driver)
        self.init()

    def draw(self, layout: UILayout) -> None:
        pass

    def get_expression(self) -> str:
        value: str = self._get_driver().expression
        return value[8:-1] if value.startswith("_") else ""

    def get_name(self) -> str:
        return self.get("name", "")

    def get_node_name(self) -> str:
        return self.get("node_name", "")

    def get_node(self) -> Optional['Node']:
        name = self.get_node_name()
        if name:
            return self.get_system().nodes.get(name)

    def get_system(self) -> 'System':
        return self.id_data.asks

    def get_shape_key(self) -> Optional[ShapeKey]:
        node = self.get_node()
        if node:
            return node.get_shape_key()

    def init(self) -> None:
        pass

    def set_expression(self, value: str) -> None:
        coefs = "_w*__w"
        value = f'{coefs}*({value})' if value else coefs
        self._get_driver().expression = value

    def set_name(self, _) -> None:
        raise AttributeError(f'{self}.name is read-only')

    expression: StringProperty(
        name="Expression",
        get=get_expression,
        set=set_expression,
        options=set()
        )

    name: StringProperty(
        name="Name",
        get=get_name,
        set=set_name,
        options=set()
        )

    node_name: StringProperty(
        name="Node",
        get=get_node_name,
        options=set()
        )

    @property
    def node(self) -> Optional["Node"]:
        return self.get_node()

    @property
    def shape_key(self) -> Optional[ShapeKey]:
        return self.get_shape_key()

    @property
    def system(self) -> 'System':
        return self.get_system()

    @property
    def variables(self) -> Variables:
        return Variables(self._get_driver().variables)


class EventListeners(PropertyGroup):
    
    internal__: CollectionProperty(
        type=PropertyGroup,
        options={'HIDDEN'}
        )

    def __iter__(self) -> Iterator[str]:
        handlers = self.id_data.asks._handlers
        for item in self.internal__:
            handler = handlers.get(item.name)
            if handler:
                yield handler

    def __len__(self) -> int:
        return len(self.internal__)


class Node(PropertyGroup):

    @staticmethod
    def _on_shapekey_name_update(node: 'Node') -> None:
        shape = node.get_shape_key()
        if shape:
            node._update_name(shape.name, node.name)

    @staticmethod
    def _on_shapekey_slider_min_update(node: 'Node') -> None:
        shape = node.get_shape_key()
        if shape:
            key = shape.id_data
            value = shape.slider_min
            for propname in (node.name, node._get_identifier()):
                key.id_properties_ui(propname).update(min=value, soft_min=value)
            node.dispatch_event(SliderMinUpdateEvent(value))

    @staticmethod
    def _on_shapekey_slider_max_update(node: 'Node') -> None:
        shape = node.get_shape_key()
        if shape:
            key = shape.id_data
            value = shape.slider_max
            for propname in (node.name, node._get_identifier()):
                key.id_properties_ui(propname).update(max=value, soft_max=value)
            node.dispatch_event(SliderMaxUpdateEvent(value))

    def _get_identifier(self) -> str:
        id_ = self.get("identifier", "")
        if id_ == "":
            id_ = str(uuid4())
            self["identifier"] = id_
        return id_

    def _init_value_driver(self) -> 'None':
        key = self.id_data
        drivers = key.animation_data_create().drivers
        fcurve = drivers.find()

    def _get_message_broker(self) -> object:
        return self.id_data.asks._brokers.setdefault(self._get_identifier(), object())

    def _subscribe_rna(self, shapekey: ShapeKey) -> None:
        from bpy import msgbus
        broker = self._get_message_broker()

        msgbus.subscribe_rna(key=shapekey.path_resolve("name", False),
                             owner=broker,
                             notify=self._on_shapekey_name_update,
                             args=(self,))

        msgbus.subscribe_rna(key=shapekey.path_resolve("slider_min", False),
                             owner=broker,
                             notify=self._on_shapekey_slider_min_update,
                             args=(self,))

        msgbus.subscribe_rna(key=shapekey.path_resolve("slider_max", False),
                             owner=broker,
                             notify=self._on_shapekey_slider_max_update,
                             args=(self,))

    def _unsubscribe_rna(self) -> None:
        broker = self.id_data.asks._brokers.pop(self._get_identifier(), None)
        if broker:
            from bpy import msgbus
            msgbus.clear_by_owner(broker)

    def _update_name(self, value: str, previous_value: str) -> None:
        self["name"] = value

        key = self.id_data
        self._update_weight_idprop(key, value, previous_value)
        self._update_weight_idprop(key, value, previous_value)

        controller = self.get_controller()
        if controller:
            controller["node_name"] = value
            variables = controller._get_driver().variables
            variables[0].data_path = f'user["{value}"]'
            variables[1].data_path = f'["{value}"]'
            self.dispatch_event(NameUpdateEvent(self, value, previous_value))

        for child in self.iter_children():
            child.dispatch_event(ParentNameUpdateEvent(child, value, previous_value))

    def __init__(self,
                 shapekey: ShapeKey,
                 controller: Optional[Controller],
                 **options: Dict[str, Any]) -> None:

        for key, value in options.items():
            self[key] = value

        self["name"] = shapekey.name
        self._subscribe_rna(shapekey)

        slider_min = shapekey.slider_min
        slider_max = shapekey.slider_max
        ui_options = {
            "default": 1.0,
            "description": "ShapeKey weight",
            "min": slider_min,
            "max": slider_max,
            "soft_min": slider_min,
            "soft_max": slider_max,
            }

        key = shapekey.id_data
        for propname in (shapekey.name, self._get_identifier()):
            rna_idprop_ui_create(key, propname, **ui_options)

        animdata = key.animation_data
        if animdata:
            fcurve = animdata.drivers.find(f'key_blocks["{shapekey.name}"].value')
            if fcurve:
                fcurve.data_path = f'["{shapekey.name}"]'

        if controller:
            self["controller_path"] = controller.path_from_id()
        else:
            # TODO setup driver
            pass

    def add_event_listener(self, listener: EventListener) -> None:
        listeners = self.listeners__.get(listener._type.__name__)
        if not listeners:
            listeners = self.listeners__.add()
            listeners["name"] = listener._type.__name__
            listeners.add().name = listener._guid
        else:
            for item in listeners:
                if item.name == listener._guid:
                    return
            listeners.add().name = listener._guid

    def append_child(self,
                     shape: Optional[ShapeKey]=None,
                     type_: Optional[Type[Controller]]=None,
                     **options: Dict[str, Any]) -> None:
        nodes: Nodes = self.get_system().nodes
        return nodes.new(shape, type_, **dict(options, parent=self))

    def dispatch_event(self, event: Event) -> None:
        controller = self.get_controller()
        if controller:
            for handler in self.event_handlers.get(event.__class__):
                handler(controller, event)

    # def draw(self, layout: UILayout) -> None:
    #     row = layout.row()
    #     icon_value = self.get_icon_value()
    #     if icon_value:
    #         row.prop(self, "name", icon_value=icon_value)
    #     else:
    #         row.prop(self, "name", icon=self.get_icon())

    def draw(self, layout: UILayout) -> None:
        controller = self.get_controller()
        if controller:
            controller.draw(layout)

    def get_ancestors(self) -> Tuple['Node']:
        return tuple(self.iter_ancestors())

    def get_children(self) -> Tuple['Node']:
        return tuple(self.iter_children())

    def get_child_count(self) -> int:
        return sum(1 for _ in self.iter_children())

    def get_controller_path(self) -> str:
        return self.get("controller_path", "")

    def get_controller(self) -> Optional[Controller]:
        path = self.get_controller_path()
        if path:
            try:
                return self.id_data.path_resolve(path)
            except ValueError:
                return None

    def get_depth(self) -> int:
        return self.get("depth", 0)

    def get_descendents(self) -> Tuple['Node']:
        return tuple(self.iter_descendents())

    def get_index(self) -> int:
        return self.get_system().nodes.internal__.find(self.get_name())

    def get_icon_value(self) -> int:
        return self.get("icon_value", 0)

    def get_icon(self) -> str:
        return self.get("icon", 'SHAPEKEY_DATA')

    def get_last_child(self) -> Optional['Node']:
        children = self.get_children()
        return None if not len(children) else children[-1]

    def get_name(self) -> str:
        return self.get("name", "")

    def get_object(self) -> Object:
        import bpy
        user = self.id_data.user
        return next(ob for ob in bpy.data.objects if ob.type in COMPAT_OBJECTS and ob.data == user)

    def get_parent(self) -> Optional['Node']:
        depth = self.get_depth() - 1
        if depth >= 0:
            index = self.get_index() - 1
            nodes = self.get_system().nodes.internal__
            while index >= 0:
                node: Node = nodes[index]
                if node.get_depth() == depth: return node
                index -= 1

    def get_shape_key(self) -> Optional['ShapeKey']:
        return self.id_data.key_blocks.get(self.get_name())

    def get_subtree(self) -> Tuple['Node']:
        return tuple(self.iter_subtree())

    def get_system(self) -> 'System':
        return self.id_data.asks

    def index_in_parent(self) -> int:
        parent = self.get_parent()
        return parent.index_of_child(self) if parent else -1

    def index_of_child(self, node: 'Node') -> int:
        for index, child in enumerate(self.iter_children()):
            if child == node:
                return index
        return -1

    def insert_child(self,
                     index: int,
                     shape: Optional[ShapeKey]=None,
                     type_: Optional[Type[Controller]]=None,
                     **options: Dict[str, Any]) -> 'Node':
        nodes: Nodes = self.get_system().nodes
        return nodes.new(shape, type_, **dict(options, index=index, parent=self))

    def is_ancestor_of(self, node: 'Node') -> bool:
        return any(item == self for item in node.iter_ancestors())

    def is_child_of(self, node: 'Node') -> bool:
        return node.is_parent_of(self)

    def is_descendant_of(self, node: 'Node') -> bool:
        return node.is_ancestor_of(self)

    def is_parent_of(self, node: 'Node') -> bool:
        return node.get_parent() == self

    def is_valid(self) -> bool:
        return self.get_shape_key() is not None

    def iter_ancestors(self) -> Iterator['Node']:
        node = self.get_parent()
        while node:
            yield node
            node = node.get_parent()

    def iter_children(self) -> Iterator['Node']:
        depth = self.get_depth() + 1
        for node in self.iter_descendents():
            if node.get_depth() == depth:
                yield node

    def iter_descendents(self) -> Iterator['Node']:
        nodes = self.get_node_tree().nodes.internal__
        index = self.get_index() + 1
        depth = self.get_depth()
        count = len(nodes)
        while index < count:
            node: Node = nodes[index]
            if node.get_depth() <= depth: break
            yield node
            index += 1

    def iter_subtree(self) -> Iterator['Node']:
        yield self
        yield from self.iter_descendents()

    def move_child(self, node: 'Node', index: int) -> None:
        children = self.get_children()
        if not any(item == node for item in children):
            raise ValueError(f'{node} is not a child of {self}')
        nodes = self.get_system().nodes.internal__
        count = len(children)
        if index < 0:
            index = max(0, count + index)
        else:
            index = min(index, count)
        prev_index = children[index].get_index()
        next_index = node.get_index()
        nodes.move(prev_index, next_index)
        index = min(prev_index, next_index)

    def remove_child(self, node: 'Node', delete: Optional[bool]=False) -> None:
        if not self.is_parent_of(node):
            raise ValueError(f'{node} is not a child of {self}')
        controller = None
        if delete:
            controller = node.get_controller()
        nodes = self.get_system().nodes.internal__
        index = node.get_index()
        nodes.remove(index)
        if controller:
            pass

    def remove_event_listener(self, listener: Callable[[Controller, Event], None]) -> None:
        listeners = self.listeners__.get(listener._type.__name__)
        if listeners:
            index = next((i for i, x in listeners.internal__ if x.name == listener._guid), -1)
            if index != -1:
                listeners.remove(index)

    def _update_weight_idprop(self, name: str, previous_name: Optional[str]="") -> None:
        fcurve = None
        weight = 1.0
        key = self.id_data
        if previous_name:
            animdata = key.animation_data
            if animdata:
                fcurve = animdata.drivers.find(f'["{previous_name}"]')
            weight = key.get(previous_name, weight)
            with suppress(KeyError):
                del key[previous_name]
        rna_idprop_ui_create(key, name, min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=weight)
        if fcurve:
            fcurve.data_path = f'["{name}"]'

    def set_name(self, value: str) -> None:
        cache = self.get_name()
        value = self.get_system().nodes.format_unique_name(value)
        shape = self.get_shape_key()
        if shape:
            shape.name = value
        else:
            self._update_name(value, cache)

    @property
    def ancestors(self) -> Tuple['Node']:
        return self.get_ancestors()

    @property
    def children(self) -> Tuple['Node']:
        return self.get_children()

    @property
    def descendents(self) -> Tuple['Node']:
        return self.get_descendents()

    controller_path: StringProperty(
        name="Controller Path",
        get=get_controller_path,
        options={'HIDDEN'}
        )

    @property
    def controller(self) -> Optional[Controller]:
        return self.get_controller()

    @controller.setter
    def controller(self, controller: Controller) -> None:
        self.set_controller(controller)

    depth: IntProperty(
        name="Depth",
        get=get_depth,
        options=set()
        )

    icon: IntProperty(
        name="Icon",
        get=get_icon,
        options=set()
        )

    index: IntProperty(
        name="Index",
        get=get_index,
        options=set()
        )

    listeners__: CollectionProperty(
        type=EventListeners,
        optinos={'HIDDEN'}
        )

    name: StringProperty(
        name="Name",
        get=get_name,
        set=set_name,
        options=set()
        )

    @property
    def object(self) -> Object:
        return self.get_object()

    @property
    def parent(self) -> Optional['Node']:
        return self.get_parent()

    @property
    def system(self) -> 'System':
        return self.get_system()


class Nodes(PropertyGroup):

    def add(self,
            shapekey: Optional[ShapeKey]=None,
            type: Optional[Controller]=None,
            **settings: Dict[str, Any]) -> Node:
        pass

    def ensure(self, shape: ShapeKey) -> Node:
        if not shape.id_data != self.id_data:
            raise ValueError(f'{shape} is not a shape key of {self.id_data}')
        return self.get(shape) or self.add(shape)

    def find(self, key: Union[str, Node, ShapeKey]) -> int:
        if isinstance(key, Node):
            if key.id_data != self.id_data:
                raise ValueError(f'{key} is not a member of {self}')
            key = key.name
        elif isinstance(key, ShapeKey):
            if not key.id_data != self.id_data:
                raise ValueError(f'{key} is not a shape key of {self.id_data}')
            key = key.name
        return self.internal__.find(key)

    def format_unique_name(self, basename: Optional[str]="Key") -> str:
        names = self.keys()
        index = 0
        value = basename
        while value in names:
            index += 1
            value = f'{basename}.{str(index).zfill(3)}'
        return value

    def get_active_index(self) -> int:
        return self.get("active_index", -1)

    def get_active(self) -> Optional['Node']:
        index = self.get_active_index()
        if index >= 0 < len(self):
            return self.internal__[index]

    def get(self, key: Union[str, ShapeKey]) -> Optional[Node]:
        if isinstance(key, ShapeKey):
            if not key.id_data == self.id_data:
                raise ValueError(f'{key} is not a shape key of {self.id_data}')
            key = key.name
        return self.internal__.get(key)

    def items(self) -> Iterator[Tuple[str, Node]]:
        return self.internal__.items()

    def keys(self) -> Iterator[str]:
        return self.internal__.keys()

    def set_active_index(self, index: int) -> None:
        count = len(self)
        if index < 0:
            index = count + index
        index = max(0, min(index, count - 1))
        self["active_index"] = index

    def set_active(self, node: 'Node') -> None:
        if node.get_system().nodes != self:
            raise ValueError(f'{self}.active=node: node is not a member of {self}')
        self.set_active_index(node.get_index())

    def new(self,
            shape: Optional[ShapeKey]=None,
            type_: Optional[Type[Controller]]=None,
            **options: Dict[str, Any]) -> Node:

        if isinstance(shape, ShapeKey):
            if shape in self:
                raise ValueError()
        else:
            type_ = shape
            shape = None

        parent: Optional[Node] = options.pop("parent", None)
        
        if parent:
            if not isinstance(parent, Node):
                raise TypeError(f'Expected parent to be Node, not {type(parent)}')

            if parent.get_system().nodes != self:
                raise ValueError(f'{parent} is not a node of {self}')

            siblings = parent.get_children()
        else:
            siblings = [node for node in self if not node.get_depth()]

        nodes = self.internal__
        count = len(siblings)
        index = options.pop("index", -1)
        
        if index < 0:
            index = max(0, count + index) if count else 0
        else:
            index = min(count, index)

        if index < count:
            index = siblings[index].get_subtree()[-1].get_index() + 1
        elif siblings:
            index = siblings[-1].get_subtree()[-1].get_index() + 1
        elif parent:
            index = parent.get_index() + 1
        else:
            index = len(nodes)

        if shape is None:
            shape = Node.get_object(self).shape_key_add(name=options.pop("name", "Key"),
                                                        from_mix=options.pop("from_mix", False))

        controller = None
        if type_:
            namespace = getattr(type_, 'NAMESPACE', "")

            collection = getattr(self.id_data.asks, namespace, None)
            if collection is None or not hasattr(collection, "internal__"):
                raise TypeError(f'{type_} is not a registered Controller')

            controller: Controller = collection.internal__.add()
            controller["name"] = str(uuid4())
            controller["node_name"] = shape.name

        nodes.add().__init__(shape, controller, **options)
        nodes.move(len(nodes)-1, index)

        return nodes[index]

    def values(self) -> Iterator[Node]:
        return iter(self)

    @property
    def active(self) -> Optional[Node]:
        return self.get_active()

    @active.setter
    def active(self, node: 'Node') -> None:
        self.set_active(node)

    active_index: IntProperty(
        name="Shape",
        get=get_active_index,
        options={'HIDDEN'}
        )

    internal__: CollectionProperty(
        type=Node,
        options={'HIDDEN'}
        )


class Internal(PropertyGroup):

    internal__: CollectionProperty(
        type=ShapeController
        )


class System(PropertyGroup):

    _users = 0
    _listeners = {}
    _brokers = {}

    internal__: PointerProperty(
        type=Internal,
        )

    nodes: PointerProperty(
        type=Nodes,
        options=set()
        )


class ASKS_OT_node_add(Operator):
    bl_idname = "asks.node_add"
    bl_label = "Add"


class ASKS_OT_node_remove(Operator):
    bl_idname = "asks.node_remove"
    bl_label = "Remove"


class ASKS_OT_node_duplicate(Operator):
    bl_idname = "asks.node_duplicate"
    bl_label = "Duplicate"


class ASKS_OT_node_mirror(Operator):
    bl_idname = "asks.node_mirror"
    bl_label = "Mirror"


class ASKS_OT_node_duplicate_and_mirror(Operator):
    bl_idname = "asks.node_duplicate_and_mirror"
    bl_label = "Duplicate & Mirror"


class ASKS_OT_node_move_first(Operator):
    bl_idname = "asks.node_move_first"
    bl_label = "Move To First"


class ASKS_OT_node_move_up(Operator):
    bl_idname = "asks.node_move_up"
    bl_label = "Move Up"


class ASKS_OT_node_move_down(Operator):
    bl_idname = "asks.node_move_down"
    bl_label = "Move Down"


class ASKS_OT_node_move_last(Operator):
    bl_idname = "asks.node_move_last"
    bl_label = "Move To Last"


class ASKS_UL_nodes(UIList):

    def draw_item(self, _0, layout: 'UILayout', _1, node: 'Node', _2, _3, _4, _5, _6) -> None:

        split = layout.split(factor=0.5)
        
        row = split.row()
        row.alignment = 'LEFT'

        for _ in node.get_depth():
            row.label(icon='BLANK1')

        icon = node.get_icon_value() or node.get_icon()
        if isinstance(icon, int):
            row.prop(node, "name", icon_value=icon, text="", translate=False, emboss=False)
        else:
            row.prop(node, "name", icon=icon, text="", translate=False, emboss=False)

        row = split.row()
        row.prop(node.id_data, f'["{node.name}"]', text="", slider=True)

        subrow = row.row()
        subrow.ui_units_x = 12

        shape = node.get_shape_key()
        if shape:
            subrow.label(text=f'{shape.value:.3f}')
        else:
            subrow.label(text="0.000")


class ASKS_MT_actions(Menu):

    DEFAULT_ACTIONS = [
        Action(ASKS_OT_node_duplicate),
        Action(ASKS_OT_node_mirror),
        Action(ASKS_OT_node_duplicate_and_mirror)
        ]

    def draw(self, context: 'Context') -> None:
        layout = self.layout
        node: Optional[Node] = context.object.data.shape_keys.asks.nodes.active
        if node:
            controller = node.get_controller()
            actions = controller.actions if controller else self.DEFAULT_ACTIONS
            for action in actions:
                layout.operator(action.operator,
                                text=action.label,
                                icon=action.icon,
                                icon_value=action.icon_value)

class ASKS_PT_nodes(Panel):

    def draw(self, context: 'Context') -> None:
        object = context.object
        system = object.data.shape_keys.asks
        layout = self.layout
        nodes = system.nodes

        row = layout.row()
        col = row.column()
        col.template_list("ASKS_UL_nodes", "", nodes, "internal__", nodes, "active_index")

        col = row.column(align=True)
        col.operator(ASKS_OT_node_add.bl_idname, text="", icon='ADD')
        col.operator(ASKS_OT_node_remove.bl_idname, text="", icon='REMOVE')
        col.separator()
        col.menu(ASKS_MT_actions.bl_idname, text="", icon='DOWNARROW_HLT')
        col.separator()
        col.operator(ASKS_OT_node_move_first.bl_idname, text="", icon='TRIA_UP_BAR')
        col.operator(ASKS_OT_node_move_up.bl_idname, text="", icon='TRIA_UP')
        col.operator(ASKS_OT_node_move_down.bl_idname, text="", icon='TRIA_DOWN')
        col.operator(ASKS_OT_node_move_last.bl_idname, text="", icon='TRIA_DOWN_BAR')


def _controller_key(type: Type[Controller]) -> str:
    return f'{type.__name__.lower()}s__'


def _on_file_load(_) -> None:
    import bpy
    for key in bpy.data.shape_keys:
        if key.is_property_set("asks"):
            node: Node
            for node in key.asks.nodes:
                shapekey = node.get_shape_key()
                if shapekey:
                    node._subscribe_rna(shapekey)


def _classes() -> List[Type[PropertyGroup]]:
    return [
        EventListeners,
        Node,
        Nodes,
        System,
        ASKS_OT_node_add,
        ASKS_OT_node_remove,
        ASKS_OT_node_duplicate,
        ASKS_OT_node_mirror,
        ASKS_OT_node_duplicate_and_mirror,
        ASKS_OT_node_move_first,
        ASKS_OT_node_move_up,
        ASKS_OT_node_move_down,
        ASKS_OT_node_move_last,
        ASKS_MT_actions,
        ASKS_UL_nodes,
        ASKS_PT_nodes
        ]


class namespace:

    _instances = {}

    @staticmethod
    def _get_registered_system() -> Type[System]:
        if not hasattr(Key, 'ASKS'):
            from bpy.utils import register_class
            from bpy.app.handlers import load_post
            for cls in _classes():
                register_class(cls)
            Key.ASKS = System
            Key.asks = PointerProperty(
                name="ASKS",
                description="Advanced Shape Key System",
                type=System,
                options=set()
                )
            load_post.append(_on_file_load)
        return Key.ASKS

    @staticmethod
    def _unregister_system() -> None:
        pass

    def __init__(self, name: str, type: Type[Controller]) -> None:
        self._instances[name] = self
        self._name = name
        self._type = type
        self._data = {"__annotations__": {"internal__": CollectionProperty(type=type)}}
        self._prop = None
        self._listeners = {}
        self._registered = False
        type.NAMESPACE = name

    def __setattr__(self, name: str, value: Any) -> None:
        function = getattr(value, "function", None)
        if callable(function):
            import bpy
            if getattr(bpy.props, function.__name__, None) is function:
                self._data["__annotations__"][name] = value
                return
        self._data[name] = value

    def event_listener(self, type: Type[Event]) -> Callable[[EventListener], EventListener]:
        def add_event_listener(listener: EventListener) -> EventListener:
            listener.asks_type = type
            listener.asks_guid = str(uuid4())
            self._listeners[listener.asks_guid] = listener
            return listener
        return add_event_listener

    def register(self) -> None:
        if not self._registered:
            from bpy.utils import register_class
            self._prop = type(self._name, (PropertyGroup,), self._data)
            register_class(self._type)
            register_class(self._prop)
            cls = self._get_registered_system()
            cls._users += 1
            cls._listeners.update(self._listeners)
            setattr(cls, self._name, PointerProperty(type=self._prop, options={'HIDDEN'}))
            self._registered = True

    def unregister(self) -> None:
        if self._registered:
            from bpy.utils import unregister_class
            with suppress(KeyError): del Key.ASKS[self._name]
            for key in self._listeners.keys():
                with suppress(KeyError): del Key.ASKS._listeners[key]
            unregister_class(self._prop)
            self._prop = None
            self._registered = False
            Key.ASKS._users -= 1
            if key.ASKS._users == 0:
                self._unregister_system()
