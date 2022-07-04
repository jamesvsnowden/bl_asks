
from typing import Any, Dict, Iterator, List, Optional, Protocol, Sequence, Tuple, TYPE_CHECKING, Union
from dataclasses import dataclass
from bpy.types import PropertyGroup
from mathutils import Vector
from bpy.props import (BoolProperty,
                       CollectionProperty,
                       EnumProperty,
                       FloatVectorProperty,
                       PointerProperty)
from .component import Component
if TYPE_CHECKING:
    from bpy.types import UILayout


class CurvePointProtocol(Protocol):
    location: Tuple[float, float]
    handle_type: str
    select: bool


@dataclass
class KeyframePoint:
    interpolation: str = 'BEZIER'
    easing: str = 'AUTO'
    co: Tuple[float, float] = (0.0, 0.0)
    handle_left_type: str = 'FREE'
    handle_right_type: str = 'FREE'
    handle_left: Tuple[float, float] = (0.0, 0.0)
    handle_right: Tuple[float, float] = (0.0, 0.0)


@dataclass
class CurvePoint:
    location: Tuple[float, float] = (0.0, 0.0)
    handle_type: str = 'AUTO'
    select: bool = False


PRESETS: Dict[str, Sequence[CurvePoint]] = {}

PRESETS['LINEAR'] = (
    CurvePoint((0.0, 0.0), 'VECTOR'),
    CurvePoint((1.0, 1.0), 'VECTOR'),
    )
PRESETS['SINE_IN'] = (
    CurvePoint((0.0, 0.0) , 'AUTO'),
    CurvePoint((0.1, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO'),
    )
PRESETS['SINE_OUT'] = (
    CurvePoint((0.0, 0.0) , 'AUTO'),
    CurvePoint((0.9, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO'),
    )
PRESETS['SINE_IN_OUT'] = (
    CurvePoint((0.0, 0.0) , 'AUTO'),
    CurvePoint((0.1, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.9, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO'),
    )
PRESETS['QUAD_IN'] = (
    CurvePoint((0.0, 0.0)   , 'AUTO'),
    CurvePoint((0.15, 0.045), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)   , 'AUTO'),
    )
PRESETS['QUAD_OUT'] = (
    CurvePoint((0.0, 0.0)   , 'AUTO'),
    CurvePoint((0.85, 0.955), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)   , 'AUTO'),
    )
PRESETS['QUAD_IN_OUT'] = (
    CurvePoint((0.0, 0.0)   , 'AUTO'),
    CurvePoint((0.15, 0.045), 'AUTO_CLAMPED'),
    CurvePoint((0.85, 0.955), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)   , 'AUTO'),
    )
PRESETS['CUBIC_IN'] = (
    CurvePoint((0.0, 0.0) , 'AUTO'),
    CurvePoint((0.2, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO'),
    )
PRESETS['CUBIC_OUT'] = (
    CurvePoint((0.0, 0.0) , 'AUTO'),
    CurvePoint((0.8, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO'),
    )
PRESETS['CUBIC_IN_OUT'] = (
    CurvePoint((0.0, 0.0) , 'AUTO'),
    CurvePoint((0.2, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.8, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO'),
    )
PRESETS['QUART_IN'] = (
    CurvePoint((0.0, 0.0)  , 'AUTO'),
    CurvePoint((0.25, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)  , 'AUTO'),
    )
PRESETS['QUART_OUT'] = (
    CurvePoint((0.0, 0.0)  , 'AUTO'),
    CurvePoint((0.75, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)  , 'AUTO'),
    )
PRESETS['QUART_IN_OUT'] = (
    CurvePoint((0.0, 0.0)  , 'AUTO'),
    CurvePoint((0.25, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.75, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)  , 'AUTO'),
    )
PRESETS['QUINT_IN'] = (
    CurvePoint((0.0, 0.0)    , 'AUTO'),
    CurvePoint((0.275, 0.025), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)    , 'AUTO'),
    )
PRESETS['QUINT_OUT'] = (
    CurvePoint((0.0, 0.0)    , 'AUTO'),
    CurvePoint((0.725, 0.975), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)    , 'AUTO'),
    )
PRESETS['QUINT_IN_OUT'] = (
    CurvePoint((0.0, 0.0)    , 'AUTO'),
    CurvePoint((0.275, 0.025), 'AUTO_CLAMPED'),
    CurvePoint((0.725, 0.975), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)    , 'AUTO'),
    )


def point_location_x(point: 'CurveComponentPoint') -> float:
    return point.location[0]


def calc_bezier_handles(p2, ht, h1, h2, prev=None, next=None) -> None:
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


class CurveComponentPoint(PropertyGroup):

    @property
    def curve(self) -> 'CurveComponent':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".points")[0])

    handle_type: EnumProperty(
        name="Handle Type",
        description="Curve interpolation at this point: Bezier or vector",
        items=[
            ('AUTO'        , "Auto Handle"        , ""),
            ('AUTO_CLAMPED', "Auto Clamped Handle", ""),
            ('VECTOR'      , "Vector Handle"      , ""),
            ],
        default='AUTO_CLAMPED',
        options=set(),
        update=lambda self, _: self.curve.process()
        )

    location: FloatVectorProperty(
        name="Location",
        description="X/Y coordinates of the curve point",
        size=2,
        subtype='XYZ',
        default=(0.0, 0.0),
        options=set(),
        update=lambda self, _: self.curve.update()
        )

    select: BoolProperty(
        name="Select",
        description="Selection state of the curve point",
        default=False,
        options=set(),
        update=lambda self, _: self.curve.process()
        )

    def __init__(self, point: CurvePointProtocol) -> None:
        self["handle_type"] = ('AUTO', 'AUTO_CLAMPED', 'VECTOR').index(point.handle_type)
        self["location"] = tuple(point.location)
        self["select"] = point.select


class CurveComponentPoints(PropertyGroup):

    collection__internal__: CollectionProperty(
        type=CurveComponentPoint,
        options={'HIDDEN'}    
        )

    def __contains__(self, point: CurveComponentPoint) -> bool:
        return any(x == point for x in self)

    def __iter__(self) -> Iterator[CurveComponentPoint]:
        return iter(self.collection__internal__)

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __getitem__(self, key: Union[int, slice]) -> Union[CurveComponentPoint,
                                                           List[CurveComponentPoint]]:
        return self.collection__internal__[key]

    def new(self, location: Optional[Tuple[float, float]]=(0.0, 0.0)) -> CurveComponentPoint:
        point = self.collection__internal__.add()
        point.__init__(location=location)

        path: str = self.path_from_id()
        component = self.id_data.path_resolve(path.rpartition(".")[0])
        component.update()

        return point

    def remove(self, point: CurveComponentPoint) -> None:
        index = next((i for i, x in enumerate(self) if x == point), -1)
        if index == -1:
            raise ValueError()

        if len(self) <= 2:
            raise RuntimeError()

        self.collection__internal__.remove(index)

        path: str = self.path_from_id()
        component = self.id_data.path_resolve(path.rpartition(".")[0])
        component.update()

    def to_bezier(self,
                  range_x: Optional[Tuple[float, float]]=None,
                  range_y: Optional[Tuple[float, float]]=None,
                  extrapolate: Optional[bool]=None) -> List[KeyframePoint]:

        points = self.collection__internal__

        if extrapolate is None:
            path: str = self.path_from_id()
            component = self.id_data.path_resolve(path.rpartition(".")[0])
            extrapolate = component.extend == 'EXTRAPOLATED'

        data = [(
            p.location.copy(),
            p.handle_type,
            Vector((0.0, 0.0)),
            Vector((0.0, 0.0))
            ) for p in points]

        if range_x:
            a, b = range_x
            if a > b:
                a, b = b, a
                for item in data:
                    item[0][0] = 1.0 - item[0][0]
                data.reverse()
            d = b - a
            for item in data:
                item[0][0] = a + item[0][0] * d

        if range_y:
            a, b = range_y
            d = b - a
            for item in data:
                item[0][1] = a + item[0][1] * d

        n = len(data) - 1
        for i, (pt, ht, h1, h2) in enumerate(data):
            calc_bezier_handles(pt, ht, h1, h2,
                                data[i-1][0] if i > 0 else None,
                                data[i+1][0] if i < n else None)

        if len(data) > 2:
            ptA, htA, h1A, h2A = data[0]
            ptN, htN, h1N, h2N = data[-1]

            if htA == 'AUTO':
                hlen = (h2A - ptA).length
                hvec = data[1][2].copy()
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
                hvec = data[-2][3].copy()
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

        if not extrapolate:
            pt = data[0]
            co = pt[0]
            hl = pt[2]
            hl[0] = 0.0
            hl[1] = co[1]

            pt = data[-1]
            co = pt[0]
            hr = pt[3]
            hr[0] = 1.0
            hr[1] = co[1]

        for index, item in enumerate(data):
            data[index] = KeyframePoint(co=item[0], handle_left=item[2], handle_right=item[3])

        return data


def curve_component_preset_get(component: 'CurveComponent') -> Sequence[CurvePoint]:
    ipo = component.interpolation
    return PRESETS[ipo] if ipo == 'LINEAR' else PRESETS[f'{ipo}{component.easing[4:]}']


def curve_component_extend_update(component: 'CurveComponent', _) -> None:
    component.process()


def curve_component_preset_update(component: 'CurveComponent', _) -> None:
    if component.interpolation != 'CUSTOM':
        component.update(curve_component_preset_get(component), component.extend)


class CurveComponent(Component, PropertyGroup):

    easing: EnumProperty(
        name="Easing",
        items=[
            ('EASE_IN'    , "In"      , "Ease in"        , 'IPO_EASE_IN'    , 0),
            ('EASE_OUT'   , "Out"     , "Ease out"       , 'IPO_EASE_OUT'   , 1),
            ('EASE_IN_OUT', "In & Out", "Ease in and out", 'IPO_EASE_IN_OUT', 2),
            ],
        default='EASE_IN_OUT',
        options=set(),
        update=curve_component_preset_update
        )

    extend: EnumProperty(
        name="Extend",
        description="Extrapolate the curve or extend it horizontally",
        items=[
            ('HORIZONTAL'  , "Horizontal"  , "", 'NONE', 0),
            ('EXTRAPOLATED', "Extrapolated", "", 'NONE', 1),
            ],
        default='HORIZONTAL',
        options=set(),
        update=curve_component_extend_update
        )

    interpolation: EnumProperty(
        name="Interpolation",
        items=[
            ('LINEAR', "Linear"      , "Linear"          , 'IPO_LINEAR', 0),
            ('SINE'  , "Sinusoidal"  , "Sinusoidal"      , 'IPO_SINE'  , 1),
            ('QUAD'  , "Quadratic"   , "Quadratic"       , 'IPO_QUAD'  , 2),
            ('CUBIC' , "Cubic"       , "Cubic"           , 'IPO_CUBIC' , 3),
            ('QUART' , "Quartic"     , "Quartic"         , 'IPO_QUART' , 4),
            ('QUINT' , "Quintic"     , "Quintic"         , 'IPO_QUINT' , 5),
            None,
            ('CUSTOM', "Custom"      , "Use custom curve", 'FCURVE'    , 6),
            ],
        default='LINEAR',
        options=set(),
        update=curve_component_preset_update
        )

    points: PointerProperty(
        name="Points",
        type=CurveComponentPoints,
        options=set()
        )

    def __init__(self, **properties: Dict[str, Any]) -> None:
        super().__init__(**properties)
        for point in curve_component_preset_get(self):
            self.points.collection__internal__.add().__init__(point)
        self.system.curve_mapping_manager.node_set(self.name, self)

    def __onfileload__(self) -> None:
        node = self.system.curve_mapping.node_get(self.name)
        if node is None:
            self.system.curve_mapping.node_set(self.name, self)

    def __ondisposed__(self) -> None:
        self.system.curve_mapping.node_remove(self.name)

    def draw(self, layout: 'UILayout', label: Optional[str]=None) -> None:
        manager = self.system.curve_mapping_manager
        node = manager.node_get(self.name)

        outer = layout.row()
        split = outer.split(factor=0.385)
        label = self.label if label is None else label
        
        row = split.row()
        row.alignment = 'RIGHT'
        row.label(text=label, icon=f'{"NONE" if label else "BLANK1"}')
        
        row = split.row()
        box = row.box()
        box.context_pointer_set("curve", self)
        box.operator_context = 'INVOKE_DEFAULT'
        row.separator(factor=2.0)

        if node is None:
            box.label(icon='ERROR', text="Missing Curve")
            box.operator("asks.curve_reload", text="Reload")
            return

        row = box.row()
        row.ui_units_y = 0.01

        ipo = self.interpolation
        
        if ipo == 'CUSTOM':
            split = row.split(factor=0.6)
            row_l = split.row(align=True)
            row_r = split.row(align=True)
            row_l.prop(self, "interpolation", text="")
            row_r.alignment = 'RIGHT'

            manager.enable_editor(self)
            htypes = {pt.handle_type for pt in node.mapping.curves[0].points if pt.select}

            subrow = row_r.row(align=True)
            subrow.alignment = 'CENTER'
            subrow.enabled = len(htypes) > 0

            for htype, icon in (('AUTO', 'HANDLE_AUTO'),
                                ('AUTO_CLAMPED', 'HANDLE_AUTOCLAMPED'),
                                ('VECTOR', 'HANDLE_VECTOR')):
                depress = len(htypes) == 1 and htype in htypes
                subrow.operator("asks.curve_point_handle_type_set",
                                text="",
                                icon=icon,
                                depress=depress).handle_type = htype

            subrow.separator()
            subrow.operator("asks.curve_point_remove", text="", icon='X')
        elif ipo == 'LINEAR':
            row.alignment = 'LEFT'
            row.prop(self, "interpolation", text="")
        else:
            row.prop(self, "interpolation", text="")
            row.prop(self, "easing", text="")

        col = box.column()
        col.scale_x = 0.01
        col.enabled = ipo == 'CUSTOM'
        col.template_curve_mapping(node, "mapping")
        col.separator(factor=0.3)

    def process(self) -> None:
        self.system.curve_mapping_manager.node_set(self.name, self)
        super().process()

    def update(self,
               points: Optional[Sequence[CurvePointProtocol]]=None,
               extend: Optional[str]="") -> None:

        print('a')

        if points:
            print('b')
            items = self.points.collection__internal__
            count = len(points)
            print('c')
            while len(items) > count: items.remove(-1)
            print('d')
            while len(items) < count: items.add()
            print('e')
            for item, point in zip(items, points): item.__init__(point)
            print('f')

        if extend:
            self["extend"] = extend

        print('g')

        points = list(self.points)
        print('h')
        ptsort = sorted(points, key=point_location_x)
        print('i')

        if points != ptsort:
            print('j')
            ptsort = [CurvePoint(pt.location, pt.handle_type, pt.select) for pt in ptsort]
            print('k')
            for point, data in zip(points, ptsort): point.__init__(data)
            print('l')

        print('m')

        self.process()
