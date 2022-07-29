
from typing import Dict, Callable, Iterator, List, Optional, Set, Union, TYPE_CHECKING
from uuid import uuid4
from bpy.types import Operator, Panel, PropertyGroup, ShapeKey
from bpy.props import (BoolProperty,
                       CollectionProperty,
                       FloatProperty,
                       IntProperty,
                       PointerProperty,
                       StringProperty)
from bpy import msgbus
from .config import POPUP_WIDTH
from .utils import PollActiveChildNode, PollActiveNode, PollSystemEnabled, split_layout
from .events import EventDispatcher
from .curves import Curve, draw_curve
from .drivers import WeightDriver
from .groups import NodeGroup
if TYPE_CHECKING:
    from bpy.types import Context, Event, FCurve, Object, UILayout

#region Iterators
#--------------------------------------------------------------------------------------------------

class NodeIterator:

    def __init__(self, root: 'Node') -> None:
        self._root = root

    def __contains__(self, node: 'Node') -> bool:
        return any(x == node for x in self)

    def __getitem__(self, key: Union[int, slice]) -> Union['Node', List['Node']]:
        if isinstance(key, int):
            if key < 0:
                nodes = list(self)
                key = len(nodes) + key
                if key < 0:
                    raise IndexError(f'{type(self)}[key]: integer key out of range')
            else:
                nodes = self
            for index, node in enumerate(nodes):
                if index == key:
                    return node
            raise IndexError(f'{type(self)}[key]: integer key out of range')
        elif isinstance(key, slice):
            return list(self)[key]
        else:
            raise TypeError(f'{type(self)}[key]: key must be int or slice, not {type(key)}')

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __iter__(self) -> Iterator['Node']:
        raise NotImplementedError()


class NodeSubtree(NodeIterator):

    def __iter__(self) -> Iterator['Node']:
        root = self._root
        nodes = root.id_data.asks.nodes.internal__
        depth = root.depth
        index = nodes.find(root.name) + 1
        limit = len(nodes)
        yield root
        while index < limit:
            node = nodes[index]
            if node.depth <= depth: break
            yield node
            index += 1


class NodeChildren(NodeIterator):

    def __iter__(self) -> Iterator['Node']:
        root = self._root
        nodes = root.id_data.asks.nodes.internal__
        depth = root.depth
        index = nodes.find(root.name) + 1
        limit = len(nodes)
        yield root
        while index < limit:
            node = nodes[index]
            node_depth = node.depth
            if node_depth <= depth: break
            if node_depth == depth + 1: yield node
            index += 1

    def add(self, key: ShapeKey, **handlers: Dict[str, Callable]) -> 'Node':
        if not isinstance(key, ShapeKey):
            raise TypeError(f'NodeChildren.add(key): key must be Shapekey, not {type(key)}')

        root = self._root
        if key.id_data != root.id_data:
            raise ValueError(f'NodeChildren.add(key): key not recognized')

        nodes = root.id_data.asks.nodes.internal__
        if key.name in nodes:
            raise ValueError(f'NodeChildren.add(key): key already exists')

        index = root.subtree[-1].index + 1
        nodes.add()
        nodes.move(len(nodes)-1, index)
        node = nodes[index]
        node.__init__(key, root, handlers)
        return node

    def move(self, node: 'Node', index: int) -> None:
        pass

    # N.B. does not remove shape keys
    def remove(self, node: 'Node') -> None:
        if not isinstance(node, Node):
            raise TypeError(f'NodeChildren.remove(node): node must be Node, not {type(node)}')
        root = self._root
        if node.parent != root:
            raise TypeError(f'NodeChildren.remove(node): node is not a child of {root}')
        nodes = root.id_data.asks.nodes.internal__
        for node in reversed(list(node.subtree)):
            node.__dispose__()
            nodes.remove(node.index)
        
#endregion Iterators

#region Messages
#--------------------------------------------------------------------------------------------------

_objects: Dict[str, object] = {}


def _shape_key_name_update_handler(shape: ShapeKey) -> None:
    node: Optional[Node] = shape.id_data.asks.nodes.get(shape)
    if node and node.name != shape.name:
        node["name"] = shape.name
        node.dispatch("name", node.name)


def _shape_key_slider_min_update_handler(key: ShapeKey) -> None:
    node: Optional[Node] = key.id_data.asks.nodes.get(key)
    if node:
        value = key.slider_min
        node.id_data.id_properties_ui(node.identifier).update(min=value, soft_min=value)
        node.dispatch("slider_min", value)


def _shape_key_slider_max_update_handler(key: ShapeKey) -> None:
    node: Optional[Node] = key.id_data.asks.nodes.get(key)
    if node:
        value = key.slider_max
        node.id_data.id_properties_ui(node.identifier).update(max=value, soft_max=value)
        node.dispatch("slider_max", value)


_message_handlers: Dict[str, Callable[[ShapeKey], None]] = {
    "name": _shape_key_name_update_handler,
    "slider_min": _shape_key_slider_min_update_handler,
    "slider_max": _shape_key_slider_max_update_handler,
    }

#endregion Messages

#region Node
#--------------------------------------------------------------------------------------------------

def _curve_update_handler(curve: 'Curve') -> None:
    _fcurve_update(curve.id_data.path_resolve(curve.path_from_id().rpartition(".")[0]))


def _group_get(node: 'Node') -> str:
    return node.get("group", "")


def _group_set(node: 'Node', value: str) -> None:
    groups = node.id_data.asks.groups
    if value not in groups:
        raise ValueError(f'Node group "{value}" does not exist')
    prev = _group_get(node)
    if value != prev:
        node["group"] = value
        if prev:
            group = groups.get(prev)
            if group and not len(tuple(group.nodes())):
                groups = groups.internal__
                groups.remove(groups.find(prev))
        node.dispatch("grouped", value)


def _input_range_min_get(node: 'Node') -> float:
    return node.get("input_range_min", 0.0)


def _input_range_min_set(node: 'Node', value: float) -> None:
    node["input_range_min"] = min(value, node.input_range_max - 0.001)
    _fcurve_update(node)


def _input_range_max_get(node: 'Node') -> float:
    return node.get("input_range_max", 1.0)


def _input_range_max_set(node: 'Node', value: float) -> None:
    node["input_range_max"] = max(value, node.input_range_min + 0.001)
    _fcurve_update(node)


def _is_interpolated_get(node: 'Node') -> bool:
    animdata = node.id_data.animation_data
    if animdata:
        fcurve = animdata.drivers.find(f'key_blocks["{node.name}"].value')
        return fcurve is not None and not fcurve.mute
    return False


def _is_interpolated_set(node: 'Node', value: bool) -> None:
    _fcurve_ensure(node).mute = not value


def _value_range_min_get(node: 'Node') -> float:
    return node.get("value_range_min", 0.0)


def _value_range_min_set(node: 'Node', value: float) -> None:
    node["value_range_min"] = min(value, node.value_range_max - 0.001)
    _fcurve_update(node)


def _value_range_max_get(node: 'Node') -> float:
    return node.get("value_range_max", 1.0)


def _value_range_max_set(node: 'Node', value: float) -> None:
    node["value_range_max"] = max(value, node.value_range_min + 0.001)
    _fcurve_update(node)


def _fcurve_ensure(node: 'Node') -> 'FCurve':
    animdata = node.id_data.animation_data_create()
    datapath = f'key_blocks["{node.name}"].value'
    return animdata.drivers.find(datapath) or animdata.drivers.new(datapath)


def _fcurve_update(node: 'Node') -> None:
    node.curve.assign(_fcurve_ensure(node),
                      (node.input_range_min, node.input_range_max),
                      (node.value_range_min, node.value_range_max))


def _driver_update(node: 'Node') -> None:

    if node.depth == 0:
        return

    driver = _fcurve_ensure(node).driver
    driver.type = 'SCRIPTED'
    driver.expression = "value"

    variables = driver.variables
    for variable in reversed(list(variables)):
        variables.remove(variable)

    variable = variables.new()
    variable.type = 'SINGLE_PROP'
    variable.name = "value"

    target = variable.targets[0]
    target.id_type = 'KEY'
    target.id = node.id_data
    target.data_path = f'["{node.identifier}"]'

    parent = node.parent
    if parent and parent.depth:
        variable = variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = "input"

        target = variable.targets[0]
        target.id_type = 'KEY'
        target.id = node.id_data
        target.data_path = f'key_blocks["{parent.name}"].value'

        driver.expression = f'input*{driver.expression}'


class Node(EventDispatcher, PropertyGroup):

    driver__: PointerProperty(type=WeightDriver)

    curve: PointerProperty(
        name="Curve",
        type=Curve,
        options=set()
        )

    depth: IntProperty(
        name="Depth",
        get=lambda self: self.get("depth", 0),
        options=set()
        )

    @property
    def driver(self) -> Optional[WeightDriver]:
        if self.is_property_set("driver__"):
            return self.driver__

    group: StringProperty(
        name="Group",
        get=_group_get,
        set=_group_set,
        options=set()
        )

    icon: StringProperty(
        name="Icon",
        default='SHAPEKEY_DATA',
        options=set()
        )

    icon_value: IntProperty(
        name="Icon",
        default=0,
        options=set()
        )

    identifier: StringProperty(
        name="Identifier",
        get=lambda self: self.get("identifier", ""),
        options={'HIDDEN'}
        )

    @property
    def index(self) -> int:
        return self.id_data.asks.nodes.internal__.find(self.name)

    input_range_min: FloatProperty(
        name="Min",
        min=-10.0,
        max=9.999,
        soft_min=0.0,
        soft_max=0.999,
        precision=3,
        get=_input_range_min_get,
        set=_input_range_min_set,
        options=set()
        )

    input_range_max: FloatProperty(
        name="Max",
        min=-9.999,
        max=10.0,
        soft_min=0.001,
        soft_max=1.0,
        precision=3,
        get=_input_range_max_get,
        set=_input_range_max_set,
        options=set()
        )

    value_range_min: FloatProperty(
        name="Min",
        min=-10.0,
        max=9.999,
        soft_min=0.0,
        soft_max=0.999,
        precision=3,
        get=_value_range_min_get,
        set=_value_range_min_set,
        options=set()
        )

    value_range_max: FloatProperty(
        name="Max",
        min=-9.999,
        max=10.0,
        soft_min=0.001,
        soft_max=1.0,
        precision=3,
        get=_value_range_max_get,
        set=_value_range_max_set,
        options=set()
        )

    @property
    def is_active(self) -> bool:
        return self.id_data.asks.nodes.active == self

    is_interpolated: BoolProperty(
        name="Interpolated",
        get=_is_interpolated_get,
        set=_is_interpolated_set,
        options=set()
        )

    def rename(self, name: str) -> None:
        if not isinstance(name, str):
            raise TypeError(f'Node.rename(name): name must be str, not {type(name)}')
        cache = self.name
        names = self.id_data.asks.node_tree.nodes.keys()
        index = 0
        value = name
        while value in names:
            index += 1
            value = f'{name}.{str(index).zfill(3)}'
        self["name"] = value
        self.dispatch("name", value, cache)

    name: StringProperty(
        name="Name",
        get=lambda self: self.get("name", ""),
        set=rename,
        options=set()
        )

    @property
    def parent(self) -> Optional['Node']:
        depth = self.depth - 1
        if depth >= 0:
            nodes = self.id_data.asks.nodes.internal__
            index = self.index - 1
            while index >= 0:
                node = nodes[index]
                if node.depth == depth: return node
                index -= 1

    @property
    def subtree(self) -> NodeSubtree:
        return NodeSubtree(self)

    @property
    def children(self) -> NodeChildren:
        return NodeChildren(self)

    @property
    def shape_key(self) -> Optional[ShapeKey]:
        return self.id_data.key_blocks.get(self.name)

    show_expanded: BoolProperty(
        name="Expand",
        default=True,
        options=set()
        )

    @property
    def value_path(self) -> str:
        return f'key_blocks["{self.name}"].value'

    def __init__(self, key: ShapeKey, parent: 'Node', handlers: Dict[str, Callable]) -> None:
        self["identifier"] = f'asks_node_{uuid4().hex}'
        self["name"] = key.name
        self["depth"] = parent.depth + 1
        self["input_range_min"] = parent.value_range_min
        self["input_range_max"] = parent.value_range_max
        self["value_range_min"] = key.slider_min
        self["value_range_max"] = key.slider_max

        curve = self.curve
        curve.__init__()
        curve.bind("updated", _curve_update_handler)

        for event_type, handler in handlers.items():
            self.bind(event_type, handler)

        key.id_data[self.identifier] = 1.0
        key.id_data.id_properties_ui(self.identifier).update(
            default=1.0,
            min=-10.0,
            max=10.0,
            soft_min=0.0,
            soft_max=1.0,
            precision=3
            )

        if key.relative_key == key.id_data.reference_key:
            rel = parent.shape_key
            if rel:
                key.relative_key = rel

        _driver_update(self)
        _fcurve_update(self)

        self.dispatch("initialized")
        self.__load__()

    def __load__(self) -> None:
        key = self.shape_key
        if key:
            options = {
                "owner": _objects.setdefault(self.identifier, object()),
                "args": (key,),
                "options": {'PERSISTENT'}
                }
            for propname, callback in _message_handlers.items():
                options["key"] = key.path_resolve(propname, False)
                options["notify"] = callback
                msgbus.subscribe_rna(**options)
        self.dispatch("loaded")

    def __dispose__(self):
        obj = _objects.get(self.identifier)
        if obj:
            msgbus.clear_by_owner(obj)
        animdata = self.id_data.animation_data
        if animdata:
            drivers = animdata.drivers
            for path in (f'key_blocks["{self.name}"].value', f'["{self.identifier}"]'):
                fcurve = drivers.find(path)
                if fcurve:
                    drivers.remove(fcurve)
        try:
            del self.id_data[self.identifier]
        except KeyError:
            pass
        self.dispatch("disposed")

#endregion Node

#region Nodes
#--------------------------------------------------------------------------------------------------

class Nodes(PropertyGroup):

    internal__: CollectionProperty(type=Node)

    def get_active_index(self) -> int:
        return PropertyGroup.get(self, "active_index", 0)

    def set_active_index(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError(f'Nodes.active_index must be int, not {type(value)}')
        value = min(len(self) - 1, max(value, 0))
        if self.get_active_index() != value:
            node = self.active
            if node:
                node.dispatch("deactivated")
            self["active_index"] = value
            node = self.active
            if node:
                node.dispatch("activated")

    active_index: IntProperty(
        name="Shape Key",
        get=get_active_index,
        set=set_active_index,
        options=set()
        )

    @property
    def active(self) -> Optional[Node]:
        index = self.get_active_index()
        nodes = self.internal__
        if index < len(nodes):
            return nodes[index]

    def __len__(self) -> int:
        return len(self.internal__)

    def __iter__(self) -> Iterator[Node]:
        return iter(self.internal__)

    def __getitem__(self, key: Union[ShapeKey, int, str, slice]) -> Union[Node, List[Node]]:
        if isinstance(key, ShapeKey):
            if key.id_data != self.id_data:
                raise ValueError(f'Nodes[key]: ShapeKey key {key} is not recognized')
            key = key.name
        if isinstance(key, (str, int, slice)):
            return self.internal__[key]
        raise TypeError(f'Nodes[key]: key must be ShapeKey, int, str or slice, not {type(key)}')

    def ensure(self, key: ShapeKey) -> Node:
        return self.get(key) or self[0].append(key)

    def find(self, key: Union[ShapeKey, str]) -> int:
        if isinstance(key, ShapeKey):
            if key.id_data != self.id_data:
                raise ValueError(f'Nodes.find(key): ShapeKey key {key} is not recognized')
            key = key.name
        if isinstance(key, str):
            return self.internal__.find(key)
        raise TypeError(f'Nodes.find(key): key must be ShapeKey or str, not {type(key)}')

    def get(self, key: Union[ShapeKey, str]) -> Optional[Node]:
        if isinstance(key, ShapeKey):
            key = key.name
        if isinstance(key, str):
            return self.internal__.get(key)
        raise TypeError(f'Nodes.get(key): key must be ShapeKey or str, not {type(key)}')

#endregion Nodes

#region Operators
#--------------------------------------------------------------------------------------------------

class ASKS_OT_node_add(PollActiveNode, Operator):
    bl_idname = "asks.node_add"
    bl_label = "Add"
    bl_description = "Add a new shape"
    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context: 'Context') -> Set[str]:
        ob = context.object
        kb = ob.shape_key_add(from_mix=False)
        ob.data.shape_keys.asks.nodes.active.children.add(kb)
        return {'FINISHED'}


class ASKS_OT_interpolation_setup(PollSystemEnabled, Operator):
    bl_idname = "asks.interpolation_setup"
    bl_label = "Interpolation"

    node = None
    node_target: StringProperty(
        name="Node",
        default="",
        options=set()
        )

    def invoke(self, context: 'Context', _: 'Event') -> Set[str]:
        node = context.object.data.shape_keys.asks.nodes.get(self.node_target)
        if node:
            self.node = node
            return context.window_manager.invoke_popup(self, width=POPUP_WIDTH)
        else:
            self.report({'ERROR'}, f'Node "{self.node_target}" not found')
            return {'CANCELLED'}

    def draw(self, context: 'Context') -> None:
        layout = self.layout
        layout.label(text=f'Interpolation ({self.node.name})', icon='GRAPH')
        layout.separator()
        _draw_interpolation_settings(layout, self.node, context.object)
        layout.separator()

    def execute(self, _: 'Context') -> Set[str]:
        return {'FINISHED'}


#endregion

#region UI
#--------------------------------------------------------------------------------------------------


def _draw_interpolation_settings(layout: 'UILayout',
                                 node: 'Node',
                                 ob: 'Object') -> None:
    key = node.shape_key
    if key:
        labels, fields, _ = split_layout(layout)

        labels.label(text="Basis")
        fields.prop_search(key, "relative_key", key.id_data, "key_blocks", text="")

        labels.label(text="Blend")
        fields.prop_search(key, "vertex_group", ob, "vertex_groups", text="")

    labels, fields, _ = split_layout(layout, align=True)
    labels.label(text="Input Range")
    fields.prop(node, "input_range_min", text="Min")
    fields.prop(node, "input_range_max", text="Max")

    labels, fields, _ = split_layout(layout, align=True)
    labels.label(text="Value Range")
    fields.prop(node, "value_range_min", text="Min")
    fields.prop(node, "value_range_max", text="Max")

    draw_curve(layout, node.curve, heading="Curve")


class ASKS_PT_interpolation(PollActiveChildNode, Panel):
    bl_idname = "ASKS_PT_interpolation"
    bl_label = "Interpolation"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_parent_id = "ASKS_PT_shape_keys"

    def draw(self, context: 'Context') -> None:
        layout = self.layout
        ob = context.object
        node = ob.data.shape_keys.asks.nodes.active
        _draw_interpolation_settings(layout, node, ob)
        key = node.shape_key
        if key:
            col = split_layout(layout, heading="Value")[1]
            col.prop(key, "value", text="")


class ASKS_PT_interpolation_popover(PollSystemEnabled, Panel):
    bl_idname = "ASKS_PT_interpolation_popover"
    bl_label = "Interpolation"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_ui_units_x = 18
    bl_options = {'INSTANCED'}

    def draw(self, context: 'Context') -> None:
        node = getattr(context, "node", None)
        if isinstance(node, Node):
            _draw_interpolation_settings(self.layout, node, context.object)


#endregion