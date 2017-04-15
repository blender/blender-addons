#######################################################
# very simple 'pixelization' or 'voxelization' engine #
#######################################################

bl_info = {
    "name": "3D Pix",
    "author": "liero",
    "version": (0, 5, 1),
    "blender": (2, 74, 0),
    "location": "View3D > Tool Shelf",
    "description": "Creates a 3d pixelated version of the object.",
    "category": "Object"}

import bpy
import mathutils
from mathutils import Vector

bpy.types.WindowManager.size = bpy.props.FloatProperty(name='Size', min=.05, max=5, default=.25, description='Size of the cube / grid')
bpy.types.WindowManager.gap = bpy.props.IntProperty(name='Gap', min=0, max=90, default=10, subtype='PERCENTAGE', description='Separation - percent of size')
bpy.types.WindowManager.smooth = bpy.props.FloatProperty(name='Smooth', min=0, max=1, default=.0, description='Smooth factor when subdividing mesh')


def pix(obj):
    sce = bpy.context.scene
    wm = bpy.context.window_manager
    obj.hide = obj.hide_render = True
    mes = obj.to_mesh(sce, True, 'RENDER')
    mes.transform(obj.matrix_world)
    dup = bpy.data.objects.new('dup', mes)
    sce.objects.link(dup)
    dup.dupli_type = 'VERTS'
    sce.objects.active = dup
    bpy.ops.object.mode_set()
    ver = mes.vertices

    for i in range(250):
        fin = True
        for i in dup.data.edges:
            d = ver[i.vertices[0]].co - ver[i.vertices[1]].co
            if d.length > wm.size:
                ver[i.vertices[0]].select = True
                ver[i.vertices[1]].select = True
                fin = False
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.subdivide(number_cuts=1, smoothness=wm.smooth)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle()
        if fin:
            break

    for i in ver:
        for n in range(3):
            i.co[n] -= (.001 + i.co[n]) % wm.size

    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.delete(type='EDGE_FACE')
    bpy.ops.object.mode_set()
    sca = wm.size * (100 - wm.gap) * .005
    bpy.ops.mesh.primitive_cube_add(layers=[True] + [False] * 19)
    bpy.ops.transform.resize(value=[sca] * 3)
    bpy.context.scene.objects.active = dup
    bpy.ops.object.parent_set(type='OBJECT')


class Pixelate(bpy.types.Operator):
    bl_idname = 'object.pixelate'
    bl_label = 'Pixelate Object'
    bl_description = 'Create a 3d pixelated version of the object.'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and context.active_object.type == 'MESH' and context.mode == 'OBJECT')

    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)
        column.prop(context.window_manager, "size")
        column.prop(context.window_manager, "gap")
        layout.prop(context.window_manager, "smooth")

    def execute(self, context):
        objeto = bpy.context.object
        pix(objeto)
        return {'FINISHED'}

classes = (
    Pixelate,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == '__main__':
    register()
