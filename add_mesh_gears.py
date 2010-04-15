# add_mesh_gear.py (c) 2009, 2010 Michel J. Anders (varkenvarken)
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****


bl_addon_info = {
    'name': 'Add Mesh: Gears',
    'author': 'Michel J. Anders (varkenvarken)',
    'version': '2.2',
    'blender': (2, 5, 3),
    'location': 'View3D > Add > Mesh ',
    'description': 'Adds a mesh Gear to the Add Mesh menu',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/Add_Mesh/Add_Gear',
    'category': 'Add Mesh'}

"""
What was needed to port it from 2.49 -> 2.50 alpha 0?

The basic functions that calculate the geometry (verts and faces) are mostly
unchanged (add_tooth, add_spoke2, add_gear)

Also, the vertex group API is changed a little bit but the concepts
are the same:
=========
vertexgroup = ob.add_vertex_group('NAME_OF_VERTEXGROUP')
for i in vertexgroup_vertex_indices:
    ob.add_vertex_to_group(i, vertexgroup, weight, 'ADD')
=========

Now for some reason the name does not 'stick' and we have to set it this way:
vertexgroup.name = 'NAME_OF_VERTEXGROUP'

Conversion to 2.50 also meant we could simply do away with our crude user
interface.
Just definining the appropriate properties in the AddGear() operator will
display the properties in the Blender GUI with the added benefit of making
it interactive: changing a property will redo the AddGear() operator providing
the user with instant feedback.

Finally we had to convert/throw away some print statements to print functions
as Blender nows uses Python 3.x

The most puzzling issue was that the built in Python zip()
function changed its behavior.
In 3.x it returns a zip object (that can be iterated over)
instead of a list of tuples.
This meant we could no longer use deepcopy(zip(...)) but had to convert the
zip object to a list of tuples first.

The code to actually implement the AddGear() function is mostly copied from
add_mesh_torus() (distributed with Blender).

Unresolved issues:

- Removing doubles:
    The algorithm should not generate a full section to begin with.
    At least the last 4 vertices don't need to be created, because the
    next section will have them as their first 4 vertices anyway.
    OLD COMMENT ON DOUBLES:
    "The code that produces the teeth of the gears produces some duplicate
    vertices. The original script just called remove_doubles() but if we
    do that in 2.50 we have a problem.
    To apply the bpy.ops.mesh.remove_doubles() operator we have to change
    to edit mode. The moment we do that we loose to possibilty to
    interactively change the properties.
    Also changing back to object mode raises a strange exception (to
    investigate). So for now, removing doubles is left to the user
    once satisfied with the chosen setting for a gear."

- No suitable icon:
    A rather minor point but I reused the torus icon for the add->mesh->gear
    menu entry as there doesn't seem to be a generic mesh icon or a way to
    add custom icons. Too bad, but as this is just eye candy it's no big deal.
"""

import bpy
import mathutils
from math import *
from copy import deepcopy
from bpy.props import *

# Constants
FACES = [
    [0, 5, 6, 1],
    [1, 6, 7, 2],
    [2, 7, 8, 3],
    [3, 8, 9, 4],
    [6, 10, 11, 7],
    [7, 11, 12, 8],
    [10, 13, 14, 11],
    [11, 14, 15, 12]]

VERT_NUM = 16   # Number of vertices

# Edgefaces
EDGEFACES = [5, 6, 10, 13, 14, 15, 12, 8, 9]
EDGEFACES2 = [i + VERT_NUM for i in EDGEFACES]  # i.e. Indices are offset by 16

# In python 3, zip() returns a zip object so we have to force the
# result into a list of lists to keep deepcopy happy later on in the script.
EFC = [[i, j, k, l] for i, j, k, l
    in zip(EDGEFACES[:-1], EDGEFACES2[:-1], EDGEFACES2[1:], EDGEFACES[1:])]
VERTS_TOOTH = [13, 14, 15, 29, 30, 31]        # Vertices on a tooth
VERTS_VALLEY = [5, 6, 8, 9, 21, 22, 24, 25]   # Vertices in a valley

#SPOKEFACES = (
#    (0, 1, 2, 5),
#    (2, 3, 4, 7),
#    (5, 2, 7, 6),
#    (5, 6, 9, 8),
#    (6, 7, 10, 9),
#    (11, 8, 13, 12),
#    (8, 9, 10, 13),
#    (13, 10, 15, 14))


# Stores the values of a list of properties and the
# operator id in a property group ('recall_op') inside the object.
# Could (in theory) be used for non-objects.
# Note: Replaces any existing property group with the same name!
# ob ... Object to store the properties in.
# op ... The operator that should be used.
# op_args ... A dictionary with valid Blender
#             properties (operator arguments/parameters).
def store_recall_properties(ob, op, op_args):
    if ob and op and op_args:
        recall_properties = {}

        # Add the operator identifier and op parameters to the properties.
        recall_properties['op'] = op.bl_idname
        recall_properties['args'] = op_args

        # Store new recall properties.
        ob['recall'] = recall_properties


# Apply view rotation to objects if "Align To" for
# new objects was set to "VIEW" in the User Preference.
def apply_object_align(context, ob):
    obj_align = bpy.context.user_preferences.edit.object_align

    if (context.space_data.type == 'VIEW_3D'
        and obj_align == 'VIEW'):
            view3d = context.space_data
            region = view3d.region_3d
            viewMatrix = region.view_matrix
            rot = viewMatrix.rotation_part()
            ob.rotation_euler = rot.invert().to_euler()


# Create a new mesh (object) from verts/edges/faces.
# verts/edges/faces ... List of vertices/edges/faces for the
#                       new mesh (as used in from_pydata).
# name ... Name of the new mesh (& object).
# edit ... Replace existing mesh data.
# Note: Using "edit" will destroy/delete existing mesh data.
def create_mesh_object(context, verts, edges, faces, name, edit):
    scene = context.scene
    obj_act = scene.objects.active

    # Can't edit anything, unless we have an active obj.
    if edit and not obj_act:
        return None

    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff.
    mesh.update()

    # Deselect all objects.
    bpy.ops.object.select_all(action='DESELECT')

    if edit:
        # Replace geometry of existing object

        # Use the active obj and select it.
        ob_new = obj_act
        ob_new.selected = True

        if obj_act.mode == 'OBJECT':
            # Get existing mesh datablock.
            old_mesh = ob_new.data

            # Set object data to nothing
            ob_new.data = None

            # Clear users of existing mesh datablock.
            old_mesh.user_clear()

            # Remove old mesh datablock if no users are left.
            if (old_mesh.users == 0):
                bpy.data.meshes.remove(old_mesh)

            # Assign new mesh datablock.
            ob_new.data = mesh

    else:
        # Create new object
        ob_new = bpy.data.objects.new(name, mesh)

        # Link new object to the given scene and select it.
        scene.objects.link(ob_new)
        ob_new.selected = True

        # Place the object at the 3D cursor location.
        ob_new.location = scene.cursor_location

        apply_object_align(context, ob_new)

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

            ob_new = obj_act

    else:
        # We are in ObjectMode.
        # Make the new object the active one.
        scene.objects.active = ob_new

    return ob_new


# a
# t
# d
# radius
# Ad
# De
# base
# p_angle
# rack
# crown
def add_tooth(a, t, d, radius, Ad, De, base, p_angle, rack=0, crown=0.0):
    """
    private function: calculate the vertex coords for a single side
    section of a gear tooth.
    Returns them as a list of tuples.
    """

    A = [a, a + t / 4, a + t / 2, a + 3 * t / 4, a + t]
    C = [cos(i) for i in A]
    S = [sin(i) for i in A]

    Ra = radius + Ad
    Rd = radius - De
    Rb = Rd - base

    # Pressure angle calc
    O = Ad * tan(p_angle)
    p_angle = atan(O / Ra)

    if radius < 0:
        p_angle = -p_angle

    if rack:
        S = [sin(t / 4) * I for I in range(-2, 3)]
        Sp = [0, sin(-t / 4 + p_angle), 0, sin(t / 4 - p_angle)]

        verts = [(Rb, radius * S[I], d) for I in range(5)]
        verts.extend([(Rd, radius * S[I], d) for I in range(5)])
        verts.extend([(radius, radius * S[I], d) for I in range(1, 4)])
        verts.extend([(Ra, radius * Sp[I], d) for I in range(1, 4)])

    else:
        Cp = [
            0,
            cos(a + t / 4 + p_angle),
            cos(a + t / 2),
            cos(a + 3 * t / 4 - p_angle)]
        Sp = [0,
            sin(a + t / 4 + p_angle),
            sin(a + t / 2),
            sin(a + 3 * t / 4 - p_angle)]

        verts = [(Rb * C[I], Rb * S[I], d)
            for I in range(5)]
        verts.extend([(Rd * C[I], Rd * S[I], d) for I in range(5)])
        verts.extend([(radius * C[I], radius * S[I], d + crown / 3)
            for I in range(1, 4)])
        verts.extend([(Ra * Cp[I], Ra * Sp[I], d + crown)
            for I in range(1, 4)])

    return verts


# a
# t
# d
# radius
# De
# base
# s
# w
# l
# gap
# width
def add_spoke2(a, t, d, radius, De, base, s, w, l, gap=0, width=19):
    """
    EXPERIMENTAL private function: calculate the vertex coords for
    a single side section of a gearspoke.
    Returns them as a list of lists.
    """

    Rd = radius - De
    Rb = Rd - base
    Rl = Rb

    verts = []
    edgefaces = []
    edgefaces2 = []
    sf = []

    if not gap:
        for N in range(width, 1, -2):
            edgefaces.append(len(v))
            ts = t / 4
            tm = a + 2 * ts
            te = asin(w / Rb)
            td = te - ts
            t4 = ts + td * (width - N) / (width - 3.0)
            A = [tm + (i - int(N / 2)) * t4 for i in range(N)]
            C = [cos(i) for i in A]
            S = [sin(i) for i in A]

            verts.extend([(Rb * I, Rb * J, d) for (I, J) in zip(C, S)])
            edgefaces2.append(len(v) - 1)

            Rb = Rb - s

        n = 0
        for N in range(width, 3, -2):
            sf.extend([(i + n, i + 1 + n, i + 2 + n, i + N + n)
                for i in range(0, N - 1, 2)])
            sf.extend([(i + 2 + n, i + N + n, i + N + 1 + n, i + N + 2 + n)
                for i in range(0, N - 3, 2)])

            n = n + N

    return v, edgefaces, edgefaces2, sf


# Create gear geometry.
# Returns:
# * A list of vertices
# * A list of faces
# * A list (group) of vertices of the tip
# * A list (group) of vertices of the valley
#
# teethNum ... Number of teeth on the gear. Set to 4 for "worm"
# radius ... Radius of the gear, negative for crown gear
# Ad ... Addendum, extent of tooth above radius.
# De ... Dedendum, extent of tooth below radius.
# base ... Base, extent of gear below radius.
# p_angle ... Pressure angle. Skewness of tooth tip. (radiant)
# width ... Width, thickness of gear.
# skew ... Skew of teeth. (radiant)
# conangle ... Conical angle of gear. (radiant)
# rack
# crown ... Inward pointing extend of crown teeth.
# spoke
# spbevel
# spwidth
# splength
# spresol
def add_gear(teethNum, radius, Ad, De, base, p_angle,
    width=1, skew=0, conangle=0, rack=0, crown=0.0, spoke=0,
    spbevel=0.1, spwidth=0.2, splength=1.0, spresol=9):
    worm = 0

    if teethNum < 5:
        worm = teethNum
        teethNum = 24

    t = 2 * pi / teethNum

    if rack:
        teethNum = 1

    scale = (radius - 2 * width * tan(conangle)) / radius

    verts = []
    faces = []
    vgroup_top = []  # Vertex group of top/tip? vertices.
    vgroup_val = []  # Vertex group of valley vertices

    M = [0]
    if worm:
        M = range(32)
        skew = radians(11.25)
        width = width / 2.0

    for W in M:
        fl = W * teethNum * VERT_NUM * 2
        vertNum = 0   # Number of vertices

        for toothCnt in range(teethNum):
            a = toothCnt * t

            for (s, d, c, first) \
                in [(W * skew, W * 2 * width - width, 1, 1), \
                ((W + 1) * skew, W * 2 * width + width, scale, 0)]:
                if worm and toothCnt % (teethNum / worm) != 0:
                    verts_tooth = add_tooth(a + s, t, d,
                        radius - De, 0.0, 0.0, base, p_angle)
                    verts.extend(verts_tooth)

                else:
                    verts_tooth = add_tooth(a + s, t, d,
                        radius * c, Ad * c, De * c, base * c, p_angle,
                        rack, crown)
                    verts.extend(verts_tooth)

                if (not worm
                    or (W == 0 and first)
                    or (W == (len(M) - 1) and not first)):
                    faces.extend([[j + vertNum + fl for j in i]
                        for i in deepcopy(FACES)])

                vertNum += len(verts_tooth)

            faces.extend([[j + toothCnt * VERT_NUM * 2 + fl for j in i]
                for i in deepcopy(EFC)])

            vgroup_top.extend([i + toothCnt * VERT_NUM * 2
                for i in VERTS_TOOTH])
            vgroup_val.extend([i + toothCnt * VERT_NUM * 2
                for i in VERTS_VALLEY])

    # EXPERIMENTAL: add spokes
    if not worm and spoke > 0:
        fl = len(v)
        for toothCnt in range(teethNum):
            a = toothCnt * t
            s = 0       # For test

            if toothCnt % spoke == 0:
                for d in (-width, width):
                    sv, edgefaces, edgefaces2, sf = add_spoke2(a + s, t, d,
                        radius * c, De * c, base * c,
                        spbevel, spwidth, splength, 0, spresol)
                    verts.extend(sv)
                    faces.extend([[j + fl for j in i] for i in sf])
                    fl += len(sv)

                d1 = fl - len(sv)
                d2 = fl - 2 * len(sv)

                faces.extend([(i + d2, j + d2, j + d1, i + d1)
                    for (i, j) in zip(edgefaces[:-1], edgefaces[1:])])
                faces.extend([(i + d2, j + d2, j + d1, i + d1)
                    for (i, j) in zip(edgefaces2[:-1], edgefaces2[1:])])

            else:
                for d in (-width, width):
                    sv, edgefaces, edgefaces2, sf = add_spoke2(a + s, t, d,
                        radius * c, De * c, base * c,
                        spbevel, spwidth, splength, 1, spresol)

                    verts.extend(sv)
                    fl += len(sv)

                d1 = fl - len(sv)
                d2 = fl - 2 * len(sv)

                #faces.extend([(i+d2, i+1+d2, i+1+d1, i+d1)
                #    for (i) in (0, 1, 2, 3)])
                #faces.extend([(i+d2, i+1+d2, i+1+d1, i+d1)
                #    for (i) in (5, 6, 7, 8)])

    return verts, faces, vgroup_top, vgroup_val


class AddGear(bpy.types.Operator):
    '''Add a gear mesh.'''
    bl_idname = "mesh.gear_add"
    bl_label = "Add Gear"
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name="",
        description="",
        default=False,
        options={'HIDDEN'})
    number_of_teeth = IntProperty(name="Number of Teeth",
        description="Number of teeth on the gear",
        min=4,
        max=200,
        default=12)
    radius = FloatProperty(name="Radius",
        description="Radius of the gear, negative for crown gear",
        min=-100.0,
        max=100.0,
        default=1.0)
    addendum = FloatProperty(name="Addendum",
        description="Addendum, extent of tooth above radius",
        min=0.01,
        max=100.0,
        default=0.1)
    dedendum = FloatProperty(name="Dedendum",
        description="Dedendum, extent of tooth below radius",
        min=0.0,
        max=100.0,
        default=0.1)
    angle = FloatProperty(name="Pressure Angle",
        description="Pressure angle, skewness of tooth tip (degrees)",
        min=0.0,
        max=45.0,
        default=20.0)
    base = FloatProperty(name="Base",
        description="Base, extent of gear below radius",
        min=0.0,
        max=100.0,
        default=0.2)
    width = FloatProperty(name="Width",
        description="Width, thickness of gear",
        min=0.05,
        max=100.0,
        default=0.2)
    skew = FloatProperty(name="Skewness",
        description="Skew of teeth (degrees)",
        min=-90.0,
        max=90.0,
        default=0.0)
    conangle = FloatProperty(name="Conical angle",
        description="Conical angle of gear (degrees)",
        min=0.0,
        max=90.0,
        default=0.0)
    crown = FloatProperty(name="Crown",
        description="Inward pointing extend of crown teeth",
        min=0.0,
        max=100.0,
        default=0.0)

    def execute(self, context):
        props = self.properties

        verts, faces, verts_tip, verts_valley = add_gear(
            props.number_of_teeth,
            props.radius,
            props.addendum,
            props.dedendum,
            props.base,
            radians(props.angle),
            props.width,
            skew=radians(props.skew),
            conangle=radians(props.conangle),
            crown=props.crown)

        # Actually create the mesh object from this geometry data.
        obj = create_mesh_object(context, verts, [], faces, "Gear", props.edit)

        # Store 'recall' properties in the object.
        recall_args_list = {
            "edit": True,
            "number_of_teeth": props.number_of_teeth,
            "radius": props.radius,
            "addendum": props.addendum,
            "dedendum": props.dedendum,
            "angle": props.angle,
            "base": props.base,
            "width": props.width,
            "skew": props.skew,
            "conangle": props.conangle,
            "crown": props.crown}
        store_recall_properties(obj, self, recall_args_list)

        # Create vertex groups from stored vertices.
        tipGroup = obj.add_vertex_group('Tips')
        for vert in verts_tip:
            obj.add_vertex_to_group(vert, tipGroup, 1.0, 'ADD')

        valleyGroup = obj.add_vertex_group('Valleys')
        for vert in verts_valley:
            obj.add_vertex_to_group(vert, valleyGroup, 1.0, 'ADD')

        return {'FINISHED'}


menu_func = (lambda self, context: self.layout.operator(AddGear.bl_idname,
                                        text="Gear", icon='PLUGIN'))


def register():
    bpy.types.register(AddGear)

    # Add "Gears" entry to the "Add Mesh" menu.
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.unregister(AddGear)

    # Remove "Gears" entry from the "Add Mesh" menu.
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
