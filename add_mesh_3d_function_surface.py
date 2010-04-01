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
from Mathutils import *
from math import *
from bpy.props import *

bl_addon_info = {
    'name': 'Add Mesh: 3D Function Surfaces',
    'author': 'Buerbaum Martin (Pontiac)',
    'version': '0.3.1',
    'blender': (2, 5, 3),
    'location': 'View3D > Add > Mesh > Z Function Surface &' \
        ' XYZ Function Surface',
    'Description': 'Create Objects using Math Formulas',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/Add_Mesh/Add_3d_Function_Surface',
    'category': 'Add Mesh'}

# More Links:
# http://gitorious.org/blender-scripts/blender-3d-function-surface
# http://blenderartists.org/forum/showthread.php?t=179043

__bpydoc__ = """
Z Function Surface

This script lets the user create a surface where the z coordinate
is a function of the x and y coordinates.

    z = f(x,y)

X,Y,Z Function Surface

This script lets the user create a surface where the x, y and z
coordinates are defiend by a function.

    x = f(u,v)
    y = f(u,v)
    z = f(u,v)

Usage:
You have to activated the script in the "Add-Ons" tab (user preferences).
The functionality can then be accessed via the
"Add Mesh" -> "Z Function Surface"
and
"Add Mesh" -> "X,Y,Z Function Surface"
menu.

Version history:
v0.3.1 - Use hidden "edit" property for "recall" operator.
    Bugfix: Z Function was mixing up div_x and div_y
v0.3 - X,Y,Z Function Surface (by Ed Mackey & tuga3d).
    Renamed old function to "Z Function Surface".
    Align the geometry to the view if the user preference says so.
    Store recall properties in newly created object.
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
safe_dict = dict([(k, globals().get(k, None)) for k in safe_list])


# Stores the values of a list of properties in a
# property group (named like the operator) in the object.
# Always replaces any existing property group with the same name!
# @todo: Should we do this in EDIT Mode? Sounds dangerous.
def obj_store_recall_properties(ob, op, prop_list):
    if ob and op and prop_list:
        #print("Storing recall data for operator: " + op.bl_idname)  # DEBUG

        # Store new recall properties.
        prop_list['recall_op'] = op.bl_idname
        ob['recall'] = prop_list


# Apply view rotation to objects if "Align To" for new objects
# was set to "VIEW" in the User Preference.
def apply_view_rotation(context, ob):
    align = bpy.context.user_preferences.edit.object_align

    if (context.space_data.type == 'VIEW_3D'
        and align == 'VIEW'):
            view3d = context.space_data
            region = view3d.region_3d
            viewMatrix = region.view_matrix
            rot = viewMatrix.rotation_part()
            ob.rotation_euler = rot.invert().to_euler()


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


def createObject(context, verts, faces, name, edit):
    '''Creates Meshes & Objects for the given lists of vertices and faces.'''

    scene = context.scene

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

    # Deselect all objects.
    bpy.ops.object.select_all(action='DESELECT')

    # Update mesh geometry after adding stuff.
    mesh.update()

    if edit:
        # Recreate geometry of existing object
        obj_act = context.active_object
        ob_new = obj_act

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')

        ob_new.data = mesh

        ob_new.selected = True

    else:
        # Create new object
        ob_new = bpy.data.objects.new(name, mesh)

        # Link new object to the given scene and select it.
        scene.objects.link(ob_new)
        ob_new.selected = True

        # Place the object at the 3D cursor location.
        ob_new.location = scene.cursor_location

        obj_act = scene.objects.active

        apply_view_rotation(context, ob_new)

    if obj_act and obj_act.mode == 'EDIT':
        if not edit:
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

    return ob_new


class AddZFunctionSurface(bpy.types.Operator):
    '''Add a surface defined defined by a function z=f(x,y)'''
    bl_idname = "mesh.primitive_z_function_surface"
    bl_label = "Add Z Function Surface"
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name="",
        description="",
        default=False,
        options={'HIDDEN'})

    equation = StringProperty(name="Z Equation",
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
        edit = self.properties.edit
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
                    print("AddZFunctionSurface: " \
                        "Could not evaluate equation '" + equation + "'\n")
                    return {'CANCELLED'}

                # Accept only real numbers (no complex types)
                # @todo: Support for "long" needed?
                if not (isinstance(z, int)
                    #or isinstance(z, long)
                    or isinstance(z, float)):
                    print("AddZFunctionSurface: " \
                        "eval() returned unsupported number type '" \
                        + str(z) + "'\n")
                    return {'CANCELLED'}

                edgeloop_cur.append(len(verts))
                verts.append((x, y, z))

            if len(edgeloop_prev) > 0:
                faces_row = createFaces(edgeloop_prev, edgeloop_cur, False)
                faces.extend(faces_row)

            edgeloop_prev = edgeloop_cur

        obj = createObject(context, verts, faces, "Z Function", edit)

        # Store 'recall' properties in the object.
        recall_prop_list = {
            "edit": True,
            "equation": equation,
            "div_x": div_x,
            "div_y": div_y,
            "size_x": size_x,
            "size_y": size_y}
        obj_store_recall_properties(obj, self, recall_prop_list)

        return {'FINISHED'}


def xyz_function_surface_faces(x_eq, y_eq, z_eq,
    range_u_min, range_u_max, range_u_step, wrap_u,
    range_v_min, range_v_max, range_v_step, wrap_v):

    verts = []
    faces = []

    uStep = (range_u_max - range_u_min) / range_u_step
    vStep = (range_v_max - range_v_min) / range_v_step

    uRange = range_u_step
    if range_u_step == 0:
        uRange = uRange + 1

    vRange = range_v_step
    if range_v_step == 0:
        vRange = vRange + 1

    for vN in range(vRange):
        v = range_v_min + (vN * vStep)

        for uN in range(uRange):
            u = range_u_min + (uN * uStep)

            safe_dict['u'] = u
            safe_dict['v'] = v

            # Try to evaluate the equation.
            try:
                x = eval(x_eq, {"__builtins__": None}, safe_dict)

            except:
                print("AddXYZFunctionSurface: " \
                    "Could not evaluate x equation '" + x_eq + "'\n")
                return {'CANCELLED'}

            try:
                y = eval(y_eq, {"__builtins__": None}, safe_dict)

            except:
                print("AddXYZFunctionSurface: " \
                    "Could not evaluate y equation '" + y_eq + "'\n")
                return {'CANCELLED'}

            try:
                z = eval(z_eq, {"__builtins__": None}, safe_dict)

            except:
                print("AddXYZFunctionSurface: " \
                    "Could not evaluate z equation '" + z_eq + "'\n")
                return {'CANCELLED'}

            # Accept only real numbers (no complex types)
            # @todo: Support for "long" needed?
            if not (isinstance(x, int)
                or isinstance(x, float)):
                print("AddXYZFunctionSurface: " \
                    "eval() returned unsupported number type '" \
                    + str(x) + " for x function.'\n")
                return {'CANCELLED'}
            if not (isinstance(y, int)
                or isinstance(y, float)):
                print("AddXYZFunctionSurface: " \
                    "eval() returned unsupported number type '" \
                    + str(y) + " for y function.'\n")
                return {'CANCELLED'}
            if not (isinstance(z, int)
                or isinstance(z, float)):
                print("AddXYZFunctionSurface: " \
                    "eval() returned unsupported number type '" \
                    + str(z) + " for z function.'\n")
                return {'CANCELLED'}

            verts.append((x, y, z))

    for vN in range(1, range_v_step + 1):
        vThis = vN

        if (vThis >= vRange):
            if wrap_v:
                vThis = 0
            else:
                continue

        for uN in range(1, range_u_step + 1):
            uThis = uN

            if (uThis >= uRange):
                if wrap_u:
                    uThis = 0
                else:
                    continue

            faces.append([(vThis * uRange) + uThis,
                (vThis * uRange) + uN - 1,
                ((vN - 1) * uRange) + uN - 1,
                ((vN - 1) * uRange) + uThis])

    return verts, faces


# Original Script "Parametric.py" by Ed Mackey.
# -> http://www.blinken.com/blender-plugins.php
# Partly converted for Blender 2.5 by tuga3d.
#
# Sphere:
# x = sin(2*pi*u)*sin(pi*v)
# y = cos(2*pi*u)*sin(pi*v)
# z = cos(pi*v)
# u_min = v_min = 0
# u_max = v_max = 1
#
# "Snail shell"
# x = 1.2**v*(sin(u)**2 *sin(v))
# y = 1.2**v*(sin(u)*cos(u))
# z = 1.2**v*(sin(u)**2 *cos(v))
# u_min = 0
# u_max = pi
# v_min = -pi/4,
# v max = 5*pi/2
class AddXYZFunctionSurface(bpy.types.Operator):
    '''Add a surface defined defined by 3 functions:''' \
    + ''' x=f(u,v), y=f(u,v) and z=f(u,v)'''
    bl_idname = "mesh.primitive_xyz_function_surface"
    bl_label = "Add X,Y,Z Function Surface"
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name="",
        description="",
        default=False,
        options={'HIDDEN'})

    x_eq = StringProperty(name="X Equation",
        description="Equation for x=f(u,v)",
        default="1.2**v*(sin(u)**2 *sin(v))")

    y_eq = StringProperty(name="Y Equation",
        description="Equation for y=f(u,v)",
        default="1.2**v*(sin(u)*cos(u))")

    z_eq = StringProperty(name="Z Equation",
        description="Equation for z=f(u,v)",
        default="1.2**v*(sin(u)**2 *cos(v))")

    range_u_min = FloatProperty(name="U min",
        description="Minimum U value. Lower boundary of U range.",
        min=-100.00,
        max=0.00,
        default=0.00)

    range_u_max = FloatProperty(name="U max",
        description="Maximum U value. Upper boundary of U range.",
        min=0.00,
        max=100.00,
        default=pi)

    range_u_step = IntProperty(name="U step",
        description="U Subdivisions",
        min=1,
        max=1024,
        default=32)

    wrap_u = BoolProperty(name="U wrap",
        description="U Wrap around",
        default=True)

    range_v_min = FloatProperty(name="V min",
        description="Minimum V value. Lower boundary of V range.",
        min=-100.00,
        max=0.00,
        default=-pi / 4)

    range_v_max = FloatProperty(name="V max",
        description="Maximum V value. Upper boundary of V range.",
        min=0.00,
        max=100.00,
        default=5 * pi / 2)

    range_v_step = IntProperty(name="V step",
        description="V Subdivisions",
        min=1,
        max=1024,
        default=32)

    wrap_v = BoolProperty(name="V wrap",
        description="V Wrap around",
        default=False)

    def execute(self, context):
        props = self.properties

        verts, faces = xyz_function_surface_faces(
                            props.x_eq,
                            props.y_eq,
                            props.z_eq,
                            props.range_u_min,
                            props.range_u_max,
                            props.range_u_step,
                            props.wrap_u,
                            props.range_v_min,
                            props.range_v_max,
                            props.range_v_step,
                            props.wrap_v)

        obj = createObject(context, verts, faces, "XYZ Function", props.edit)

        # Store 'recall' properties in the object.
        recall_prop_list = {
            "edit": True,
            "x_eq": props.x_eq,
            "y_eq": props.y_eq,
            "z_eq": props.z_eq,
            "range_u_min": props.range_u_min,
            "range_u_max": props.range_u_max,
            "range_u_step": props.range_u_step,
            "wrap_u": props.wrap_u,
            "range_v_min": props.range_v_min,
            "range_v_max": props.range_v_max,
            "range_v_step": props.range_v_step,
            "wrap_v": props.wrap_v}
        obj_store_recall_properties(obj, self, recall_prop_list)

        return {'FINISHED'}


################################
import space_info

# Define "3D Function Surface" menu
menu_func_z = (lambda self, context: self.layout.operator(
    AddZFunctionSurface.bl_idname,
    text="Z Function Surface",
    icon="PLUGIN"))
menu_func_xyz = (lambda self, context: self.layout.operator(
    AddXYZFunctionSurface.bl_idname,
    text="X,Y,Z Function Surface",
    icon="PLUGIN"))


def register():
    # Register the operators/menus.
    bpy.types.register(AddZFunctionSurface)
    bpy.types.register(AddXYZFunctionSurface)

    # Add menus to the "Add Mesh" menu
    space_info.INFO_MT_mesh_add.append(menu_func_z)
    space_info.INFO_MT_mesh_add.append(menu_func_xyz)


def unregister():
    # Unregister the operators/menus.
    bpy.types.unregister(AddZFunctionSurface)
    bpy.types.unregister(AddXYZFunctionSurface)

    # Remove menus from the "Add Mesh" menu.
    space_info.INFO_MT_mesh_add.remove(menu_func_z)
    space_info.INFO_MT_mesh_add.remove(menu_func_xyz)

if __name__ == "__main__":
    register()
