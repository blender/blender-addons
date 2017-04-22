# gpl author: Ryan Inch (Imaginer)

from bpy.types import Menu
from . import utils_core


class MasterSymmetryMenu(Menu):
    bl_label = "Symmetry Options"
    bl_idname = "VIEW3D_MT_sv3_master_symmetry_menu"

    @classmethod
    def poll(self, context):
        return utils_core.get_mode() in (
                        utils_core.sculpt,
                        utils_core.texture_paint
                        )

    def draw(self, context):
        menu = utils_core.Menu(self)

        if utils_core.get_mode() == utils_core.texture_paint:
            menu.add_item().prop(context.tool_settings.image_paint,
                                 "use_symmetry_x", toggle=True)
            menu.add_item().prop(context.tool_settings.image_paint,
                                 "use_symmetry_y", toggle=True)
            menu.add_item().prop(context.tool_settings.image_paint,
                                 "use_symmetry_z", toggle=True)
        else:
            menu.add_item().menu(SymmetryMenu.bl_idname)
            menu.add_item().menu(SymmetryRadialMenu.bl_idname)
            menu.add_item().prop(context.tool_settings.sculpt,
                                 "use_symmetry_feather", toggle=True)


class SymmetryMenu(Menu):
    bl_label = "Symmetry"
    bl_idname = "VIEW3D_MT_sv3_symmetry_menu"

    def draw(self, context):
        menu = utils_core.Menu(self)

        menu.add_item().label(text="Symmetry")
        menu.add_item().separator()

        menu.add_item().prop(context.tool_settings.sculpt,
                             "use_symmetry_x", toggle=True)
        menu.add_item().prop(context.tool_settings.sculpt,
                             "use_symmetry_y", toggle=True)
        menu.add_item().prop(context.tool_settings.sculpt,
                             "use_symmetry_z", toggle=True)


class SymmetryRadialMenu(Menu):
    bl_label = "Radial"
    bl_idname = "VIEW3D_MT_sv3_symmetry_radial_menu"

    def draw(self, context):
        menu = utils_core.Menu(self)

        menu.add_item().label(text="Radial")
        menu.add_item().separator()

        menu.add_item("column").prop(context.tool_settings.sculpt,
                                     "radial_symmetry", text="", slider=True)
