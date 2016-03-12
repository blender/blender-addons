# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Bone Selection Sets",
    "author": "Dan Eicher, Antony Riakiotakis, Inês Almeida",
    "version": (2, 0, 0),
    "blender": (2, 75, 0),
    "location": "Properties > Object Data (Armature) > Selection Sets",
    "description": "List of Bone sets for easy selection while animating",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Animation/SelectionSets",
    "category": "Animation",
}

import bpy
from bpy.types import (
    Operator,
    Menu,
    Panel,
    UIList,
    PropertyGroup,
)

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    CollectionProperty,
    BoolVectorProperty,
    FloatVectorProperty,
)

# Data Structure ##############################################################

# Note: bones are stored by name, this means that if the bone is renamed,
# there can be problems. However, bone renaming is unlikely during animation
class SelectionEntry(PropertyGroup):
    name = StringProperty(name="Bone Name")


class SelectionSet(PropertyGroup):
    name = StringProperty(name="Set Name")
    bone_ids = CollectionProperty(type=SelectionEntry)


# UI Panel w/ UIList ##########################################################

class POSE_MT_selection_sets_specials(Menu):
    bl_label = "Selection Sets Specials"

    def draw(self, context):
        layout = self.layout

        # TODO
        #layout.operator("pose.selection_sets_sort", icon='SORTALPHA', text="Sort by Name").sort_type = 'NAME'


class POSE_PT_selection_sets(Panel):
    bl_label = "Selection Sets"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return (context.object
            and context.object.type == 'ARMATURE'
            and context.object.pose)

    def draw(self, context):
        layout = self.layout

        ob = context.object
        arm = context.object

        row = layout.row()
        row.enabled = (context.mode == 'POSE')

        # UI list
        rows = 4  if len(arm.selection_sets) > 0 else 1
        row.template_list(
            "POSE_UL_selection_set", "", # type and unique id
            arm, "selection_sets", # pointer to the CollectionProperty
            arm, "active_selection_set", # pointer to the active identifier
            rows=rows
        )

        # add/remove/specials UI list Menu
        col = row.column(align=True)
        col.operator("pose.selection_set_add", icon='ZOOMIN', text="")
        col.operator("pose.selection_set_remove", icon='ZOOMOUT', text="")
        # TODO specials like sorting
        #col.menu("POSE_MT_selection_sets_specials", icon='DOWNARROW_HLT', text="")

        # TODO move up/down arrows

        # buttons
        row = layout.row()

        sub = row.row(align=True)
        sub.operator("pose.selection_set_assign", text="Assign")
        sub.operator("pose.selection_set_unassign", text="Remove")

        sub = row.row(align=True)
        sub.operator("pose.selection_set_select", text="Select")
        sub.operator("pose.selection_set_deselect", text="Deselect")


class POSE_UL_selection_set(UIList):
    def draw_item(self, context, layout, data, set, icon, active_data, active_propname, index):
        layout.prop(set, "name", text="", icon='GROUP_BONE', emboss=False)


# Operators ###################################################################

class PluginOperator(Operator):
    @classmethod
    def poll(self, context):
        return (context.object and
                context.object.type == 'ARMATURE' and
                context.mode == 'POSE')

class NeedSelSetPluginOperator(PluginOperator):
    @classmethod
    def poll(self, context):
        if super().poll(context):
            arm =  context.object
            return (arm.active_selection_set < len(arm.selection_sets))
        return False


class POSE_OT_selection_set_add(PluginOperator):
    bl_idname = "pose.selection_set_add"
    bl_label = "Create Selection Set"
    bl_description = "Creates a new empty Selection Set"
    bl_options = {'UNDO', 'REGISTER'}

    created_counter = 0

    def execute(self, context):
        arm = context.object

        new_sel_set = arm.selection_sets.add()

        # naming
        new_sel_set.name  = "SelectionSet"
        if POSE_OT_selection_set_add.created_counter > 0:
            new_sel_set.name += ".{:03d}".format(POSE_OT_selection_set_add.created_counter)
        POSE_OT_selection_set_add.created_counter += 1

        # select newly created set
        arm.active_selection_set = len(arm.selection_sets) - 1

        return {'FINISHED'}


class POSE_OT_selection_set_remove(NeedSelSetPluginOperator):
    bl_idname = "pose.selection_set_remove"
    bl_label = "Delete Selection Set"
    bl_description = "Delete a Selection Set"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        arm = context.object

        arm.selection_sets.remove(arm.active_selection_set)

        # change currently active selection set
        numsets = len(arm.selection_sets)
        if (arm.active_selection_set > (numsets - 1) and numsets > 0):
            arm.active_selection_set = len(arm.selection_sets) - 1

        return {'FINISHED'}


class POSE_OT_selection_set_assign(NeedSelSetPluginOperator):
    bl_idname = "pose.selection_set_assign"
    bl_label = "Add Bones to Selection Set"
    bl_description = "Add selected bones to Selection Set"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        arm = context.object
        pose = arm.pose
        act_sel_set = arm.selection_sets[arm.active_selection_set]

        #if arm.active_selection_set <= 0:
        #    arm.selection_sets.add()
            #TODO naming convention
        #    return {'FINISHED'}

        # iterate only the selected bones in current pose that are not hidden
        for bone in context.selected_pose_bones:
            if bone.name not in act_sel_set.bone_ids:
                bone_id = act_sel_set.bone_ids.add()
                bone_id.name = bone.name

        return {'FINISHED'}


class POSE_OT_selection_set_unassign(NeedSelSetPluginOperator):
    bl_idname = "pose.selection_set_unassign"
    bl_label = "Remove Bones from Selection Set"
    bl_description = "Remove selected bones from Selection Set"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        arm = context.object
        pose = arm.pose
        act_sel_set = arm.selection_sets[arm.active_selection_set]

        # iterate only the selected bones in current pose that are not hidden
        for bone in context.selected_pose_bones:
            if bone.name in act_sel_set.bone_ids:
                idx = act_sel_set.bone_ids.find(bone.name)
                act_sel_set.bone_ids.remove(idx)

        return {'FINISHED'}


class POSE_OT_selection_set_select(NeedSelSetPluginOperator):
    bl_idname = "pose.selection_set_select"
    bl_label = "Select Selection Set"
    bl_description = "Add Selection Set bones to current selection"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        arm = context.object
        pose = arm.pose
        act_sel_set = arm.selection_sets[arm.active_selection_set]

        for bone in context.visible_pose_bones:
            if bone.name in act_sel_set.bone_ids:
                 bone.bone.select = True

        return {'FINISHED'}


class POSE_OT_selection_set_deselect(NeedSelSetPluginOperator):
    bl_idname = "pose.selection_set_deselect"
    bl_label = "Deselect Selection Set"
    bl_description = "Remove Selection Set bones from current selection"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        arm = context.object
        pose = arm.pose
        act_sel_set = arm.selection_sets[arm.active_selection_set]

        for bone in context.selected_pose_bones:
            if bone.name in act_sel_set.bone_ids:
                bone.bone.select = False

        return {'FINISHED'}


# Registry ####################################################################

classes = (
    POSE_MT_selection_sets_specials,
    POSE_PT_selection_sets,
    POSE_UL_selection_set,
    SelectionEntry,
    SelectionSet,
    POSE_OT_selection_set_add,
    POSE_OT_selection_set_remove,
    POSE_OT_selection_set_assign,
    POSE_OT_selection_set_unassign,
    POSE_OT_selection_set_select,
    POSE_OT_selection_set_deselect,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.selection_sets = CollectionProperty(
        type=SelectionSet,
        name="Selection Sets",
        description="List of groups of bones for easy selection"
    )
    bpy.types.Object.active_selection_set = IntProperty(
        name="Active Selection Set",
        description="Index of the currently active selection set",
        default=0
    )


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Object.selection_sets
    del bpy.types.Object.active_selection_set


if __name__ == "__main__":
    register()
