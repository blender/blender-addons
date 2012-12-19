#====================== BEGIN GPL LICENSE BLOCK ======================
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
#======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

bl_info = {
    "name": "Rigify",
    "author": "Nathan Vegdahl",
    "blender": (2, 57, 0),
    "location": "View3D > Add > Armature",
    "description": "Adds various Rig Templates",
    "location": "Armature properties",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
                "Scripts/Rigging/Rigify",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"
                   "func=detail&aid=25546",
    "category": "Rigging"}


if "bpy" in locals():
    import imp
    imp.reload(generate)
    imp.reload(ui)
    imp.reload(utils)
    imp.reload(metarig_menu)
else:
    from . import generate, ui, utils, metarig_menu

import bpy
import os


def get_rig_list(path):
    """ Recursively searches for rig types, and returns a list.
    """
    rigs = []
    MODULE_DIR = os.path.dirname(__file__)
    RIG_DIR_ABS = os.path.join(MODULE_DIR, utils.RIG_DIR)
    SEARCH_DIR_ABS = os.path.join(RIG_DIR_ABS, path)
    files = os.listdir(SEARCH_DIR_ABS)
    files.sort()

    for f in files:
        is_dir = os.path.isdir(os.path.join(SEARCH_DIR_ABS, f))  # Whether the file is a directory
        if f[0] in {".", "_"}:
            pass
        elif f.count(".") >= 2 or (is_dir and "." in f):
            print("Warning: %r, filename contains a '.', skipping" % os.path.join(SEARCH_DIR_ABS, f))
        else:
            if is_dir:
                # Check directories
                module_name = os.path.join(path, f).replace(os.sep, ".")
                try:
                    rig = utils.get_rig_type(module_name)
                except ImportError as e:
                    print("Rigify: " + str(e))
                else:
                    # Check if it's a rig itself
                    if not hasattr(rig, "Rig"):
                        # Check for sub-rigs
                        ls = get_rig_list(os.path.join(path, f, ""))  # "" adds a final slash
                        rigs.extend(["%s.%s" % (f, l) for l in ls])
                    else:
                        rigs += [f]

            elif f.endswith(".py"):
                # Check straight-up python files
                t = f[:-3]
                module_name = os.path.join(path, t).replace(os.sep, ".")
                try:
                    utils.get_rig_type(module_name).Rig
                except (ImportError, AttributeError):
                    pass
                else:
                    rigs += [t]
    rigs.sort()
    return rigs


rig_list = get_rig_list("")


collection_list = []
for r in rig_list:
    a = r.split(".")
    if len(a) >= 2 and a[0] not in collection_list:
        collection_list += [a[0]]


col_enum_list = [("All", "All", ""), ("None", "None", "")]
for c in collection_list:
    col_enum_list += [(c, c, "")]


class RigifyName(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()


class RigifyParameters(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()


class RigifyArmatureLayer(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="Layer Name", default=" ")
    row = bpy.props.IntProperty(name="Layer Row", default=1, min=1, max=32)


##### REGISTER #####

def register():
    ui.register()
    metarig_menu.register()

    bpy.utils.register_class(RigifyName)
    bpy.utils.register_class(RigifyParameters)
    bpy.utils.register_class(RigifyArmatureLayer)

    bpy.types.PoseBone.rigify_type = bpy.props.StringProperty(name="Rigify Type", description="Rig type for this bone")
    bpy.types.PoseBone.rigify_parameters = bpy.props.CollectionProperty(type=RigifyParameters)

    bpy.types.Armature.rigify_layers = bpy.props.CollectionProperty(type=RigifyArmatureLayer)

    IDStore = bpy.types.WindowManager
    IDStore.rigify_collection = bpy.props.EnumProperty(items=col_enum_list, default="All", name="Rigify Active Collection", description="The selected rig collection")
    IDStore.rigify_types = bpy.props.CollectionProperty(type=RigifyName)
    IDStore.rigify_active_type = bpy.props.IntProperty(name="Rigify Active Type", description="The selected rig type")

    # Add rig parameters
    for rig in rig_list:
        r = utils.get_rig_type(rig).Rig
        try:
            r.add_parameters(RigifyParameters)
        except AttributeError:
            pass


def unregister():
    del bpy.types.PoseBone.rigify_type
    del bpy.types.PoseBone.rigify_parameters

    IDStore = bpy.types.WindowManager
    del IDStore.rigify_collection
    del IDStore.rigify_types
    del IDStore.rigify_active_type

    bpy.utils.unregister_class(RigifyName)
    bpy.utils.unregister_class(RigifyParameters)
    bpy.utils.unregister_class(RigifyArmatureLayer)

    metarig_menu.unregister()
    ui.unregister()
