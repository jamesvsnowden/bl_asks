# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Advanced Shape Key System",
    "description": "Advanced Shape Key System",
    "author": "James Snowden",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "https://jamesvsnowden.xyz/addons/asks/docs",
    "tracker_url": "https://github.com/jamesvsnowden/bl_asks/issues",
    "category": "Animation",
}

from bpy.app.handlers import persistent
from .config import COMPAT_OBJECTS
from .utils import ShapeKeyReference, ASKS_UL_shape_key_references
from .events import EventProxy, EventProxies
from .curves import (CurvePoint,
                     CurvePoints,
                     Curve,
                     ASKS_OT_curve_point_handle_type_set,
                     ASKS_OT_curve_point_remove
                     )
from .drivers import (WeightDriver,
                      ASKS_OT_driver_add,
                      ASKS_OT_combination_variable_add,
                      ASKS_OT_driver_remove,
                      ASKS_OT_driver_setup,
                      ASKS_UL_combination_variables,
                      ASKS_PT_weight,
                      ASKS_PT_weight_popover,
                      )
from .groups import NodeGroup, NodeGroups, ASKS_OT_group_add
from .nodes import (Node,
                    Nodes,
                    ASKS_OT_node_add,
                    ASKS_OT_interpolation_setup,
                    ASKS_PT_interpolation,
                    ASKS_PT_interpolation_popover)
from .system import (System,
                     ASKS_OT_system_enable,
                     ASKS_PT_shape_keys_subpanel,
                     ASKS_UL_shape_keys,
                     ASKS_PT_shape_keys)


@persistent
def _on_load(_) -> None:
    import bpy
    for ob in bpy.data.objects:
        if ob.type in COMPAT_OBJECTS:
            key = ob.data.shape_keys
            if key and key.is_property_set("asks") and key.asks.enabled:
                for node in key.asks.nodes:
                    node.__load__()


CLASSES = [
    ShapeKeyReference,
    EventProxy,
    EventProxies,
    CurvePoint,
    CurvePoints,
    Curve,
    WeightDriver,
    Node,
    Nodes,
    NodeGroup,
    NodeGroups,
    ASKS_OT_group_add,
    ASKS_OT_node_add,
    System,
    ASKS_OT_curve_point_handle_type_set,
    ASKS_OT_curve_point_remove,
    ASKS_OT_system_enable,
    ASKS_OT_driver_add,
    ASKS_OT_driver_remove,
    ASKS_OT_driver_setup,
    ASKS_UL_combination_variables,
    ASKS_OT_combination_variable_add,
    ASKS_OT_interpolation_setup,
    ASKS_PT_shape_keys_subpanel,
    ASKS_UL_shape_key_references,
    ASKS_UL_shape_keys,
    ASKS_PT_shape_keys,
    ASKS_PT_weight,
    ASKS_PT_weight_popover,
    ASKS_PT_interpolation,
    ASKS_PT_interpolation_popover,
    ]

preview_collections = {}

def register() -> None:
    from os.path import dirname, join
    from bpy.types import DATA_PT_shape_keys, Key
    from bpy.props import PointerProperty
    from bpy.utils import previews, register_class
    from bpy.app.handlers import load_post
    from .system import _shape_keys_panel_poll_override

    for cls in CLASSES:
        register_class(cls)

    preview = previews.new()
    preview.images_location = join(dirname(__file__), "icons")
    preview_collections["img"] = preview

    path = join(preview.images_location, f'listsep.png')
    ASKS_UL_shape_keys.sep_icon = preview.load(path, path, 'IMAGE').icon_id

    Key.asks = PointerProperty(type=System)
    DATA_PT_shape_keys.poll = classmethod(_shape_keys_panel_poll_override)
    load_post.append(_on_load)


def unregister() -> None:
    from sys import modules
    from bpy.types import DATA_PT_shape_keys, Key
    from bpy.utils import previews, unregister_class
    from bpy.app.handlers import load_post
    from .system import SHAPE_KEYS_PANEL_POLL_ORIGINAL

    for preview in preview_collections.values():
        previews.remove(preview)

    load_post.remove(_on_load)
    DATA_PT_shape_keys.poll = SHAPE_KEYS_PANEL_POLL_ORIGINAL
    del Key.asks
    for cls in reversed(CLASSES):
        unregister_class(cls)


    mods = dict(sorted(modules.items(), key=lambda x: x[0]))   
    for name in list(mods.keys()):
        if name.startswith(__name__):
            del modules[name]
