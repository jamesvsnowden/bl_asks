

from typing import Optional, Protocol, TYPE_CHECKING, Sequence, Set, Tuple
import bpy
from bpy.types import Operator, PropertyGroup
from .curve_component import CurveComponent
if TYPE_CHECKING:
    from bpy.types import CurveMapping, ShaderNodeTree


class CurvePointProtocol(Protocol):
    handle_type: str
    location: Tuple[float, float]
    select: bool


class CurveProtocol(Protocol):
    extend: str
    points: Sequence[CurvePointProtocol]


_editing = set()

def _differ(component: CurveComponent, mapping: 'CurveMapping') -> bool:
    if component.extend != mapping.extend:
        return True
    else:
        cpts = component.points
        mpts = mapping.curves[0].points
        if len(cpts) != len(mpts):
            return True
        else:
            for cpt, mpt in zip(cpts, mpts):
                if cpt.handle_type != mpt.handle_type:
                    return True
                else:
                    aco = cpt.location
                    bco = mpt.location
                    if aco[0] != bco[0] or aco[1] != bco[1]:
                        return True
        return False


def _check_for_updates() -> None:
    for curve in _editing:
        tree = CurveMappingManager.node_tree_get()
        if tree is not None:
            node = tree.nodes.get(curve.node_identifier)
            if node is not None:
                mapping = node.mapping
                if _differ(curve, mapping):
                    curve.update(mapping.curves[0].points, mapping.extend)
    _editing.clear()


class ASKS_OT_curve_reload(Operator):

    bl_idname = "blcmap.node_ensure"
    bl_label = "Ensure Curve"
    bl_description = "Ensure the curve exists"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return isinstance(getattr(context, "curve", None), CurveComponent)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        curve: Optional[CurveComponent] = getattr(context, "curve", None)
        if not isinstance(curve, CurveComponent):
            self.report({'ERROR'}, (f'{self.__class__.__name__} '
                                    f'Invalid context.curve {curve.__class__.__name__}'))
            return {'CANCELLED'}
        curve.system.curve_mapping_manager.node_set(curve.name, curve)
        return {'FINISHED'}


class ASKS_OT_curve_point_remove(Operator):

    bl_idname = "asks.curve_point_remove"
    bl_label = "Remove"
    bl_description = "Remove selected points"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return isinstance(getattr(context, "curve", None), CurveComponent)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        tree = CurveMappingManager.node_tree_get()
        if tree:
            data: CurveComponent = getattr(context, "curve")
            node = tree.nodes.get(data.name)
            if node:
                curve = node.mapping.curves[0]
                for point in reversed(list(filter(lambda pt: pt.select, curve.points))):
                    curve.points.remove(point)
                node.mapping.update()
        return {'FINISHED'}


class ASKS_OT_curve_point_handle_type_set(Operator):

    bl_idname = "asks.curve_point_handle_type_set"
    bl_label = "Handle Type"
    bl_description = "Set the handle type of selected curve point(s)"
    bl_options = {'INTERNAL'}

    handle_type: bpy.props.EnumProperty(
        name="Handle Type",
        description="Curve interpolation at this point: Bezier or vector",
        items=[
            ('AUTO'        , "Auto Handle"        , "", 'HANDLE_AUTO', 0),
            ('AUTO_CLAMPED', "Auto Clamped Handle", "", 'HANDLE_AUTOCLAMPED', 1),
            ('VECTOR'      , "Vector Handle"      , "", 'HANDLE_VECTOR', 2),
            ],
        default='AUTO',
        options=set(),
        )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return isinstance(getattr(context, "curve", None), CurveComponent)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        tree = CurveMappingManager.node_tree_get()
        if tree:
            data: CurveComponent = getattr(context, "curve")
            node = tree.nodes.get(data.name)
            if node:
                value = self.handle_type
                for point in node.mapping.curves[0].points:
                    if point.select:
                        point.handle_type = value
                node.mapping.update()
        return {'FINISHED'}


class CurveMappingManager(PropertyGroup):

    @staticmethod
    def enable_editor(component: CurveComponent) -> None:
        _editing.add(component)
        if not bpy.app.timers.is_registered(_check_for_updates):
            bpy.app.timers.register(_check_for_updates, first_interval=1.0)

    @staticmethod
    def node_tree_get(ensure: Optional[bool]=False) -> Optional['ShaderNodeTree']:
        tree = bpy.data.node_groups.get('ASKS')
        if tree is None and ensure:
            tree = bpy.data.node_groups.new('ASKS', "ShaderNodeTree")
            tree.use_fake_user = True
        return tree

    def node_get(self, name: str) -> bool:
        tree = self.node_tree_get()
        return tree is not None and tree.nodes.get(name) is not None

    def node_set(self, name: str, data: CurveProtocol) -> None:
        tree = self.node_tree_get(True)
        node = tree.nodes.get(name)

        if node is None:
            node = tree.nodes.new("ShaderNodeVectorCurve")
            node.name = name

        mapping = node.mapping
        mapping.clip_min_x = 0.0
        mapping.clip_max_x = 1.0
        mapping.clip_min_y = 0.0
        mapping.clip_max_y = 1.0
        mapping.use_clip = True
        mapping.extend = data.extend

        length = max(len(data.points), 2)
        points = mapping.curves[0].points

        while len(points) > length: points.remove(points[-2])
        while len(points) < length: points.new(0.0, 0.0)

        for point, props in zip(points, data.points):
            point.handle_type = props.handle_type
            point.location = props.location
            point.select = props.select

        mapping.update()

    def node_remove(self, name: str) -> None:
        tree = self.node_tree_get(False)
        if tree is not None:
            node = tree.nodes.get(name)
            if node is not None:
                tree.nodes.remove(node)
