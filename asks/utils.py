
from typing import Optional, Tuple, TYPE_CHECKING
from mathutils import Matrix, Vector
from bpy.types import PropertyGroup, UIList
from bpy.props import BoolProperty
from .config import COMPAT_OBJECTS, COMPAT_ENGINES
if TYPE_CHECKING:
    from bpy.types import Context, UILayout


class ShapeKeyReference(PropertyGroup):
    select: BoolProperty(
        name="Select",
        default=False,
        options=set()
        )


class PollSystemEnabled:

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        engine = context.engine
        if engine in COMPAT_ENGINES:
            obj = context.object
            if obj is not None and obj.type in COMPAT_OBJECTS:
                key = obj.data.shape_keys
                return key is not None and key.is_property_set("asks") and key.asks.enabled
        return False


class PollActiveNode(PollSystemEnabled):

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        if super().poll(context):
            nodes = context.object.data.shape_keys.asks.nodes
            index = nodes.active_index
            return index < len(nodes)
        return False


class PollActiveChildNode(PollSystemEnabled):

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        if super().poll(context):
            nodes = context.object.data.shape_keys.asks.nodes
            index = nodes.active_index
            return index > 0 < len(nodes)
        return False


class ASKS_UL_shape_key_references(UIList):
    def draw_item(self, _0, layout: 'UILayout', _1, item: ShapeKeyReference, _2, _3, _4, _5) -> None:
        layout.label(icon='SHAPEKEY_DATA', text=item.name)
        row = layout.row()
        row.alignment = 'RIGHT'
        row.prop(item, "select",
                 text="",
                 icon=f'CHECKBOX_{"" if item.select else "DE"}HLT',
                 emboss=False)


def split_layout(layout: 'UILayout',
                 heading: Optional[str]="",
                 align: Optional[bool]=False,
                 decorate: Optional[bool]=False) -> Tuple['UILayout', 'UILayout', 'UILayout']:
    row = layout.row()
    col = row.column(align=align)
    extras = row.column(align=align)
    if not decorate:
        extras.label(icon='BLANK1')
    split = col.split(factor=1/3)
    labels = split.column(align=align)
    labels.alignment = 'RIGHT'
    if heading:
        labels.label(text=heading)
    fields = split.column(align=align)
    return labels, fields, extras


def compose_matrix(location: Optional[Tuple[float, float, float]]=(0., 0., 0.),
                   rotation: Optional[Tuple[float, float, float, float]]=(1., 0., 0., 0.),
                   scale: Optional[Tuple[float, float, float]]=(1., 1., 1.)) -> None:
    matrix = Matrix.Identity(3)
    matrix[0][0] = scale[0]
    matrix[1][1] = scale[1]
    matrix[2][2] = scale[2]
    matrix = (rotation.to_matrix() @ matrix).to_4x4()
    matrix[0][3] = location[0]
    matrix[1][3] = location[1]
    matrix[2][3] = location[2]
    return matrix


def flatten_matrix(matrix: Matrix) -> Tuple[float, float, float, float,
                                            float, float, float, float,
                                            float, float, float, float,
                                            float, float, float, float]:
    return sum((matrix.col[i].to_tuple() for i in range(4)), tuple())


def aim_vector(quaternion: Tuple[float, float, float, float]) -> Vector:
    w, x, y, z = quaternion
    return Vector((2.0*(x*y-w*z), 1.0-2.0*(x*x+z*z), 2.0*(y*z+w*x)))

