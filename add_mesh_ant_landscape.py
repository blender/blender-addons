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
    "name": "Add Mesh: ANT Landscape",
    "author": "Jimmy Hazevoet",
    "version": "0.1.0 July-2010",
    "blender": (2, 5, 3),
    "location": "Add Mesh menu",
    "description": "Adds a landscape primitive",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/",
    "tracker_url": "https://projects.blender.org/tracker/index.php?func=detail&aid=23130&group_id=153&atid=469",
    "category": "Add Mesh"}

# import modules
import bpy
from bpy.props import *
from mathutils import *
from noise import *
from math import *

###------------------------------------------------------------
# calculates the matrix for the new object depending on user pref
def align_matrix(context):
    loc = TranslationMatrix(context.scene.cursor_location)
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

# some functions for marbleNoise
def no_bias(a):
    return a

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
        s = -cos(x**2+y**2)/(x**2+y**2+0.5)
    elif shape == 2:
        # swirl
        x = x*2
        y = y*2
        s = ( x*sin( x*x+y*y ) + y*cos( x*x+y*y ) )
    elif shape == 3:
        # bumps
        x = x*2
        y = y*2
        s = (sin( x*pi ) + sin( y*pi ))
    elif shape == 4:
        # y grad.
        s = y*pi
    elif shape == 5:
        # x grad.
        s = x*pi
    else:
        # marble
        s = ((x+y)*5)
    return s

# marbleNoise
def marble_noise(x,y, origin, size, shape, bias, sharpnes, depth, turb, basis ):
    x = x / size
    y = y / size
    s = shapes(x,y,shape)

    x += origin[0]
    y += origin[1]
    value = s + turb * turbulence_vector((x,y,0.0), depth, 0, basis )[0]

    if bias == 1:
        value = sin_bias( value )
    elif bias == 2:
        value = tri_bias( value )
    elif bias == 3:
        value = saw_bias( value )
    else:
        value = no_bias( value )

    if sharpnes == 1:
        value = sharp( value )
    elif sharpnes == 2:
        value = sharper( value )
    else:
        value = soft( value )

    return value

# Shattered_hTerrain:
def shattered_hterrain( x,y, H, lacunarity, octaves, offset, distort, basis ):
    d = ( turbulence_vector( ( x, y, 0.0 ), 6, 0, 0, 0.5, 2.0 )[0] * 0.5 + 0.5 )*distort*0.5
    t0 = ( turbulence_vector( ( x+d, y+d, 0.0 ), 0, 0, 7, 0.5, 2.0 )[0] + 0.5 )
    t2 = ( hetero_terrain(( x*2, y*2, t0*0.25 ), H, lacunarity, octaves, offset, basis ) )
    return (( t0*t2 )+t2*0.5)*0.5

# landscape_gen
def landscape_gen(x,y,falloffsize,options=[0,1.0,1, 0,0,1.0,0,6,1.0,2.0,1.0,2.0,0,0,0, 1.0,0.0,1,0.0,1.0,0]):

    # options
    rseed    = options[0]
    nsize    = options[1]
    ntype      = int( options[2][0] )
    nbasis     = int( options[3][0] )
    vlbasis    = int( options[4][0] )
    distortion = options[5]
    hard       = options[6]
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
    terrace      = options[21]

    # origin
    if rseed == 0:
        origin = 0.0,0.0,0.0
        origin_x = 0.0
        origin_y = 0.0
    else:
        # randomise origin
        seed_set( rseed )
        origin = random_unit_vector()
        origin_x = 0.5 - origin[0] * 1000
        origin_y = 0.5 - origin[1] * 1000

    # adjust noise size and origin
    ncoords = ( x / nsize + origin_x, y / nsize + origin_y, 0.0 )

    # noise basis type's
    if nbasis == 9: nbasis = 14  # to get cellnoise basis you must set 14 instead of 9 (is this a bug?)
    if vlbasis ==9: vlbasis = 14
    # noise type's
    if ntype == 0:   value = multi_fractal(        ncoords, dimension, lacunarity, depth, nbasis ) * 0.5
    elif ntype == 1: value = ridged_multi_fractal( ncoords, dimension, lacunarity, depth, offset, gain, nbasis ) * 0.5
    elif ntype == 2: value = hybrid_multi_fractal( ncoords, dimension, lacunarity, depth, offset, gain, nbasis ) * 0.5
    elif ntype == 3: value = hetero_terrain(       ncoords, dimension, lacunarity, depth, offset, nbasis ) * 0.25
    elif ntype == 4: value = fractal(              ncoords, dimension, lacunarity, depth, nbasis )
    elif ntype == 5: value = turbulence_vector(    ncoords, depth, hard, nbasis )[0]
    elif ntype == 6: value = vl_vector(            ncoords, distortion, nbasis, vlbasis ) + 0.5
    elif ntype == 7: value = cell( ncoords ) + 0.5
    elif ntype == 8: value = shattered_hterrain( ncoords[0],ncoords[1], dimension, lacunarity, depth, offset, distortion, nbasis ) * 0.5
    elif ntype == 9: value = marble_noise( x*2.0/falloffsize,y*2.0/falloffsize, origin, nsize, marbleshape, marblebias, marblesharpnes, depth, distortion, nbasis )
    else:
        value = 0.0

    # adjust height
    if invert !=0:
        value = (1-value) * height + heightoffset
    else:
        value = value * height + heightoffset

    # edge falloff
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

    # terraces / terrain layers
    if terrace !=0:
        terrace *=2
        steps = ( sin( value*terrace*pi ) * ( 0.1/terrace*pi ) )
        value = ( value * (1.0-0.5) + steps*0.5 ) * 2.0

    # clamp height
    if ( value < sealevel ): value = sealevel
    if ( value > platlevel ): value = platlevel

    return value

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
    Subdivision = IntProperty(name="Subdivisions",
                min=4, soft_min=4,
                max=1024, soft_max=1024,
                default=64,
                description="Mesh x y subdivisions")

    MeshSize = FloatProperty(name="Mesh Size",
                min=0.01, soft_min=0.01,
                max=100000.0, soft_max=100000.0,
                default=2.0,
                description="Mesh size in blender units")

    RandomSeed = IntProperty(name="Random Seed",
                min=0, soft_min=0,
                max=999, soft_max=999,
                default=0,
                description="Random seed")

    NoiseSize = FloatProperty(name="Noise Size",
                min=0.01, soft_min=0.01,
                max=10000.0, soft_max=10000.0,
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
                ("7","Cellnoise","Cellnoise"),
                ("8","Shattered_hTerrain","Shattered_hTerrain"),
                ("9","Marble","Marble")]
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
                min=0.0, soft_min=0.0,
                max=100.0, soft_max=100.0,
                default=1.0,
                description="Distortion amount")

    HardNoise = BoolProperty(name="Hard",
                default=True,
                description="Hard noise")

    NoiseDepth = IntProperty(name="Depth",
                min=1, soft_min=1,
                max=12, soft_max=12,
                default=6,
                description="Noise Depth - number of frequencies in the fBm.")

    mDimension = FloatProperty(name="Dimension",
                min=0.01, soft_min=0.01,
                max=2.0, soft_max=2.0, 
                default=1.0,
                description="H - fractal dimension of the roughest areas.")

    mLacunarity = FloatProperty(name="Lacunarity",
                min=0.01, soft_min=0.01,
                max=6.0, soft_max=6.0,
                default=2.0,
                description="Lacunarity - gap between successive frequencies.")

    mOffset = FloatProperty(name="Offset",
                min=0.01, soft_min=0.01,
                max=6.0, soft_max=6.0,
                default=1.0,
                description="Offset - it raises the terrain from 'sea level'.")

    mGain = FloatProperty(name="Gain",
                min=0.01, soft_min=0.01,
                max=6.0, soft_max=6.0,
                default=1.0,
                description="Gain - scale factor.")

    BiasTypes = [
                ("0","None","None"),
                ("1","Sin","Sin"),
                ("2","Tri","Tri"),
                ("3","Saw","Saw")]
    MarbleBias = EnumProperty(name="Bias",
                description="Marble bias",
                default='1',
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


    Invert = BoolProperty(name="Invert Height",
                default=False,
                description="Invert height")

    Height = FloatProperty(name="Height",
                min=0.0, soft_min=0.0,
                max=10000.0, soft_max=10000.0,
                default=0.5,
                description="Height scale")

    Offset = FloatProperty(name="Offset",
                min=-10000.0, soft_min=-10000.0,
                max=10000.0, soft_max=10000.0,
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
                min=-10000.0, soft_min=-10000.0,
                max=10000.0, soft_max=10000.0,
                default=0.0,
                description="Sealevel")

    Plateaulevel = FloatProperty(name="Plateau",
                min=-10000.0, soft_min=-10000.0,
                max=10000.0, soft_max=10000.0,
                default=1.0,
                description="Plateau level")

    Terrace = IntProperty(name="Terrace",
                min=0, soft_min=0,
                max=100, soft_max=100,
                default=0,
                description="Terrain layers amount")

    ###------------------------------------------------------------
    # Draw
    def draw(self, context):
        props = self.properties
        layout = self.layout

        box = layout.box()
        box.prop(props, 'Subdivision')
        box.prop(props, 'MeshSize')

        box = layout.box()
        box.prop(props, 'RandomSeed')

        box = layout.box()
        box.prop(props, 'NoiseType')
        if props.NoiseType != '7':
            box.prop(props, 'BasisType')

        box.prop(props, 'NoiseSize')
        if props.NoiseType == '0':
            box.prop(props, 'NoiseDepth')
            box.prop(props, 'mDimension')
            box.prop(props, 'mLacunarity')
        if props.NoiseType == '1':
            box.prop(props, 'NoiseDepth')
            box.prop(props, 'mDimension')
            box.prop(props, 'mLacunarity')
            box.prop(props, 'mOffset')
            box.prop(props, 'mGain')
        if props.NoiseType == '2':
            box.prop(props, 'NoiseDepth')
            box.prop(props, 'mDimension')
            box.prop(props, 'mLacunarity')
            box.prop(props, 'mOffset')
            box.prop(props, 'mGain')
        if props.NoiseType == '3':
            box.prop(props, 'NoiseDepth')
            box.prop(props, 'mDimension')
            box.prop(props, 'mLacunarity')
            box.prop(props, 'mOffset')
        if props.NoiseType == '4':
            box.prop(props, 'NoiseDepth')
            box.prop(props, 'mDimension')
            box.prop(props, 'mLacunarity')
        if props.NoiseType == '5':
            box.prop(props, 'NoiseDepth')
            box.prop(props, 'HardNoise')
        if props.NoiseType == '6':
            box.prop(props, 'VLBasisType')
            box.prop(props, 'Distortion')
        #if props.NoiseType == '7':
        if props.NoiseType == '8':
            box.prop(props, 'NoiseDepth')
            box.prop(props, 'mDimension')
            box.prop(props, 'mLacunarity')
            box.prop(props, 'mOffset')
            box.prop(props, 'Distortion')
        if props.NoiseType == '9':
            box.prop(props, 'MarbleShape')
            box.prop(props, 'MarbleBias')
            box.prop(props, 'MarbleSharp')
            box.prop(props, 'NoiseDepth')
            box.prop(props, 'Distortion')

        box = layout.box()
        box.prop(props, 'Invert')
        box.prop(props, 'Height')
        box.prop(props, 'Offset')
        box.prop(props, 'Plateaulevel')
        box.prop(props, 'Sealevel')
        box.prop(props, 'Terrace')
        box.prop(props, 'Falloff')

    ###------------------------------------------------------------
    # Execute
    def execute(self, context):
        # turn off undo
        undo = bpy.context.user_preferences.edit.global_undo
        bpy.context.user_preferences.edit.global_undo = False

        # deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        props = self.properties
        edit = props.edit

        # options
        sub_d = props.Subdivision
        size_me = props.MeshSize
        options = [
            props.RandomSeed,    #0
            props.NoiseSize,     #1
            props.NoiseType,     #2
            props.BasisType,     #3
            props.VLBasisType,   #4
            props.Distortion,    #5
            props.HardNoise,     #6
            props.NoiseDepth,    #7
            props.mDimension,    #8
            props.mLacunarity,   #9
            props.mOffset,       #10
            props.mGain,         #11
            props.MarbleBias,    #12
            props.MarbleSharp,   #13
            props.MarbleShape,   #14
            props.Invert,        #15
            props.Height,        #16
            props.Offset,        #17
            props.Falloff,       #18
            props.Sealevel,      #19
            props.Plateaulevel,  #20
            props.Terrace        #21
            ]

        # Main function
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

                z = landscape_gen(x,y,size_me,options)

                edgeloop_cur.append(len(verts))
                verts.append((x, y, z))

            if len(edgeloop_prev) > 0:
                faces_row = createFaces(edgeloop_prev, edgeloop_cur)
                faces.extend(faces_row)

            edgeloop_prev = edgeloop_cur

        obj = create_mesh_object(context, verts, [], faces, "Landscape", edit, self.align_matrix)
        # restore pre operator undo state
        bpy.context.user_preferences.edit.global_undo = undo
        return {'FINISHED'}

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
