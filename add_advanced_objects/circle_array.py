# gpl author: Antonis Karvelas

# -*- coding: utf-8 -*-

bl_info = {
    "name": "Circle Array",
    "author": "Antonis Karvelas",
    "version": (1, 0),
    "blender": (2, 6, 7),
    "location": "View3D > Object > Circle_Array",
    "description": "Uses an existing array and creates an empty, "
                   "rotates it properly and makes a Circle Array",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"
    }


import bpy
from bpy.types import Operator
from math import radians


class Circle_Array(Operator):
    bl_label = "Circle Array"
    bl_idname = "objects.circle_array_operator"
    bl_description = ("Creates an Array Modifier with offset empty object\n"
                      "Works with Mesh, Curve, Text & Surface")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def check_empty_name(self, context):
        new_name, def_name = "", "EMPTY_C_Array"
        suffix = 1
        try:
            # first slap a simple linear count + 1 for numeric suffix, if it fails
            # harvest for the rightmost numbers and append the max value
            list_obj = []
            obj_all = context.scene.objects
            list_obj = [obj.name for obj in obj_all if obj.name.startswith(def_name)]
            new_name = "{}_{}".format(def_name, len(list_obj) + 1)

            if new_name in list_obj:
                from re import findall
                test_num = [findall("\d+", words) for words in list_obj]
                suffix += max([int(l[-1]) for l in test_num])
                new_name = "{}_{}".format(def_name, suffix)
            return new_name
        except:
            return None

    def execute(self, context):
        try:
            allowed_obj = ['MESH', 'CURVE', 'SURFACE', 'FONT']
            if context.active_object.type not in allowed_obj:
                self.report(
                    {"WARNING"},
                    "Operation Cancelled. The active object is not of "
                    "Mesh, Curve, Surface or Font type"
                    )
                return {'CANCELLED'}

            default_name = self.check_empty_name(context) or "EMPTY_C_Array"
            bpy.ops.object.modifier_add(type='ARRAY')

            if len(bpy.context.selected_objects) == 2:
                list = bpy.context.selected_objects
                active = list[0]
                active.modifiers[0].use_object_offset = True
                active.modifiers[0].use_relative_offset = False
                active.select = False
                bpy.context.scene.objects.active = list[0]
                bpy.ops.view3d.snap_cursor_to_selected()
                if active.modifiers[0].offset_object is None:
                    bpy.ops.object.add(type='EMPTY')
                    empty_name = bpy.context.active_object
                    empty_name.name = default_name
                    active.modifiers[0].offset_object = empty_name
                else:
                    empty_name = active.modifiers[0].offset_object

                bpy.context.scene.objects.active = active
                num = active.modifiers["Array"].count
                rotate_num = 360 / num
                active.select = True
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
                empty_name.rotation_euler = (0, 0, radians(rotate_num))
                empty_name.select = False
                active.select = True
                bpy.ops.object.origin_set(type="ORIGIN_CURSOR")

                return {'FINISHED'}
            else:
                active = context.active_object
                active.modifiers[0].use_object_offset = True
                active.modifiers[0].use_relative_offset = False
                bpy.ops.view3d.snap_cursor_to_selected()
                if active.modifiers[0].offset_object is None:
                    bpy.ops.object.add(type='EMPTY')
                    empty_name = bpy.context.active_object
                    empty_name.name = default_name
                    active.modifiers[0].offset_object = empty_name
                else:
                    empty_name = active.modifiers[0].offset_object

                bpy.context.scene.objects.active = active
                num = active.modifiers["Array"].count
                rotate_num = 360 / num
                active.select = True
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
                empty_name.rotation_euler = (0, 0, radians(rotate_num))
                empty_name.select = False
                active.select = True

                return {'FINISHED'}
        except Exception as e:
            self.report({'WARNING'},
                        "Circle Array operator could not be executed (See the console for more info)")
            print("\n[objects.circle_array_operator]\nError: {}\n".format(e))

            return {'CANCELLED'}


# Register
def circle_array_menu(self, context):
    self.layout.operator(Circle_Array.bl_idname, text="Circle_Array")


def register():
    bpy.utils.register_class(Circle_Array)
    bpy.types.VIEW3D_MT_object.append(circle_array_menu)


def unregister():
    bpy.utils.unregister_class(Circle_Array)
    bpy.types.VIEW3D_MT_object.remove(circle_array_menu)


if __name__ == "__main__":
    register()
