
from typing import Optional, Set, Tuple, TYPE_CHECKING
import bpy
from mathutils import Euler, Matrix, Quaternion, Vector
from bpy.types import Operator, Panel, PropertyGroup, UIList
from bpy.props import (BoolProperty,
                       BoolVectorProperty,
                       CollectionProperty,
                       EnumProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       IntProperty,
                       PointerProperty,
                       StringProperty)
from .config import POPUP_WIDTH
from .utils import (ShapeKeyReference,
                    PollSystemEnabled,
                    PollActiveChildNode,
                    compose_matrix,
                    flatten_matrix,
                    aim_vector,
                    split_layout)
from .curves import Curve, draw_curve
if TYPE_CHECKING:
    from bpy.types import (ChannelDriverVariables,
                           Context,
                           Driver,
                           DriverVariable,
                           Event,
                           FCurve,
                           UILayout)
    from .nodes import Node


SUBTYPE_ENUM_ITEMS = [
    ('AVERAGE', "Average Value", ""),
    ('SUM', "Sum Values", ""),
    ('SCRIPTED', "Scripted Expression", ""),
    ('MIN', "Minimum Value", ""),
    ('MAX', "Maximum Value", ""),
    ]

TYPE_ENUM_ITEMS = [
    ('CONE', "Cone", "", 'CONE', 0),
    ('POSE', "Pose", "", 'POSE_HLT', 1),
    ('COMBINATION', "Combination", "", 'SELECT_INTERSECT', 2),
    ('CUSTOM', "Custom", "", 'DRIVER', 3),
    ]

TYPE_ENUM_INDEX = {
    _item[0]: _item[4] for _item in TYPE_ENUM_ITEMS
    }

TYPE_ENUM_ICONS = {
    _item[0]: _item[3] for _item in TYPE_ENUM_ITEMS
    }


def _fcurve_get(driver: 'WeightDriver', ensure: Optional[bool]=False) -> Optional['FCurve']:
    animdata = driver.id_data.animation_data
    if animdata is None:
        if ensure: animdata = driver.id_data.animation_data_create()
        else: return
    fcurve = animdata.drivers.find(driver.data_path)
    if fcurve is None and ensure:
        fcurve = animdata.drivers.new(driver.data_path)
    return fcurve


def _variables_clear(variables: 'ChannelDriverVariables') -> None:
    for variable in reversed(list(variables)):
        variables.remove(variable)


def _cone_driver_expression_format(value: Quaternion) -> None:
    x, y, z = aim_vector(value)
    # The function runs through the following steps:
    # - Convert the target bone's (local space) rotation quaternion to a direction vector
    # - Calculate the dot product between the pose's direction vector and the target bone's rotation vector
    # - Range the result and apply a inverse sine function to negate the effect of the dot product calculation so that the fcurve operates in the 0-1 range
    return f'(asin(2.0*(x*y-w*z)*{x:.3f}+(1.0-2.0*(x*x+z*z))*{y:.3f}+2.0*(y*z+w*x)*{z:.3f})--(pi/2.0))/pi'


def _combination_driver_expression_update(driver: 'Driver', type_: str) -> None:
    keys = tuple(driver.variables.keys())
    if not len(keys):
        driver.expression = "0.0"
    elif type_ == 'MULTIPLY':
        driver.expression = f'{"*".join(keys)}'
    elif type_ == 'MIN':
        driver.expression = f'min({",".join(keys)})'
    elif type_ == 'MAX':
        driver.expression = f'max({",".join(keys)})'
    else:
        driver.expression = f'({"+".join(keys)})/{str(float(len(keys)))}'


def _pose_driver_update(driver: 'Driver', settings: 'WeightDriver') -> None:
    variables = driver.variables
    _variables_clear(variables)

    id_ = bpy.data.objects.get(settings.data_target)
    if not id_:
        driver.expression = "0.0"
        return

    posedata = []
    poseprop = f'{settings.data_path[2:-2]}_pose'
    normprop = f'{settings.data_path[2:-2]}_norm'

    flags = settings.use_location
    if True in flags:
        for index, (value, inuse) in enumerate(zip(settings.location, flags)):
            if inuse:
                input_ = variables.new()
                input_.type = 'TRANSFORMS'
                input_.name = next(var_names)

                target = input_.targets[0]
                target.transform_type = f'LOC_{"XYZ"[index]}'
                target.transform_space = 'LOCAL_SPACE'
                target.id = id_
                target.bone_target = settings.bone_target

                param = variables.new()
                param.type = 'SINGLE_PROP'
                param.name = next(var_names)

                target = param.targets[0]
                target.id_type = 'KEY'
                target.id = settings.id_data
                target.data_path = f'["{poseprop}"][{len(posedata)}]'

                posedata.append(value)
                parts.append(f'pow({input_.name}-{param.name},2.0)')

                norm = variables.new()
                norm.type = 'SINGLE_PROP'
                norm.name = next(var_names)

                target = norm.targets[0]
                target.id_type = 'KEY'
                target.id = group.id_data
                target.data_path = idprop_path(group, 0)

                distances.append(f'sqrt({"+".join(parts)})/{norm.name}')


def _weight_driver_subtype_update_handler(driver: 'WeightDriver', _: 'Context') -> None:
    if driver.type == 'CUSTOM':
        _fcurve_get(driver, True).type = driver.subtype


def _bone_target_get(driver: 'WeightDriver') -> str:
    fc = _fcurve_get(driver)
    if fc:
        vars_ = fc.driver.variables
        if len(vars_):
            return vars_[0].targets[0].bone_target
    return ""


def _bone_target_set(driver: 'WeightDriver', value: str) -> None:
    if driver.type != 'CUSTOM':
        fc = _fcurve_get(driver)
        if fc:
            for var in fc.driver.variables:
                var.targets[0].bone_target = value


def _data_target_get(driver: 'WeightDriver') -> str:
    fc = _fcurve_get(driver)
    if fc:
        vars_ = fc.driver.variables
        if len(vars_):
            id_ = vars_[0].targets[0].id
            if id_: return id_.name
    return driver.get("data_target", "")


def _data_target_set(driver: 'WeightDriver', value: str) -> None:
    driver["data_target"] = value
    if driver.type != 'CUSTOM':
        vars_ = _fcurve_get(driver, True).driver.variables
        import bpy
        ob = bpy.data.objects.get(value)
        if ob:
            if len(vars_) == 0:
                var = vars_.new()
                var.targets[0].id = ob
            else:
                for var in vars_:
                    tgt = var.targets[0]
                    if tgt.id_type == 'OBJECT':
                        tgt.id = ob


def _curve_update_handler(curve: Curve) -> None:
    driver = curve.id_data.path_resolve(curve.path_from_id().rpartition(".")[0])
    _driver_curve_update_handler(driver)


def _driver_curve_update_handler(driver: 'WeightDriver') -> None:
    fcurve = _fcurve_get(driver, True)
    rangex = None
    rangey = None
    type_ = driver.type
    if type_ in {'CONE', 'COMBINATION'}:
        rangex = (1.0-driver.radius, 1.0)
        rangey = (driver.value_range_min, driver.value_range_max)
    driver.curve.assign(fcurve, rangex, rangey)


def _mute_get(driver: 'WeightDriver') -> bool:
    fcurve = _fcurve_get(driver)
    return fcurve is None or fcurve.mute


def _mute_set(driver: 'WeightDriver', value: bool) -> None:
    _fcurve_get(driver, True).mute = value


def _transform_update_handler(driver: 'WeightDriver', _: 'Context') -> None:
    type_ = driver.type
    if type_ == 'CONE':
        driver = _fcurve_get(driver, True).driver
        driver.expression = _cone_driver_expression_format(driver.rotation_quaternion)


def _location_get(driver: 'WeightDriver') -> Vector:
    return driver.transform.to_translation()


def _location_set(driver: 'WeightDriver', value: Tuple[float, float, float]) -> None:
    driver.transform = compose_matrix(value,
                                        driver.rotation_quaternion,
                                        driver.scale)


def _radius_update_handler(driver: 'WeightDriver', _: 'Context') -> None:
    if driver.type == 'CONE':
        _driver_curve_update_handler(driver)


def _rotation_euler_get(driver: 'WeightDriver') -> Euler:
    return driver.transform.to_euler()


def _rotation_euler_set(driver: 'WeightDriver', value: Tuple[float, float, float]) -> None:
    driver.transform = compose_matrix(driver.location,
                                        Euler(value).to_quaternion(),
                                        driver.scale)


def _rotation_order_update_handler(driver: 'WeightDriver', _: 'Context') -> None:
    # TODO
    pass


def _rotation_quaternion_get(driver: 'WeightDriver') -> Quaternion:
    return driver.transform.to_quaternion()


def _rotation_quaternion_set(driver: 'WeightDriver',
                                  value: Tuple[float, float, float, float]) -> None:
    driver.transform = compose_matrix(driver.location,
                                        value,
                                        driver.scale)


def _rotation_axis_get(driver: 'WeightDriver') -> Vector:
    return _rotation_quaternion_get(driver).to_axis_angle()[0]


def _rotation_axis_set(driver: 'WeightDriver', value: Tuple[float, float, float]) -> None:
    driver.transform = compose_matrix(driver.location,
                                        Quaternion(value, driver.rotation_angle),
                                        driver.scale)


def _rotation_angle_get(driver: 'WeightDriver') -> float:
    return _rotation_quaternion_get(driver).to_axis_angle()[1]


def _rotation_angle_set(driver: 'WeightDriver', value: float) -> None:
    driver.transform = compose_matrix(driver.location,
                                        Quaternion(driver.rotation_axis, value),
                                        driver.scale)


def _rotation_mode_update_handler(driver: 'WeightDriver', _: 'Context') -> None:
    # TODO
    pass


def _scale_get(driver: 'WeightDriver') -> Vector:
    return driver.transform.to_scale()


def _scale_set(driver: 'WeightDriver', value: Tuple[float, float, float]) -> None:
    driver.transform = compose_matrix(driver.location,
                                        driver.rotation_quaternion,
                                        value)


def _swing_twist_axis_update_handler(driver: 'WeightDriver', _: 'Context') -> None:
    # TODO
    pass


def _value_range_min_get(driver: 'WeightDriver') -> float:
    return driver.get("value_range_min", 0.0)


def _value_range_min_set(driver: 'WeightDriver', value: float) -> None:
    driver["value_range_min"] = min(value, driver.value_range_max - 0.001)
    _driver_curve_update_handler(driver)
    

def _value_range_max_get(driver: 'WeightDriver') -> float:
    return driver.get("value_range_max", 1.0)


def _value_range_max_set(driver: 'WeightDriver', value: float) -> None:
    driver["value_range_max"] = max(value, driver.value_range_min + 0.001)
    _driver_curve_update_handler(driver)


def _use_location_update_handler(driver: 'WeightDriver', _: 'Context') -> None:
    # TODO
    pass


def _use_rotation_update_handler(driver: 'WeightDriver', _: 'Context') -> None:
    # TODO
    pass


def _use_scale_update_handler(driver: 'WeightDriver', _: 'Context') -> None:
    # TODO
    pass



class WeightDriver(PropertyGroup):

    auto_adjust_radius: BoolProperty(
        name="Auto-Adjust",
        default=False,
        options=set()
        )

    bone_target: StringProperty(
        name="Bone",
        get=_bone_target_get,
        set=_bone_target_set,
        )

    combination_type: EnumProperty(
        name="Mode",
        description="The method to use when calculating the combination shape key's value",
        items=[
            ('MULTIPLY', "Multiply", "Multiply the driver values"),
            ('MIN', "Lowest", "Use the lowest driver value"),
            ('MAX', "Highest", "Use the highest driver value"),
            ('AVERAGE', "Average", "Use the average of the driver values"),
            ],
        default='MULTIPLY',
        options=set(),
        )

    combination_variable_active_index: IntProperty(
        name="Node",
        min=0,
        default=0,
        options=set()
        )

    curve: PointerProperty(
        name="Curve",
        type=Curve,
        options=set()
        )

    data_target: StringProperty(
        name="Object",
        get=_data_target_get,
        set=_data_target_set,
        options=set()
        )

    data_path: StringProperty(
        name="Path",
        get=lambda self: self.get("data_path", ""),
        options=set()
        )

    mute: BoolProperty(
        name="Mute",
        get=_mute_get,
        set=_mute_set,
        options=set()
        )

    location: FloatVectorProperty(
        name="Location",
        size=3,
        subtype='XYZ',
        get=_location_get,
        set=_location_set,
        options=set()
        )

    radius: FloatProperty(
        name="Radius",
        min=0.0,
        max=1.0,
        default=1.0,
        precision=3,
        options=set(),
        update=_radius_update_handler
        )

    rotation_angle: FloatProperty(
        name="Angle",
        subtype='ANGLE',
        get=_rotation_angle_get,
        set=_rotation_angle_set,
        options=set()
        )

    rotation_axis: FloatVectorProperty(
        name="Axis",
        size=3,
        subtype='XYZ',
        get=_rotation_axis_get,
        set=_rotation_axis_set,
        options=set()
        )

    rotation_euler: FloatVectorProperty(
        name="Rotation",
        size=3,
        subtype='EULER',
        get=_rotation_euler_get,
        set=_rotation_euler_set,
        options=set()
        )

    rotation_mode: EnumProperty(
        name="Mode",
        description="Rotation Mode",
        items=[
            ('EULER'     , "Euler"     , "Euler angles"       ),
            ('QUATERNION', "Quaternion", "Quaternion rotation"),
            ('SWING'     , "Swing"     , "Swing rotation"     ),
            ('TWIST'     , "Twist"     , "Twist rotation"     ),
            ],
        default='QUATERNION',
        options=set(),
        update=_rotation_mode_update_handler
        )

    rotation_order: EnumProperty(
        name="Order",
        description="Euler rotation order",
        items=[
            ('AUTO', "Auto", "Euler using the rotation order of the target"),
            ('XYZ' , "XYZ" , "Euler using the XYZ rotation order"),
            ('XZY' , "XZY" , "Euler using the XZY rotation order"),
            ('YXZ' , "YXZ" , "Euler using the YXZ rotation order"),
            ('YZX' , "YZX" , "Euler using the YZX rotation order"),
            ('ZXY' , "ZXY" , "Euler using the ZXY rotation order"),
            ('ZYX' , "ZYX" , "Euler using the ZYX rotation order"),
            ],
        default='AUTO',
        options=set(),
        update=_rotation_order_update_handler
        )

    rotation_quaternion: FloatVectorProperty(
        name="Rotation",
        size=4,
        subtype='QUATERNION',
        get=_rotation_quaternion_get,
        set=_rotation_quaternion_set,
        options=set()
        )

    scale: FloatVectorProperty(
        name="Scale",
        size=3,
        subtype='XYZ',
        get=_scale_get,
        set=_scale_set,
        options=set()
        )

    swing_twist_axis: EnumProperty(
        name="Axis",
        description="The rotation axis to use",
        items=[
            ('X', "X", "X-axis"),
            ('Y', "Y", "Y-axis"),
            ('Z', "Z", "Z-axis"),
            ],
        default='Y',
        options=set(),
        update=_swing_twist_axis_update_handler
        )

    show_rotation_mode: EnumProperty(
        name="Mode",
        items=[
            ('EULER'     , "Euler"     , "Euler angles"       ),
            ('QUATERNION', "Quaternion", "Quaternion rotation"),
            ('AXIS_ANGLE', "Axis/Angle", "Axis/Angle rotation"),
            ],
        default='QUATERNION',
        options=set()
        )

    subtype: EnumProperty(
        name="Type",
        items=SUBTYPE_ENUM_ITEMS,
        options=set(),
        update=_weight_driver_subtype_update_handler
        )

    transform: FloatVectorProperty(
        name="Matrix",
        size=16,
        update=_transform_update_handler,
        subtype='MATRIX',
        default=flatten_matrix(Matrix.Identity(4)),
        options=set()
        )

    type: EnumProperty(
        name="Type",
        items=TYPE_ENUM_ITEMS,
        get=lambda self: self.get("type", 0),
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

    use_location: BoolVectorProperty(
        name="Location",
        size=3,
        subtype='XYZ',
        default=(False, False, False),
        options=set(),
        update=_use_location_update_handler
        )

    use_rotation: BoolVectorProperty(
        name="Rotation",
        size=3,
        subtype='XYZ',
        default=(False, False, False),
        options=set(),
        update=_use_rotation_update_handler
        )

    use_scale: BoolVectorProperty(
        name="Scale",
        size=3,
        subtype='XYZ',
        default=(False, False, False),
        options=set(),
        update=_use_scale_update_handler
        )

    def __init__(self, type_: str, path: str) -> None:
        self["type"] = TYPE_ENUM_INDEX[type_]
        self["data_path"] = path
        
        curve = self.curve
        curve.__init__()
        curve.bind("updated", _curve_update_handler)

        fcurve = _fcurve_get(self, True)
        driver = fcurve.driver
        vars_ = driver.variables

        if type_ == 'CUSTOM':
            if not len(vars_):
                var = vars_.new()
                var.name = "var"
                var.type = 'TRANSFORMS'

        elif type_ == 'CONE':
            self["radius"] = 0.2
            driver.type = 'SCRIPTED'
            driver.expression = _cone_driver_expression_format(self.rotation_quaternion)
            _variables_clear(vars_)
            for axis in 'WXYZ':
                var = vars_.new()
                var.name = axis.lower()
                var.type = 'TRANSFORMS'
                tgt = var.targets[0]
                tgt.transform_type = f'ROT_{axis}'
                tgt.transform_space = 'LOCAL_SPACE'
                tgt.rotation_mode = 'QUATERNION'

        elif type_ == 'COMBINATION':
            driver.type = 'SCRIPTED'
            driver.expression = "0.0"
            _variables_clear(vars_)

        elif type_ == 'POSE':
            driver.type = 'SCRIPTED'
            driver.expression = "0.0"
            _variables_clear(vars_)


#region Draw Functions
#--------------------------------------------------------------------------------------------------


def draw_pose_driver_settings(layout: 'UILayout', node: 'Node') -> None:
    settings = node.driver

    col = split_layout(layout, heading="Group", align=True)[1]
    box = col.box()
    row = box.row(align=True)
    grp = node.group

    subrow = row.row(align=True)
    subrow.alert = bool(grp) and grp not in node.id_data.asks.groups
    subrow.prop_search(node, "group",
                       node.id_data.asks.groups, "internal__",
                       text="",
                       icon='GROUP')

    row.operator("asks.group_add",
                 text="",
                 icon='ADD')

    if grp:
        group = node.id_data.asks.groups.get(grp)
        if group:
            box = col.box()
            box.separator()

            col = split_layout(box, heading="Target", align=True)[1]
            col.prop_search(settings, "data_target", bpy.data, "objects",
                            text="",
                            icon='OBJECT_DATA')

            tgt = settings.data_target
            if tgt:
                obj = bpy.data.objects.get(tgt)
                if obj and obj.type == 'ARMATURE':
                    col.prop_search(settings, "bone_target", obj.data, "bones",
                                    text="",
                                    icon='BONE_DATA')

            row = split_layout(box, heading="Location")[1].row(align=True)
            row.prop(settings, "use_location", text="", toggle=True)

            col = split_layout(box, heading="Rotation")[1]
            row = col.row(align=True)
            row.prop(settings, "rotation_mode", text="")

            mode = settings.rotation_mode
            if mode != 'QUATERNION':
                subrow = row.row(align=True)
                subrow.alignment = 'RIGHT'
                if mode == 'EULER':
                    subrow.prop(settings, "rotation_order", text="")
                    row = col.row(align=True)
                    row.prop(settings, "use_rotation", text="", toggle=True)
                else:
                    subrow.prop(settings, "swing_twist_axis", text="")

            row = split_layout(box, heading="Scale")[1].row(align=True)
            row.prop(settings, "use_scale", text="", toggle=True)

            box.separator()

    layout.separator()

    box = split_layout(layout, heading="Pose")[1].box()
    box.separator()

    _, fields, extras = split_layout(box, heading="Location", align=True)
    for index, axis in enumerate('XYZ'):
        fields.prop(settings, "location", text=axis, index=index)

    _, fields, extras = split_layout(box, heading="Rotation", align=True)
    fields.prop(settings, "show_rotation_mode", text="")

    mode = settings.show_rotation_mode
    if mode == 'QUATERNION':
        for index, axis in enumerate('WXYZ'):
            fields.prop(settings, "rotation_quaternion", text=axis, index=index)

    elif mode == 'AXIS_ANGLE':
        fields.prop(settings, "rotation_angle", text="W")
        for index, axis in enumerate('XYZ'):
            fields.prop(settings, "rotation_axis", text=axis, index=index)

    elif mode == 'EULER':
        for index, axis in enumerate('XYZ'):
            fields.prop(settings, "rotation_euler", text=axis, index=index)

    _, fields, extras = split_layout(box, heading="Scale", align=True)
    for index, axis in enumerate('XYZ'):
        fields.prop(settings, "scale", text=axis, index=index)

    col = split_layout(box, heading="Radius")[1]
    
    row = col.row()
    row.enabled = not settings.auto_adjust_radius
    row.prop(settings, "radius", text="", slider=True)

    row = col.row()
    row.alignment = 'RIGHT'
    row.label(text="Auto-Adjust")
    row.prop(settings, "auto_adjust_radius", text="")

    layout.separator()


def draw_cone_driver_settings(layout: 'UILayout', node: 'Node') -> None:
    settings = node.driver

    col = split_layout(layout, heading="Target", align=True)[1]
    col.prop_search(settings, "data_target", bpy.data, "objects",
                    text="",
                    icon='OBJECT_DATA')

    tgt = settings.data_target
    if tgt:
        obj = bpy.data.objects.get(tgt)
        if obj and obj.type == 'ARMATURE':
            col.prop_search(settings, "bone_target", obj.data, "bones",
                            text="",
                            icon='BONE_DATA')

    col = split_layout(layout, heading="Center", align=True)[1]
    col.prop(settings, "show_rotation_mode", text="")

    mode = settings.show_rotation_mode
    if mode == 'QUATERNION':
        for i, axis in enumerate('WXYZ'):
            col.prop(settings, "rotation_quaternion", text=axis, index=i)

    elif mode == 'AXIS_ANGLE':
        col.prop(settings, "rotation_angle", text="W")
        for i, axis in enumerate('XYZ'):
            col.prop(settings, "rotation_axis", text=axis, index=i)

    elif mode == 'EULER':
        for i, axis in enumerate('XYZ'):
            col.prop(settings, "rotation_euler", text=axis, index=i)

    col = draw_curve(layout, settings.curve, heading="Falloff")
    col.prop(settings, "radius", text="Radius", slider=True)


def draw_combination_driver_settings(layout: 'UILayout', node: 'Node') -> None:
    settings = node.driver

    col = split_layout(layout, heading="Type")[1]
    col.prop(settings, "combination_type", text="")

    fc = _fcurve_get(settings)
    if fc:
        _, fields, extras = split_layout(layout, heading="Combination Of", decorate=True)
        fields.template_list("ASKS_UL_combination_variables", "",
                            fc.driver, "variables",
                            settings, "combination_variable_active_index")
        extras.operator("asks.combination_variable_add",
                        text="",
                        icon='ADD').node_target = node.name

    col = draw_curve(layout, settings.curve, heading="Falloff")
    col.prop(settings, "radius", text="Radius", slider=True)


DRAW_FUNCTION_LUT = {
    'CONE': draw_cone_driver_settings,
    'COMBINATION': draw_combination_driver_settings,
    'POSE': draw_pose_driver_settings,
    }

#endregion

#region Operators
#--------------------------------------------------------------------------------------------------

class ASKS_OT_driver_add(PollSystemEnabled, Operator):
    bl_idname = "asks.driver_add"
    bl_label = "Add Driver"
    bl_options = {'INTERNAL', 'UNDO'}

    node_target: StringProperty(
        name="Node",
        default="",
        options=set()
        )

    type: EnumProperty(
        name="Type",
        items=TYPE_ENUM_ITEMS,
        options=set()
        )

    def execute(self, context: 'Context') -> Set[str]:
        node = context.object.data.shape_keys.asks.nodes.get(self.node_target)

        if node is None:
            self.report({'ERROR'}, f'Node "{self.node_target}" not found')
            return {'CANCELLED'}

        if node.is_property_set("driver__"):
            self.report({'ERROR'}, f'Node "{node.name}" already has driver')

        node.driver__.__init__(self.type, f'["{node.identifier}"]')
        return {'FINISHED'}


class ASKS_OT_combination_variable_add(PollSystemEnabled, Operator):
    bl_idname = "asks.combination_variable_add"
    bl_label = "Add"
    bl_options = {'INTERNAL', 'UNDO'}
    node = None

    active_index: IntProperty(
        min=0,
        default=0,
        options=set()
        )

    node_target: StringProperty(
        name="Node",
        default="",
        options=set()
        )

    nodes: CollectionProperty(
        name="Nodes",
        type=ShapeKeyReference,
        options=set()
        )

    def invoke(self, context: 'Context', _: 'Event') -> Set[str]:
        nodes = context.object.data.shape_keys.asks.nodes

        node = nodes.get(self.node_target)
        if node is None:
            self.report({'ERROR'})
            return {'CANCELLED'}

        settings = node.driver
        if settings is None or settings.type != 'COMBINATION':
            self.report({'ERROR'})
            return {'CANCELLED'}

        used = []
        for var in _fcurve_get(settings, True).driver.variables:
            used.append(var.targets[0].data_path[12:-8])

        subtree = node.subtree
        lower = subtree[0].index
        upper = subtree[-1].index

        items = self.nodes
        items.clear()

        for index, node in enumerate(nodes.internal__):
            if index > 0 and (index < lower or index > upper):
                name = node.name
                if name not in used:
                    items.add().name = name

        self.node = node
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _: 'Context') -> None:
        self.layout.template_list("ASKS_UL_shape_key_references", "",
                                  self, "nodes",
                                  self, "active_index")

    def execute(self, context: 'Context') -> Set[str]:
        # TODO handle errors
        key = context.object.data.shape_keys
        node = self.node
        settings = node.driver
        fcurve = _fcurve_get(settings, True)
        vars_ = fcurve.driver.variables

        for item in filter(lambda x: x.select, self.nodes):
            var = vars_.new()
            var.name = f'k{len(vars_)}'
            var.type = 'SINGLE_PROP'

            tgt = var.targets[0]
            tgt.id_type = 'KEY'
            tgt.id = key
            tgt.data_path = f'key_blocks["{item.name}"].value'

        _combination_driver_expression_update(fcurve.driver, settings.combination_type)
        return {'FINISHED'}


class ASKS_OT_driver_remove(PollSystemEnabled, Operator):
    bl_idname = "asks.driver_remove"
    bl_label = "Remove Driver"
    bl_options = {'INTERNAL', 'UNDO'}

    node_target: StringProperty(
        name="Node",
        default="",
        options=set()
        )

    def execute(self, context: 'Context') -> Set[str]:
        # TODO
        return {'FINISHED'}


class ASKS_OT_driver_setup(PollSystemEnabled, Operator):
    bl_idname = 'asks.driver_setup'
    bl_label = "Driver"

    node = None
    node_target: StringProperty(
        name="Node",
        default="",
        options=set()
        )

    def invoke(self, context: 'Context', _: 'Event') -> Set[str]:
        node = context.object.data.shape_keys.asks.nodes.get(self.node_target)
        if node:
            if not node.driver:
                self.report({'ERROR'}, f'Node "{self.node_target}" does not have a driver.')
                return {'CANCELLED'}
            self.node = node
            return context.window_manager.invoke_popup(self, width=POPUP_WIDTH)
        else:
            self.report({'ERROR'}, f'Node "{self.node_target}" not found.')
            return {'CANCELLED'}

    def draw(self, _: 'Context') -> None:
        node = self.node
        if node:
            settings = node.driver
            if settings:
                layout = self.layout
                layout.label(text=f'Driver ({node.name})',
                             icon=TYPE_ENUM_ICONS[settings.type])
                layout.separator()
                DRAW_FUNCTION_LUT[settings.type](layout, node)
                layout.separator()
                
    def execute(self, _: 'Context') -> Set[str]:
        return {'FINISHED'}

#endregion

#region UI
#--------------------------------------------------------------------------------------------------

class ASKS_UL_combination_variables(UIList):

    def draw_item(self, _0, ui: 'UILayout', _1, var: 'DriverVariable', _2, _3, _4, _5) -> None:
        ui.label(icon='SHAPEKEY_DATA', text=var.targets[0].data_path[12:-8])

class ASKS_PT_weight(PollActiveChildNode, Panel):
    bl_idname = 'ASKS_PT_weight'
    bl_label = "Weight"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_parent_id = "ASKS_PT_shape_keys"

    def draw(self, context: 'Context') -> None:
        layout = self.layout
        node = context.object.data.shape_keys.asks.nodes.active
        settings = node.driver

        _, fields, extras = split_layout(layout, heading="Driver", decorate=True)
    
        if settings is None:
            fields.operator_menu_enum("ASKS_OT_driver_add", "type",
                                      text="Add Driver",
                                      icon='DRIVER').node_target = node.name
            extras.label(icon='BLANK1')
        else:
            fields.enabled = False
            fields.prop(settings, "type", text="")
            extras.operator("ASKS_OT_driver_remove", text="", icon='X')

            DRAW_FUNCTION_LUT[settings.type](layout, node)

        col = split_layout(layout, heading="Value")[1]
        col.prop(node.id_data, f'["{node.identifier}"]', text="", slider=True)


class ASKS_PT_weight_popover(PollSystemEnabled, Panel):
    bl_idname = "ASKS_PT_weight_popover"
    bl_label = "Weight"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_ui_units_x = 18
    bl_options = {'INSTANCED'}

    def draw(self, context: 'Context') -> None:
        node = getattr(context, "node", None)
        if node:
            settings = getattr(node, "driver", None)
            if isinstance(settings, WeightDriver):
                DRAW_FUNCTION_LUT[settings.type](self.layout, node)

#endregion