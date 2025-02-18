# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# author Daniel Schalla, maintained by meta-androcto

bl_info = {
    "name": "Tri-lighting",
    "author": "Daniel Schalla",
    "version": (0, 1, 5),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Lights",
    "description": "Add 3 Point Lighting to Selected / Active Object",
    "warning": "",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/lighting/trilighting.html",
    "category": "Lighting",
}

import bpy
from bpy.types import Operator
from bpy.props import (
        EnumProperty,
        FloatProperty,
        IntProperty,
        )
from math import (
        sin, cos,
        radians,
        sqrt,
        )


class OBJECT_OT_TriLighting(Operator):
    bl_idname = "object.trilighting"
    bl_label = "Tri-Lighting Creator"
    bl_description = ("Add 3 Point Lighting to Selected / Active Object\n"
                      "Needs an existing Active Object")
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {'CYCLES', 'EEVEE'}

    height: FloatProperty(
            name="Height",
            default=5
            )
    distance: FloatProperty(
            name="Distance",
            default=5,
            min=0.1,
            subtype="DISTANCE"
            )
    energy: IntProperty(
            name="Base Energy",
            default=3,
            min=1
            )
    contrast: IntProperty(
            name="Contrast",
            default=50,
            min=-100, max=100,
            subtype="PERCENTAGE"
            )
    leftangle: IntProperty(
            name="Left Angle",
            default=26,
            min=1, max=90,
            subtype="ANGLE"
            )
    rightangle: IntProperty(
            name="Right Angle",
            default=45,
            min=1, max=90,
            subtype="ANGLE"
            )
    backangle: IntProperty(
            name="Back Angle",
            default=235,
            min=90, max=270,
            subtype="ANGLE"
            )
    Light_Type_List = [
            ('POINT', "Point", "Point Light"),
            ('SUN', "Sun", "Sun Light"),
            ('SPOT', "Spot", "Spot Light"),
            ('AREA', "Area", "Area Light")
            ]
    primarytype: EnumProperty(
            attr='tl_type',
            name="Key Type",
            description="Choose the types of Key Lights you would like",
            items=Light_Type_List,
            default='AREA'
            )
    secondarytype: EnumProperty(
            attr='tl_type',
            name="Fill + Back Type",
            description="Choose the types of secondary Lights you would like",
            items=Light_Type_List,
            default="AREA"
            )

    # Shape and Size Properties for the lights
    Light_Shape_List = [
            ('SQUARE', "Square", "Square Light"),
            ('RECTANGLE', "Rectangle", "Rectangular Light"),
            ('DISK', "Disk", "Disk Light"),
            ('ELLIPSE', "Ellipse", "Elliptical Light")
            ]
    key_light_shape: EnumProperty(
            name="Key Light Shape",
            items=Light_Shape_List,
            default='SQUARE'
            )
    secondary_light_shape: EnumProperty(
            name="Fill + Back Light Shape",
            items=Light_Shape_List,
            default='SQUARE'
            )
    key_light_size: FloatProperty(
            name="Key Light Size",
            default=0.25,
            min=0
            )
    secondary_light_size: FloatProperty(
            name="Fill + Back Light Size",
            default=0.25,
            min=0
            )

    # New properties for shadow_soft_size
    shadow_soft_size_key: FloatProperty(
        name="Key Light Shadow Soft Size",
        default=0.0,
        min=0.0
    )

    shadow_soft_size_fill: FloatProperty(
        name="Fill + Back Light Shadow Soft Size",
        default=0.0,
        min=0.0
    )

    # New properties for Spot Light (size in degrees, not in Blender units)
    spot_size_key: FloatProperty(
        name="Key Spot Light Size (in Degrees)",
        default=45.0,
        min=1.0,
        max=180.0
    )
    spot_blend_key: FloatProperty(
        name="Key Spot Light Blend",
        default=0.150,
        min=0.0,
        max=1.0
    )

    spot_size_fill: FloatProperty(
        name="Fill + Back Spot Light Size (in Degrees)",
        default=45.0,
        min=1.0,
        max=180.0
    )
    spot_blend_fill: FloatProperty(
        name="Fill + Back Spot Light Blend",
        default=0.150,
        min=0.0,
        max=1.0
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def draw(self, context):
        layout = self.layout

        layout.label(text="Position:")
        col = layout.column(align=True)
        col.prop(self, "height")
        col.prop(self, "distance")

        layout.label(text="Light:")
        col = layout.column(align=True)
        col.prop(self, "energy")
        col.prop(self, "contrast")

        layout.label(text="Orientation:")
        col = layout.column(align=True)
        col.prop(self, "leftangle")
        col.prop(self, "rightangle")
        col.prop(self, "backangle")

        col = layout.column()
        col.label(text="Key Light Type:")
        col.prop(self, "primarytype", text="")
        col.label(text="Fill + Back Type:")
        col.prop(self, "secondarytype", text="")

        # Shape and Size for Key Light
        col.label(text="Key Light Shape and Size:")
        if self.primarytype == 'AREA':
            col.prop(self, "key_light_shape")
            col.prop(self, "key_light_size")

        # Add shadow_soft_size for the key light (only if Spot or Point is selected)
        if self.primarytype in {'POINT', 'SPOT'}:
            col.label(text="Key Light Shadow Soft Size:")
            col.prop(self, "shadow_soft_size_key")

        # Add Spot Size and Blend for Spot
        if self.primarytype == 'SPOT':
            col.label(text="Key Spot Light Size (in Degrees):")
            col.prop(self, "spot_size_key")
            col.label(text="Key Spot Light Blend:")
            col.prop(self, "spot_blend_key")

        # Shape and Size for Fill + Back Light
        col.label(text="Fill + Back Light Shape and Size:")
        if self.secondarytype == 'AREA':
            col.prop(self, "secondary_light_shape")
            col.prop(self, "secondary_light_size")

        # Add shadow_soft_size for the Fill + Back Light (only if Spot or Point is selected)
        if self.secondarytype in {'POINT', 'SPOT'}:
            col.label(text="Fill + Back Light Shadow Soft Size:")
            col.prop(self, "shadow_soft_size_fill")

        # Add Spot Size and Blend for Fill + Back
        if self.secondarytype == 'SPOT':
            col.label(text="Fill + Back Spot Light Size (in Degrees):")
            col.prop(self, "spot_size_fill")
            col.label(text="Fill + Back Spot Light Blend:")
            col.prop(self, "spot_blend_fill")

    def execute(self, context):
        try:
            collection = context.collection
            scene = context.scene
            view = context.space_data
            if view.type == 'VIEW_3D':
                camera = view.camera
            else:
                camera = scene.camera

            if (camera is None):
                cam_data = bpy.data.cameras.new(name='Camera')
                cam_obj = bpy.data.objects.new(name='Camera', object_data=cam_data)
                collection.objects.link(cam_obj)
                scene.camera = cam_obj
                bpy.ops.view3d.camera_to_view()
                camera = cam_obj
                # Leave camera view again, otherwise redo does not work correctly.
                bpy.ops.view3d.view_camera()

            obj = bpy.context.view_layer.objects.active

            # Calculate Energy for each Lamp
            if(self.contrast > 0):
                keyEnergy = self.energy
                backEnergy = (self.energy / 100) * abs(self.contrast)
                fillEnergy = (self.energy / 100) * abs(self.contrast)
            else:
                keyEnergy = (self.energy / 100) * abs(self.contrast)
                backEnergy = self.energy
                fillEnergy = self.energy

            # Calculate Direction for each Lamp

            # Calculate current Distance and get Delta
            obj_position = obj.location
            cam_position = camera.location

            delta_position = cam_position - obj_position
            vector_length = sqrt(
                            (pow(delta_position.x, 2) +
                             pow(delta_position.y, 2) +
                             pow(delta_position.z, 2))
                            )
            if not vector_length:
                # division by zero most likely
                self.report({'WARNING'},
                            "Operation Cancelled. No viable object in the scene")

                return {'CANCELLED'}

            single_vector = (1 / vector_length) * delta_position

            # Calc back position
            singleback_vector = single_vector.copy()
            singleback_vector.x = cos(radians(self.backangle)) * single_vector.x + \
                                  (-sin(radians(self.backangle)) * single_vector.y)

            singleback_vector.y = sin(radians(self.backangle)) * single_vector.x + \
                                 (cos(radians(self.backangle)) * single_vector.y)

            backx = obj_position.x + self.distance * singleback_vector.x
            backy = obj_position.y + self.distance * singleback_vector.y

            backData = bpy.data.lights.new(name="TriLamp-Back", type=self.secondarytype)
            backData.energy = backEnergy

            if self.secondarytype == 'AREA':
                backData.shape = self.secondary_light_shape
                backData.size = self.secondary_light_size

            if self.secondarytype == 'SPOT':
                backData.spot_size = radians(self.spot_size_fill)  # Conversion from degrees to radians
                backData.spot_blend = self.spot_blend_fill

            if self.secondarytype in {'POINT', 'SPOT'}:
                backData.shadow_soft_size = self.shadow_soft_size_fill

            backLamp = bpy.data.objects.new(name="TriLamp-Back", object_data=backData)
            collection.objects.link(backLamp)
            backLamp.location = (backx, backy, self.height)

            trackToBack = backLamp.constraints.new(type="TRACK_TO")
            trackToBack.target = obj
            trackToBack.track_axis = "TRACK_NEGATIVE_Z"
            trackToBack.up_axis = "UP_Y"

            # Calc right position
            singleright_vector = single_vector.copy()
            singleright_vector.x = cos(radians(self.rightangle)) * single_vector.x + \
                                  (-sin(radians(self.rightangle)) * single_vector.y)

            singleright_vector.y = sin(radians(self.rightangle)) * single_vector.x + \
                                  (cos(radians(self.rightangle)) * single_vector.y)

            rightx = obj_position.x + self.distance * singleright_vector.x
            righty = obj_position.y + self.distance * singleright_vector.y

            rightData = bpy.data.lights.new(name="TriLamp-Fill", type=self.secondarytype)
            rightData.energy = fillEnergy
            if self.secondarytype == 'AREA':
                rightData.shape = self.secondary_light_shape
                rightData.size = self.secondary_light_size
            if self.secondarytype == 'SPOT':
                rightData.spot_size = radians(self.spot_size_fill)  # Conversion from degrees to radians
                rightData.spot_blend = self.spot_blend_fill
            if self.secondarytype in {'POINT', 'SPOT'}:
                rightData.shadow_soft_size = self.shadow_soft_size_fill

            rightLamp = bpy.data.objects.new(name="TriLamp-Fill", object_data=rightData)
            collection.objects.link(rightLamp)
            rightLamp.location = (rightx, righty, self.height)
            trackToRight = rightLamp.constraints.new(type="TRACK_TO")
            trackToRight.target = obj
            trackToRight.track_axis = "TRACK_NEGATIVE_Z"
            trackToRight.up_axis = "UP_Y"

            # Calc left position
            singleleft_vector = single_vector.copy()
            singleleft_vector.x = cos(radians(-self.leftangle)) * single_vector.x + \
                                (-sin(radians(-self.leftangle)) * single_vector.y)
            singleleft_vector.y = sin(radians(-self.leftangle)) * single_vector.x + \
                                (cos(radians(-self.leftangle)) * single_vector.y)
            leftx = obj_position.x + self.distance * singleleft_vector.x
            lefty = obj_position.y + self.distance * singleleft_vector.y

            leftData = bpy.data.lights.new(name="TriLamp-Key", type=self.primarytype)
            leftData.energy = keyEnergy
            if self.primarytype == 'AREA':
                leftData.shape = self.key_light_shape
                leftData.size = self.key_light_size
            if self.primarytype == 'SPOT':
                leftData.spot_size = radians(self.spot_size_key)  # Conversion from degrees to radians
                leftData.spot_blend = self.spot_blend_key
            if self.primarytype in {'POINT', 'SPOT'}:
                leftData.shadow_soft_size = self.shadow_soft_size_key

            leftLamp = bpy.data.objects.new(name="TriLamp-Key", object_data=leftData)
            collection.objects.link(leftLamp)
            leftLamp.location = (leftx, lefty, self.height)
            trackToLeft = leftLamp.constraints.new(type="TRACK_TO")
            trackToLeft.target = obj
            trackToLeft.track_axis = "TRACK_NEGATIVE_Z"
            trackToLeft.up_axis = "UP_Y"

        except Exception as e:
            self.report({'WARNING'},
                        "Some operations could not be performed (See Console for more info)")

            print("\n[Add Advanced  Objects]\nOperator: "
                  "object.trilighting\nError: {}".format(e))

            return {'CANCELLED'}

        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_TriLighting.bl_idname, text="3 Point Lights", icon='LIGHT')



# Register all operators and menu
def register():
    bpy.utils.register_class(OBJECT_OT_TriLighting)
    bpy.types.VIEW3D_MT_light_add.append(menu_func)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_TriLighting)
    bpy.types.VIEW3D_MT_light_add.remove(menu_func)

if __name__ == "__main__":
    register()
