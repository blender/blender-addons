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

bl_addon_info = {
    "name": "Rigify",
    "author": "Nathan Vegdahl",
    "version": (0, 5),
    "blender": (2, 5, 5),
    "api": 33110,
    "location": "Armature properties",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Rigging"}

if "bpy" in locals():
    reload(generate)
    reload(ui)
    reload(utils)
    reload(metarig_menu)
else:
    from rigify import generate, ui, utils, metarig_menu

import bpy
import bpy_types
import os


def get_rig_list(path):
    """ Recursively searches for rig types, and returns a list.
    """
    rigs = []
    MODULE_DIR = os.path.dirname(__file__)
    RIG_DIR_ABS = os.path.join(MODULE_DIR, utils.RIG_DIR)
    SEARCH_DIR_ABS = os.path.join(RIG_DIR_ABS, path)
    path_strip = path.strip(os.sep)
    files = os.listdir(SEARCH_DIR_ABS)
    files.sort()

    for f in files:
        if not f.startswith("_") and not f.startswith("."):
            f_abs = os.path.join(SEARCH_DIR_ABS, f)
            if os.path.isdir(f_abs):
                # Check directories
                try:
                    rig = utils.get_rig_type(os.path.join(path_strip, f).replace(os.sep, "."))
                except ImportError as e:
                    print("Rigify: " + str(e))
                else:
                    # Check if it's a rig itself
                    if not hasattr(rig, "Rig"):
                        # Check for sub-rigs
                        ls = get_rig_list(os.path.join(path, f, "")) # "" adds a final slash
                        rigs.extend(["%s.%s" % (f, l) for l in ls])
                    else:
                        rigs += [f]

            elif f.endswith(".py"):
                # Check straight-up python files
                t = f[:-3]
                try:
                    utils.get_rig_type((path + t).replace("/", ".")).Rig
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


class RigifyName(bpy.types.IDPropertyGroup):
    name = bpy.props.StringProperty()


class RigifyParameters(bpy.types.IDPropertyGroup):
    name = bpy.props.StringProperty()


for rig in rig_list:
    r = utils.get_rig_type(rig).Rig
    try:
        r.add_parameters(RigifyParameters)
    except AttributeError:
        pass


##### REGISTER #####

def register():
    bpy.types.PoseBone.rigify_type = bpy.props.StringProperty(name="Rigify Type", description="Rig type for this bone.")
    bpy.types.PoseBone.rigify_parameters = bpy.props.CollectionProperty(type=RigifyParameters)

    bpy.types.Scene.rigify_collection = bpy.props.EnumProperty(items=col_enum_list, default="All", name="Rigify Active Collection", description="The selected rig collection")
    bpy.types.Scene.rigify_types = bpy.props.CollectionProperty(type=RigifyName)
    bpy.types.Scene.rigify_active_type = bpy.props.IntProperty(name="Rigify Active Type", description="The selected rig type.")

    metarig_menu.register()


def unregister():
    del bpy.types.PoseBone.rigify_type
    del bpy.types.PoseBone.rigify_parameters

    del bpy.types.Scene.rigify_collection
    del bpy.types.Scene.rigify_types
    del bpy.types.Scene.rigify_active_type

    metarig_menu.unregister()

