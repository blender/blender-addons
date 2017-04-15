# gpl: author Rebellion

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty


def add_lamps(self, context):
    try:
        if self.bKeyLight:
            keyLight = bpy.data.lamps.new(name="Key_Light", type="SPOT")
            ob = bpy.data.objects.new("Key_Light", keyLight)
            constraint = ob.constraints.new(type='COPY_LOCATION')
            constraint.use_offset = True
            constraint.owner_space = 'LOCAL'
            constraint.target = self.camera
            constraint = ob.constraints.new(type='TRACK_TO')
            constraint.target = self.target
            constraint.track_axis = 'TRACK_NEGATIVE_Z'
            constraint.up_axis = 'UP_X'
            constraint.owner_space = 'LOCAL'
            bpy.context.scene.objects.link(ob)
            ob.rotation_euler[2] = -0.785398

        if self.bFillLight:
            fillLight = bpy.data.lamps.new(name="Fill_Light", type="SPOT")
            ob = bpy.data.objects.new("Fill_Light", fillLight)
            constraint = ob.constraints.new(type='COPY_LOCATION')
            constraint.use_offset = True
            constraint.owner_space = 'LOCAL'
            constraint.target = self.camera
            constraint = ob.constraints.new(type='TRACK_TO')
            constraint.target = self.target
            constraint.track_axis = 'TRACK_NEGATIVE_Z'
            constraint.up_axis = 'UP_X'
            constraint.owner_space = 'LOCAL'
            bpy.context.scene.objects.link(ob)
            ob.rotation_euler[2] = 0.785398
            ob.data.energy = 0.3

        if self.bBackLight:
            backLight = bpy.data.lamps.new(name="Back_Light", type="SPOT")
            ob = bpy.data.objects.new("Back_Light", backLight)
            constraint = ob.constraints.new(type='COPY_LOCATION')
            constraint.use_offset = True
            constraint.owner_space = 'LOCAL'
            constraint.target = self.camera
            constraint = ob.constraints.new(type='TRACK_TO')
            constraint.target = self.target
            constraint.track_axis = 'TRACK_NEGATIVE_Z'
            constraint.up_axis = 'UP_X'
            constraint.owner_space = 'LOCAL'
            bpy.context.scene.objects.link(ob)
            ob.rotation_euler[2] = 3.14159
            ob.data.energy = 0.2

        if self.camera_constraint:
            constraint = self.camera.constraints.new(type='TRACK_TO')
            constraint.target = self.target
            constraint.track_axis = 'TRACK_NEGATIVE_Z'
            constraint.up_axis = 'UP_Y'

    except Exception as e:
        self.report({'WARNING'},
                    "Some operations could not be performed (See Console for more info)")

        print("\n[object.add_light_template]\nError: {}".format(e))


class OBJECT_OT_add_light_template(Operator):
    bl_idname = "object.add_light_template"
    bl_label = "Add Light Template"
    bl_description = "Add Key, Fill & Back Lights"
    bl_options = {'REGISTER', 'UNDO'}

    camera = None
    target = None

    bKeyLight = BoolProperty(
                    name="Key Light",
                    default=True
                    )
    bFillLight = BoolProperty(
                    name="Fill Light",
                    default=True
                    )
    bBackLight = BoolProperty(
                    name="Back Light",
                    default=True
                    )
    camera_constraint = BoolProperty(
                    name="Camera Constraint",
                    default=False
                    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        objects = context.selected_objects

        if len(objects) == 2:
            for ob in objects:
                if ob.type == 'CAMERA':
                    self.camera = ob
                else:
                    self.target = ob
        elif len(objects) == 1:
            if objects[0].type == 'CAMERA':
                self.camera = objects[0]
                bpy.ops.object.empty_add()
                self.target = context.active_object
            else:
                self.camera = context.scene.camera
                self.target = context.active_object
        elif len(objects) == 0:
            bpy.ops.object.empty_add()
            self.target = context.active_object
            self.camera = context.scene.camera

        add_lamps(self, context)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(OBJECT_OT_add_light_template)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_light_template)


if __name__ == "__main__":
    register()
