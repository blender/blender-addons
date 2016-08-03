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

# <pep8 compliant>

# ----------------------------------------------------------
# Author: Antonio Vazquez (antonioya)
# ----------------------------------------------------------

# ----------------------------------------------
# Define Addon info
# ----------------------------------------------
bl_info = {
    "name": "Archimesh",
    "author": "Antonio Vazquez (antonioya)",
    "location": "View3D > Add > Mesh > Archimesh",
    "version": (1, 1, 2),
    "blender": (2, 6, 8),
    "description": "Generate rooms, doors, windows, kitchen cabinets, "
                   "shelves, roofs, stairs and other architecture stuff.",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Add Mesh"}

import sys
import os

# ----------------------------------------------
# Add to Phyton path (once only)
# ----------------------------------------------
path = sys.path
flag = False
for item in path:
    if "archimesh" in item:
        flag = True
if flag is False:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'archimesh'))
    print("archimesh: added to phytonpath")

# ----------------------------------------------
# Import modules
# ----------------------------------------------
if "bpy" in locals():
    import imp
    imp.reload(achm_room_maker)
    imp.reload(achm_door_maker)
    imp.reload(achm_window_maker)
    imp.reload(achm_roof_maker)
    imp.reload(achm_column_maker)
    imp.reload(achm_stairs_maker)
    imp.reload(achm_kitchen_maker)
    imp.reload(achm_shelves_maker)
    imp.reload(achm_books_maker)
    imp.reload(achm_lamp_maker)
    imp.reload(achm_curtain_maker)
    imp.reload(achm_venetian_maker)
    imp.reload(achm_main_panel)
    imp.reload(achm_window_panel)
    print("archimesh: Reloaded multifiles")
else:
    import achm_books_maker
    import achm_column_maker
    import achm_curtain_maker
    import achm_venetian_maker
    import achm_door_maker
    import achm_kitchen_maker
    import achm_lamp_maker
    import achm_main_panel
    import achm_roof_maker
    import achm_room_maker
    import achm_shelves_maker
    import achm_stairs_maker
    import achm_window_maker
    import achm_window_panel

    print("archimesh: Imported multifiles")

# noinspection PyUnresolvedReferences
import bpy
# noinspection PyUnresolvedReferences
from bpy.props import *

# ----------------------------------------------------------
# Decoration assets
# ----------------------------------------------------------


class AchmInfoMtMeshDecorationAdd(bpy.types.Menu):
    bl_idname = "INFO_MT_mesh_decoration_add"
    bl_label = "Decoration assets"

    # noinspection PyUnusedLocal
    def draw(self, context):
        self.layout.operator("mesh.archimesh_books", text="Add Books", icon="PLUGIN")
        self.layout.operator("mesh.archimesh_lamp", text="Add Lamp", icon="PLUGIN")
        self.layout.operator("mesh.archimesh_roller", text="Add Roller curtains", icon="PLUGIN")
        self.layout.operator("mesh.archimesh_venetian", text="Add Venetian blind", icon="PLUGIN")
        self.layout.operator("mesh.archimesh_japan", text="Add Japanese curtains", icon="PLUGIN")

# ----------------------------------------------------------
# Registration
# ----------------------------------------------------------


class AchmInfoMtMeshCustomMenuAdd(bpy.types.Menu):
    bl_idname = "INFO_MT_mesh_custom_menu_add"
    bl_label = "Archimesh"

    # noinspection PyUnusedLocal
    def draw(self, context):
        self.layout.operator_context = 'INVOKE_REGION_WIN'
        self.layout.operator("mesh.archimesh_room", text="Add Room", icon="PLUGIN")
        self.layout.operator("mesh.archimesh_door", text="Add Door", icon="PLUGIN")
        self.layout.operator("mesh.archimesh_window", text="Add Rail Window", icon="PLUGIN")
        self.layout.operator("mesh.archimesh_winpanel", text="Add Panel Window", icon="PLUGIN")
        self.layout.operator("mesh.archimesh_kitchen", text="Add Cabinet", icon="PLUGIN")
        self.layout.operator("mesh.archimesh_shelves", text="Add Shelves", icon="PLUGIN")
        self.layout.operator("mesh.archimesh_column", text="Add Column", icon="PLUGIN")
        self.layout.operator("mesh.archimesh_stairs", text="Add Stairs", icon="PLUGIN")
        self.layout.operator("mesh.archimesh_roof", text="Add Roof", icon="PLUGIN")
        self.layout.menu("INFO_MT_mesh_decoration_add", text="Decoration props", icon="GROUP")

# --------------------------------------------------------------
# Register all operators and panels
# --------------------------------------------------------------
# Define menu


# noinspection PyUnusedLocal
def AchmMenu_func(self, context):
    self.layout.menu("INFO_MT_mesh_custom_menu_add", icon="PLUGIN")


def register():
    bpy.utils.register_class(AchmInfoMtMeshCustomMenuAdd)
    bpy.utils.register_class(AchmInfoMtMeshDecorationAdd)
    bpy.utils.register_class(achm_room_maker.AchmRoom)
    bpy.utils.register_class(achm_room_maker.AchmRoomGeneratorPanel)
    bpy.utils.register_class(achm_room_maker.AchmExportRoom)
    bpy.utils.register_class(achm_room_maker.AchmImportRoom)
    bpy.utils.register_class(achm_door_maker.AchmDoor)
    bpy.utils.register_class(achm_door_maker.AchmDoorObjectgeneratorpanel)
    bpy.utils.register_class(achm_window_maker.AchmWindows)
    bpy.utils.register_class(achm_window_maker.AchmWindowObjectgeneratorpanel)
    bpy.utils.register_class(achm_roof_maker.AchmRoof)
    bpy.utils.register_class(achm_column_maker.AchmColumn)
    bpy.utils.register_class(achm_stairs_maker.AchmStairs)
    bpy.utils.register_class(achm_kitchen_maker.AchmKitchen)
    bpy.utils.register_class(achm_kitchen_maker.AchmExportInventory)
    bpy.utils.register_class(achm_shelves_maker.AchmShelves)
    bpy.utils.register_class(achm_books_maker.AchmBooks)
    bpy.utils.register_class(achm_lamp_maker.AchmLamp)
    bpy.utils.register_class(achm_curtain_maker.AchmRoller)
    bpy.utils.register_class(achm_curtain_maker.AchmJapan)
    bpy.utils.register_class(achm_venetian_maker.AchmVenetian)
    bpy.utils.register_class(achm_venetian_maker.AchmVenetianObjectgeneratorpanel)
    bpy.utils.register_class(achm_main_panel.ArchimeshMainPanel)
    bpy.utils.register_class(achm_main_panel.AchmHoleAction)
    bpy.utils.register_class(achm_main_panel.AchmPencilAction)
    bpy.utils.register_class(achm_main_panel.AchmRunHintDisplayButton)
    bpy.utils.register_class(achm_window_panel.AchmWinPanel)
    bpy.utils.register_class(achm_window_panel.AchmWindowEditPanel)
    bpy.types.INFO_MT_mesh_add.append(AchmMenu_func)

    # Define properties
    bpy.types.Scene.archimesh_select_only = bpy.props.BoolProperty(
            name="Only selected",
            description="Apply auto holes only to selected objects",
            default=False,
            )
    bpy.types.Scene.archimesh_ceiling = bpy.props.BoolProperty(
            name="Ceiling",
            description="Create a ceiling",
            default=False,
            )
    bpy.types.Scene.archimesh_floor = bpy.props.BoolProperty(
            name="Floor",
            description="Create a floor automatically",
            default=False,
            )

    bpy.types.Scene.archimesh_merge = bpy.props.BoolProperty(
            name="Close walls",
            description="Close walls to create a full closed room",
            default=False,
            )

    bpy.types.Scene.archimesh_text_color = bpy.props.FloatVectorProperty(
            name="Hint color",
            description="Color for the text and lines",
            default=(0.173, 0.545, 1.0, 1.0),
            min=0.1,
            max=1,
            subtype='COLOR',
            size=4,
            )
    bpy.types.Scene.archimesh_walltext_color = bpy.props.FloatVectorProperty(
            name="Hint color",
            description="Color for the wall label",
            default=(1, 0.8, 0.1, 1.0),
            min=0.1,
            max=1,
            subtype='COLOR',
            size=4,
            )
    bpy.types.Scene.archimesh_font_size = bpy.props.IntProperty(
            name="Text Size",
            description="Text size for hints",
            default=14, min=10, max=150,
            )
    bpy.types.Scene.archimesh_wfont_size = bpy.props.IntProperty(
            name="Text Size",
            description="Text size for wall labels",
            default=16, min=10, max=150,
            )
    bpy.types.Scene.archimesh_hint_space = bpy.props.FloatProperty(
            name='Separation', min=0, max=5, default=0.1,
            precision=2,
            description='Distance from object to display hint',
            )
    bpy.types.Scene.archimesh_gl_measure = bpy.props.BoolProperty(
            name="Measures",
            description="Display measures",
            default=True,
            )
    bpy.types.Scene.archimesh_gl_name = bpy.props.BoolProperty(
            name="Names",
            description="Display names",
            default=True,
            )
    bpy.types.Scene.archimesh_gl_ghost = bpy.props.BoolProperty(
            name="All",
            description="Display measures for all objects,"
            " not only selected",
            default=True,
            )

    # OpenGL flag
    wm = bpy.types.WindowManager
    # register internal property
    wm.archimesh_run_opengl = bpy.props.BoolProperty(default=False)


def unregister():
    bpy.utils.unregister_class(AchmInfoMtMeshCustomMenuAdd)
    bpy.utils.unregister_class(AchmInfoMtMeshDecorationAdd)
    bpy.utils.unregister_class(achm_room_maker.AchmRoom)
    bpy.utils.unregister_class(achm_room_maker.AchmRoomGeneratorPanel)
    bpy.utils.unregister_class(achm_room_maker.AchmExportRoom)
    bpy.utils.unregister_class(achm_room_maker.AchmImportRoom)
    bpy.utils.unregister_class(achm_door_maker.AchmDoor)
    bpy.utils.unregister_class(achm_door_maker.AchmDoorObjectgeneratorpanel)
    bpy.utils.unregister_class(achm_window_maker.AchmWindows)
    bpy.utils.unregister_class(achm_window_maker.AchmWindowObjectgeneratorpanel)
    bpy.utils.unregister_class(achm_roof_maker.AchmRoof)
    bpy.utils.unregister_class(achm_column_maker.AchmColumn)
    bpy.utils.unregister_class(achm_stairs_maker.AchmStairs)
    bpy.utils.unregister_class(achm_kitchen_maker.AchmKitchen)
    bpy.utils.unregister_class(achm_kitchen_maker.AchmExportInventory)
    bpy.utils.unregister_class(achm_shelves_maker.AchmShelves)
    bpy.utils.unregister_class(achm_books_maker.AchmBooks)
    bpy.utils.unregister_class(achm_lamp_maker.AchmLamp)
    bpy.utils.unregister_class(achm_curtain_maker.AchmRoller)
    bpy.utils.unregister_class(achm_curtain_maker.AchmJapan)
    bpy.utils.unregister_class(achm_venetian_maker.AchmVenetian)
    bpy.utils.unregister_class(achm_venetian_maker.AchmVenetianObjectgeneratorpanel)
    bpy.utils.unregister_class(achm_main_panel.ArchimeshMainPanel)
    bpy.utils.unregister_class(achm_main_panel.AchmHoleAction)
    bpy.utils.unregister_class(achm_main_panel.AchmPencilAction)
    bpy.utils.unregister_class(achm_main_panel.AchmRunHintDisplayButton)
    bpy.utils.unregister_class(achm_window_panel.AchmWinPanel)
    bpy.utils.unregister_class(achm_window_panel.AchmWindowEditPanel)
    bpy.types.INFO_MT_mesh_add.remove(AchmMenu_func)

    # Remove properties
    del bpy.types.Scene.archimesh_select_only
    del bpy.types.Scene.archimesh_ceiling
    del bpy.types.Scene.archimesh_floor
    del bpy.types.Scene.archimesh_merge
    del bpy.types.Scene.archimesh_text_color
    del bpy.types.Scene.archimesh_walltext_color
    del bpy.types.Scene.archimesh_font_size
    del bpy.types.Scene.archimesh_wfont_size
    del bpy.types.Scene.archimesh_hint_space
    del bpy.types.Scene.archimesh_gl_measure
    del bpy.types.Scene.archimesh_gl_name
    del bpy.types.Scene.archimesh_gl_ghost
    # remove OpenGL data
    achm_main_panel.AchmRunHintDisplayButton.handle_remove(achm_main_panel.AchmRunHintDisplayButton, bpy.context)
    wm = bpy.context.window_manager
    p = 'archimesh_run_opengl'
    if p in wm:
        del wm[p]


if __name__ == '__main__':
    register()
