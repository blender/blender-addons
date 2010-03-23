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

import bpy
from Mathutils import *
from math import *
from bpy.props import *

bl_addon_info = {
    'name': 'Recall object operator',
    'author': 'Buerbaum Martin (Pontiac)',
    'version': '0.1.1',
    'blender': (2, 5, 3),
    'location': 'View3D > Tool Shelf > Recall object creation operator',
    'url': '',
    'category': '3D View'}


__bpydoc__ = """
Recall object operator

Generic functions to re-create an object that was created
with a "Add Mesh" operator.

The "Add Mesh" operator has to store the "recall" information
in the object properties for this to work.

Usage:

Select an "recall enabled" object and click the "Edit" button
in the "recall" apnel of the Tool Shelf.

Known issues:

The recall doesn't take the rotation/scaling of the
exiting object into account.
i.e. The new object will be created as if it's created
manually at the location of the exiting object.
This also means that "align to view" may affect
rotation of the new object.

v0.1.1 - Removed changes to 3D cursor.
    Removed removal of objects (Has to be handled in "Add Mesh" operator now.)
v0.1 - Initial revision
"""


# Find operator by bl_idname.
# Independent from the format of bl_idname.
# <SPACE>_OT_xxxx and <space>.xxxx are supported.
def get_operator_by_idname(bl_idname):
    list = bl_idname.split(".")

    # Check if splitting didn't work.
    if len(list) <= 1:
        # String format was NOT <space>.xxxx.
        list = bl_idname.split("_OT_")

        # Check if splitting didn't work.
        if len(list) <= 1:
            # String format was NOT <SPACE>_OT_xxxx.
            return None

        # Splitting by _OT_ worked.
        # Make space type lowercase
        list[0].lower()

    space_type = getattr(bpy.ops, list[0], None)
    if not space_type:
        return None

    op = getattr(space_type, list[1], None)
    if not op:
        return None

    return op


class VIEW3D_OT_recall_object_operator(bpy.types.Operator):
    '''Recall object operator'''
    bl_idname = "view3d.recall_object_operator"
    bl_label = "Recall/re-execute operator for the selected object."
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene
        ob = scene.objects.active

        if (ob
            and len(context.selected_objects) == 1
            and ob == context.selected_objects[0]
            and ob.items()):

            if 'recall' in ob:
                r = ob['recall'].convert_to_pyobject()

                # Check if an operator string was defined.
                if "recall_op" in r:
                    op_idname = r["recall_op"]

                    print("Recalling operator: " + op_idname)

                    # Find and recall operator
                    op = get_operator_by_idname(op_idname)
                    if op:
                        # Prepare the stored data as arguments for the op.
                        args = dict([(k[0], k[1]) for k in r.items()])

                        # We need to remove the "recall_op" string.
                        del args["recall_op"]

                        # Execute the operator with the unpacked parameters.
                        op(**args)

                    else:
                        print("No operator found for idname " + op_idname)
                        return {'CANCELLED'}

                    return {'FINISHED'}

                else:
                    print("No operator found in recall data!")
                    return {'CANCELLED'}

            else:
                print("No recall information found in object!")
                return {'CANCELLED'}


class VIEW3D_OT_recall_panel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Recall object creation operator"

    def poll(self, context):
        scene = context.scene
        ob = scene.objects.active

        # Only show this panel if the object has "recall" data.
        if (ob
            and context.selected_objects
            and len(context.selected_objects) == 1
            and ob == context.selected_objects[0]
            and 'recall' in ob):
            return True

        return False

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.recall_object_operator",
            text="Edit (replace)")

################################


def register():
    # Register the operators/menus.
    bpy.types.register(VIEW3D_OT_recall_object_operator)
    bpy.types.register(VIEW3D_OT_recall_panel)


def unregister():
    # Unregister the operators/menus.
    bpy.types.unregister(VIEW3D_OT_recall_object_operator)
    bpy.types.unregister(VIEW3D_OT_recall_panel)

if __name__ == "__main__":
    register()
