
from typing import Dict, Iterator, List, Optional, Protocol, Sequence, Set, Tuple, Union, TYPE_CHECKING
from uuid import uuid4
from dataclasses import dataclass
from asks.utils import split_layout
from mathutils import Vector
from bpy.types import FCurve, Operator, PropertyGroup, UILayout
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatVectorProperty, PointerProperty, StringProperty
from bpy.app import timers
from .events import EventDispatcher
if TYPE_CHECKING:
    from bpy.types import Context, CurveMapping, NodeMapping, NodeTree

class CurvePointProtocol(Protocol):
    location: Tuple[float, float]
    handle_type: str
    select: bool

#region Utilities
#--------------------------------------------------------------------------------------------------

_active_curves: Set['Curve'] = set()

def _check_curves_match(curve: 'Curve', mapping: 'CurveMapping') -> bool:
    cpts = curve.points
    mpts = mapping.curves[0].points
    if len(cpts) != len(mpts):
        return True
    for cpt, mpt in zip(cpts, mpts):
        if cpt.handle_type != mpt.handle_type:
            return True
        aco = cpt.location
        bco = mpt.location
        if aco[0] != bco[0] or aco[1] != bco[1]:
            return True
    return False


def _check_active_curves():
    for curve in _active_curves:
        tree = curve.id_data.asks.nodetree__
        if tree is not None:
            node = tree.nodes.get(curve.identifier)
            if node is not None and _check_curves_match(curve, node.mapping):
                # TODO remap curve points to 0-1 ranges ?
                curve.points.__init__(node.mapping.curves[0].points)
                curve.dispatch("updated")
    _active_curves.clear()


def _calc_bezier_handles(p2, ht, h1, h2, prev=None, next=None) -> None:
    pt = Vector((0.0, 0.0))

    if prev is None:
        p3 = next
        pt[0] = 2.0 * p2[0] - p3[0]
        pt[1] = 2.0 * p2[1] - p3[1]
        p1 = pt
    else:
        p1 = prev

    if next is None:
        p1 = prev
        pt[0] = 2.0 * p2[0] - p1[0]
        pt[1] = 2.0 * p2[1] - p1[1]
        p3 = pt
    else:
        p3 = next

    dvec_a = p2 - p1
    dvec_b = p3 - p2
    len_a = dvec_a.length
    len_b = dvec_b.length

    if len_a == 0.0:
        len_a = 1.0
    if len_b == 0.0:
        len_b = 1.0

    if ht in ('AUTO', 'AUTO_CLAMPED'):
        tvec = Vector((
            dvec_b[0] / len_b + dvec_a[0] / len_a,
            dvec_b[1] / len_b + dvec_a[1] / len_a))

        length = tvec.length * 2.5614
        if length != 0.0:
            ln = -(len_a / length)
            h1[0] = p2[0] + tvec[0] * ln
            h1[1] = p2[1] + tvec[1] * ln
            if ht == 'AUTO_CLAMPED' and prev is not None and next is not None:
                ydiff1 = prev[1] - p2[1]
                ydiff2 = next[1] - p2[1]
                if (ydiff1 <= 0.0 and ydiff2 <= 0.0) or (ydiff1 >= 0.0 and ydiff2 >= 0.0):
                    h1[1] = p2[1]
                else:
                    if ydiff1 <= 0.0:
                        if prev[1] > h1[1]:
                            h1[1] = prev[1]
                    else:
                        if prev[1] < h1[1]:
                            h1[1] = prev[1]

            ln = len_b / length
            h2[0] = p2[0] + tvec[0] * ln
            h2[1] = p2[1] + tvec[1] * ln
            if ht == 'AUTO_CLAMPED' and prev is not None and next is not None:
                ydiff1 = prev[1] - p2[1]
                ydiff2 = next[1] - p2[1]
                if (ydiff1 <= 0.0 and ydiff2 <= 0.0) or (ydiff1 >= 0.0 and ydiff2 >= 0.0):
                    h2[1] = p2[1]
                else:
                    if ydiff1 <= 0.0:
                        if next[1] < h2[1]:
                            h2[1] = next[1]
                    else:
                        if next[1] > h2[1]:
                            h2[1] = next[1]

    else: # ht == VECTOR
        h1[0] = p2[0] + dvec_a[0] * (-1.0/3.0)
        h1[1] = p2[1] + dvec_a[1] * (-1.0/3.0)
        h2[0] = p2[0] + dvec_b[0] * (1.0/3.0)
        h2[1] = p2[1] + dvec_b[1] * (1.0/3.0)


def _get_node_tree(curve: 'Curve', ensure: Optional[bool]=False) -> Optional['NodeTree']:
    asks = curve.id_data.asks
    tree = asks.nodetree__
    if tree is None and ensure:
        import bpy
        tree = bpy.data.node_groups.new(name=f'asks_node_tree_{asks.identifier}')
        asks.nodetree__ = tree
    return tree


def _add_node(curve: 'Curve') -> None:
    tree = _get_node_tree(curve, True)
    node = tree.nodes.new("ShaderNodeVectorCurve")
    node.name = curve.identifier
    mapping = node.mapping
    mapping.extend = 'HORIZONTAL'
    mapping.clip_min_x = 0.0
    mapping.clip_max_x = 1.0
    mapping.clip_min_y = 0.0
    mapping.clip_max_y = 1.0
    mapping.use_clip = True
    mapping.update()

#endregion Utilities

#region Presets
#--------------------------------------------------------------------------------------------------


@dataclass
class CurvePointPreset:
    location: Tuple[float, float] = (0.0, 0.0)
    handle_type: str = 'AUTO'
    select: bool = False


PRESETS: Dict[str, Tuple[CurvePointPreset]] = {}

PRESETS['LINEAR'] = (
    CurvePointPreset((0.0, 0.0), 'VECTOR'),
    CurvePointPreset((1.0, 1.0), 'VECTOR'),
    )

PRESETS['SINE_IN'] = (
    CurvePointPreset((0.0, 0.0) , 'AUTO'),
    CurvePointPreset((0.1, 0.03), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0) , 'AUTO'),
    )

PRESETS['SINE_OUT'] = (
    CurvePointPreset((0.0, 0.0) , 'AUTO'),
    CurvePointPreset((0.9, 0.97), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0) , 'AUTO'),
    )

PRESETS['SINE_IN_OUT'] = (
    CurvePointPreset((0.0, 0.0) , 'AUTO'),
    CurvePointPreset((0.1, 0.03), 'AUTO_CLAMPED'),
    CurvePointPreset((0.9, 0.97), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0) , 'AUTO'),
    )

PRESETS['QUAD_IN'] = (
    CurvePointPreset((0.0, 0.0)   , 'AUTO'),
    CurvePointPreset((0.15, 0.045), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0)   , 'AUTO'),
    )

PRESETS['QUAD_OUT'] = (
    CurvePointPreset((0.0, 0.0)   , 'AUTO'),
    CurvePointPreset((0.85, 0.955), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0)   , 'AUTO'),
    )

PRESETS['QUAD_IN_OUT'] = (
    CurvePointPreset((0.0, 0.0)   , 'AUTO'),
    CurvePointPreset((0.15, 0.045), 'AUTO_CLAMPED'),
    CurvePointPreset((0.85, 0.955), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0)   , 'AUTO'),
    )

PRESETS['CUBIC_IN'] = (
    CurvePointPreset((0.0, 0.0) , 'AUTO'),
    CurvePointPreset((0.2, 0.03), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0) , 'AUTO'),
    )

PRESETS['CUBIC_OUT'] = (
    CurvePointPreset((0.0, 0.0) , 'AUTO'),
    CurvePointPreset((0.8, 0.97), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0) , 'AUTO'),
    )

PRESETS['CUBIC_IN_OUT'] = (
    CurvePointPreset((0.0, 0.0) , 'AUTO'),
    CurvePointPreset((0.2, 0.03), 'AUTO_CLAMPED'),
    CurvePointPreset((0.8, 0.97), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0) , 'AUTO'),
    )

PRESETS['QUART_IN'] = (
    CurvePointPreset((0.0, 0.0)  , 'AUTO'),
    CurvePointPreset((0.25, 0.03), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0)  , 'AUTO'),
    )

PRESETS['QUART_OUT'] = (
    CurvePointPreset((0.0, 0.0)  , 'AUTO'),
    CurvePointPreset((0.75, 0.97), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0)  , 'AUTO'),
    )

PRESETS['QUART_IN_OUT'] = (
    CurvePointPreset((0.0, 0.0)  , 'AUTO'),
    CurvePointPreset((0.25, 0.03), 'AUTO_CLAMPED'),
    CurvePointPreset((0.75, 0.97), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0)  , 'AUTO'),
    )

PRESETS['QUINT_IN'] = (
    CurvePointPreset((0.0, 0.0)    , 'AUTO'),
    CurvePointPreset((0.275, 0.025), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0)    , 'AUTO'),
    )

PRESETS['QUINT_OUT'] = (
    CurvePointPreset((0.0, 0.0)    , 'AUTO'),
    CurvePointPreset((0.725, 0.975), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0)    , 'AUTO'),
    )

PRESETS['QUINT_IN_OUT'] = (
    CurvePointPreset((0.0, 0.0)    , 'AUTO'),
    CurvePointPreset((0.275, 0.025), 'AUTO_CLAMPED'),
    CurvePointPreset((0.725, 0.975), 'AUTO_CLAMPED'),
    CurvePointPreset((1.0, 1.0)    , 'AUTO'),
    )

#endregion Presets

#region Points
#--------------------------------------------------------------------------------------------------

HANDLE_TYPE_ENUM_ITEMS = [
    ('AUTO'        , "Auto Handle"        , "", 'HANDLE_AUTO', 0),
    ('AUTO_CLAMPED', "Auto Clamped Handle", "", 'HANDLE_AUTOCLAMPED', 1),
    ('VECTOR'      , "Vector Handle"      , "", 'HANDLE_VECTOR', 2),
    ]

HANDLE_TYPE_ENUM_INDEX = {
    _item[0]: _item[4] for _item in HANDLE_TYPE_ENUM_ITEMS
    }


def _curve_point_update(point: 'CurvePoint', context: 'Context') -> None:
    curve: 'Curve' = point.id_data.path_resolve(curve.path_from_id().rpartition(".points")[0])
    curve.__load__()
    curve.dispatch("updated")


class CurvePoint(PropertyGroup):

    handle_type: EnumProperty(
        name="Handle Type",
        description="Curve interpolation at this point: Bezier or vector",
        items=HANDLE_TYPE_ENUM_ITEMS,
        default='AUTO_CLAMPED',
        options=set(),
        update=_curve_point_update
        )

    location: FloatVectorProperty(
        name="Location",
        description="X/Y coordinates of the curve point",
        size=2,
        subtype='XYZ',
        default=(0.0, 0.0),
        options=set(),
        update=_curve_point_update
        )

    select: BoolProperty(
        name="Select",
        description="Selection state of the curve point",
        default=False,
        options=set(),
        update=_curve_point_update
        )

    def __init__(self, data: CurvePointProtocol) -> None:
        self["handle_type"] = HANDLE_TYPE_ENUM_INDEX[data.handle_type]
        self["location"] = tuple(data.location)
        self["select"] = data.select


class CurvePoints(PropertyGroup):

    internal__: CollectionProperty(
        type=CurvePoint,
        options={'HIDDEN'}    
        )

    def __init__(self, points: Sequence[CurvePointProtocol]) -> None:
        items_ = self.internal__
        length = len(items_)
        number = len(points)
        while length > number:
            items_.remove(0)
            length -= 1
        while length < number:
            items_.add()
            length += 1
        for item, point in zip(items_, points):
            item.__init__(point)

    def __contains__(self, point: CurvePoint) -> bool:
        return any(x == point for x in self)

    def __iter__(self) -> Iterator[CurvePoint]:
        return iter(self.internal__)

    def __len__(self) -> int:
        return len(self.internal__)

    def __getitem__(self, key: Union[int, slice]) -> Union[CurvePoint, List[CurvePoint]]:
        return self.internal__[key]

#endregion Points

#region Curve
#--------------------------------------------------------------------------------------------------

EASING_ENUM_ITEMS = [
    ('EASE_IN'    , "In"      , "Ease in"        , 'IPO_EASE_IN'    , 0),
    ('EASE_OUT'   , "Out"     , "Ease out"       , 'IPO_EASE_OUT'   , 1),
    ('EASE_IN_OUT', "In & Out", "Ease in and out", 'IPO_EASE_IN_OUT', 2),
    ]

EASING_ENUM_INDEX = {
    _item[0]: _item[4] for _item in EASING_ENUM_ITEMS
    }

TYPE_ENUM_ITEMS = [
    ('LINEAR', "Linear"      , "Linear"          , 'IPO_LINEAR', 0),
    ('SINE'  , "Sinusoidal"  , "Sinusoidal"      , 'IPO_SINE'  , 1),
    ('QUAD'  , "Quadratic"   , "Quadratic"       , 'IPO_QUAD'  , 2),
    ('CUBIC' , "Cubic"       , "Cubic"           , 'IPO_CUBIC' , 3),
    ('QUART' , "Quartic"     , "Quartic"         , 'IPO_QUART' , 4),
    ('QUINT' , "Quintic"     , "Quintic"         , 'IPO_QUINT' , 5),
    None,
    ('CUSTOM', "Custom"      , "Use custom curve", 'FCURVE'    , 6),
    ]

TYPE_ENUM_INDEX = {
    _item[0]: _item[4] for _item in TYPE_ENUM_ITEMS if _item
    }


def _curve_easing_update_handler(curve: 'Curve', _: 'Context') -> None:
    type_ = curve.type
    if type_ not in {'CUSTOM', 'LINEAR'}:
        pts = PRESETS[f'{type_}{curve.easing[4:]}']
        curve.points.__init__(pts)
        curve.__load__()
        curve.dispatch("updated")


def _curve_type_update_handler(curve: 'Curve', _: 'Context') -> None:
    type_ = curve.type
    if type_ != 'CUSTOM':
        pts = PRESETS[type_] if type_ == 'LINEAR' else PRESETS[f'{type_}{curve.easing[4:]}']
        curve.points.__init__(pts)
        curve.__load__()
        curve.dispatch("updated")


class Curve(EventDispatcher, PropertyGroup):

    easing: EnumProperty(
        name="Easing",
        items=EASING_ENUM_ITEMS,
        default='EASE_IN_OUT',
        options=set(),
        update=_curve_easing_update_handler
        )

    identifier: StringProperty(
        name="Identifier",
        get=lambda self: self.get("identifier", ""),
        options=set()
        )

    points: PointerProperty(
        name="Points",
        type=CurvePoints,
        options=set()
        )

    type: EnumProperty(
        name="Type",
        items=TYPE_ENUM_ITEMS,
        default='LINEAR',
        options=set(),
        update=_curve_type_update_handler
        )

    def __init__(self) -> None:
        self["identifier"] = f'asks_curve_{uuid4().hex}'
        self.points.__init__(PRESETS['LINEAR'])
        _add_node(self)

    def __load__(self) -> None:
        tree = _get_node_tree(self)
        if tree:
            node = tree.nodes.get(self.identifier)
            if node:
                pts = node.mapping.curves[0].points
                amt = len(self.points)
                while len(pts) > amt: pts.remove(pts[-2])
                while len(pts) < amt: pts.new(0.0, 0.0)
                for pt, data in zip(pts, self.points):
                    pt.handle_type = data.handle_type
                    pt.location = data.location
                    pt.select = data.select
                node.mapping.update()

    def assign(self,
               fcurve: FCurve,
               input_range: Optional[Tuple[float, float]]=None,
               value_range: Optional[Tuple[float, float]]=None) -> None:

        if not isinstance(fcurve, FCurve):
            raise TypeError()

        pts = [(
            p.location.copy(),
            p.handle_type,
            Vector((0.0, 0.0)),
            Vector((0.0, 0.0))
            ) for p in self.points.internal__]

        if input_range:
            a, b = input_range
            if a > b:
                a, b = b, a
                for pt in pts:
                    co = pt[0]
                    co[0] = 1.0 - co[0]
                pts.reverse()
            d = b - a
            for pt in pts:
                co = pt[0]
                co[0] = a + co[0] * d

        if value_range:
            a, b = value_range
            if a > b:
                a, b = b, a
                for pt in pts:
                    co = pt[0]
                    co[1] = 1.0 - co[1]
                pts.reverse()
            d = b - a
            for pt in pts:
                co = pt[0]
                co[1] = a + co[1] * d

        n = len(pts) - 1
        for i, (pt, ht, h1, h2) in enumerate(pts):
            _calc_bezier_handles(pt, ht, h1, h2,
                                pts[i-1][0] if i > 0 else None,
                                pts[i+1][0] if i < n else None)

        if len(pts) > 2:
            ptA, htA, h1A, h2A = pts[0]
            ptN, htN, h1N, h2N = pts[-1]

            if htA == 'AUTO':
                hlen = (h2A - ptA).length
                hvec = pts[1][2].copy()
                if hvec[0] < ptA[0]:
                    hvec[0] = ptA[0]

                hvec -= ptA
                nlen = hvec.length
                if nlen > 0.00001:
                    hvec *= hlen / nlen
                    h2A[0] = hvec[0] + ptA[0]
                    h2A[1] = hvec[1] + ptA[1]
                    h1A[0] = ptA[0] - hvec[0]
                    h1A[1] = ptA[1] - hvec[1]

            if htN == 'AUTO':
                hlen = (h1N - ptN).length
                hvec = pts[-2][3].copy()
                if hvec[0] > ptN[0]:
                    hvec[0] = ptN[0]

                hvec -= ptN
                nlen = hvec.length
                if nlen > 0.00001:
                    hvec *= hlen / nlen
                    h1N[0] = hvec[0] + ptN[0]
                    h1N[1] = hvec[1] + ptN[1]
                    h2N[0] = ptN[0] - hvec[0]
                    h2N[1] = ptN[1] - hvec[1]

        pt = pts[0]
        co = pt[0]
        hl = pt[2]
        hl[0] = 0.0
        hl[1] = co[1]

        pt = pts[-1]
        co = pt[0]
        hr = pt[3]
        hr[0] = 1.0
        hr[1] = co[1]

        kfs = fcurve.keyframe_points
        nkf = len(kfs)
        npt = len(pts)

        while nkf > npt:
            kfs.remove(kfs[-1])
            nkf -= 1

        for i, pt in enumerate(pts):
            if i < nkf:
                kf = kfs[i]
            else:
                co = pt[0]
                kf = kfs.insert(co[0], co[1])
            
            kf.interpolation = 'BEZIER'
            kf.easing = 'AUTO'
            kf.co = pt[0]
            kf.handle_left_type = 'FREE'
            kf.handle_right_type = 'FREE'
            kf.handle_left = pt[2]
            kf.handle_right = pt[3]


def draw_curve(layout: 'UILayout',
               curve: Curve,
               heading: Optional[str]="Curve") -> 'UILayout':

    _, fields, extras = split_layout(layout, heading=heading, decorate=True)

    box = fields.box()
    box.context_pointer_set("curve", curve)
    box.operator_context = 'INVOKE_DEFAULT'

    # if (not curve.is_property_set("node_identifier") or
    #     not nodetree_node_exists(curve.node_identifier)
    #     ):
    #     row = box.row()
    #     row.label(icon='ERROR', text="Missing Curve")
    #     row.operator(BLCMAP_OT_node_ensure.bl_idname, text="Reload")
    #     return

    node = curve.id_data.asks.nodetree__.nodes[curve.identifier]

    header = box.row()
    header.ui_units_y = 0.01

    split = header.split(factor=0.5)
    leading = split.row(align=True)
    trailing = split.row(align=True)

    type_ = curve.type
    if type_ == 'CUSTOM':
        _active_curves.add(curve)
        if not timers.is_registered(_check_active_curves):
            timers.register(_check_active_curves, first_interval=1.0)

        leading.prop(curve, "type", text="")

        selected = {
            pt.handle_type for pt in node.mapping.curves[0].points if pt.select
            }

        subrow = trailing.row(align=True)
        subrow.alignment = 'CENTER'
        subrow.enabled = len(selected) > 0

        for htype, icon in (('AUTO', 'HANDLE_AUTO'),
                            ('AUTO_CLAMPED', 'HANDLE_AUTOCLAMPED'),
                            ('VECTOR', 'HANDLE_VECTOR')):
            depress = len(selected) == 1 and htype in selected
            subrow.operator(ASKS_OT_curve_point_handle_type_set.bl_idname,
                            text="",
                            icon=icon,
                            depress=depress).handle_type = htype

        subrow.separator()
        subrow.operator(ASKS_OT_curve_point_remove.bl_idname,
                        text="",
                        icon='X')

    else:
        leading.prop(curve, "type", text="")
        if type_ != 'LINEAR':
            trailing.prop(curve, "easing", text="")

    trailing.separator()

    # subrow = trailing.row(align=True)
    # subrow.alignment = 'RIGHT'
    # subrow.operator(ASKS_OT_curve_copy.bl_idname, icon='COPYDOWN', text="")
    # subrow.operator(ASKS_OT_curve_paste.bl_idname, icon='PASTEDOWN', text="")

    body = box.column()
    body.scale_x = 0.01
    body.enabled = type_ == 'CUSTOM'
    body.template_curve_mapping(node, "mapping")
    body.separator(factor=0.3)

    # TODO
    extras.label(icon='BLANK1')

    return fields
#endregion Curve

#region Operators
#--------------------------------------------------------------------------------------------------

class CurveOperatorMixin:
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        return isinstance(getattr(context, "curve", None), Curve)

    @staticmethod
    def resolve_node_mapping(context: 'Context') -> Optional['NodeMapping']:
        curve = getattr(context, "curve", None)
        if curve:
            tree = _get_node_tree(curve)
            if tree:
                node = tree.nodes.get(curve.identifier)
                if node:
                    return node.mapping


class ASKS_OT_curve_point_handle_type_set(CurveOperatorMixin, Operator):
    bl_idname = "asks.curve_point_handle_type_set"
    bl_label = "Handle Type"
    bl_description = "Set the handle type of selected curve point(s)"
    
    handle_type: EnumProperty(
        name="Handle Type",
        description="Curve interpolation at this point: Bezier or vector",
        items=HANDLE_TYPE_ENUM_ITEMS,
        default='AUTO',
        options=set(),
        )

    def execute(self, context: 'Context') -> Set[str]:
        mapping = self.resolve_node_mapping(context)
        if mapping:
            ht = self.handle_type
            for pt in mapping.curves[0].points:
                if pt.select:
                    pt.handle_type = ht
            mapping.update()
        return {'FINISHED'}


class ASKS_OT_curve_point_remove(CurveOperatorMixin, Operator):
    bl_idname = "asks.curve_point_remove"
    bl_label = "Remove"
    bl_description = "Remove selected points"

    def execute(self, context: 'Context') -> Set[str]:
        mapping = self.resolve_node_mapping(context)
        if mapping:
            pts = mapping.curves[0].points
            for pt in reversed(list(filter(lambda pt: pt.select, pts))):
                pts.remove(pt)
            mapping.update()
        return {'FINISHED'}

#endregion Operators
