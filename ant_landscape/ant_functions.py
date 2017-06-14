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

# Another Noise Tool - Functions
# Jim Hazevoet

# import modules
import bpy
from bpy.props import (
        BoolProperty,
        FloatProperty,
        StringProperty,
        EnumProperty,
        IntProperty,
        PointerProperty
        )
from mathutils.noise import (
        seed_set,
        turbulence,
        turbulence_vector,
        fractal,
        hybrid_multi_fractal,
        multi_fractal,
        ridged_multi_fractal,
        hetero_terrain,
        random_unit_vector,
        variable_lacunarity,
        )
from math import (
        floor, sqrt,
        sin, cos, pi,
        )

# ------------------------------------------------------------
# Create a new mesh (object) from verts/edges/faces.
# verts/edges/faces ... List of vertices/edges/faces for the
#                    new mesh (as used in from_pydata).
# name ... Name of the new mesh (& object)

from bpy_extras import object_utils

def create_mesh_object(context, verts, edges, faces, name):
    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, [], faces)

    # Update mesh geometry after adding stuff.
    mesh.update()

    #new_ob = bpy.data.objects.new(name, mesh)
    #context.scene.objects.link(new_ob)
    return object_utils.object_data_add(context, mesh, operator=None)
    #return new_ob


# Generate XY Grid
def grid_gen(sub_d_x, sub_d_y, tri, meshsize_x, meshsize_y, props, water_plane, water_level):
    verts = []
    faces = []
    for i in range (0, sub_d_x):
        x = meshsize_x * (i / (sub_d_x - 1) - 1 / 2)
        for j in range(0, sub_d_y):
            y = meshsize_y * (j / (sub_d_y - 1) - 1 / 2)
            if water_plane:
                z = water_level
            else:
                z = noise_gen((x, y, 0), props)

            verts.append((x,y,z))

    count = 0
    for i in range (0, sub_d_y * (sub_d_x - 1)):
        if count < sub_d_y - 1 :
            A = i + 1
            B = i
            C = (i + sub_d_y)
            D = (i + sub_d_y) + 1
            if tri:
                faces.append((A, B, D))
                faces.append((B, C, D))
            else:
                faces.append((A, B, C, D))
            count = count + 1
        else:
            count = 0

    return verts, faces


# Generate UV Sphere
def sphere_gen(sub_d_x, sub_d_y, tri, meshsize, props, water_plane, water_level):
    verts = []
    faces = []
    sub_d_x += 1
    sub_d_y += 1
    for i in range(0, sub_d_x):
        for j in range(0, sub_d_y):
            u = sin(j * pi * 2 / (sub_d_y - 1)) * cos(-pi / 2 + i * pi / (sub_d_x - 1)) * meshsize / 2
            v = cos(j * pi * 2 / (sub_d_y - 1)) * cos(-pi / 2 + i * pi / (sub_d_x - 1)) * meshsize / 2
            w = sin(-pi / 2 + i * pi / (sub_d_x - 1)) * meshsize / 2
            if water_plane:
                h = water_level
            else:
                h = noise_gen((u, v, w), props) / meshsize
            verts.append(((u + u * h), (v + v * h), (w + w * h)))

    count = 0
    for i in range (0, sub_d_y * (sub_d_x - 1)):
        if count < sub_d_y - 1 :
            A = i + 1
            B = i
            C = (i + sub_d_y)
            D = (i + sub_d_y) + 1
            if tri:
                faces.append((A, B, D))
                faces.append((B, C, D))
            else:
                faces.append((A, B, C, D))
            count = count + 1
        else:
            count = 0

    return verts, faces


# Z normal value to vertex group (Slope map)
class AntVgSlopeMap(bpy.types.Operator):
    bl_idname = "mesh.ant_slope_map"
    bl_label = "Weight from Slope"
    bl_description = "A.N.T. Slope Map - z normal value to vertex group weight"
    bl_options = {'REGISTER', 'UNDO'}

    z_method = EnumProperty(
            name="Method:",
            default='SLOPE_Z',
            items=[
                ('SLOPE_Z', "Slope Z", "Slope for planar mesh"),
                ('SLOPE_XYZ', "Slope XYZ", "Slope for spherical mesh")
                ])
    group_name = StringProperty(
            name="Vertex Group Name:",
            default="Slope",
            description="Name"
            )
    select_flat = BoolProperty(
            name="Vert Select:",
            default=True,
            description="Select vertices on flat surface"
            )
    select_range = FloatProperty(
            name="Vert Select Range:",
            default=0.0,
            min=0.0,
            max=1.0,
            description="Increase to select more vertices"
            )

    @classmethod
    def poll(cls, context):
        ob = context.object
        return (ob and ob.type == 'MESH')


    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


    def execute(self, context):
        message = "Popup Values: %d, %f, %s, %s" % \
            (self.select_flat, self.select_range, self.group_name, self.z_method)
        self.report({'INFO'}, message)

        ob = bpy.context.active_object
        dim = ob.dimensions

        if self.select_flat:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.context.tool_settings.mesh_select_mode = [True, False, False]
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.vertex_group_add()
        vg_normal = ob.vertex_groups.active

        for v in ob.data.vertices:
            if self.z_method == 'SLOPE_XYZ':
                zval = (v.co.normalized() * v.normal.normalized()) * 2 - 1
            else:
                zval = v.normal[2]

            vg_normal.add([v.index], zval, 'REPLACE')

            if self.select_flat:
                if zval >= (1.0 - self.select_range):
                    v.select = True

        vg_normal.name = self.group_name

        return {'FINISHED'}


# ------------------------------------------------------------
# A.N.T. Noise:

# Functions for marble_noise:
def sin_bias(a):
    return 0.5 + 0.5 * sin(a)


def cos_bias(a):
    return 0.5 + 0.5 * cos(a)


def tri_bias(a):
    b = 2 * pi
    a = 1 - 2 * abs(floor((a * (1 / b)) + 0.5) - (a * (1 / b)))
    return a


def saw_bias(a):
    b = 2 * pi
    n = int(a / b)
    a -= n * b
    if a < 0:
        a += b
    return a / b


def soft(a):
    return a


def sharp(a):
    return a**0.5


def sharper(a):
    return sharp(sharp(a))


def shapes(x, y, z, shape=0):
    p = pi
    if shape is 1:
        # ring
        x = x * p
        y = y * p
        s = cos(x**2 + y**2) / (x**2 + y**2 + 0.5)
    elif shape is 2:
        # swirl
        x = x * p
        y = y * p
        s = ((x * sin(x * x + y * y) + y * cos(x * x + y * y)) / (x**2 + y**2 + 0.5))
    elif shape is 3:
        # bumps
        x = x * p
        y = y * p
        z = z * p
        s = 1 - ((cos(x * p) + cos(y * p) + cos(z * p)) - 0.5)
    elif shape is 4:
        # wave
        x = x * p * 2
        y = y * p * 2
        s = sin(x + sin(y))
    elif shape is 5:
        # x grad.
        s = (z * p)
    elif shape is 6:
        # y grad.
        s = (y * p)
    elif shape is 7:
        # x grad.
        s = (x * p)
    else:
        # marble default
        s = ((x + y + z) * 5)
    return s


# marble_noise
def marble_noise(x, y, z, origin, size, shape, bias, sharpnes, turb, depth, hard, basis, amp, freq):

    s = shapes(x, y, z, shape)
    x += origin[0]
    y += origin[1]
    z += origin[2]
    value = s + turb * turbulence_vector((x, y, z), depth, hard, basis)[1]

    if bias is 1:
        value = cos_bias(value)
    elif bias is 2:
        value = tri_bias(value)
    elif bias is 3:
        value = saw_bias(value)
    else:
        value = sin_bias(value)

    if sharpnes is 1:
        value = 1.0 - sharp(value)
    elif sharpnes is 2:
        value = 1.0 - sharper(value)
    elif sharpnes is 3:
        value = soft(value)
    elif sharpnes is 4:
        value = sharp(value)
    elif sharpnes is 5:
        value = sharper(value)
    else:
        value = 1.0 - soft(value)

    return value


# vl_noise_turbulence: 
def vlnTurbMode(coords, distort, basis, vlbasis, hardnoise):
    # hard noise
    if hardnoise:
        return (abs(-variable_lacunarity(coords, distort, basis, vlbasis)))
    # soft noise
    else:
        return variable_lacunarity(coords, distort, basis, vlbasis)


def vl_noise_turbulence(coords, distort, depth, basis, vlbasis, hardnoise, amp, freq):
    x, y, z = coords
    value = vlnTurbMode(coords, distort, basis, vlbasis, hardnoise)
    i=0
    for i in range(depth):
        i+=1
        value += vlnTurbMode((x * (freq * i), y * (freq * i), z * (freq * i)), distort, basis, vlbasis, hardnoise) * (amp * 0.5 / i)
    return value


## duo_multiFractal:
def double_multiFractal(coords, H, lacunarity, octaves, offset, gain, basis, vlbasis):
    x, y, z = coords
    n1 = multi_fractal((x * 1.5 + 1, y * 1.5 + 1, z * 1.5 + 1), 1.0, 1.0, 1.0, basis) * (offset * 0.5)
    n2 = multi_fractal((x - 1, y - 1, z - 1), H, lacunarity, octaves, vlbasis) * (gain * 0.5)
    return (n1 * n1 + n2 * n2) * 0.5


## distorted_heteroTerrain:
def distorted_heteroTerrain(coords, H, lacunarity, octaves, offset, distort, basis, vlbasis):
    x, y, z = coords
    h1 = (hetero_terrain((x, y, z), 1.0, 2.0, 1.0, 1.0, basis) * 0.5)
    d =  h1 * distort
    h2 = (hetero_terrain((x + d, y + d, z + d), H, lacunarity, octaves, offset, vlbasis) * 0.25)
    return (h1 * h1 + h2 * h2) * 0.5


## SlickRock:
def slick_rock(coords, H, lacunarity, octaves, offset, gain, distort, basis, vlbasis):
    x, y, z = coords
    n = multi_fractal((x,y,z), 1.0, 2.0, 2.0, basis) * distort * 0.25
    r = ridged_multi_fractal((x + n, y + n, z + n), H, lacunarity, octaves, offset + 0.1, gain * 2, vlbasis)
    return (n + (n * r)) * 0.5


## vlhTerrain
def vl_hTerrain(coords, H, lacunarity, octaves, offset, basis, vlbasis, distort):
    x, y, z = coords
    ht = hetero_terrain((x, y, z), H, lacunarity, octaves, offset, basis ) * 0.25
    vl = ht * variable_lacunarity((x, y, z), distort, basis, vlbasis) * 0.5 + 0.5
    return vl * ht


# another turbulence
def ant_turbulence(coords, depth, hardnoise, nbasis, amp, freq, distortion):
    x, y, z = coords
    tv = turbulence_vector((x + 1, y + 2, z + 3), depth, hardnoise, nbasis, amp, freq)
    d = (distortion * tv[0]) * 0.25
    return (d + ((tv[0] - tv[1]) * (tv[2])**2))


# shattered_hterrain:
def shattered_hterrain(coords, H, lacunarity, octaves, offset, distort, basis):
    x, y, z = coords
    d = (turbulence_vector(coords, 6, 0, 0)[0] * 0.5 + 0.5) * distort * 0.5
    t1 = (turbulence_vector((x + d, y + d, z + d), 0, 0, 7)[0] + 0.5)
    t2 = (hetero_terrain((x * 2, y * 2, z * 2), H, lacunarity, octaves, offset, basis) * 0.5)
    return ((t1 * t2) + t2 * 0.5) * 0.5


# strata_hterrain
def strata_hterrain(coords, H, lacunarity, octaves, offset, distort, basis):
    x, y, z = coords
    value = hetero_terrain((x, y, z), H, lacunarity, octaves, offset, basis) * 0.5
    steps = (sin(value * (distort * 5) * pi) * (0.1 / (distort * 5) * pi))
    return (value * (1.0 - 0.5) + steps * 0.5)


# Planet Noise by: Farsthary
# https://farsthary.com/2010/11/24/new-planet-procedural-texture/
def planet_noise(coords, oct=6, hard=0, noisebasis=1, nabla=0.001):
    x, y, z = coords
    d = 0.001
    offset = nabla * 1000
    x = turbulence((x, y, z), oct, hard, noisebasis)
    y = turbulence((x + offset, y, z), oct, hard, noisebasis)
    z = turbulence((x, y + offset, z), oct, hard, noisebasis)
    xdy = x - turbulence((x, y + d, z), oct, hard, noisebasis)
    xdz = x - turbulence((x, y, z + d), oct, hard, noisebasis)
    ydx = y - turbulence((x + d, y, z), oct, hard, noisebasis)
    ydz = y - turbulence((x, y, z + d), oct, hard, noisebasis)
    zdx = z - turbulence((x + d, y, z), oct, hard, noisebasis)
    zdy = z - turbulence((x, y + d, z), oct, hard, noisebasis)
    return (zdy - ydz), (zdx - xdz), (ydx - xdy)


# ------------------------------------------------------------
# landscape_gen
def noise_gen(coords, props):

    terrain_name = props[0]
    cursor = props[1]
    smooth = props[2]
    triface = props[3]
    sphere = props[4]
    land_mat = props[5]
    water_mat = props[6]
    texture_name = props[7]
    subd_x = props[8]
    subd_y = props[9]
    meshsize_x = props[10]
    meshsize_y = props[11]
    meshsize = props[12]
    rseed = props[13]
    x_offset = props[14]
    y_offset = props[15]
    z_offset = props[16]
    size_x = props[17]
    size_y = props[18]
    size_z = props[19]
    nsize = props[20]
    ntype = props[21]
    nbasis = int(props[22])
    vlbasis = int(props[23])
    distortion = props[24]
    hardnoise = int(props[25])
    depth = props[26]
    amp = props[27]
    freq = props[28]
    dimension = props[29]
    lacunarity = props[30]
    offset = props[31]
    gain = props[32]
    marblebias = int(props[33])
    marblesharpnes = int(props[34])
    marbleshape = int(props[35])
    height = props[36]
    height_invert = props[37]
    height_offset = props[38]
    maximum = props[39]
    minimum = props[40]
    falloff = int(props[41])
    edge_level = props[42]
    falloffsize_x = props[43]
    falloffsize_y = props[44]
    stratatype = props[45]
    strata = props[46]
    addwater = props[47]
    waterlevel = props[48]

    x, y, z = coords

    # Origin
    if rseed is 0:
        origin = x_offset, y_offset, z_offset
        origin_x = x_offset
        origin_y = y_offset
        origin_z = z_offset
        o_range = 1.0
    else:
        # Randomise origin
        o_range = 10000.0
        seed_set(rseed)
        origin = random_unit_vector()
        ox = (origin[0] * o_range)
        oy = (origin[1] * o_range)
        oz = (origin[2] * o_range)
        origin_x = (ox - (ox / 2)) + x_offset
        origin_y = (oy - (oy / 2)) + y_offset
        origin_z = (oz - (oz / 2)) + z_offset

    ncoords = (x / (nsize * size_x) + origin_x, y / (nsize * size_y) + origin_y, z / (nsize * size_z) + origin_z)

    # Noise basis type's
    if nbasis == 9:
        nbasis = 14  # Cellnoise
    if vlbasis == 9:
        vlbasis = 14

    # Noise type's
    if ntype in [0, 'multi_fractal']:
        value = multi_fractal(ncoords, dimension, lacunarity, depth, nbasis) * 0.5

    elif ntype in [1, 'ridged_multi_fractal']:
        value = ridged_multi_fractal(ncoords, dimension, lacunarity, depth, offset, gain, nbasis) * 0.5

    elif ntype in [2, 'hybrid_multi_fractal']:
        value = hybrid_multi_fractal(ncoords, dimension, lacunarity, depth, offset, gain, nbasis) * 0.5

    elif ntype in [3, 'hetero_terrain']:
        value = hetero_terrain(ncoords, dimension, lacunarity, depth, offset, nbasis) * 0.25

    elif ntype in [4, 'fractal']:
        value = fractal(ncoords, dimension, lacunarity, depth, nbasis)

    elif ntype in [5, 'turbulence_vector']:
        value = turbulence_vector(ncoords, depth, hardnoise, nbasis, amp, freq)[0]

    elif ntype in [6, 'variable_lacunarity']:
        value = variable_lacunarity(ncoords, distortion, nbasis, vlbasis)

    elif ntype in [7, 'marble_noise']:
        value = marble_noise(
                        (ncoords[0] - origin_x + x_offset),
                        (ncoords[1] - origin_y + y_offset), 
                        (ncoords[2] - origin_z + z_offset),
                        (origin[0] + x_offset, origin[1] + y_offset, origin[2] + z_offset), nsize,
                        marbleshape, marblebias, marblesharpnes,
                        distortion, depth, hardnoise, nbasis, amp, freq
                        )
    elif ntype in [8, 'shattered_hterrain']:
        value = shattered_hterrain(ncoords, dimension, lacunarity, depth, offset, distortion, nbasis)

    elif ntype in [9, 'strata_hterrain']:
        value = strata_hterrain(ncoords, dimension, lacunarity, depth, offset, distortion, nbasis)

    elif ntype in [10, 'ant_turbulence']:
        value = ant_turbulence(ncoords, depth, hardnoise, nbasis, amp, freq, distortion)

    elif ntype in [11, 'vl_noise_turbulence']:
        value = vl_noise_turbulence(ncoords, distortion, depth, nbasis, vlbasis, hardnoise, amp, freq)

    elif ntype in [12, 'vl_hTerrain']:
        value = vl_hTerrain(ncoords, dimension, lacunarity, depth, offset, nbasis, vlbasis, distortion)

    elif ntype in [13, 'distorted_heteroTerrain']:
        value = distorted_heteroTerrain(ncoords, dimension, lacunarity, depth, offset, distortion, nbasis, vlbasis)

    elif ntype in [14, 'double_multiFractal']:
        value = double_multiFractal(ncoords, dimension, lacunarity, depth, offset, gain, nbasis, vlbasis)

    elif ntype in [15, 'slick_rock']:
        value = slick_rock(ncoords,dimension, lacunarity, depth, offset, gain, distortion, nbasis, vlbasis)

    elif ntype in [16, 'planet_noise']:
        value = planet_noise(ncoords, depth, hardnoise, nbasis)[2] * 0.5 + 0.5

    elif ntype in [17, 'blender_texture']:
        if texture_name != "" and texture_name in bpy.data.textures:
            value = bpy.data.textures[texture_name].evaluate(ncoords)[3]
        else:
            value = 0.0
    else:
        value = 0.5

    # Adjust height
    if height_invert:
        value = (1.0 - value) * height + height_offset
    else:
        value = value * height + height_offset

    # Edge falloff:
    if not sphere:
        if falloff:
            ratio_x, ratio_y = abs(x) * 2 / meshsize_x, abs(y) * 2 / meshsize_y
            fallofftypes = [0,
                            sqrt(ratio_y**falloffsize_y),
                            sqrt(ratio_x**falloffsize_x),
                            sqrt(ratio_x**falloffsize_x + ratio_y**falloffsize_y)
                           ]
            dist = fallofftypes[falloff]
            value -= edge_level
            if(dist < 1.0):
                dist = (dist * dist * (3 - 2 * dist))
                value = (value - value * dist) + edge_level
            else:
                value = edge_level

    # Strata / terrace / layers
    if stratatype not in [0, "0"]:
        if stratatype in [1, "1"]:
            strata = strata / height
            strata *= 2
            steps = (sin(value * strata * pi) * (0.1 / strata * pi))
            value = (value * 0.5 + steps * 0.5) * 2.0

        elif stratatype in [2, "2"]:
            strata = strata / height
            steps = -abs(sin(value * strata * pi) * (0.1 / strata * pi))
            value = (value * 0.5 + steps * 0.5) * 2.0

        elif stratatype in [3, "3"]:
            strata = strata / height
            steps = abs(sin(value * strata * pi) * (0.1 / strata * pi))
            value = (value * 0.5 + steps * 0.5) * 2.0

        elif stratatype in [4, "4"]:
            strata = strata / height
            value = int( value * strata ) * 1.0 / strata

        elif stratatype in [5, "5"]:
            strata = strata / height
            steps = (int( value * strata ) * 1.0 / strata)
            value = (value * (1.0 - 0.5) + steps * 0.5)

    # Clamp height min max
    if (value < minimum):
        value = minimum
    if (value > maximum):
        value = maximum

    return value


# ------------------------------------------------------------
# draw properties

def draw_ant_refresh(self, context):
    layout = self.layout
    if self.auto_refresh is False:
        self.refresh = False
    elif self.auto_refresh is True:
        self.refresh = True
    row = layout.box().row()
    split = row.split()
    split.scale_y = 1.5
    split.prop(self, "auto_refresh", toggle=True, icon_only=True, icon='AUTO')
    split.prop(self, "refresh", toggle=True, icon_only=True, icon='FILE_REFRESH')


def draw_ant_main(self, context, generate=True):
    layout = self.layout
    box = layout.box()
    box.prop(self, "show_main_settings", toggle=True)
    if self.show_main_settings:
        if generate:
            row = box.row(align=True)
            split = row.split(align=True)
            split.prop(self, "at_cursor", toggle=True, icon_only=True, icon='CURSOR')
            split.prop(self, "smooth_mesh", toggle=True, icon_only=True, icon='SOLID')
            split.prop(self, "tri_face", toggle=True, icon_only=True, icon='MESH_DATA')

            if not self.sphere_mesh:
                row = box.row(align=True)
                row.prop(self, "sphere_mesh", toggle=True)
            else:
                row = box.row(align=True)
                split = row.split(0.5, align=True)
                split.prop(self, "sphere_mesh", toggle=True)
                split.prop(self, "remove_double", toggle=True)

            box.prop(self, "ant_terrain_name")
            box.prop_search(self, "land_material",  bpy.data, "materials")

        col = box.column(align=True)
        col.prop(self, "subdivision_x")
        col.prop(self, "subdivision_y")
        col = box.column(align=True)
        if self.sphere_mesh:
            col.prop(self, "mesh_size")
        else:
            col.prop(self, "mesh_size_x")
            col.prop(self, "mesh_size_y")


def draw_ant_noise(self, context):
    layout = self.layout
    box = layout.box()
    box.prop(self, "show_noise_settings", toggle=True)
    if self.show_noise_settings:
        box.prop(self, "noise_type")
        if self.noise_type == "blender_texture":
            box.prop_search(self, "texture_block", bpy.data, "textures")
        else:
            box.prop(self, "basis_type")

        col = box.column(align=True)
        col.prop(self, "random_seed")
        col = box.column(align=True)
        col.prop(self, "noise_offset_x")
        col.prop(self, "noise_offset_y")
        col.prop(self, "noise_offset_z")
        col.prop(self, "noise_size_x")
        col.prop(self, "noise_size_y")
        col.prop(self, "noise_size_z")
        col = box.column(align=True)
        col.prop(self, "noise_size")

        col = box.column(align=True)
        if self.noise_type == "multi_fractal":
            col.prop(self, "noise_depth")
            col.prop(self, "dimension")
            col.prop(self, "lacunarity")
        elif self.noise_type == "ridged_multi_fractal":
            col.prop(self, "noise_depth")
            col.prop(self, "dimension")
            col.prop(self, "lacunarity")
            col.prop(self, "offset")
            col.prop(self, "gain")
        elif self.noise_type == "hybrid_multi_fractal":
            col.prop(self, "noise_depth")
            col.prop(self, "dimension")
            col.prop(self, "lacunarity")
            col.prop(self, "offset")
            col.prop(self, "gain")
        elif self.noise_type == "hetero_terrain":
            col.prop(self, "noise_depth")
            col.prop(self, "dimension")
            col.prop(self, "lacunarity")
            col.prop(self, "offset")
        elif self.noise_type == "fractal":
            col.prop(self, "noise_depth")
            col.prop(self, "dimension")
            col.prop(self, "lacunarity")
        elif self.noise_type == "turbulence_vector":
            col.prop(self, "noise_depth")
            col.prop(self, "amplitude")
            col.prop(self, "frequency")
            col.separator()
            row = col.row(align=True)
            row.prop(self, "hard_noise", expand=True)
        elif self.noise_type == "variable_lacunarity":
            box.prop(self, "vl_basis_type")
            box.prop(self, "distortion")
        elif self.noise_type == "marble_noise":
            box.prop(self, "marble_shape")
            box.prop(self, "marble_bias")
            box.prop(self, "marble_sharp")
            col = box.column(align=True)
            col.prop(self, "distortion")
            col.prop(self, "noise_depth")
            col.separator()
            row = col.row(align=True)
            row.prop(self, "hard_noise", expand=True)
        elif self.noise_type == "shattered_hterrain":
            col.prop(self, "noise_depth")
            col.prop(self, "dimension")
            col.prop(self, "lacunarity")
            col.prop(self, "offset")
            col.prop(self, "distortion")
        elif self.noise_type == "strata_hterrain":
            col.prop(self, "noise_depth")
            col.prop(self, "dimension")
            col.prop(self, "lacunarity")
            col.prop(self, "offset")
            col.prop(self, "distortion", text="Strata")
        elif self.noise_type == "ant_turbulence":
            col.prop(self, "noise_depth")
            col.prop(self, "amplitude")
            col.prop(self, "frequency")
            col.prop(self, "distortion")
            col.separator()
            row = col.row(align=True)
            row.prop(self, "hard_noise", expand=True)
        elif self.noise_type == "vl_noise_turbulence":
            col.prop(self, "noise_depth")
            col.prop(self, "amplitude")
            col.prop(self, "frequency")
            col.prop(self, "distortion")
            col.separator()
            col.prop(self, "vl_basis_type")
            col.separator()
            row = col.row(align=True)
            row.prop(self, "hard_noise", expand=True)
        elif self.noise_type == "vl_hTerrain":
            col.prop(self, "noise_depth")
            col.prop(self, "dimension")
            col.prop(self, "lacunarity")
            col.prop(self, "offset")
            col.prop(self, "distortion")
            col.separator()
            col.prop(self, "vl_basis_type")
        elif self.noise_type == "distorted_heteroTerrain":
            col.prop(self, "noise_depth")
            col.prop(self, "dimension")
            col.prop(self, "lacunarity")
            col.prop(self, "offset")
            col.prop(self, "distortion")
            col.separator()
            col.prop(self, "vl_basis_type")
        elif self.noise_type == "double_multiFractal":
            col.prop(self, "noise_depth")
            col.prop(self, "dimension")
            col.prop(self, "lacunarity")
            col.prop(self, "offset")
            col.prop(self, "gain")
            col.separator()
            col.prop(self, "vl_basis_type")
        elif self.noise_type == "slick_rock":
            col.prop(self, "noise_depth")
            col.prop(self, "dimension")
            col.prop(self, "lacunarity")
            col.prop(self, "gain")
            col.prop(self, "offset")
            col.prop(self, "distortion")
            col.separator()
            col.prop(self, "vl_basis_type")
        elif self.noise_type == "planet_noise":
            col.prop(self, "noise_depth")
            col.separator()
            row = col.row(align=True)
            row.prop(self, "hard_noise", expand=True)


def draw_ant_displace(self, context, generate=True):
    layout = self.layout
    box = layout.box()
    box.prop(self, "show_displace_settings", toggle=True)
    if self.show_displace_settings:
        col = box.column(align=True)
        row = col.row(align=True).split(0.92, align=True)
        row.prop(self, "height")
        row.prop(self, "height_invert", toggle=True, text="", icon='ARROW_LEFTRIGHT')
        col.prop(self, "height_offset")
        col.prop(self, "maximum")
        col.prop(self, "minimum")
        if generate:
            if not self.sphere_mesh:
                col = box.column()
                col.prop(self, "edge_falloff")
                if self.edge_falloff is not "0":
                    col = box.column(align=True)
                    col.prop(self, "edge_level")
                    if self.edge_falloff in ["2", "3"]:
                        col.prop(self, "falloff_x")
                    if self.edge_falloff in ["1", "3"]:
                        col.prop(self, "falloff_y")
        else:
            col = box.column(align=False)
            col.prop(self, "use_vgroup", toggle=True)

        col = box.column()
        col.prop(self, "strata_type")
        if self.strata_type is not "0":
            col = box.column()
            col.prop(self, "strata")


def draw_ant_water(self, context):
    layout = self.layout
    box = layout.box()
    col = box.column()
    col.prop(self, "water_plane", toggle=True)
    if self.water_plane:
        col = box.column(align=True)
        col.prop_search(self, "water_material",  bpy.data, "materials")
        col = box.column()
        col.prop(self, "water_level")


# Store propereties
def store_properties(operator, ob):
    ob.ant_landscape.ant_terrain_name = operator.ant_terrain_name
    ob.ant_landscape.at_cursor = operator.at_cursor
    ob.ant_landscape.smooth_mesh = operator.smooth_mesh
    ob.ant_landscape.tri_face = operator.tri_face
    ob.ant_landscape.sphere_mesh = operator.sphere_mesh
    ob.ant_landscape.land_material = operator.land_material
    ob.ant_landscape.water_material = operator.water_material
    ob.ant_landscape.texture_block = operator.texture_block
    ob.ant_landscape.subdivision_x = operator.subdivision_x
    ob.ant_landscape.subdivision_y = operator.subdivision_y
    ob.ant_landscape.mesh_size_x = operator.mesh_size_x
    ob.ant_landscape.mesh_size_y = operator.mesh_size_y
    ob.ant_landscape.mesh_size = operator.mesh_size
    ob.ant_landscape.random_seed = operator.random_seed
    ob.ant_landscape.noise_offset_x = operator.noise_offset_x
    ob.ant_landscape.noise_offset_y = operator.noise_offset_y
    ob.ant_landscape.noise_offset_z = operator.noise_offset_z
    ob.ant_landscape.noise_size_x = operator.noise_size_x
    ob.ant_landscape.noise_size_y = operator.noise_size_y
    ob.ant_landscape.noise_size_z = operator.noise_size_z
    ob.ant_landscape.noise_size = operator.noise_size
    ob.ant_landscape.noise_type = operator.noise_type
    ob.ant_landscape.basis_type = operator.basis_type
    ob.ant_landscape.vl_basis_type = operator.vl_basis_type
    ob.ant_landscape.distortion = operator.distortion
    ob.ant_landscape.hard_noise = operator.hard_noise
    ob.ant_landscape.noise_depth = operator.noise_depth
    ob.ant_landscape.amplitude = operator.amplitude
    ob.ant_landscape.frequency = operator.frequency
    ob.ant_landscape.dimension = operator.dimension
    ob.ant_landscape.lacunarity = operator.lacunarity
    ob.ant_landscape.offset = operator.offset
    ob.ant_landscape.gain = operator.gain
    ob.ant_landscape.marble_bias = operator.marble_bias
    ob.ant_landscape.marble_sharp = operator.marble_sharp
    ob.ant_landscape.marble_shape = operator.marble_shape
    ob.ant_landscape.height = operator.height
    ob.ant_landscape.height_invert = operator.height_invert
    ob.ant_landscape.height_offset = operator.height_offset
    ob.ant_landscape.maximum = operator.maximum
    ob.ant_landscape.minimum = operator.minimum
    ob.ant_landscape.edge_falloff = operator.edge_falloff
    ob.ant_landscape.edge_level = operator.edge_level
    ob.ant_landscape.falloff_x = operator.falloff_x
    ob.ant_landscape.falloff_y = operator.falloff_y
    ob.ant_landscape.strata_type = operator.strata_type
    ob.ant_landscape.strata = operator.strata
    ob.ant_landscape.water_plane = operator.water_plane
    ob.ant_landscape.water_level = operator.water_level
    ob.ant_landscape.use_vgroup = operator.use_vgroup
    ob.ant_landscape.show_main_settings = operator.show_main_settings
    ob.ant_landscape.show_noise_settings = operator.show_noise_settings
    ob.ant_landscape.show_displace_settings = operator.show_displace_settings
    #print("A.N.T. Landscape Object Properties:")
    #for k in ob.ant_landscape.keys():
    #    print(k, "-", ob.ant_landscape[k])
    return ob

