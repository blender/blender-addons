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
    'name': 'Add Curve: Torus Knots',
    'author': 'testscreenings',
    'version': '0.1',
    'blender': (2, 5, 2),
    'location': 'Add Curve Menu',
    'description': 'adds many types of knots',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/Curve/Torus_Knot',
    'tracker_url': 'https://projects.blender.org/tracker/index.php?'\
        'func=detail&aid=22403&group_id=153&atid=469',
    'category': 'Add Curve'}
##------------------------------------------------------------
#### import modules
import bpy
from bpy.props import *
from mathutils import *
from math import *

##------------------------------------------------------------
# calculates the matrix for the new object
# depending on user pref
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

##------------------------------------------------------------
#### Curve creation functions

# get array of vertcoordinates acording to splinetype
def vertsToPoints(Verts):
    vertArray = []

    for v in Verts:
        vertArray += v
        vertArray.append(1) #for nurbs w=1

    return vertArray

# create new CurveObject from vertarray and splineType
def createCurve(vertArray, GEO, align_matrix):
    # options to vars
    splineType = 'NURBS'
    name = 'Torus_Knot'

    # create curve
    scene = bpy.context.scene
    newCurve = bpy.data.curves.new(name, type = 'CURVE') # curvedatablock
    newSpline = newCurve.splines.new(type = splineType) # spline

    # create spline from vertarray
    newSpline.points.add(int(len(vertArray)*0.25 - 1))
    newSpline.points.foreach_set('co', vertArray)
    newSpline.endpoint_u = True

    # Curve settings
    newCurve.dimensions = '3D'
    newSpline.cyclic_u = True
    newSpline.endpoint_u = True
    newSpline.order_u = 4

    # GEO Options
    surf = GEO[0]
    bDepth = GEO[1]
    bRes = GEO[2]
    extrude = GEO[3]
    width = GEO[4]
    res = GEO[5]

    if surf:
        newCurve.bevel_depth = bDepth
        newCurve.bevel_resolution = bRes
        newCurve.front = False
        newCurve.back = False
        newCurve.extrude = extrude
        newCurve.width = width
        newCurve.resolution_u = res

    # create object with newCurve
    new_obj = bpy.data.objects.new(name, newCurve) # object
    scene.objects.link(new_obj) # place in active scene
    new_obj.selected = True # set as selected
    scene.objects.active = new_obj  # set as active
    new_obj.matrix = align_matrix # apply matrix

    return

########################################################################
####################### Knot Definitions ###############################
########################################################################

#### TORUS KNOT
def Torus_Knot_Curve(p=2, q=3, w=1, res=24, formula=0, h=1, u=1 ,v=1, rounds=2):
    newPoints = []
    angle = 2*rounds
    step = angle/(res-1)
    scale = h
    height = w

    for i in range(res-1):
        t = ( i*step*pi)
        
        x = (2 * scale + cos((q*t)/p*v)) * cos(t * u)
        y = (2 * scale + cos((q*t)/p*v)) * sin(t * u)
        z = sin(q*t/p) * height
        
        newPoints.append([x,y,z])

    return newPoints

##------------------------------------------------------------
# Main Function
def main(context, param, GEO, options, align_matrix):
    # deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # options
    splineType = 'NURBS'


    # get verts
    verts = Torus_Knot_Curve(param[0], param[1], param[2], param[3], param[4],
                              param[5], param[6], param[7], param[8])

    # turn verts into array
    vertArray = vertsToPoints(verts)

    # create object
    createCurve(vertArray, GEO, align_matrix)

    return

class torus_knot_plus(bpy.types.Operator):
    ''''''
    bl_idname = "torus_knot_plus"
    bl_label = "Torus Knot +"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "adds many types of knots"

    # align_matrix for the invoke
    align_matrix = Matrix()

    #### general options
    options_plus = BoolProperty(name="plus options",
                default=False,
                description="Show more options (the plus part).")

    #### GEO Options
    geo_surf = BoolProperty(name="Surface",
                default=True)
    geo_bDepth = FloatProperty(name="bevel",
                default=0.08,
                min=0, soft_min=0)
    geo_bRes = IntProperty(name="bevel res",
                default=2,
                min=0, soft_min=0,
                max=4, soft_max=4)
    geo_extrude = FloatProperty(name="extrude",
                default=0.0,
                min=0, soft_min=0)
    geo_width = FloatProperty(name="width",
                default=1.0,
                min=0, soft_min=0)
    geo_res = IntProperty(name="resolution",
                default=12,
                min=1, soft_min=1)


    #### Parameters
    torus_res = IntProperty(name="Resoulution",
                default=200,
                min=3, soft_min=3,
                description='Resolution, Number of controlverticies.')
    torus_p = IntProperty(name="p",
                default=2,
                min=1, soft_min=1,
                #max=1, soft_max=1,
                description="p")
    torus_q = IntProperty(name="q",
                default=3,
                min=1, soft_min=1,
                #max=1, soft_max=1,
                description="q")
    torus_w = FloatProperty(name="Height",
                default=1,
                #min=0, soft_min=0,
                #max=1, soft_max=1,
                description="Height in Z")
    torus_h = FloatProperty(name="Scale",
                default=1,
                #min=0, soft_min=0,
                #max=1, soft_max=1,
                description="Scale, in XY")
    torus_u = IntProperty(name="u",
                default=1,
                min=1, soft_min=1,
                #max=1, soft_max=1,
                description="u")
    torus_v = IntProperty(name="v",
                default=1,
                min=1, soft_min=1,
                #max=1, soft_max=1,
                description="v")
    torus_formula = IntProperty(name="Variation",
                default=0,
                min=0, soft_min=0,
                max=10, soft_max=10)
    torus_rounds = IntProperty(name="Rounds",
                default=2,
                min=1, soft_min=1,
                #max=1, soft_max=1,
                description="Rounds")

    ##### DRAW #####
    def draw(self, context):
        props = self.properties
        layout = self.layout

        # general options        
        col = layout.column()
        #col.prop(props, 'KnotType') waits for more knottypes
        col.label(text="Torus Knot Parameters")

        # Parameters 
        box = layout.box()
        box.prop(props, 'torus_res')
        box.prop(props, 'torus_w')
        box.prop(props, 'torus_h')
        box.prop(props, 'torus_p')
        box.prop(props, 'torus_q')
        box.prop(props, 'options_plus')
        if props.options_plus:
            box.prop(props, 'torus_u')
            box.prop(props, 'torus_v')
            box.prop(props, 'torus_rounds')

        # surface Options
        col = layout.column()
        col.label(text="Geometry Options")
        box = layout.box()
        box.prop(props, 'geo_surf')
        if props.geo_surf:
            box.prop(props, 'geo_bDepth')
            box.prop(props, 'geo_bRes')
            box.prop(props, 'geo_extrude')
            #box.prop(props, 'geo_width') # not really good
            box.prop(props, 'geo_res')
    
    ##### POLL #####
    def poll(self, context):
        return context.scene != None

    ##### EXECUTE #####
    def execute(self, context):
        # turn off undo
        undo = bpy.context.user_preferences.edit.global_undo
        bpy.context.user_preferences.edit.global_undo = False

        props = self.properties

        if not props.options_plus:
            props.torus_rounds = props.torus_p

        # Parameters
        param = [
            props.torus_p,          #0
            props.torus_q,          #1
            props.torus_w,          #2
            props.torus_res,        #3
            props.torus_formula,    #4
            props.torus_h,          #5
            props.torus_u,          #6
            props.torus_v,          #7
            props.torus_rounds      #8
            ]

        # GEO Options
        GEO = [
            props.geo_surf,         #0
            props.geo_bDepth,       #1
            props.geo_bRes,         #2
            props.geo_extrude,      #3
            props.geo_width,        #4
            props.geo_res           #5
            ]

        # Options
        options = [
            # general properties
            ]


        # main function
        main(context, param, GEO, options, self.align_matrix)
        
        # restore pre operator undo state
        bpy.context.user_preferences.edit.global_undo = undo

        return {'FINISHED'}

    ##### INVOKE #####
    def invoke(self, context, event):
        # store creation_matrix
        self.align_matrix = align_matrix(context)
        self.execute(context)

        return {'FINISHED'}

################################################################################
##### REGISTER #####

torus_knot_plus_button = (lambda self, context: self.layout.operator
            (torus_knot_plus.bl_idname, text="Torus Knot +", icon="PLUGIN"))

classes = [
torus_knot_plus
    ]

def register():
    register = bpy.types.register
    for cls in classes:
        register(cls)

    bpy.types.INFO_MT_curve_add.append(torus_knot_plus_button)

def unregister():
    unregister = bpy.types.unregister
    for cls in classes:
        unregister(cls)

    bpy.types.INFO_MT_curve_add.remove(torus_knot_plus_button)

if __name__ == "__main__":
    register()
