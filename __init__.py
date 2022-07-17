
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4
from bpy.types import PropertyGroup
from bpy.props import StringProperty
import bpy


def _broadcast(origin: PropertyGroup,
               target: PropertyGroup,
               handle: str,
               *args: Tuple[Any],
               **kwargs: Dict[str, Any]) -> None:
    for key in target.keys():
        value = getattr(target, key, None)
        if isinstance(value, PropertyGroup):
            handler = getattr(value, handle, None)
            if callable(handler):
                handler(origin, *args, **kwargs)
            _broadcast(origin, value, handler, *args, **kwargs)


def broadcast(origin: PropertyGroup,
                    event: str,
                    *args: Tuple[Any],
                    **kwargs: Dict[str, Any]) -> None:
    _broadcast(origin, origin, f'on_{event.lower()}', *args, **kwargs)


def dispatch(origin: PropertyGroup,
                   event: str,
                   *args: Tuple[Any],
                   **kwargs: Dict[str, Any]) -> None:
    path: str = origin.path_from_id()
    if "." in path:
        try:
            target = origin.id_data.path_resolve(path.rpartition(".")[0])
        except ValueError:
            pass
        else:
            if isinstance(target, PropertyGroup):
                handler = getattr(target, f'on_{event.lower()}', None)
                if not callable(handler) or handler(*args, **kwargs) is not False:
                    dispatch_event(target, event, *args, **kwargs)


class Data:

    pass


class Node(PropertyGroup):

    identifier: StringProperty(
        get=lambda self: self.get("identifier", ""),
        options={'HIDDEN'}
        )

    data_path: StringProperty(
        options={'HIDDEN'}
        )

    @property
    def data(self) -> Optional[PropertyGroup]:
        try:
            return self.id_data.path_resolve(self.data_path)
        except ValueError:
            return None

    icon: StringProperty(
        get=lambda self: self.get("icon", 'NONE'),
        options={'HIDDEN'}
        )

    name: StringProperty(

        )

    @property
    def parent(self) -> Optional['Node']:
        pass

    def __init__(self, data: Optional[PropertyGroup]=None) -> None:
        if data:
            self["data_path"] = data.path_from_id()


class Item(PropertyGroup):

   #name: StringProperty()
    node: StringProperty()


class Nodes(PropertyGroup):

    nodes__: CollectionProperty(

        )

    items__: CollectionProperty(
        type=PropertyGroup
        )

    def new(self, name: Optional[str]="Key", data: Optional[PropertyGroup]=None) -> Node:
        node = self.nodes__.add()
        node["name"] = name
        node.__init__(data)
        
        item = self.items__.add()
        item["name"] = node.identifier
        item["node"] = node.name

        return node

    def get(self, name: str) -> Optional[Node]:
        pass

    def lookup(self, identifier: str) -> Optional[Node]:
        pass


class Tree(bpy.types.PropertyGroup):

    pass