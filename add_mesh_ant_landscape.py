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

bl_addon_info = {
    "name": "ANT Landscape",
    "author": "Jimmy Hazevoet",
    "version": (0,1,0),
    "blender": (2, 5, 3),
    "api": 31965,
    "location": "Add Mesh menu",
    "description": "Adds a landscape primitive",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Add_Mesh/ANT_Landscape",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=23130&group_id=153&atid=469",
    "category": "Add Mesh"}

'''
Another Noise Tool: Landscape mesh generator

MESH OPTIONS:
Mesh update:     Turn this on for interactive mesh update.
Sphere:          Generate sphere or a grid mesh. (Turn height falloff off for sphere mesh)
Smooth:          Generate smooth shaded mesh.
Subdivision:     Number of mesh subdivisions, higher numbers gives more detail but also slows down the script.
Mesh size:       X,Y size of the grid mesh (in blender units).

NOISE OPTIONS: ( Most of these options are the same as in blender textures. )
Random seed:     Use this to randomise the origin of the noise function.
Noise size:      Size of the noise.
Noise type:      Available noise types: multiFractal, ridgedMFractal, hybridMFractal, heteroTerrain, Turbulence, Distorted Noise, Cellnoise, Shattered_hTerrain, Marble
Noise basis:     Blender, Perlin, NewPerlin, Voronoi_F1, Voronoi_F2, Voronoi_F3, Voronoi_F4, Voronoi_F2-F1, Voronoi Crackle, Cellnoise
VLNoise basis:   Blender, Perlin, NewPerlin, Voronoi_F1, Voronoi_F2, Voronoi_F3, Voronoi_F4, Voronoi_F2-F1, Voronoi Crackle, Cellnoise
Distortion:      Distortion amount.
Hard:            Hard/Soft turbulence noise.
Depth:           Noise depth, number of frequencies in the fBm.
Dimension:       Musgrave: Fractal dimension of the roughest areas.
Lacunarity:      Musgrave: Gap between successive frequencies.
Offset:          Musgrave: Raises the terrain from sea level.
Gain:            Musgrave: Scale factor.
Marble Bias:     Sin, Tri, Saw
Marble Sharpnes: Soft, Sharp, Sharper
Marble Shape:    Shape of the marble function: Default, Ring, Swirl, X, Y

HEIGHT OPTIONS:
Invert:          Invert terrain height.
Height:          Scale terrain height.
Offset:          Terrain height offset.
Falloff:         Terrain height falloff: Type 1, Type 2, X, Y
Sealevel:        Flattens terrain below sealevel.
Platlevel:       Flattens terrain above plateau level.
Strata:          Strata amount, number of strata/terrace layers.
Strata type:     Strata types, Smooth, Sharp-sub, Sharp-add
'''

# import modules
import bpy
from bpy.props import *
from mathutils import *
from noise import *
from math import *


###------------------------------------------------------------
# calculates the matrix for the new object depending on user pref
def align_matrix(context):
    loc = Matrix.Translation(context.scene.cursor_location)
    obj_align = context.user_preferences.edit.object_align
    if (context.space_data.type == 'VIEW_3D'
        and obj_align == 'VIEW'):
        rot = context.space_data.region_3d.view_matrix.rotation_part().invert().resize4x4()
    else:
        rot = Matrix()
    align_matrix = loc * rot
    return align_matrix

# Create a new mesh (object) from verts/edges/faces.
# verts/edges/faces ... List of vertices/edges/faces for the
#                    new mesh (as used in from_pydata).
# name ... Name of the new mesh (& object).
# edit ... Replace existing mesh data.
# Note: Using "edit" will destroy/delete existing mesh data.
def create_mesh_object(context, verts, edges, faces, name, edit, align_matrix):
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
        ob_new.select = True

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
        ob_new.select = True

        # Place the object at the 3D cursor location.
        # apply viewRotaion
        ob_new.matrix_world = align_matrix

    if obj_act and obj_act.mode == 'EDIT':
        if not edit:
            # We are in EditMode, switch to ObjectMode.
            bpy.ops.object.mode_set(mode='OBJECT')

            # Select the active object as well.
            obj_act.select = True

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

# A very simple "bridge" tool.
# Connects two equally long vertex rows with faces.
# Returns a list of the new faces (list of  lists)
#
# vertIdx1 ... First vertex list (list of vertex indices).
# vertIdx2 ... Second vertex list (list of vertex indices).
# closed ... Creates a loop (first & last are closed).
# flipped ... Invert the normal of the face(s).
#
# Note: You can set vertIdx1 to a single vertex index to create
#    a fan/star of faces.
# Note: If both vertex idx list are the same length they have
#    to have at least 2 vertices.
def createFaces(vertIdx1, vertIdx2, closed=False, flipped=False):
    faces = []

    if not vertIdx1 or not vertIdx2:
        return None

    if len(vertIdx1) < 2 and len(vertIdx2) < 2:
        return None

    fan = False
    if (len(vertIdx1) != len(vertIdx2)):
        if (len(vertIdx1) == 1 and len(vertIdx2) > 1):
            fan = True
        else:
            return None

    total = len(vertIdx2)

    if closed:
        # Bridge the start with the end.
        if flipped:
            face = [
                vertIdx1[0],
                vertIdx2[0],
                vertIdx2[total - 1]]
            if not fan:
                face.append(vertIdx1[total - 1])
            faces.append(face)

        else:
            face = [vertIdx2[0], vertIdx1[0]]
            if not fan:
                face.append(vertIdx1[total - 1])
            face.append(vertIdx2[total - 1])
            faces.append(face)

    # Bridge the rest of the faces.
    for num in range(total - 1):
        if flipped:
            if fan:
                face = [vertIdx2[num], vertIdx1[0], vertIdx2[num + 1]]
            else:
                face = [vertIdx2[num], vertIdx1[num],
                    vertIdx1[num + 1], vertIdx2[num + 1]]
            faces.append(face)
        else:
            if fan:
                face = [vertIdx1[0], vertIdx2[num], vertIdx2[num + 1]]
            else:
                face = [vertIdx1[num], vertIdx2[num],
                    vertIdx2[num + 1], vertIdx1[num + 1]]
            faces.append(face)

    return faces


###------------------------------------------------------------
###------------------------------------------------------------
# some functions for marble_noise
def sin_bias(a):
    return 0.5 + 0.5 * sin(a)

def tri_bias(a):
    b = 2 * pi
    a = 1 - 2 * abs(floor((a * (1/b))+0.5) - (a*(1/b)))
    return a

def saw_bias(a):
    b = 2 * pi
    n = int(a/b)
    a -= n * b
    if a < 0: a += b
    return a / b

def soft(a):
    return a

def sharp(a):
    return a**0.5

def sharper(a):
    return sharp(sharp(a))

def shapes(x,y,shape=0):
    if shape == 1:
        # ring
        x = x*2
        y = y*2
        s = (-cos(x**2+y**2)/(x**2+y**2+0.5))
    elif shape == 2:
        # swirl
        x = x*2
        y = y*2
        s = (( x*sin( x*x+y*y ) + y*cos( x*x+y*y ) ) / (x**2+y**2+0.5))
    elif shape == 3:
        # bumps
        x = x*2
        y = y*2
        s = ((cos( x*pi ) + cos( y*pi ))-0.5)
    elif shape == 4:
        # y grad.
        s = (y*pi)
    elif shape == 5:
        # x grad.
        s = (x*pi)
    else:
        # marble
        s = ((x+y)*5)
    return s

# marble_noise
def marble_noise(x,y,z, origin, size, shape, bias, sharpnes, turb, depth, hard, basis ):
    x = x / size
    y = y / size
    z = z / size
    s = shapes(x,y,shape)

    x += origin[0]
    y += origin[1]
    z += origin[2]
    value = s + turb * turbulence_vector((x,y,z), depth, hard, basis )[0]

    if bias == 1:
        value = tri_bias( value )
    elif bias == 2:
        value = saw_bias( value )
    else:
        value = sin_bias( value )

    if sharpnes == 1:
        value = sharp( value )
    elif sharpnes == 2:
        value = sharper( value )
    else:
        value = soft( value )

    return value

###------------------------------------------------------------
# custom noise types

# shattered_hterrain:
def shattered_hterrain( x,y,z, H, lacunarity, octaves, offset, distort, basis ):
    d = ( turbulence_vector( ( x, y, z ), 6, 0, 0 )[0] * 0.5 + 0.5 )*distort*0.5
    t1 = ( turbulence_vector( ( x+d, y+d, z ), 0, 0, 7 )[0] + 0.5 )
    t2 = ( hetero_terrain(( x*2, y*2, z*2 ), H, lacunarity, octaves, offset, basis )*0.5 )
    return (( t1*t2 )+t2*0.5) * 0.5

# strata_hterrain
def strata_hterrain( x,y,z, H, lacunarity, octaves, offset, distort, basis ):
    value = hetero_terrain(( x, y, z ), H, lacunarity, octaves, offset, basis )*0.5
    steps = ( sin( value*(distort*5)*pi ) * ( 0.1/(distort*5)*pi ) )
    return ( value * (1.0-0.5) + steps*0.5 )

###------------------------------------------------------------
# landscape_gen
def landscape_gen(x,y,z,falloffsize,options=[0,1.0,1, 0,0,1.0,0,6,1.0,2.0,1.0,2.0,0,0,0, 1.0,0.0,1,0.0,1.0,0,0,0]):

    # options
    rseed    = options[0]
    nsize    = options[1]
    ntype      = int( options[2][0] )
    nbasis     = int( options[3][0] )
    vlbasis    = int( options[4][0] )
    distortion = options[5]
    hardnoise  = options[6]
    depth      = options[7]
    dimension  = options[8]
    lacunarity = options[9]
    offset     = options[10]
    gain       = options[11]
    marblebias     = int( options[12][0] )
    marblesharpnes = int( options[13][0] )
    marbleshape    = int( options[14][0] )
    invert       = options[15]
    height       = options[16]
    heightoffset = options[17]
    falloff      = int( options[18][0] )
    sealevel     = options[19]
    platlevel    = options[20]
    strata       = options[21]
    stratatype   = options[22]
    sphere       = options[23]

    # origin
    if rseed == 0:
        origin = 0.0,0.0,0.0
        origin_x = 0.0
        origin_y = 0.0
        origin_z = 0.0
    else:
        # randomise origin
        seed_set( rseed )
        origin = random_unit_vector()
        origin_x = ( 0.5 - origin[0] ) * 1000.0
        origin_y = ( 0.5 - origin[1] ) * 1000.0
        origin_z = ( 0.5 - origin[2] ) * 1000.0

    # adjust noise size and origin
    ncoords = ( x / nsize + origin_x, y / nsize + origin_y, z / nsize + origin_z )

    # noise basis type's
    if nbasis == 9: nbasis = 14  # to get cellnoise basis you must set 14 instead of 9
    if vlbasis ==9: vlbasis = 14
    # noise type's
    if ntype == 0:   value = multi_fractal(        ncoords, dimension, lacunarity, depth, nbasis ) * 0.5
    elif ntype == 1: value = ridged_multi_fractal( ncoords, dimension, lacunarity, depth, offset, gain, nbasis ) * 0.5
    elif ntype == 2: value = hybrid_multi_fractal( ncoords, dimension, lacunarity, depth, offset, gain, nbasis ) * 0.5
    elif ntype == 3: value = hetero_terrain(       ncoords, dimension, lacunarity, depth, offset, nbasis ) * 0.25
    elif ntype == 4: value = fractal(              ncoords, dimension, lacunarity, depth, nbasis )
    elif ntype == 5: value = turbulence_vector(    ncoords, depth, hardnoise, nbasis )[0]
    elif ntype == 6: value = vl_vector(            ncoords, distortion, nbasis, vlbasis ) + 0.5
    elif ntype == 7: value = marble_noise( x*2.0/falloffsize,y*2.0/falloffsize,z*2/falloffsize, origin, nsize, marbleshape, marblebias, marblesharpnes, distortion, depth, hardnoise, nbasis )
    elif ntype == 8: value = shattered_hterrain( ncoords[0], ncoords[1], ncoords[2], dimension, lacunarity, depth, offset, distortion, nbasis )
    elif ntype == 9: value = strata_hterrain( ncoords[0], ncoords[1], ncoords[2], dimension, lacunarity, depth, offset, distortion, nbasis )
    else:
        value = 0.0

    # adjust height
    if invert !=0:
        value = (1-value) * height + heightoffset
    else:
        value = value * height + heightoffset

    # edge falloff
    if sphere == 0: # no edge falloff if spherical
        if falloff != 0:
            fallofftypes = [ 0, sqrt((x*x)**2+(y*y)**2), sqrt(x*x+y*y), sqrt(y*y), sqrt(x*x) ]
            dist = fallofftypes[ falloff]
            if falloff ==1:
                radius = (falloffsize/2)**2
            else:
                radius = falloffsize/2
            value = value - sealevel
            if( dist < radius ):
                dist = dist / radius
                dist = ( (dist) * (dist) * ( 3-2*(dist) ) )
                value = ( value - value * dist ) + sealevel
            else:
                value = sealevel

    # strata / terrace / layered
    if stratatype !='0':
        strata = strata / height
    if stratatype == '1':
        strata *= 2
        steps = ( sin( value*strata*pi ) * ( 0.1/strata*pi ) )
        value = ( value * (1.0-0.5) + steps*0.5 ) * 2.0
    elif stratatype == '2':
        steps = -abs( sin( value*(strata)*pi ) * ( 0.1/(strata)*pi ) )
        value =( value * (1.0-0.5) + steps*0.5 ) * 2.0 
    elif stratatype == '3':
        steps = abs( sin( value*(strata)*pi ) * ( 0.1/(strata)*pi ) )
        value =( value * (1.0-0.5) + steps*0.5 ) * 2.0
    else:
        value = value

    # clamp height
    if ( value < sealevel ): value = sealevel
    if ( value > platlevel ): value = platlevel

    return value


# generate grid
def grid_gen( sub_d, size_me, options ):

    verts = []
    faces = []
    edgeloop_prev = []

    delta = size_me / float(sub_d - 1)
    start = -(size_me / 2.0)

    for row_x in range(sub_d):
        edgeloop_cur = []
        x = start + row_x * delta
        for row_y in range(sub_d):
            y = start + row_y * delta
            z = landscape_gen(x,y,0.0,size_me,options)

            edgeloop_cur.append(len(verts))
            verts.append((x,y,z))

        if len(edgeloop_prev) > 0:
            faces_row = createFaces(edgeloop_prev, edgeloop_cur)
            faces.extend(faces_row)

        edgeloop_prev = edgeloop_cur

    return verts, faces


# generate sphere
def sphere_gen( sub_d, size_me, options ):

    verts = []
    faces = []
    edgeloop_prev = []

    for row_x in range(sub_d):
        edgeloop_cur = []
        for row_y in range(sub_d):
            u = sin(row_y*pi*2/(sub_d-1)) * cos(-pi/2+row_x*pi/(sub_d-1)) * size_me/2
            v = cos(row_y*pi*2/(sub_d-1)) * cos(-pi/2+row_x*pi/(sub_d-1)) * size_me/2
            w = sin(-pi/2+row_x*pi/(sub_d-1)) * size_me/2
            h = landscape_gen(u,v,w,size_me,options) / size_me
            u,v,w = u+u*h, v+v*h, w+w*h

            edgeloop_cur.append(len(verts))
            verts.append((u, v, w))

        if len(edgeloop_prev) > 0:
            faces_row = createFaces(edgeloop_prev, edgeloop_cur)
            faces.extend(faces_row)

        edgeloop_prev = edgeloop_cur

    return verts, faces


###------------------------------------------------------------
# Add landscape
class landscape_add(bpy.types.Operator):
    '''Add a landscape mesh'''
    bl_idname = "Add_landscape"
    bl_label = "Landscape"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Add landscape mesh"

    # edit - Whether to add or update.
    edit = BoolProperty(name="",
        description="",
        default=False,
        options={'HIDDEN'})

    # align_matrix for the invoke
    align_matrix = Matrix()

    # properties
    AutoUpdate = BoolProperty(name="Mesh update",
                default=True,
                description="Update mesh")

    SphereMesh = BoolProperty(name="Sphere",
                default=False,
                description="Generate Sphere mesh")

    SmoothMesh = BoolProperty(name="Smooth",
                default=True,
                description="Shade smooth")

    Subdivision = IntProperty(name="Subdivisions",
                min=4,
                max=6400,
                default=64,
                description="Mesh x y subdivisions")

    MeshSize = FloatProperty(name="Mesh Size",
                min=0.01,
                max=100000.0,
                default=2.0,
                description="Mesh size")

    RandomSeed = IntProperty(name="Random Seed",
                min=0,
                max=9999,
                default=0,
                description="Randomize noise origin")

    NoiseSize = FloatProperty(name="Noise Size",
                min=0.01,
                max=10000.0,
                default=1.0,
                description="Noise size")

    NoiseTypes = [
                ("0","multiFractal","multiFractal"),
                ("1","ridgedMFractal","ridgedMFractal"),
                ("2","hybridMFractal","hybridMFractal"),
                ("3","heteroTerrain","heteroTerrain"),
                ("4","fBm","fBm"),
                ("5","Turbulence","Turbulence"),
                ("6","Distorted Noise","Distorted Noise"),
                ("7","Marble","Marble"),
                ("8","Shattered_hTerrain","Shattered_hTerrain"),
                ("9","Strata_hTerrain","Strata_hTerrain")]
                
    NoiseType = EnumProperty(name="Type",
                description="Noise type",
                items=NoiseTypes)

    BasisTypes = [
                ("0","Blender","Blender"),
                ("1","Perlin","Perlin"),
                ("2","NewPerlin","NewPerlin"),
                ("3","Voronoi_F1","Voronoi_F1"),
                ("4","Voronoi_F2","Voronoi_F2"),
                ("5","Voronoi_F3","Voronoi_F3"),
                ("6","Voronoi_F4","Voronoi_F4"),
                ("7","Voronoi_F2-F1","Voronoi_F2-F1"),
                ("8","Voronoi Crackle","Voronoi Crackle"),
                ("9","Cellnoise","Cellnoise")]
    BasisType = EnumProperty(name="Basis",
                description="Noise basis",
                items=BasisTypes)

    VLBasisTypes = [
                ("0","Blender","Blender"),
                ("1","Perlin","Perlin"),
                ("2","NewPerlin","NewPerlin"),
                ("3","Voronoi_F1","Voronoi_F1"),
                ("4","Voronoi_F2","Voronoi_F2"),
                ("5","Voronoi_F3","Voronoi_F3"),
                ("6","Voronoi_F4","Voronoi_F4"),
                ("7","Voronoi_F2-F1","Voronoi_F2-F1"),
                ("8","Voronoi Crackle","Voronoi Crackle"),
                ("9","Cellnoise","Cellnoise")]
    VLBasisType = EnumProperty(name="VLBasis",
                description="VLNoise basis",
                items=VLBasisTypes)

    Distortion = FloatProperty(name="Distortion",
                min=0.01,
                max=1000.0,
                default=1.0,
                description="Distortion amount")

    HardNoise = BoolProperty(name="Hard",
                default=True,
                description="Hard noise")

    NoiseDepth = IntProperty(name="Depth",
                min=1,
                max=16,
                default=6,
                description="Noise Depth - number of frequencies in the fBm.")

    mDimension = FloatProperty(name="Dimension",
                min=0.01,
                max=2.0,
                default=1.0,
                description="H - fractal dimension of the roughest areas.")

    mLacunarity = FloatProperty(name="Lacunarity",
                min=0.01,
                max=6.0,
                default=2.0,
                description="Lacunarity - gap between successive frequencies.")

    mOffset = FloatProperty(name="Offset",
                min=0.01,
                max=6.0,
                default=1.0,
                description="Offset - raises the terrain from sea level.")

    mGain = FloatProperty(name="Gain",
                min=0.01,
                max=6.0,
                default=1.0,
                description="Gain - scale factor.")

    BiasTypes = [
                ("0","Sin","Sin"),
                ("1","Tri","Tri"),
                ("2","Saw","Saw")]
    MarbleBias = EnumProperty(name="Bias",
                description="Marble bias",
                items=BiasTypes)

    SharpTypes = [
                ("0","Soft","Soft"),
                ("1","Sharp","Sharp"),
                ("2","Sharper","Sharper")]
    MarbleSharp = EnumProperty(name="Sharp",
                description="Marble sharp",
                items=SharpTypes)

    ShapeTypes = [
                ("0","Default","Default"),
                ("1","Ring","Ring"),
                ("2","Swirl","Swirl"),
                ("3","Bump","Bump"),
                ("4","Y","Y"),
                ("5","X","X")]
    MarbleShape = EnumProperty(name="Shape",
                description="Marble shape",
                items=ShapeTypes)

    Invert = BoolProperty(name="Invert",
                default=False,
                description="Invert noise input")

    Height = FloatProperty(name="Height",
                min=0.01,
                max=10000.0,
                default=0.5,
                description="Height scale")

    Offset = FloatProperty(name="Offset",
                min=-10000.0,
                max=10000.0,
                default=0.0,
                description="Height offset")

    fallTypes = [
                ("0","None","None"),
                ("1","Type 1","Type 1"),
                ("2","Type 2","Type 2"),
                ("3","Y","Y"),
                ("4","X","X")]
    Falloff = EnumProperty(name="Falloff",
                description="Edge falloff",
                default="1",
                items=fallTypes)

    Sealevel = FloatProperty(name="Sealevel",
                min=-10000.0,
                max=10000.0,
                default=0.0,
                description="Sealevel")

    Plateaulevel = FloatProperty(name="Plateau",
                min=-10000.0,
                max=10000.0,
                default=1.0,
                description="Plateau level")

    Strata = FloatProperty(name="Strata",
                min=0.01,
                max=1000.0,
                default=3.0,
                description="Strata amount")

    StrataTypes = [
                ("0","None","None"),
                ("1","Type 1","Type 1"),
                ("2","Type 2","Type 2"),
                ("3","Type 3","Type 3")]
    StrataType = EnumProperty(name="Strata",
                description="Strata type",
                default="0",
                items=StrataTypes)

    ###------------------------------------------------------------
    # Draw
    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.prop(self.properties, 'AutoUpdate')
        box.prop(self.properties, 'SphereMesh')
        box.prop(self.properties, 'SmoothMesh')
        box.prop(self.properties, 'Subdivision')
        box.prop(self.properties, 'MeshSize')

        box = layout.box()
        box.prop(self.properties, 'NoiseType')
        if self.NoiseType != '7':
            box.prop(self.properties, 'BasisType')
        box.prop(self.properties, 'RandomSeed')
        box.prop(self.properties, 'NoiseSize')
        if self.NoiseType == '0':
            box.prop(self.properties, 'NoiseDepth')
            box.prop(self.properties, 'mDimension')
            box.prop(self.properties, 'mLacunarity')
        if self.NoiseType == '1':
            box.prop(self.properties, 'NoiseDepth')
            box.prop(self.properties, 'mDimension')
            box.prop(self.properties, 'mLacunarity')
            box.prop(self.properties, 'mOffset')
            box.prop(self.properties, 'mGain')
        if self.NoiseType == '2':
            box.prop(self.properties, 'NoiseDepth')
            box.prop(self.properties, 'mDimension')
            box.prop(self.properties, 'mLacunarity')
            box.prop(self.properties, 'mOffset')
            box.prop(self.properties, 'mGain')
        if self.NoiseType == '3':
            box.prop(self.properties, 'NoiseDepth')
            box.prop(self.properties, 'mDimension')
            box.prop(self.properties, 'mLacunarity')
            box.prop(self.properties, 'mOffset')
        if self.NoiseType == '4':
            box.prop(self.properties, 'NoiseDepth')
            box.prop(self.properties, 'mDimension')
            box.prop(self.properties, 'mLacunarity')
        if self.NoiseType == '5':
            box.prop(self.properties, 'NoiseDepth')
            box.prop(self.properties, 'HardNoise')
        if self.NoiseType == '6':
            box.prop(self.properties, 'VLBasisType')
            box.prop(self.properties, 'Distortion')
        if self.NoiseType == '7':
            box.prop(self.properties, 'MarbleShape')
            box.prop(self.properties, 'MarbleBias')
            box.prop(self.properties, 'MarbleSharp')
            box.prop(self.properties, 'Distortion')
            box.prop(self.properties, 'NoiseDepth')
            box.prop(self.properties, 'HardNoise')
        if self.NoiseType == '8':
            box.prop(self.properties, 'NoiseDepth')
            box.prop(self.properties, 'mDimension')
            box.prop(self.properties, 'mLacunarity')
            box.prop(self.properties, 'mOffset')
            box.prop(self.properties, 'Distortion')
        if self.NoiseType == '9':
            box.prop(self.properties, 'NoiseDepth')
            box.prop(self.properties, 'mDimension')
            box.prop(self.properties, 'mLacunarity')
            box.prop(self.properties, 'mOffset')
            box.prop(self.properties, 'Distortion')

        box = layout.box()
        box.prop(self.properties, 'Invert')
        box.prop(self.properties, 'Height')
        box.prop(self.properties, 'Offset')
        box.prop(self.properties, 'Plateaulevel')
        box.prop(self.properties, 'Sealevel')
        if self.SphereMesh == False:
            box.prop(self.properties, 'Falloff')
        box.prop(self.properties, 'StrataType')
        if self.StrataType != '0':
            box.prop(self.properties, 'Strata')

    ###------------------------------------------------------------
    # Execute
    def execute(self, context):

        edit = self.edit

        #mesh update
        if self.AutoUpdate != 0:

            # turn off undo
            undo = bpy.context.user_preferences.edit.use_global_undo
            bpy.context.user_preferences.edit.use_global_undo = False

            # deselect all objects
            bpy.ops.object.select_all(action='DESELECT')

            # options
            options = [
                self.RandomSeed,    #0
                self.NoiseSize,     #1
                self.NoiseType,     #2
                self.BasisType,     #3
                self.VLBasisType,   #4
                self.Distortion,    #5
                self.HardNoise,     #6
                self.NoiseDepth,    #7
                self.mDimension,    #8
                self.mLacunarity,   #9
                self.mOffset,       #10
                self.mGain,         #11
                self.MarbleBias,    #12
                self.MarbleSharp,   #13
                self.MarbleShape,   #14
                self.Invert,        #15
                self.Height,        #16
                self.Offset,        #17
                self.Falloff,       #18
                self.Sealevel,      #19
                self.Plateaulevel,  #20
                self.Strata,        #21
                self.StrataType,    #22
                self.SphereMesh     #23
                ]

            # Main function
            if self.SphereMesh !=0:
                # sphere
                verts, faces = sphere_gen( self.Subdivision, self.MeshSize, options )
            else:
                # grid
                verts, faces = grid_gen( self.Subdivision, self.MeshSize, options )

            # create mesh object
            obj = create_mesh_object(context, verts, [], faces, "Landscape", edit, self.align_matrix)

            # sphere, remove doubles
            if self.SphereMesh !=0:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.remove_doubles(limit=0.0001)
                bpy.ops.object.mode_set(mode='OBJECT')

            # Shade smooth
            if self.SmoothMesh !=0:
                bpy.ops.object.shade_smooth()

            # restore pre operator undo state
            bpy.context.user_preferences.edit.use_global_undo = undo

            return {'FINISHED'}
        else:
            return {'PASS_THROUGH'}

    def invoke(self, context, event):
        self.align_matrix = align_matrix(context)
        self.execute(context)
        return {'FINISHED'}

###------------------------------------------------------------
# Register
import space_info

    # Define "Landscape" menu
def menu_func_landscape(self, context):
    self.layout.operator(landscape_add.bl_idname, text="Landscape", icon="PLUGIN")

def register():
    space_info.INFO_MT_mesh_add.append(menu_func_landscape)

def unregister():
    space_info.INFO_MT_mesh_add.remove(menu_func_landscape)

if __name__ == "__main__":
    register()
