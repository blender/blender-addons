
import bpy
from bpy.props import (FloatProperty,
                       FloatVectorProperty,
                       IntProperty,
                       BoolProperty,
                       StringProperty)

from .bpybraid import awesome_braid, defaultCircle
'''
bl_info = {
    "name": "New Braid",
    "author": "Jared Forsyth <github.com/jaredly>",
    "version": (1, 0),
    "blender": (2, 6, 0),
    "location": "View3D > Add > Mesh > New Braid",
    "description": "Adds a new Braid",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"}
'''
from bpy.types import Operator


class Braid(Operator):
    '''Add a Braid'''
    bl_idname = 'mesh.add_braid'
    bl_label = 'New Braid'
    bl_description = 'Create a new braid'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    strands = IntProperty(name='strands', min=2, max=100, default=3)
    sides = IntProperty(name='sides', min=2, max=100, default=5)
    radius = FloatProperty(name='radius', default=1)
    thickness = FloatProperty(name='thickness', default=.3)
    strandsize = FloatProperty(name='strandsize', default=.3, min=.01, max=10)
    width = FloatProperty(name='width', default=.2)
    resolution = IntProperty(name='resolution', min=1, default=2, max=100)
    pointy = BoolProperty(name='pointy', default=False)

    def execute(self, context):
        circle = defaultCircle(self.strandsize)
        context.scene.objects.link(circle)
        braid = awesome_braid(self.strands, self.sides,
                              bevel=circle.name,
                              pointy=self.pointy,
                              radius=self.radius,
                              mr=self.thickness,
                              mz=self.width,
                              resolution=self.resolution)
        base = context.scene.objects.link(braid)

        for ob in context.scene.objects:
            ob.select = False
        base.select = True
        context.scene.objects.active = braid
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.prop(self, 'strands')
        box.prop(self, 'sides')
        box.prop(self, 'radius')
        box.prop(self, 'thickness')
        box.prop(self, 'strandsize')
        box.prop(self, 'width')
        box.prop(self, 'resolution')
        box.prop(self, 'pointy')


def add_object_button(self, context):
    self.layout.operator(Braid.bl_idname, text="Add Braid", icon='PLUGIN')


def register():
    bpy.utils.register_class(Braid)
    bpy.types.INFO_MT_mesh_add.append(add_object_button)


def unregister():
    bpy.utils.unregister_class(Braid)
    bpy.types.INFO_MT_mesh_add.remove(add_object_button)

if __name__ == "__main__":
    register()
