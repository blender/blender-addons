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

import bpy
import Mathutils
from math import *
from bpy.props import *

bl_addon_info = {
    'name': 'Add Mesh: 3D Function Surface',
    'author': 'Buerbaum Martin (Pontiac)',
    'version': '0.2.3',
    'blender': '2.5.3',
    'location': 'View3D > Add > Mesh > 3D Function Surface',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/" \
        "Scripts/Add_3d_Function_Surface',
    'category': 'Add Mesh'}

# More Links:
# http://gitorious.org/blender-scripts/blender-3d-function-surface
# http://blenderartists.org/forum/showthread.php?t=179043

__bpydoc__ = """
3D Function Surface

This script lets the user create a surface where the z coordinate
is a function of the x and y coordinates.

    z = f(x,y)

Usage:
You have to activated the script in the "Add-Ons" tab (user preferences).
The functionality can then be accessed via the
"Add Mesh" -> "3D Function Surface" menu.

Version history:
v0.2.3 - Use bl_addon_info for Add-On information.
v0.2.2 - Fixed Add-On registration text.
v0.2.1 - Fixed some new API stuff.
    Mainly we now have the register/unregister functions.
    Also the new() function for objects now accepts a mesh object.
    Changed the script so it can be managed from the "Add-Ons" tab
    in the user preferences.
    Added dummy "PLUGIN" icon.
    Corrected FSF address.
    Clean up of tooltips.
v0.2 - Added security check for eval() function
    Check return value of eval() for complex numbers.
v0.1.1 - Use 'CANCELLED' return value when failing.
    Updated web links.
v0.1 - Initial revision.
"""


# List of safe functions for eval()
safe_list = ['math', 'acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh',
    'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp', 'hypot',
    'ldexp', 'log', 'log10', 'modf', 'pi', 'pow', 'radians',
    'sin', 'sinh', 'sqrt', 'tan', 'tanh']

# Use the list to filter the local namespace
safe_dict = dict([(k, locals().get(k, None)) for k in safe_list])

# Add any needed builtins back in.
safe_dict['abs'] = abs


def createFaces(vertIdx1, vertIdx2, ring):
    '''
    A very simple "bridge" tool.
    Connects two equally long vertex-loops with faces and
    returns a list of the new faces.

    Parameters
        vertIdx1 ... List of vertex indices of the first loop.
        vertIdx2 ... List of vertex indices of the second loop.
    '''
    faces = []

    if (len(vertIdx1) != len(vertIdx2)) or (len(vertIdx1) < 2):
        return None

    total = len(vertIdx1)

    if (ring):
        # Bridge the start with the end.
        faces.append([vertIdx2[0], vertIdx1[0],
            vertIdx1[total - 1], vertIdx2[total - 1]])

    # Bridge the rest of the faces.
    for num in range(total - 1):
        faces.append([vertIdx1[num], vertIdx2[num],
            vertIdx2[num + 1], vertIdx1[num + 1]])

    return faces


def createObject(scene, verts, faces, name):
    '''Creates Meshes & Objects for the given lists of vertices and faces.'''

    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Add the geometry to the mesh.
    #mesh.add_geometry(len(verts), 0, len(faces))
    #mesh.verts.foreach_set("co", unpack_list(verts))
    #mesh.faces.foreach_set("verts_raw", unpack_face_list(faces))

    # To quote the documentation:
    # "Make a mesh from a list of verts/edges/faces Until we have a nicer
    #  way to make geometry, use this."
    # http://www.blender.org/documentation/250PythonDoc/
    # bpy.types.Mesh.html#bpy.types.Mesh.from_pydata
    mesh.from_pydata(verts, [], faces)

    # ugh - Deselect all objects.
    for ob in scene.objects:
        ob.selected = False

    # Update mesh geometry after adding stuff.
    mesh.update()

    # Create a new object.
    ob_new = bpy.data.objects.new(name, mesh)

    # Link new object to the given scene and select it.
    scene.objects.link(ob_new)
    ob_new.selected = True

    # Place the object at the 3D cursor location.
    ob_new.location = scene.cursor_location

    obj_act = scene.objects.active

    if obj_act and obj_act.mode == 'EDIT':
        # We are in EditMode, switch to ObjectMode.
        bpy.ops.object.mode_set(mode='OBJECT')

        # Select the active object as well.
        obj_act.selected = True

        # Apply location of new object.
        scene.update()

        # Join new object into the active.
        bpy.ops.object.join()

        # Switching back to EditMode.
        bpy.ops.object.mode_set(mode='EDIT')

    else:
        # We are in ObjectMode.
        # Make the new object the active one.
        scene.objects.active = ob_new


class Add3DFunctionSurface(bpy.types.Operator):
    '''Add a surface defined defined by a function z=f(x,y)'''
    bl_idname = "mesh.primitive_3d_function_surface"
    bl_label = "Add 3D Function Surface"
    bl_options = {'REGISTER', 'UNDO'}

    equation = StringProperty(name="Equation",
        description="Equation for z=f(x,y)",
        default="1 - ( x**2 + y**2 )")

    div_x = IntProperty(name="X Subdivisions",
        description="Number of vertices in x direction.",
        default=16,
        min=3,
        max=256)
    div_y = IntProperty(name="Y Subdivisions",
        description="Number of vertices in y direction.",
        default=16,
        min=3,
        max=256)

    size_x = FloatProperty(name="X Size",
        description="Size of the x axis.",
        default=2.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")
    size_y = FloatProperty(name="Y Size",
        description="Size of the y axis.",
        default=2.0,
        min=0.01,
        max=100.0,
        unit="LENGTH")

    def execute(self, context):
        equation = self.properties.equation
        div_x = self.properties.div_x
        div_y = self.properties.div_y
        size_x = self.properties.size_x
        size_y = self.properties.size_y

        verts = []
        faces = []

        delta_x = size_x / float(div_x - 1)
        delta_y = size_y / float(div_y - 1)
        start_x = -(size_x / 2.0)
        start_y = -(size_y / 2.0)

        edgeloop_prev = []

        for row_x in range(div_x):
            edgeloop_cur = []

            for row_y in range(div_y):
                x = start_x + row_x * delta_x
                y = start_y + row_y * delta_y
                z = 0

                # Try to evaluate the equation.
                try:
                    safe_dict['x'] = x
                    safe_dict['y'] = y
                    z = eval(equation, {"__builtins__": None}, safe_dict)

                except:
                    print("Add3DFunctionSurface: " \
                        "Could not evaluate equation '" + equation + "'\n")
                    return {'CANCELLED'}

                # Accept only real numbers (no complex types)
                # @todo: Support for "long" needed?
                if not (isinstance(z, int)
                    #or isinstance(z, long)
                    or isinstance(z, float)):
                    print("Add3DFunctionSurface: " \
                        "eval() returned unsupported number type '" \
                        + str(z) + "'\n")
                    return {'CANCELLED'}

                edgeloop_cur.append(len(verts))
                verts.append([x, y, z])

            if len(edgeloop_prev) > 0:
                faces_row = createFaces(edgeloop_prev, edgeloop_cur, False)
                faces.extend(faces_row)

            edgeloop_prev = edgeloop_cur

        createObject(context.scene, verts, faces, "3D Function")

        return {'FINISHED'}


################################
import space_info

# Define "3D Function Surface" menu
menu_func = (lambda self, context: self.layout.operator(
    Add3DFunctionSurface.bl_idname,
    text="3D Function Surface",
    icon="PLUGIN"))


def register():
    # Register the operators/menus.
    bpy.types.register(Add3DFunctionSurface)

    # Add "3D Function Surface" menu to the "Add Mesh" menu
    space_info.INFO_MT_mesh_add.append(menu_func)


def unregister():
    # Unregister the operators/menus.
    bpy.types.unregister(Add3DFunctionSurface)

    # Remove "3D Function Surface" menu from the "Add Mesh" menu.
    space_info.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
