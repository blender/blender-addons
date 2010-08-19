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
    "name": "Add Curve: Torus Knots",
    "author": "testscreenings",
    "version": "0.1",
    "blender": (2, 5, 3),
    "location": "View3D > Add > Curve",
    "description": "Adds many types of knots",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Curve/Torus_Knot",
    "tracker_url": "https://projects.blender.org/tracker/index.php?func=detail&aid=22403&group_id=153&atid=469",
    "category": "Add Curve"}
    
    
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
    loc = Matrix.Translation(context.scene.cursor_location)
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
def createCurve(vertArray, props, align_matrix):
    # options to vars
    splineType = 'NURBS'
    name = 'Torus_Knot'

    # create curve
    scene = bpy.context.scene
    newCurve = bpy.data.curves.new(name, type = 'CURVE') # curvedatablock
    newSpline = newCurve.splines.new(type = splineType)  # spline

    # create spline from vertarray
    newSpline.points.add(int(len(vertArray)*0.25 - 1))
    newSpline.points.foreach_set('co', vertArray)
    newSpline.use_endpoint_u = True

    # Curve settings
    newCurve.dimensions = '3D'
    newSpline.use_cyclic_u = True
    newSpline.use_endpoint_u = True
    newSpline.order_u = 4

    if props.geo_surf:
        newCurve.bevel_depth = props.geo_bDepth
        newCurve.bevel_resolution = props.geo_bRes
        newCurve.front = False
        newCurve.back = False
        newCurve.extrude = props.geo_extrude
        newCurve.width = props.geo_width
        newCurve.resolution_u = props.geo_res

    # create object with newCurve
    new_obj = bpy.data.objects.new(name, newCurve)  # object
    scene.objects.link(new_obj)                     # place in active scene
    new_obj.select = True                           # set as selected
    scene.objects.active = new_obj                  # set as active
    new_obj.matrix_world = align_matrix             # apply matrix

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
def main(context, props, align_matrix):
    # deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # options
    splineType = 'NURBS'


    # get verts
    verts = Torus_Knot_Curve(props.torus_p,
                            props.torus_q,
                            props.torus_w,
                            props.torus_res,
                            props.torus_formula,
                            props.torus_h,
                            props.torus_u,
                            props.torus_v,
                            props.torus_rounds)

    # turn verts into array
    vertArray = vertsToPoints(verts)

    # create object
    createCurve(vertArray, props, align_matrix)

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
    @classmethod
    def poll(cls, context):
        return context.scene != None

    ##### EXECUTE #####
    def execute(self, context):
        # turn off undo
        undo = bpy.context.user_preferences.edit.use_global_undo
        bpy.context.user_preferences.edit.use_global_undo = False

        props = self.properties

        if not props.options_plus:
            props.torus_rounds = props.torus_p

        # main function
        main(context, props, self.align_matrix)
        
        # restore pre operator undo state
        bpy.context.user_preferences.edit.use_global_undo = undo

        return {'FINISHED'}

    ##### INVOKE #####
    def invoke(self, context, event):
        # store creation_matrix
        self.align_matrix = align_matrix(context)
        self.execute(context)

        return {'FINISHED'}

################################################################################
##### REGISTER #####

def torus_knot_plus_button(self, context):
    self.layout.operator(torus_knot_plus.bl_idname, text="Torus Knot +", icon="PLUGIN")


def register():
    bpy.types.INFO_MT_curve_add.append(torus_knot_plus_button)

def unregister():
    bpy.types.INFO_MT_curve_add.remove(torus_knot_plus_button)

if __name__ == "__main__":
    register()
