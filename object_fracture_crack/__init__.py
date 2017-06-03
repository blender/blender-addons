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


if 'bpy' in locals():
    import imp
    imp.reload(operator)

else:
    from . import operator

import bpy
import os

bl_info = {
    "name": "Cell Fracture Crack It",
    "author": "Nobuyuki Hirakata",
    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "View3D > Toolshelf > Creat Tab",
    "description": "Displaced Cell Fracture Addon",
    "warning": "Make sure to enable 'Object: Cell Fracture' Addon",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Object/CrackIt",
    "category": "Object"
}

def register():
    bpy.utils.register_module(__name__)
    
    # Input on toolshelf before execution --------------------------
    #  In Panel subclass, In bpy.types.Operator subclass, reference them by context.scene.~.
    
    bpy.types.Scene.crackit_fracture_childverts = bpy.props.BoolProperty(
        name = 'From Child Verts',
        description = "Use child object's vertices and position for origin of crack.",
        default = False
    )
    bpy.types.Scene.crackit_fracture_scalex = bpy.props.FloatProperty(
        name = 'Scale X',
        description = "Scale X",
        default = 1.00,
        min = 0.00,
        max = 1.00
    )
    bpy.types.Scene.crackit_fracture_scaley = bpy.props.FloatProperty(
        name = 'Scale Y',
        description = "Scale Y",
        default = 1.00,
        min = 0.00,
        max = 1.00
    )
    bpy.types.Scene.crackit_fracture_scalez = bpy.props.FloatProperty(
        name = 'Scale Z',
        description = "Scale Z",
        default = 1.00,
        min = 0.00,
        max = 1.00
    )
    bpy.types.Scene.crackit_fracture_div = bpy.props.IntProperty(
        name = 'Max Crack',
        description = "Max Crack",
        default = 100,
        min = 0,
        max = 10000
    )
    bpy.types.Scene.crackit_fracture_margin = bpy.props.FloatProperty(
        name = 'Margin Size',
        description = "Margin Size",
        default = 0.001,
        min = 0.000,
        max = 1.000
    )
    bpy.types.Scene.crackit_extrude_offset = bpy.props.FloatProperty(
        name = 'Extrude',
        description = "Extrude Offset",
        default = 0.10,
        min = 0.00,
        max = 2.00
    )
    bpy.types.Scene.crackit_extrude_random = bpy.props.FloatProperty(
        name = 'Random',
        description = "Extrude Random",
        default = 0.30,
        min = -1.00,
        max = 1.00
    )
    # Path of the addon.
    bpy.types.Scene.crackit_material_addonpath = os.path.dirname(__file__)
    # Selection of material preset.
    bpy.types.Scene.crackit_material_preset = bpy.props.EnumProperty(
        name = 'Preset',
        description = "Material Preset",
        items = [('crackit_organic_mud', 'Organic Mud', "Mud material"),
                ('crackit_mud1', 'Mud', "Mud material"),
                ('crackit_tree1_moss1', 'Tree1_moss', "Tree Material"),
                ('crackit_tree2_dry1', 'Tree2_dry', "Tree Material"),
                ('crackit_tree3_red1', 'Tree3_red', "Tree Material"),
                ('crackit_rock1', 'Rock', "Rock Material")]
    )

def unregister():
    # Delete bpy.types.Scene.~.
    del bpy.types.Scene.crackit_fracture_scalex
    del bpy.types.Scene.crackit_fracture_scaley
    del bpy.types.Scene.crackit_fracture_scalez
    del bpy.types.Scene.crackit_fracture_div
    del bpy.types.Scene.crackit_fracture_margin
    del bpy.types.Scene.crackit_extrude_offset
    
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
