
from typing import Set, Type, TYPE_CHECKING
from uuid import uuid4
from asks.utils import PollActiveNode
from bpy.types import DATA_PT_shape_keys, NodeTree, Operator, Panel, PropertyGroup, UILayout, UIList
from bpy.props import BoolProperty, PointerProperty, StringProperty
from .config import COMPAT_ENGINES, COMPAT_OBJECTS
from .nodes import Nodes
from .groups import NodeGroups
if TYPE_CHECKING:
    from bpy.types import Context
    from .nodes import Node


class System(PropertyGroup):

    nodetree__: PointerProperty(type=NodeTree)

    enabled: BoolProperty(
        name="Enabled",
        get=lambda self: self.get("enabled", False),
        options=set()
        )

    identifier: StringProperty(
        name="Identifier",
        get=lambda self: self.get("identifier", ""),
        options=set()
        )

    groups: PointerProperty(
        name="Groups",
        type=NodeGroups,
        options=set()
        )

    nodes: PointerProperty(
        name="Nodes",
        type=Nodes,
        options=set()
        )

    def __init__(self) -> None:
        import bpy
        self["identifier"] = f'asks_{uuid4().hex}'
        self.nodetree__ = bpy.data.node_groups.new(self.identifier, "ShaderNodeTree")
        key = self.id_data
        
        basis = self.nodes.internal__.add()
        basis["identifier"] = f'asks_node_{uuid4().hex}'
        basis["name"] = key.key_blocks[0].name
        basis["depth"] = 0
        basis.curve.__init__()
        key[basis.identifier] = 1.0

        children = basis.children
        for kb in key.key_blocks[1:]:
            children.add(kb)

        self["enabled"] = True

    def __dispose__(self) -> None:
        self["enabled"] = False


class ASKS_OT_system_enable(Operator):
    bl_idname = "asks.system_enable"
    bl_label = "Enable Advanced Shape Key System"
    bl_description = ""
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        engine = context.engine
        if engine in COMPAT_ENGINES:
            obj = context.object
            if obj is not None and obj.type in COMPAT_OBJECTS:
                key = obj.data.shape_keys
                return key is None or not key.is_property_set("asks") or not key.asks.enabled

    def execute(self, context: 'Context') -> Set[str]:
        context.object.data.shape_keys.asks.__init__()
        return {'FINISHED'}


SHAPE_KEYS_PANEL_POLL_ORIGINAL = DATA_PT_shape_keys.poll


def _shape_keys_panel_poll_override(cls: Type[Panel], context: 'Context') -> bool:
    engine = context.engine
    if engine in COMPAT_ENGINES:
        obj = context.object
        if obj is not None and obj.type in COMPAT_OBJECTS:
            key = obj.data.shape_keys
            return key is None or not key.is_property_set("asks") or not key.asks.enabled
    return False


class ASKS_PT_shape_keys_subpanel(Panel):
    bl_idname = "ASKS_PT_shape_keys_subpanel"
    bl_label = "ASKS"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'HIDE_HEADER'}
    bl_parent_id = "DATA_PT_shape_keys"

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        engine = context.engine
        if engine in COMPAT_ENGINES:
            obj = context.object
            if obj is not None and obj.type in COMPAT_OBJECTS:
                key = obj.data.shape_keys
                return ((key is not None
                         and key.use_relative
                         and len(key.key_blocks) > 0)
                         and (not key.is_property_set("asks")
                              or not key.asks.enabled))
        return False

    def draw(self, _) -> None:
        self.layout.operator("asks.system_enable")


class ASKS_UL_shape_keys(UIList):

    sep_icon = 0

    def filter_items(self, _, nodes: Nodes, prop):

        nodes = getattr(nodes, prop)
        flags = [self.bitflag_filter_item] * len(nodes)
        count = len(nodes)
        order = list(range(count))
        depth = -1

        for index, node in enumerate(nodes):

            if depth > -1 and node.depth > depth:
                flags[index] &= ~self.bitflag_filter_item
                continue

            if (not node.show_expanded
                and index < count - 1
                and nodes[index+1].depth == node.depth + 1
                ):
                depth = node.depth
                continue

            depth = -1

        return flags, order

    def draw_item(self, _0, layout: 'UILayout', nodes: 'Nodes', node: 'Node', _2, _3, _4, index: int) -> None:
        sep = self.sep_icon
        spl = layout.split(factor=0.4)
        spl.emboss = 'NONE'

        tree = spl.row(align=True)
        opts = spl.row(align=True)

        opts_data = opts.row(align=True)
        opts_ctrl = opts.row(align=True)
        opts_ctrl.label(icon_value=sep)

        opts_data_spl = opts_data.split(factor=0.5)
        opts_data_wgt = opts_data_spl.row(align=True)
        opts_data_wgt.label(icon_value=sep)
        opts_data_val = opts_data_spl.row(align=True)
        opts_data_val.label(icon_value=sep)

        depth = node.depth
        shape = node.shape_key

        if depth:
            for _ in range(node.depth - 1):
                tree.label(icon_value=sep)

            if index < len(nodes) - 1 and nodes[index + 1].depth > depth:
                tree.prop(node, "show_expanded",
                         text="",
                         icon=f'DISCLOSURE_TRI_{"DOWN" if node.show_expanded else "RIGHT"}',
                         emboss=False)
            else:
                tree.label(icon_value=sep)

        # name
        icon = node.icon_value
        if icon:
            tree.prop(node, "name",
                      text="",
                      translate=False,
                      icon_value=icon)
        else:
            icon = node.icon
            tree.prop(node, "name",
                      text="",
                      translate=False,
                      icon=icon)

        # weight value
        if depth:
            driver = node.driver
            if driver:
                opts_data_wgt.context_pointer_set("node", node)
                opts_data_wgt.prop(driver, "mute",
                                   text="",
                                   icon_value=UILayout.enum_item_icon(driver, "type", driver.type))
                opts_data_wgt.popover('ASKS_PT_weight_popover',
                                      text="",
                                      icon='DOWNARROW_HLT')
            else:
                opts_data_wgt.label(icon='BLANK1')
                opts_data_wgt.operator_menu_enum("ASKS_OT_driver_add", "type",
                                                 text="",
                                                 icon='DOWNARROW_HLT'
                                                 ).node_target = node.name
            # TODO prop not extant
            subrow = opts_data_wgt.row(align=True)
            subrow.enabled = driver is None or driver.mute
            subrow.prop(node.id_data, f'["{node.identifier}"]', text="")
        else:
            subrow = opts_data_wgt.row(align=True)
            subrow.alignment = 'CENTER'
            subrow.label(text="WEIGHT")

        # interpolated value
        if depth:
            opts_data_val.prop(node, "is_interpolated",
                               text="",
                               icon=f'RADIOBUT_{"ON" if node.is_interpolated else "OFF"}')

            subrow = opts_data_val.row(align=True)
            subrow.enabled = node.is_interpolated
            subrow.context_pointer_set("node", node)
            subrow.popover('ASKS_PT_interpolation_popover', text="", icon='DOWNARROW_HLT')

            subrow = opts_data_val.row(align=True)
            subrow.enabled = not node.is_interpolated
            subrow.prop(shape, "value", text="")
        else:
            subrow = opts_data_val.row(align=True)
            subrow.alignment = 'CENTER'
            subrow.label(text="INTERPOLATED")

        # controls
        if depth:
            opts_ctrl.prop(shape, "mute",
                           text="",
                           icon=f'CHECKBOX_{"DE" if shape.mute else ""}HLT',
                           emboss=False)
            
        else:
            opts_ctrl.label(icon='BLANK1')


class ASKS_PT_shape_keys(PollActiveNode, Panel):
    bl_idname = "ASKS_PT_shape_keys"
    bl_label = "Shape Keys"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    def draw(self, context: 'Context') -> None:
        layout = self.layout
        nodes = context.object.data.shape_keys.asks.nodes
        row = layout.row()
        col = row.column()
        col.template_list("ASKS_UL_shape_keys", "", nodes, "internal__", nodes, "active_index", rows=10)
        col = row.column(align=True)
        col.operator("ASKS_OT_node_add", text="", icon='ADD')
