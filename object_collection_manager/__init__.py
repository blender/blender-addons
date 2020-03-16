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

# Copyright 2011, Ryan Inch

bl_info = {
    "name": "Collection Manager",
    "description": "Manage collections and their objects",
    "author": "Ryan Inch",
    "version": (2,0,0),
    "blender": (2, 80, 0),
    "location": "View3D - Object Mode (Shortcut - M)",
    "warning": '',  # used for warning icon and text in addons panel
    "doc_url": "{BLENDER_MANUAL_URL}/addons/interface/collection_manager.html",
    "category": "Interface",
}


if "bpy" in locals():
    import importlib

    importlib.reload(internals)
    importlib.reload(operators)
    importlib.reload(preferences)
    importlib.reload(qcd_move_widget)
    importlib.reload(qcd_operators)
    importlib.reload(ui)

else:
    from . import internals
    from . import operators
    from . import preferences
    from . import qcd_move_widget
    from . import qcd_operators
    from . import ui

import os
import bpy
import bpy.utils.previews
from bpy.app.handlers import persistent
from bpy.types import PropertyGroup
from bpy.props import (
    CollectionProperty,
    EnumProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    PointerProperty,
    )


class CollectionManagerProperties(PropertyGroup):
    cm_list_collection: CollectionProperty(type=internals.CMListCollection)
    cm_list_index: IntProperty(update=ui.update_selection)

    show_exclude: BoolProperty(default=True, name="Exclude from View Layer")
    show_selectable: BoolProperty(default=True, name="Selectable")
    show_hide_viewport: BoolProperty(default=True, name="Hide in Viewport")
    show_disable_viewport: BoolProperty(default=False, name="Disable in Viewports")
    show_render: BoolProperty(default=False, name="Disable in Renders")

    in_phantom_mode: BoolProperty(default=False)

    update_header: CollectionProperty(type=internals.CMListCollection)

    qcd_slots_blend_data: StringProperty()


addon_keymaps = []

classes = (
    internals.CMListCollection,
    internals.CMSendReport,
    operators.ExpandAllOperator,
    operators.ExpandSublevelOperator,
    operators.CMExcludeOperator,
    operators.CMUnExcludeAllOperator,
    operators.CMRestrictSelectOperator,
    operators.CMUnRestrictSelectAllOperator,
    operators.CMHideOperator,
    operators.CMUnHideAllOperator,
    operators.CMDisableViewportOperator,
    operators.CMUnDisableViewportAllOperator,
    operators.CMDisableRenderOperator,
    operators.CMUnDisableRenderAllOperator,
    operators.CMNewCollectionOperator,
    operators.CMRemoveCollectionOperator,
    operators.CMSetCollectionOperator,
    operators.CMPhantomModeOperator,
    preferences.CMPreferences,
    qcd_move_widget.QCDMoveWidget,
    qcd_operators.MoveToQCDSlot,
    qcd_operators.ViewQCDSlot,
    qcd_operators.ViewMoveQCDSlot,
    qcd_operators.RenumerateQCDSlots,
    ui.CM_UL_items,
    ui.CollectionManager,
    ui.CMRestrictionTogglesPanel,
    CollectionManagerProperties,
    )

@persistent
def depsgraph_update_post_handler(dummy):
    if qcd_operators.move_triggered:
        qcd_operators.move_triggered = False
        return

    qcd_operators.move_selection.clear()
    qcd_operators.move_active = None
    qcd_operators.get_move_selection()
    qcd_operators.get_move_active()

@persistent
def save_internal_data(dummy):
    cm = bpy.context.scene.collection_manager

    cm.qcd_slots_blend_data = internals.qcd_slots.get_data_for_blend()

@persistent
def load_internal_data(dummy):
    cm = bpy.context.scene.collection_manager
    data = cm.qcd_slots_blend_data

    if not data:
        return

    internals.qcd_slots.load_blend_data(data)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    pcoll.load("active_icon_base", os.path.join(icons_dir, "minus.png"), 'IMAGE', True)
    pcoll.load("active_icon_text", os.path.join(icons_dir, "minus.png"), 'IMAGE', True)
    pcoll.load("active_icon_text_sel", os.path.join(icons_dir, "minus.png"), 'IMAGE', True)
    ui.preview_collections["icons"] = pcoll


    bpy.types.Scene.collection_manager = PointerProperty(type=CollectionManagerProperties)

    bpy.types.VIEW3D_HT_header.append(ui.view3d_header_qcd_slots)

    # create the global menu hotkey
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
    kmi = km.keymap_items.new('view3d.collection_manager', 'M', 'PRESS')
    addon_keymaps.append((km, kmi))

    # create qcd hotkeys
    qcd_hotkeys = [
        ["ONE", False, "1"],
        ["TWO", False, "2"],
        ["THREE", False, "3"],
        ["FOUR", False, "4"],
        ["FIVE", False, "5"],
        ["SIX", False, "6"],
        ["SEVEN", False, "7"],
        ["EIGHT", False, "8"],
        ["NINE", False, "9"],
        ["ZERO", False, "10"],
        ["ONE", True, "11"],
        ["TWO", True, "12"],
        ["THREE", True, "13"],
        ["FOUR", True, "14"],
        ["FIVE", True, "15"],
        ["SIX", True, "16"],
        ["SEVEN", True, "17"],
        ["EIGHT", True, "18"],
        ["NINE", True, "19"],
        ["ZERO", True, "20"],
    ]

    for key in qcd_hotkeys:
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
        kmi = km.keymap_items.new('view3d.view_qcd_slot', key[0], 'PRESS', alt=key[1])
        kmi.properties.slot = key[2]
        kmi.properties.toggle = False
        addon_keymaps.append((km, kmi))

        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
        kmi = km.keymap_items.new('view3d.view_qcd_slot', key[0], 'PRESS',shift=True,  alt=key[1])
        kmi.properties.slot = key[2]
        kmi.properties.toggle = True
        addon_keymaps.append((km, kmi))

    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
    kmi = km.keymap_items.new('view3d.qcd_move_widget', 'V', 'PRESS')
    addon_keymaps.append((km, kmi))

    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post_handler)
    bpy.app.handlers.save_pre.append(save_internal_data)
    bpy.app.handlers.load_post.append(load_internal_data)

def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post_handler)
    bpy.app.handlers.save_pre.remove(save_internal_data)
    bpy.app.handlers.load_post.remove(load_internal_data)

    for cls in classes:
        bpy.utils.unregister_class(cls)

    for pcoll in ui.preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    ui.preview_collections.clear()
    ui.last_icon_theme_text = None
    ui.last_icon_theme_text_sel = None

    del bpy.types.Scene.collection_manager

    bpy.types.VIEW3D_HT_header.remove(ui.view3d_header_qcd_slots)

    # remove keymaps when add-on is deactivated
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
