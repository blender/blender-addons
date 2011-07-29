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

bl_info = {
    "name": "Autodesk FBX format",
    "author": "Campbell Barton",
    "blender": (2, 5, 7),
    "api": 35622,
    "location": "File > Import-Export",
    "description": "Import-Export FBX meshes, UV's, vertex colors, materials, textures, cameras and lamps",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Import-Export/Autodesk_FBX",
    "tracker_url": "",
    "support": 'OFFICIAL',
    "category": "Import-Export"}

# To support reload properly, try to access a package var, if it's there, reload everything
if "bpy" in locals():
    import imp
    if "export_fbx" in locals():
        imp.reload(export_fbx)


import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty

from bpy_extras.io_utils import (ExportHelper,
                                 path_reference_mode,
                                 axis_conversion,
                                 axis_conversion_ensure,
                                 )


class ExportFBX(bpy.types.Operator, ExportHelper):
    '''Selection to an ASCII Autodesk FBX'''
    bl_idname = "export_scene.fbx"
    bl_label = "Export FBX"
    bl_options = {'PRESET'}

    filename_ext = ".fbx"
    filter_glob = StringProperty(default="*.fbx", options={'HIDDEN'})

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    use_selection = BoolProperty(name="Selected Objects", description="Export selected objects on visible layers", default=False)
# 	EXP_OBS_SCENE = BoolProperty(name="Scene Objects", description="Export all objects in this scene", default=True)
    global_scale = FloatProperty(name="Scale", description="Scale all data, (Note! some imports dont support scaled armatures)", min=0.01, max=1000.0, soft_min=0.01, soft_max=1000.0, default=1.0)

    axis_forward = EnumProperty(
            name="Forward",
            items=(('X', "X Forward", ""),
                   ('Y', "Y Forward", ""),
                   ('Z', "Z Forward", ""),
                   ('-X', "-X Forward", ""),
                   ('-Y', "-Y Forward", ""),
                   ('-Z', "-Z Forward", ""),
                   ),
            default='-Z',
            )

    axis_up = EnumProperty(
            name="Up",
            items=(('X', "X Up", ""),
                   ('Y', "Y Up", ""),
                   ('Z', "Z Up", ""),
                   ('-X', "-X Up", ""),
                   ('-Y', "-Y Up", ""),
                   ('-Z', "-Z Up", ""),
                   ),
            default='Y',
            )

    object_types = EnumProperty(
            name="Object Types",
            options={'ENUM_FLAG'},
            items=(('EMPTY', "Empty", ""),
                   ('CAMERA', "Camera", ""),
                   ('LAMP', "Lamp", ""),
                   ('ARMATURE', "Armature", ""),
                   ('MESH', "Mesh", ""),
                   ),
            default={'EMPTY', 'CAMERA', 'LAMP', 'ARMATURE', 'MESH'},
            )

    mesh_apply_modifiers = BoolProperty(name="Apply Modifiers", description="Apply modifiers to mesh objects", default=True)

    mesh_smooth_type = EnumProperty(
            name="Smoothing",
            items=(('OFF', "Off", "Don't write smoothing"),
                   ('FACE', "Face", "Write face smoothing"),
                   ('EDGE', "Edge", "Write edge smoothing"),
                   ),
            default='FACE',
            )

#    EXP_MESH_HQ_NORMALS = BoolProperty(name="HQ Normals", description="Generate high quality normals", default=True)
    # armature animation
    ANIM_ENABLE = BoolProperty(name="Enable Animation", description="Export keyframe animation", default=True)
    ANIM_OPTIMIZE = BoolProperty(name="Optimize Keyframes", description="Remove double keyframes", default=True)
    ANIM_OPTIMIZE_PRECISSION = FloatProperty(name="Precision", description="Tolerence for comparing double keyframes (higher for greater accuracy)", min=1, max=16, soft_min=1, soft_max=16, default=6.0)
# 	ANIM_ACTION_ALL = BoolProperty(name="Current Action", description="Use actions currently applied to the armatures (use scene start/end frame)", default=True)
    ANIM_ACTION_ALL = BoolProperty(name="All Actions", description="Use all actions for armatures, if false, use current action", default=False)

    batch_mode = EnumProperty(
            name="Batch Mode",
            items=(('OFF', "Off", "Active scene to file"),
                   ('SCENE', "Scene", "Each scene as a file"),
                   ('GROUP', "Group", "Each group as a file"),
                   ),
            )

    BATCH_OWN_DIR = BoolProperty(name="Own Dir", description="Create a dir for each exported file", default=True)
    use_metadata = BoolProperty(name="Use Metadata", default=True, options={'HIDDEN'})

    path_mode = path_reference_mode

    @property
    def check_extension(self):
        return self.batch_mode == 'OFF'

    def check(self, context):
        return axis_conversion_ensure(self, "axis_forward", "axis_up")

    def execute(self, context):
        from mathutils import Matrix
        if not self.filepath:
            raise Exception("filepath not set")

        global_matrix = Matrix()
        global_matrix[0][0] = global_matrix[1][1] = global_matrix[2][2] = self.global_scale
        global_matrix = global_matrix * axis_conversion(to_forward=self.axis_forward, to_up=self.axis_up).to_4x4()

        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "global_scale", "check_existing", "filter_glob"))
        keywords["global_matrix"] = global_matrix

        from . import export_fbx
        return export_fbx.save(self, context, **keywords)


def menu_func(self, context):
    self.layout.operator(ExportFBX.bl_idname, text="Autodesk FBX (.fbx)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()
