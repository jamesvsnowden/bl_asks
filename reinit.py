
from typing import Any, Dict, Iterator, List, Optional, Type, Union
from uuid import uuid4
import bpy
from rna_prop_ui import rna_idprop_ui_create as idprop_create

# node registration
# load/unload system (with use_relative handler)

# build curve component

# TreeNode.__init__(type_, shapekey)
# Node.__init__(treenode, shapekey)
# if node_tree.loaded:
#   Node.__load__()

# Node.__init__(shapekey)
# TreeNode.__init__(node)
# Node.__ready__()
# if parent:
#   Node.__parented__()


_brokers: Dict[str, object] = {}


class NodeSubtree:

    def __init__(self, node: 'Node') -> None:
        self._node = node
        self._item = node_tree_item(node)

    def __contains__(self, node: 'Node') -> bool:
        return any(x == node for x in self)

    def __len__(self) -> int:
        node = self._node
        item = self._item
        data = node.id_data

        items = data.asks.tree.internal__
        index = items.find(item["name"]) + 1
        depth = item["_depth"]
        limit = len(items)
        count = 1

        while index < limit:
            if items[index]["_depth"] <= depth: break
            index += 1

        return count

    def __iter__(self) -> Iterator['Node']:
        node = self._node
        item = self._item
        data = node.id_data

        items = data.asks.tree.internal__
        index = items.find(item["name"]) + 1
        depth = item["_depth"]
        limit = len(items)

        yield node
        while index < limit:
            item = items[index]
            if item["_depth"] <= depth: break
            yield data.path_resolve(item["_nodepath"])
            index += 1

    def __getitem__(self, key: Union[int, slice]) -> 'Node':
        if isinstance(key, slice):
            return list(self)[key]
        if isinstance(key, int):
            if key == 0:
                return self._node

            if key < 0:
                key = len(self) + key

            node = self._node
            item = self._item
            data = node.id_data

            items = data.asks.tree.internal__
            index = items.find(item["name"]) + 1
            depth = item["_depth"]
            limit = len(items)
            count = 1

            while index < limit:
                item = items[index]
                if item["_depth"] <= depth: break
                if count == key: return data.path_resolve(item["_nodepath"])
                count += 1
                index += 1

            raise IndexError()
        raise TypeError()


class NodeChildren:

    def __init__(self, node: 'Node') -> None:
        self._node = node
        self._item = node._tree_node_resolve()

    def __contains__(self, node: 'Node') -> None:
        return any(x == node for x in self)

    def __iter__(self) -> Iterator['Node']:
        node = self._node
        item = self._item
        data = node.id_data

        items = data.asks.node_tree.nodes.internal__
        index = items.find(item["name"]) + 1
        depth = item["_depth"]
        limit = len(items)

        while index < limit:
            item = items[index]
            prop = item["_depth"]
            if prop <= depth:
                break
            if prop == depth + 1:
                yield data.path_resolve(item["_nodepath"])
            index += 1

    def __len__(self) -> int:
        node = self._node
        item = self._item
        data = node.id_data

        items = data.asks.node_tree.nodes.internal__
        index = items.find(item["name"]) + 1
        depth = item["_depth"]
        limit = len(items)
        count = 0

        while index < limit:
            value = items[index]["_depth"]
            if value <= depth: break
            if value == depth + 1: count += 1
            index += 1

        return count

    def __getitem__(self, key: Union[str, int, slice]) -> Union['Node', List['Node']]:
        pass

    def append(self, type_: Type['Node'], **properties: Dict[str, Any]) -> 'Node':
        if not issubclass(type_, Node): raise TypeError()
        return _node_create(self.id_data, type_, properties, self)

    def find(self, key: Union[str, 'Node']) -> int:
        '''
        '''
        if isinstance(key, str):
            return next((i for i, x in enumerate(self) if x.name == key), -1)

        if isinstance(key, Node):
            return next((i for i, x in enumerate(self) if x == key), -1)

        raise TypeError((f'{type(self)}.find(key): '
                         f'Expected key to be str or Node, not {type(key)}'))

    def get(self, name: str, default: Optional[Any]=None) -> Any:
        '''
        '''
        if not isinstance(name, str):
            raise TypeError((f'{type(self)}.get(name, default=None): '
                             f'Expected name to be str, not {type(name)}'))

        try:
            return self[name]
        except KeyError:
            return default

    def insert(self, index: int, type_: Type['Node'], **properties: Dict[str, Any]) -> 'Node':
        '''
        '''
        if not isinstance(index, int):
            raise TypeError((f'{type(self)}.insert(index, node, **properties): '
                             f'Expected index to be int, not {type(index)}'))

        if not issubclass(type_, Node):
            raise TypeError((f'{type(self)}.insert(index, type_, **properties): '
                             f'Expected type_ to be subclass of Node, not {type(type_)}'))

        key = self.id_data

        if not hasattr(key.asks, type_.NAMESPACE):
            raise ValueError((f'{type(self)}.insert(index, type_, **properties): '
                              f'node type {type(type_)} has not been registered'))

        return _node_create(key, type_, properties, self, index)

    def move(self, key: Union['Node', int], index: int) -> None:
        if isinstance(key, int):
            try:
                key = self[key]
            except IndexError: raise IndexError()
        elif not isinstance(key, Node): raise TypeError()
        if not isinstance(index, int): raise TypeError()
        # TODO

    def remove(self, node: 'Node') -> None:
        '''
        '''
        if not isinstance(node, Node):
            raise TypeError((f'{type(self)}.remove(node): '
                             f'Expected node to be Node, not {type(node)}'))
        
        if node not in self:
            raise ValueError((f'{type(self)}.remove(node): '
                              f'node is not a child of {self._node}'))
        
        _node_remove(node)


class NodeBase:

    def _name_get(self) -> str:
        return self.get("_name")

    def _name_set(self, value: str) -> None:
        self["_name"] = value

    name: bpy.props.StringProperty(
        get=lambda self: self._name_get(),
        set=lambda self, value: self._name_set(value)
        )

    def __init__(self, name: str) -> None:
        self["name"] = str(uuid4())
        self["_name"] = name


class Node(NodeBase):

    NAMESPACE = ''

    def _tree_node_resolve(self) -> 'TreeNode':
        return self.id_data.path_resolve(self["_tree_path"])

    def _input_driver(self, ensure: Optional[bool]=False) -> Optional[bpy.types.FCurve]:
        animdata = self.id_data.animation_data
        if animdata is None:
            if ensure:
                return self.id_data.animation_data_create().drivers.new(self.input_path)
        else:
            path = self.input_path
            fcurve = animdata.drivers.find(path)
            if fcurve is None and ensure:
                fcurve = animdata.drivers.new(path)
            return fcurve

    def _name_set(self, value: str) -> None:
        value = uniqname(self.id_data.asks.tree, value)
        self["_name"] = value
        self._tree_node_resolve()["_name"] = value
        self.__renamed__()

    def _value_driver(self, ensure: Optional[bool]=False) -> Optional[bpy.types.FCurve]:
        animdata = self.id_data.animation_data
        if animdata is None:
            if ensure:
                return self.id_data.animation_data_create().drivers.new(self.value_path)
        else:
            path = self.value_path
            fcurve = animdata.drivers.find(path)
            if fcurve is None and ensure:
                fcurve = animdata.drivers.new(path)
            return fcurve

    def _value_driver_init(self, fcurve: bpy.types.FCurve) -> None:
        driver = fcurve.driver

        vars = driver.variables
        spec = [("_i", self.input_path)]
        expr = "_i"
        node = self.parent

        if node:
            spec.insert(0, ("_v", node.value_path))
            expr = f'_v*{expr}'

        driver.type = 'SCRIPTED'
        driver.expression = expr
        
        for var in reversed(list(vars)):
            vars.remove(var)

        for name, path in spec:
            var = vars.new()
            var.type = 'SINGLE_PROP'
            var.name = name

            tgt = var.targets[0]
            tgt.id_type = 'KEY'
            tgt.id = self.id_data
            tgt.data_path = path

    @property
    def children(self) -> NodeChildren:
        return NodeChildren(self)

    @property
    def input_path(self) -> str:
        return f'["{self["_name"]}"]'

    @property
    def node_tree(self) -> 'NodeTree':
        return self.system.node_tree

    @property
    def parent(self) -> Optional['Node']:
        item = self._node_tree_item_resolve()
        depth = item["_depth"] - 1
        if depth >= 0:
            items = self.id_data.asks.tree.items.internal__
            index = items.find(item["_name"]) - 1
            while index >= 0:
                item = items[index]
                if item["_depth"] == depth: return item._node_resolve()
                index -= 1

    @property
    def shape_key(self) -> Optional[bpy.types.ShapeKey]:
        return self.id_data.key_blocks.get(self.get("_name", ""))

    @property
    def subtree(self) -> NodeSubtree:
        return NodeSubtree(self)

    @property
    def system(self) -> 'System':
        return self.id_data.asks

    @property
    def value_path(self) -> str:
        return f'key_blocks["{self["_name"]}"].value'

    def __init__(self, treenode: 'TreeNode', shapekey: bpy.types.ShapeKey) -> None:
        super().__init__(shapekey.name)
        
        id_ = self.identifier
        key = self.id_data

        min_ = shapekey.slider_min
        max_ = shapekey.slider_max
        idprop_create(key, id_, default=1.0, min=min_, max=max_, soft_min=min_, soft_max=max_)

        self["_name"] = shapekey.name
        self["input_path"] = f'["{id_}"]'
        self["_tree_path"] = f'asks.tree.nodes["{treenode["name"]}"]'

        self._value_driver_init(self._value_driver(True))

    def __load__(self) -> None:
        pass

    def __unload__(self) -> None:
        pass




    def __renamed__(self) -> None:
        for node in self.children:
            node.__parent_renamed__(self)

    def __parent_renamed__(self, node: 'Node') -> None:
        pass

    def __parented__(self, node: 'Node') -> None:
        fc = driver_ensure(self.id_data, self.value_path)
        _output_driver_init(fc.driver, self, node)

    def __unparented__(self) -> None:
        fc = driver_ensure(self.id_data, self.value_path)
        _output_driver_init(fc.driver, self)






node = key.in_betweens.internal__.add()
node.__init__(shape)
key.asks.node_tree.nodes[0].append_child(node)

key.asks.node_tree.nodes[0].append_child(key.in_betweens.add(), shapekey, )

def register():
    import sys
    asks = sys.modules.get("ASKS")
    if asks:
        asks.register_namespace()








def node_shape_key_interface_name_set(node: 'NodeShapeKeyInterface', value: str) -> None:
    pass


def _shape_key_name_update_handler(shapekey: bpy.types.ShapeKey, identifier: str) -> None:
    item = shapekey.id_data.asks.tree.items.get(identifier)
    if item:
        name = shapekey.name
        node = tree_item_node(item)
        item["_name"] = name
        node["_name"] = name
        node.__renamed__()

class NodeShapeKeyInterface(Node):

    name: bpy.props.StringProperty(
        name="Name",
        get=node_name_get,
        set=node_shape_key_interface_name_set,
        options=set()
        )

    @property
    def shape_key(self) -> Optional[bpy.types.ShapeKey]:
        return self.id_data.key_blocks.get(self["_shapekey"])

    def __init__(self, **properties: Dict[str, Any]) -> None:
        kb = properties.pop("shape_key", None)

        if kb is None:
            name = uniqname(self.id_data, properties.pop("name", "Key"))
            ob = key_object_resolve(self.id_data)
            kb = ob.shape_key_add(name=name, from_mix=False)
        elif not isinstance(kb, bpy.types.ShapeKey):
            raise TypeError()
        # FIXME
        elif kb.name in self.id_data.asks.tree.items.internal__:
            raise ValueError()

        name = kb.name
        properties.update(name=name, _shapekey=name, value_path=f'["{name}"]')
        super().__init__(**properties)

    def __load__(self) -> None:
        from bpy import msgbus
        kb = self.shape_key
        if kb:
            msgbus.susbcribe_rna(owner=_brokers.setdefault(self["name"], object()),
                                 key=kb.path_resolve("name", False),
                                 notify=_shape_key_name_update_handler,
                                 args=(kb, self["name"]))

    def __unload__(self) -> None:
        owner = _brokers.get(self["name"])
        if owner:
            from bpy import msgbus
            msgbus.clear_by_owner(owner)

    def __renamed__(self) -> None:
        kb = self.shape_key
        if kb:
            kb["name"] = self.name
            self["_shapekey"] = kb.name
        super().__renamed__()




class ShapeNode(Node, bpy.types.PropertyGroup):

    pass


def node_tree_item_name_get(item: 'TreeNode') -> str:
    return item.get("_name", "")


def node_tree_item_name_set(item: 'TreeNode', value: str) -> None:
    value = uniqname(item.id_data.asks.tree, value)
    item["_name"] = value
    node = tree_item_node(item)
    node["_name"] = value
    node.__renamed__()


class TreeNode(bpy.types.PropertyGroup):

    name: bpy.props.StringProperty(
        name="Name",
        get=node_tree_item_name_get,
        set=node_tree_item_name_set,
        options=set()
        )

    def __init__(self, type_: Type[Node], **properties: Dict[str, Any]) -> None:
        self["name"] = generate_id()
        properties["_itempath"] = f'asks.tree.internal__["{self["name"]}"]'
        node: Node = getattr(self.id_data.asks, type_.NAMESPACE).internal__.add()
        node.__init__(**properties)
        self["_nodepath"] = f'asks.{type_.NAMESPACE}["{node["name"]}"]'


def uniqname(tree: 'NodeTree', base: str) -> str:
    pass


def _node_tree_active_index_update_handler(tree: 'NodeTree', _: bpy.types.Context) -> None:
    pass


class NodeTree:

    internal__: bpy.props.PointerProperty(
        type=TreeNode,
        options={'HIDDEN'}
        )

    active_index: bpy.props.IntProperty(
        name="Node",
        min=0,
        default=0,
        update=_node_tree_active_index_update_handler,
        options=set()
        )

    @property
    def active(self) -> Optional['Node']:
        index = self.active_index
        if index < len(self): return self[index]

    def __iter__(self) -> Iterator[Node]:
        for item in self.internal__:
            yield tree_item_node(item)

    def __len__(self) -> int:
        return len(self.internal__)

    def append(self, type_: Type[Node], **properties: Dict[str, Any]) -> Node:
        '''
        '''
        if not issubclass(type_, Node):
            raise TypeError((f'{type(self)}.append(type_, **properties): '
                             f'Expected type_ to be subclass of Node, not {type(type_)}'))

        if not hasattr(self.id_data.asks, type_.NAMESPACE):
            raise ValueError((f'{type(self)}.append(type_, **properties): '
                              f'node type {type(type_)} has not been registered'))

        return _node_create(self.id_data, type_, properties)


    def insert(self, index: int, type_: Type[Node], **properties: Dict[str, Any]) -> Node:
        '''
        '''
        if not isinstance(index, int):
            raise TypeError((f'{type(self)}.insert(index, type_, **properties): '
                             f'Expected index to be int, not {type(index)}'))

        if not issubclass(type_, Node):
            raise TypeError((f'{type(self)}.insert(index, type_, **properties): '
                             f'Expected type_ to be subclass of Node, not {type(type_)}'))

        if not hasattr(self.id_data.asks, type_.NAMESPACE):
            raise ValueError((f'{type(self)}.insert(index, type_, **properties): '
                              f'node type {type(type_)} has not been registered'))

        return _node_create(self.id_data, type_, properties, index=index)

    def remove(self, node: 'Node') -> None:
        '''
        '''
        if not isinstance(node, Node):
            raise TypeError((f'{type(self)}.remove(node): '
                             f'Expected node to be Node, not {type(node)}'))

        if node.id_data != self.id_data:
            raise ValueError((f'{type(self)}.remove(node): '
                              f'node is not in tree {self}'))

        _node_remove(node)


def system_loaded(system: 'System') -> bool:
    return system.get("loaded", False)


class System(bpy.types.PropertyGroup):

    loaded: bpy.props.BoolProperty(
        name="Loaded",
        get=system_loaded,
        options=set()
        )

    node_tree: bpy.props.PointerProperty(
        type=NodeTree
        )


def _node_create(key: bpy.types.Key,
                 type_: Type[Node],
                 properties: Dict[str, Any],
                 parent: Optional['Node']=None,
                 index: Optional[int]=None) -> 'Node':

    pass


def _node_remove(node: 'Node') -> None:
    pass


def _on_file_load(_) -> None:
    import bpy
    for key in bpy.data.shape_keys:
        if key.is_property_set("asks"):
            sys = key.asks
            if sys.loaded:
                for node in sys.tree:
                    node.__load__()

