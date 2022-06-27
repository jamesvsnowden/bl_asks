
from typing import TYPE_CHECKING
from bpy.types import Panel
if TYPE_CHECKING:
    from bpy.types import Context

COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}
COMPAT_OBJECTS = {'MESH', 'LATTICE', 'CURVE', 'SURFACE'}


class EntitySettingsPanel(Panel):

    bl_idname = "ASKS_PT_entity_settings"
    bl_parent_id = "DATA_PT_shape_keys"
    bl_label = "ASKS"
    bl_description = ""
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        if context.engine in COMPAT_ENGINES:
            object = context.object
            if object is not None and object.type in COMPAT_OBJECTS:
                shapekey = object.active_shape_key
                if shapekey is not None:
                    key = shapekey.id_data
                    if key.is_property_set("asks"):
                        return shapekey in key.asks.entities
        return False

    def draw(self, context: 'Context') -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = True
        shapekey = context.object.active_shape_key
        shapekey.id_data.asks.entities[shapekey].draw(layout)
