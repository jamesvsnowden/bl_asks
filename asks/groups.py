
from typing import Iterator, TYPE_CHECKING, List, Optional, Set, Tuple, Union
from bpy.types import Operator, PropertyGroup
from bpy.props import CollectionProperty, StringProperty
from .utils import PollSystemEnabled
if TYPE_CHECKING:
    from bpy.types import Context
    from .nodes import Node


def name_get(group: 'NodeGroup') -> str:
    return group.get("name", "")


def name_set(group: 'NodeGroup', name: str) -> None:
    groups = group.id_data.asks.groups

    value = name
    index = 0
    while value in groups:
        index += 1
        value = f'{name}.{str(index).zfill(3)}'

    for node in group.nodes():
        node.group__ = value

    group["name"] = value


class NodeGroup(PropertyGroup):

    name: StringProperty(
        name="Name",
        get=name_get,
        set=name_set,
        options=set()
        )

    def nodes(self) -> Iterator['Node']:
        name = self.name
        return filter(lambda node: node.group == name, self.id_data.asks.nodes)

    def __init__(self, name: Optional[str]="Group") -> None:
        self.name = name


class NodeGroups(PropertyGroup):

    internal__: CollectionProperty(
        type=NodeGroup,
        options={'HIDDEN'}
        )

    def __contains__(self, key: str) -> bool:
        return key in self.internal__

    def __iter__(self) -> Iterator[NodeGroup]:
        return iter(self.internal__)

    def __len__(self) -> int:
        return len(self.internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[NodeGroup, List[NodeGroup]]:
        return self.internal__[key]

    def get(self, key: str) -> Optional[NodeGroup]:
        return self.internal__.get(key)

    def keys(self) -> Iterator[str]:
        return self.internal__.keys()

    def items(self) -> Iterator[Tuple[str, NodeGroup]]:
        return self.internal__.items()

    def values(self) -> Iterator[NodeGroup]:
        return self.internal__.values()

class ASKS_OT_group_add(PollSystemEnabled, Operator):
    bl_idname = "asks.group_add"
    bl_label = "Add Group"
    bl_description = ""
    bl_options = {'INTERNAL', 'UNDO'}

    name: StringProperty(
        name="Name",
        default="Group",
        options=set()
        )

    def execute(self, context: 'Context') -> Set[str]:
        context.object.data.shape_keys.asks.groups.internal__.add().__init__(self.name)
        return {'FINISHED'}
