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
    'url': '',
    'description': 'adds many types of knots',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/Curve/Torus_Knot',
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
# sets bezierhandles to auto
def setBezierHandles(obj, mode = 'AUTOMATIC'):
    scene = bpy.context.scene
    if obj.type != 'CURVE':
        return
    scene.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT', toggle=True)
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.handle_type_set(type=mode)
    bpy.ops.object.mode_set(mode='OBJECT', toggle=True)

# get array of vertcoordinates acording to splinetype
def vertsToPoints(Verts, splineType):
    # main vars
    vertArray = []

    # array for BEZIER spline output (V3)
    if splineType == 'BEZIER':
        for v in Verts:
            vertArray += v

    # array for nonBEZIER output (V4)
    else:
        for v in Verts:
            vertArray += v
            if splineType == 'NURBS':
                vertArray.append(1) #for nurbs w=1
            else: #for poly w=0
                vertArray.append(0)
    return vertArray

# create new CurveObject from vertarray and splineType
def createCurve(vertArray, GEO, options, curveOptions, align_matrix):
    # options to vars
    splineType = options[0] # output splineType 'POLY' 'NURBS' 'BEZIER'
    name = options[1] # KnotType as name

    # create curve
    scene = bpy.context.scene
    newCurve = bpy.data.curves.new(name, type = 'CURVE') # curvedatablock
    newSpline = newCurve.splines.new(type = splineType) # spline

    # create spline from vertarray
    if splineType == 'BEZIER':
        newSpline.bezier_points.add(int(len(vertArray)*0.33))
        newSpline.bezier_points.foreach_set('co', vertArray)
    else:
        newSpline.points.add(int(len(vertArray)*0.25 - 1))
        newSpline.points.foreach_set('co', vertArray)
        newSpline.endpoint_u = True

    # set curveOptions
    shape = curveOptions[0]
    cyclic_u = curveOptions[1]
    endp_u = curveOptions[2]
    order_u = curveOptions[3]
    handleType = curveOptions[4]

    newCurve.dimensions = shape
    newSpline.cyclic_u = cyclic_u
    newSpline.endpoint_u = endp_u
    newSpline.order_u = order_u

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

    # set bezierhandles
    if splineType == 'BEZIER':
        setBezierHandles(new_obj, handleType)

    return

########################################################################
####################### Knot Definitions ###############################
########################################################################

#### TORUS KNOT
def Torus_Knot_Curve(p=2, q=3, w=1, res=24, formula=0, h=1, u=1 ,v=1, rounds=2):
    newPoints = []
    angle = (2.0/360.0)*360*rounds
    #angle = 360/pi
    step = angle/(res-1)
    scale = h
    height = w

    if formula == 0:
        for i in range(res-1):
            t = ( i*step*pi)
            
            x = (2 * scale + cos((q*t)/p*v)) * cos(t * u)
            y = (2 * scale + cos((q*t)/p*v)) * sin(t * u)
            z = sin(q*t/p) * height
            
            newPoints.append([x,y,z])
    
    if formula == 1:
        for i in range(res-1):
            t = ( i*step)
            
            x = ((2*w + cos((q*t)/p)) * cos(t*p)) * sin(t/p)
            y = ((2*w + cos((q*t)/p)) * sin(t*p)) * sin(t/p)
            z = sin(q*t/p)
            
            newPoints.append([x,y,z])
    
    if formula == 2:
        for i in range(res-1):
            t = ( i*step)
            beta = t*pi
            
            r = 0.8 + 1.6 * sin(q * beta/p)
            theta = 2 * beta
            phi = 0.6 * pi * sin(q * beta/p)
            
            x = r * cos(phi) * cos(theta)
            y = r * cos(phi) * sin(theta)
            z = r * sin(phi)
            
            newPoints.append([x,y,z])


    #newPoints = [[-1,-1,0], [-1,1,0], [1,1,0], [1,-1,0]]
    return newPoints

##------------------------------------------------------------
# Main Function
def main(context, param, GEO, options, curveOptions, align_matrix):
    # deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # options
    knotType = options[1]
    splineType = options[0]


    # get verts
    if knotType == 'Torus_Knot':
        verts = Torus_Knot_Curve(param[0], param[1], param[2], param[3], param[4],
                                  param[5], param[6], param[7], param[8])

    # turn verts into array
    vertArray = vertsToPoints(verts, splineType)

    # create object
    createCurve(vertArray, GEO, options, curveOptions, align_matrix)

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
    KnotTypes = [
                ('Torus_Knot', 'Torus Knot', 'Torus_Knot')
                ]
    KnotType = EnumProperty(name="Type",
                description="Form of Curve to create",
                items=KnotTypes)
    SplineTypes = [
                ('NURBS', 'Nurbs', 'NURBS'),
                ('POLY', 'Poly', 'POLY'),
                ('BEZIER', 'Bezier', 'BEZIER')]
    outputType = EnumProperty(name="Output splines",
                description="Type of splines to output",
                items=SplineTypes)

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

    #### Curve Options
    shapeItems = [
                ('3D', '3D', '3D'),
                ('2D', '2D', '2D')]
    shape = EnumProperty(name="2D / 3D",
                items=shapeItems,
                description="2D or 3D Curve")
    cyclic_u = BoolProperty(name="Cyclic",
                default=True,
                description="make curve closed")
    endp_u = BoolProperty(name="endpoint_u",
                default=True,
                description="stretch to endpoints")
    order_u = IntProperty(name="order_u",
                default=4,
                min=2, soft_min=2,
                max=6, soft_max=6,
                description="Order of nurbs spline")
    bezHandles = [
                ('VECTOR', 'Vector', 'VECTOR'),
                ('AUTOMATIC', 'Auto', 'AUTOMATIC')]
    handleType = EnumProperty(name="Handle type",
                description="bezier handles type",
                items=bezHandles)

    #### Parameters
    torus_res = IntProperty(name="Resoulution",
                default=200,
                min=3, soft_min=3,
                description='Resolution')
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
    torus_w = FloatProperty(name="height",
                default=1,
                #min=0, soft_min=0,
                #max=1, soft_max=1,
                description="height")
    torus_h = FloatProperty(name="scale",
                default=1,
                #min=0, soft_min=0,
                #max=1, soft_max=1,
                description="scale")
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
    torus_rounds = IntProperty(name="rounds",
                default=2,
                min=1, soft_min=1,
                #max=1, soft_max=1,
                description="rounds")

    ##### DRAW #####
    def draw(self, context):
        props = self.properties
        layout = self.layout

        # general options        
        col = layout.column()
        #col.prop(props, 'KnotType') waits for more knottypes
        col.label(text=props.KnotType+" Parameters")

        # Parameters per KnotType
        box = layout.box()
        if props.KnotType == 'Torus_Knot':
            #box.prop(props, 'torus_formula')
            box.prop(props, 'torus_res')
            box.prop(props, 'torus_p')
            box.prop(props, 'torus_q')
            box.prop(props, 'torus_u')
            box.prop(props, 'torus_v')
            box.prop(props, 'torus_rounds')
            box.prop(props, 'torus_w')
            box.prop(props, 'torus_h')

        # Output Type
        col = layout.column()
        #col.label(text="Output Curve Type")
        #row = layout.row()
        #row.prop(props, 'outputType', expand=True)
        #col = layout.column()
        #col.label(text="Curve Options")

        # Curve options
        #box = layout.box()
        #if props.outputType == 'NURBS':
            #box.row().prop(props, 'shape', expand=True)
            #box.prop(props, 'cyclic_u')
            #box.prop(props, 'endp_u')
            #box.prop(props, 'order_u')

        #if props.outputType == 'POLY':
            #box.row().prop(props, 'shape', expand=True)
            #box.prop(props, 'cyclic_u')

        if props.outputType == 'BEZIER':
            #box.row().prop(props, 'shape', expand=True)
            col.row().prop(props, 'handleType', expand=True)
            #box.prop(props, 'cyclic_u')

        # surface Options
        col = layout.column()
        col.label(text="Geometry Options")
        box = layout.box()
        box.prop(props, 'geo_surf')
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
            props.outputType,       #0
            props.KnotType          #1
            ]

        # Curve options
        curveOptions = [
            props.shape,            #0
            props.cyclic_u,         #1
            props.endp_u,           #2
            props.order_u,          #4
            props.handleType        #5
            ]

        # main function
        main(context, param, GEO, options, curveOptions, self.align_matrix)
        
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
