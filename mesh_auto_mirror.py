######################################################################################################
# An simple add-on to auto cut in two and mirror an object                                           #
# Actualy partialy uncommented (see further version)                                                 #
# Author: Lapineige                                                                                  #
# License: GPL v3                                                                                    #
######################################################################################################


############# Add-on description (used by Blender)

bl_info = {
    "name": "Auto Mirror",
    "description": "Super fast cutting and mirroring for mesh",
    "author": "Lapineige",
    "version": (2, 4, 1),
    "blender": (2, 7, 1),
    "location": "View 3D > Toolbar > Tools tab > AutoMirror (panel)",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Modeling/AutoMirror",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Mesh"}


import bpy
from mathutils import Vector

bpy.types.Scene.AutoMirror_axis = bpy.props.EnumProperty(
            items = [
            ("x", "X", "", 1),
            ("y", "Y", "", 2),
            ("z", "Z", "", 3)],
            description="Axis used by the mirror modifier"
            )
bpy.types.Scene.AutoMirror_orientation = bpy.props.EnumProperty(
            items = [
            ("positive","Positive", "", 1),
            ("negative", "Negative", "", 2)],
            description="Choose the side along the axis of the editable part (+/- coordinates)"
            )
bpy.types.Scene.AutoMirror_threshold = bpy.props.FloatProperty(
            default= 0.001,
            min= 0.001,
            description="Vertices closer than this distance are merged on the loopcut"
            )
bpy.types.Scene.AutoMirror_toggle_edit = bpy.props.BoolProperty(
            default= True,
            description="If not in edit mode, change mode to edit"
            )
bpy.types.Scene.AutoMirror_cut = bpy.props.BoolProperty(
            default= True,
            description="If enabeled, cut the mesh in two parts and mirror it. If not, just make a loopcut"
            )
bpy.types.Scene.AutoMirror_clipping = bpy.props.BoolProperty(
            default=True
            )
bpy.types.Scene.AutoMirror_use_clip = bpy.props.BoolProperty(
            default=True,
            description="Use clipping for the mirror modifier"
            )
bpy.types.Scene.AutoMirror_show_on_cage = bpy.props.BoolProperty(
            default=True,
            description="Enable to edit the cage (it's the classical modifier's option)"
            )
bpy.types.Scene.AutoMirror_apply_mirror = bpy.props.BoolProperty(
            description="Apply the mirror modifier (useful to symmetrise the mesh)"
            )

############### Operator

class AlignVertices(bpy.types.Operator):
    """  """
    bl_idname = "object.align_vertices"
    bl_label = "Align Vertices on 1 Axis"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.object.mode_set(mode = 'OBJECT')

        x1,y1,z1 = bpy.context.scene.cursor_location
        bpy.ops.view3d.snap_cursor_to_selected()

        x2,y2,z2 = bpy.context.scene.cursor_location

        bpy.context.scene.cursor_location[0],bpy.context.scene.cursor_location[1],bpy.context.scene.cursor_location[2]  = 0,0,0

        #Vertices coordinate to 0 (local coordinate, so on the origin)
        for vert in bpy.context.object.data.vertices:
            if vert.select:
                if bpy.context.scene.AutoMirror_axis == 'x':
                    axis = 0
                elif bpy.context.scene.AutoMirror_axis == 'y':
                    axis = 1
                elif bpy.context.scene.AutoMirror_axis == 'z':
                    axis = 2
                vert.co[axis] = 0
        #
        bpy.context.scene.cursor_location = x2,y2,z2

        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

        bpy.context.scene.cursor_location = x1,y1,z1

        bpy.ops.object.mode_set(mode = 'EDIT')
        return {'FINISHED'}

class AutoMirror(bpy.types.Operator):
    """ Automatically cut an object along an axis """
    bl_idname = "object.automirror"
    bl_label = "AutoMirror"
    bl_options = {'REGISTER'} # 'UNDO' ?

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        if bpy.context.object and bpy.context.object.type == 'MESH':
            layout.prop(context.scene, "AutoMirror_axis", text="Mirror axis")
            layout.prop(context.scene, "AutoMirror_orientation", text="Orientation")
            layout.prop(context.scene, "AutoMirror_threshold", text="Threshold")
            layout.prop(context.scene, "AutoMirror_toggle_edit", text="Toggle edit")
            layout.prop(context.scene, "AutoMirror_cut", text="Cut and mirror")
            if bpy.context.scene.AutoMirror_cut:
                layout.prop(context.scene, "AutoMirror_clipping", text="Clipping")
                layout.prop(context.scene, "AutoMirror_apply_mirror", text="Apply mirror")
        else:
            layout.label(icon="ERROR", text="No mesh selected")

    def get_local_axis_vector(self, context, X, Y, Z, orientation):
        loc = context.object.location
        bpy.ops.object.mode_set(mode="OBJECT") # Needed to avoid to translate vertices

        v1 = Vector((loc[0],loc[1],loc[2]))
        bpy.ops.transform.translate(
            value=(X*orientation, Y*orientation, Z*orientation),
            constraint_axis=((X==1), (Y==1), (Z==1)),
            constraint_orientation='LOCAL')
        v2 = Vector((loc[0],loc[1],loc[2]))
        bpy.ops.transform.translate(
            value=(-X*orientation, -Y*orientation, -Z*orientation),
            constraint_axis=((X==1), (Y==1), (Z==1)),
            constraint_orientation='LOCAL')

        bpy.ops.object.mode_set(mode="EDIT")
        return v2-v1

    def execute(self, context):
        X,Y,Z = 0,0,0
        if bpy.context.scene.AutoMirror_axis == 'x':
            X = 1
        elif bpy.context.scene.AutoMirror_axis == 'y':
            Y = 1
        elif bpy.context.scene.AutoMirror_axis == 'z':
            Z = 1

        current_mode = bpy.context.object.mode # Save the current mode

        if bpy.context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT") # Go to edit mode
        bpy.ops.mesh.select_all(action='SELECT') # Select all the vertices
        if bpy.context.scene.AutoMirror_orientation == 'positive':
            orientation = 1
        else:
            orientation = -1
        cut_normal = self.get_local_axis_vector(context, X, Y, Z, orientation)

        bpy.ops.mesh.bisect(plane_co=(bpy.context.object.location[0],
                                      bpy.context.object.location[1],
                                      bpy.context.object.location[2]),
                                      plane_no=cut_normal,
                                      use_fill= False,
                                      clear_inner= bpy.context.scene.AutoMirror_cut,
                                      clear_outer= 0,
                                      threshold= bpy.context.scene.AutoMirror_threshold) # Cut the mesh

        bpy.ops.object.align_vertices() # Use to align the vertices on the origin, needed by the "threshold"

        if not bpy.context.scene.AutoMirror_toggle_edit:
            bpy.ops.object.mode_set(mode=current_mode) # Reload previous mode

        if bpy.context.scene.AutoMirror_cut:
            bpy.ops.object.modifier_add(type='MIRROR') # Add a mirror modifier
            bpy.context.object.modifiers[-1].use_x = X # Choose the axis to use, based on the cut's axis
            bpy.context.object.modifiers[-1].use_y = Y
            bpy.context.object.modifiers[-1].use_z = Z
            bpy.context.object.modifiers[-1].use_clip = context.scene.AutoMirror_use_clip
            bpy.context.object.modifiers[-1].show_on_cage = context.scene.AutoMirror_show_on_cage
            if bpy.context.scene.AutoMirror_apply_mirror:
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.modifier_apply(apply_as= 'DATA', modifier= bpy.context.object.modifiers[-1].name)
                if bpy.context.scene.AutoMirror_toggle_edit:
                    bpy.ops.object.mode_set(mode='EDIT')
                else:
                    bpy.ops.object.mode_set(mode=current_mode)

        return {'FINISHED'}

#################### Panel

class BisectMirror(bpy.types.Panel):
    """ The AutoMirror panel on the toolbar tab 'Tools' """
    bl_label = "Auto Mirror"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Tools"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        if bpy.context.object and bpy.context.object.type == 'MESH':
            layout.operator("object.automirror")
            layout.prop(context.scene, "AutoMirror_axis", text="Mirror Axis", expand=True)
            layout.prop(context.scene, "AutoMirror_orientation", text="Orientation")
            layout.prop(context.scene, "AutoMirror_threshold", text="Threshold")
            layout.prop(context.scene, "AutoMirror_toggle_edit", text="Toggle Edit")
            layout.prop(context.scene, "AutoMirror_cut", text="Cut and Mirror")
            if bpy.context.scene.AutoMirror_cut:
                row = layout.row()
                row.prop(context.scene, "AutoMirror_use_clip", text="Use Clip")
                row.prop(context.scene, "AutoMirror_show_on_cage", text="Editable")
                layout.prop(context.scene, "AutoMirror_apply_mirror", text="Apply Mirror")

        else:
            layout.label(icon="ERROR", text="No mesh selected")


def register():
    bpy.utils.register_class(BisectMirror)
    bpy.utils.register_class(AutoMirror)
    bpy.utils.register_class(AlignVertices)


def unregister():
    bpy.utils.unregister_class(BisectMirror)
    bpy.utils.unregister_class(AutoMirror)
    bpy.utils.unregister_class(AlignVertices)


if __name__ == "__main__":
    register()
