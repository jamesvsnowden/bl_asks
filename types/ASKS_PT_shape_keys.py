
from typing import TYPE_CHECKING, Set
from bpy.types import Panel
if TYPE_CHECKING:
    from bpy.types import Context

class ASKS_PT_shape_keys(Panel):

    bl_label = "Shape Keys"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}
    COMPAT_OBJECTS = {'MESH', 'LATTICE', 'CURVE', 'SURFACE'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        engine = context.engine
        if engine in cls.COMPAT_ENGINES:
            object = context.object
            return object is not None and object.type in cls.COMPAT_OBJECTS

    def draw(self, context: 'Context') -> Set[str]:
        layout = self.layout

        ob = context.object
        key = ob.data.shape_keys
        kb = ob.active_shape_key

        enable_edit = ob.mode != 'EDIT'
        enable_edit_value = False
        enable_pin = False

        if enable_edit or (ob.use_shape_key_edit_mode and ob.type == 'MESH'):
            enable_pin = True
            if ob.show_only_shape_key is False:
                enable_edit_value = True

        entities = key.asks.entities
        rowcount = 5 if kb else 3

        row = layout.row()
        row.template_list("ASKS_UL_shape_keys", "",
                          entities, "collection__internal__",
                          entities, "active_index", rows=rowcount)

        col = row.column(align=True)

        col.menu("ASKS_MT_entity_create_menu", icon='ADD', text="")
        col.operator("asks.entity_remove", icon='REMOVE', text="")

        col.separator()

        col.menu("ASKS_MT_entity_action_menu", icon='DOWNARROW_HLT', text="")

        if kb:
            col.separator()

            sub = col.column(align=True)
            sub.operator("object.shape_key_move", icon='TRIA_UP', text="").type = 'UP'
            sub.operator("object.shape_key_move", icon='TRIA_DOWN', text="").type = 'DOWN'

            split = layout.split(factor=0.4)
            row = split.row()
            row.enabled = enable_edit
            row.prop(key, "use_relative")

            row = split.row()
            row.alignment = 'RIGHT'

            sub = row.row(align=True)
            sub.label()  # XXX, for alignment only
            subsub = sub.row(align=True)
            subsub.active = enable_pin
            subsub.prop(ob, "show_only_shape_key", text="")
            sub.prop(ob, "use_shape_key_edit_mode", text="")

            sub = row.row()
            if key.use_relative:
                sub.operator("object.shape_key_clear", icon='X', text="")
            else:
                sub.operator("object.shape_key_retime", icon='RECOVER_LAST', text="")

            layout.use_property_split = True
            if key.use_relative:
                if ob.active_shape_key_index != 0:
                    row = layout.row()
                    row.active = enable_edit_value
                    row.prop(kb, "value")

                    col = layout.column()
                    sub.active = enable_edit_value
                    sub = col.column(align=True)
                    sub.prop(kb, "slider_min", text="Range Min")
                    sub.prop(kb, "slider_max", text="Max")

                    col.prop_search(kb, "vertex_group", ob, "vertex_groups", text="Vertex Group")
                    col.prop_search(kb, "relative_key", key, "key_blocks", text="Relative To")

            else:
                layout.prop(kb, "interpolation")
                row = layout.column()
                row.active = enable_edit_value
                row.prop(key, "eval_time")
