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


bl_info = {
    "name": "SpiroFit and BounceSpline",
    "author": "Antonio Osprite, Liero, Atom, Jimmy Hazevoet",
    "version": (0, 2, 0),
    "blender": (2, 78, 0),
    "location": "Toolshelf > Misc Tab",
    "description": "SpiroFit and BounceSpline adds splines to Mesh",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
}


import bpy
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        )
from mathutils import (
        Matrix,
        Vector,
        )
from math import (
        sin,
        cos,
        pi
        )
from bpy.types import Operator
import random as r


# ------------------------------------------------------------
#
def use_random_seed(seed):
    r.seed(seed)
    return

# ------------------------------------------------------------
# Generate new curve object from given points
# ------------------------------------------------------------

def add_curve_object(verts, matrix,
                    x_ray=False,
                    spline_type='BEZIER',
                    spline_resolution=12,
                    bevel=0.0,
                    bevel_resolution=0,
                    spline_random_radius=0.0):

    curve = bpy.data.curves.new('Spline','CURVE')
    curve.dimensions = '3D'
    spline = curve.splines.new(spline_type)
    cur = bpy.data.objects.new('Curve',curve)

    if spline_type == 'BEZIER':
        spline.bezier_points.add(int(len(verts)-1))
        for i in range(len(verts)):
            spline.bezier_points[i].co = verts[i]
            spline.bezier_points[i].handle_right_type = 'AUTO'
            spline.bezier_points[i].handle_left_type = 'AUTO'
            spline.bezier_points[i].radius += r.random() * spline_random_radius
    else:
        spline.points.add(int(len(verts)-1))
        for i in range(len(verts)):
            spline.points[i].co = verts[i][0], verts[i][1], verts[i][2], 1

    bpy.context.scene.objects.link(cur)
    cur.data.use_uv_as_generated = True
    cur.data.resolution_u = spline_resolution
    cur.data.fill_mode = 'FULL'
    cur.data.bevel_depth = bevel
    cur.data.bevel_resolution = bevel_resolution
    cur.matrix_world = matrix
    if x_ray:
        cur.show_x_ray = x_ray
    return


# ------------------------------------------------------------
# Spirofit, original blender 2.45 script by: Antonio Osprite
# http://www.kino3d.com/forum/viewtopic.php?t=5374
# ------------------------------------------------------------

def distance(v1, v2):
    d = (Vector(v1) - Vector(v2)).length
    return d


def spiral_point(step, radius, z_coord, spires, waves, wave_height, rndm):
    x = radius * cos(spires * step) + (r.random() - 0.5) * rndm
    y = radius * sin(spires * step) + (r.random() - 0.5) * rndm
    z = z_coord + (cos(waves * step * pi) * wave_height) + (r.random() - 0.5) * rndm
    return [x, y, z]


# ray cast
def object_mapping_ray_cast(obj, vert, center, offset):
    intersections = []
    ray = Vector(vert)
    orig = Vector(center)
    direction = ray - orig
    poly = obj.data.polygons
    for f in poly:
        foo, hit, nor, index = obj.ray_cast(orig, direction)
        if hit:
            intersections.append(hit + offset * nor)

    if len(intersections) > 0:
        mapped = min([(distance(i, vert), i) for i in intersections])[1]
    else:
        mapped = orig
    return [mapped[0], mapped[1], mapped[2]]


# closest point
def object_mapping_closest_point(obj, vert, offset):
    cpom = obj.closest_point_on_mesh(vert)
    mapped = cpom[1] + cpom[2] * offset
    return [mapped[0], mapped[1], mapped[2]]


def spirofit_spline(obj,
                    spires=4,
                    spire_resolution=4,
                    waves=0,
                    wave_height=0.0,
                    rndm_spire=0.0,
                    offset=0.0,
                    map_method='RAYCAST'):

    points = []
    bb = obj.bound_box
    bb_xmin = min([ v[0] for v in bb ])
    bb_ymin = min([ v[1] for v in bb ])
    bb_zmin = min([ v[2] for v in bb ])
    bb_xmax = max([ v[0] for v in bb ])
    bb_ymax = max([ v[1] for v in bb ])
    bb_zmax = max([ v[2] for v in bb ])

    radius = distance([bb_xmax, bb_ymax, bb_zmin], [bb_xmin, bb_ymin, bb_zmin]) / 2.0
    height = bb_zmax - bb_zmin
    cx = (bb_xmax + bb_xmin) / 2.0
    cy = (bb_ymax + bb_ymin) / 2.0
    center = [cx, cy, bb_zmin]

    cp = spiral_point(bb_zmin, radius, bb_zmin, spires, waves, wave_height, 0)
    if map_method == 'RAYCAST':
        cp = object_mapping_ray_cast(obj, cp, center, offset)
    elif map_method == 'CLOSESTPOINT':
        cp = object_mapping_closest_point(obj, cp, offset)

    steps = spires * spire_resolution
    for i in range(1, steps + 1):
        t = bb_zmin + (2 * pi / steps) * i
        z = bb_zmin + (float(height) / steps) * i
        center = [cx, cy, z]

        cp = spiral_point(t, radius, z, spires, waves, wave_height, rndm_spire)
        if map_method == 'RAYCAST':
            cp = object_mapping_ray_cast(obj, cp, center, offset)
        elif map_method == 'CLOSESTPOINT':
            cp = object_mapping_closest_point(obj, cp, offset)

        points.append(cp)
    return points


# ------------------------------------------------------------

class SpiroFitSpline(bpy.types.Operator):
    bl_idname = "object.add_spirofit_spline"
    bl_label = "SpiroFit"
    bl_description="Wrap selected mesh in a spiral"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    map_method = bpy.props.EnumProperty(
                name="Mapping Method",
                default='CLOSESTPOINT',
                description="Mapping method",
                items=[('RAYCAST', 'Ray cast', 'Ray cast'),
                        ('CLOSESTPOINT', 'Closest point', 'Closest point')]
                        )

    spire_resolution = bpy.props.IntProperty(
                name="Spire Resolution",
                default=8,
                min=3,
                max=256,
                soft_max=128,
                description="Spire resolution for one turn"
                )
    spires = bpy.props.IntProperty(
                name="Spires",
                default=4,
                min=1,
                max=512,
                soft_max=256,
                description="Number of spire turns"
                )
    waves = bpy.props.IntProperty(
                name="Waves",
                default=0,
                min=0,
                description="Waves amount"
                )
    wave_height = bpy.props.FloatProperty(
                name="Wave intensity",
                default=0.1,
                min=0.0,
                description="Wave intensity scale"
                )
    rndm_spire = bpy.props.FloatProperty(
                name="Randomize",
                default=0.0,
                min=0.0,
                description="Randomize spire"
                )
    offset = bpy.props.FloatProperty(
                name="Offset",
                default=0.0,
                description="Use normal direction to offset spline"
                )
    spline_type = bpy.props.EnumProperty(
                name="Spline type",
                default='BEZIER',
                description="Spline type",
                items=[('POLY', 'Poly', 'POLY'),
                        ('BEZIER', 'Bezier', 'BEZIER')]
                        )
    spline_resolution = bpy.props.IntProperty(
                name="Resolution u",
                default=12,
                min=0,
                max=64,
                description="Curve resolution u"
                )
    bevel = bpy.props.FloatProperty(
                name="Bevel radius",
                default=0.0,
                min=0.0,
                precision=3,
                description="Bevel depth"
                )
    bevel_res = bpy.props.IntProperty(
                name="Bevel resolution",
                default=0,
                min=0,
                max=32,
                description="Bevel resolution"
                )
    spline_random_radius = bpy.props.FloatProperty(
                name="Random bevel radius",
                default=0.0,
                min=0.0,
                description="Random radius amount"
                )
    random_seed = bpy.props.IntProperty(
                name="Random seed",
                default=2,
                min=0,
                description="Random seed number"
                )
    x_ray = bpy.props.BoolProperty(
                name="X-Ray",
                default=True,
                description = "Make the object draw in front of others"
                )
    refresh = bpy.props.BoolProperty(
                name="Refresh",
                description="Refresh spline",
                default=False
                )
    auto_refresh = bpy.props.BoolProperty(
                name="Auto",
                description="Auto refresh spline",
                default=True
                )


    @classmethod
    def poll(self, context):
        ob = context.active_object
        return ((ob is not None) and
                (ob.type == 'MESH') and
                (context.mode == 'OBJECT'))


    def invoke(self, context, event):
        self.refresh = True
        return self.execute(context)


    def execute(self, context):
        if not self.refresh:
            return {'PASS_THROUGH'}

        undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False

        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        obj = context.active_object
        matrix = obj.matrix_world

        if self.random_seed:
            use_random_seed(self.random_seed)

        points = spirofit_spline(obj,
                        self.spires,
                        self.spire_resolution,
                        self.waves,
                        self.wave_height,
                        self.rndm_spire,
                        self.offset,
                        self.map_method
                        )

        add_curve_object(points,
                        matrix,
                        self.x_ray,
                        self.spline_type,
                        self.spline_resolution,
                        self.bevel,
                        self.bevel_res,
                        self.spline_random_radius
                        )

        if self.auto_refresh is False:
            self.refresh = False

        context.user_preferences.edit.use_global_undo = undo
        return {'FINISHED'}


    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, 'x_ray', toggle=True)
        row.separator()
        if self.auto_refresh is False:
            self.refresh = False
        elif self.auto_refresh is True:
            self.refresh = True
        row.prop(self, 'auto_refresh', toggle=True, icon='AUTO', text="")
        row.prop(self, 'refresh', toggle=True, icon='FILE_REFRESH', text="")
        row.separator()
        properties = row.operator('object.add_spirofit_spline', text="Add New")
        col.separator()
        col = layout.column(align=False)
        col.prop(self, 'map_method')
        col = layout.column(align=True)
        col.prop(self, 'spire_resolution')
        col.prop(self, 'spires')
        col.prop(self, 'offset')
        col.prop(self, 'waves')
        col.prop(self, 'wave_height')
        col.prop(self, 'rndm_spire')
        col.prop(self, 'random_seed')
        col.separator()
        col = layout.column(align=True)
        col.prop(self, 'spline_type')
        col.separator()
        col.prop(self, 'spline_resolution')
        col.prop(self, 'bevel')
        if self.spline_type == 'BEZIER':
            col.prop(self, 'spline_random_radius')
        col.prop(self, 'bevel_res')


# ------------------------------------------------------------
# Bounce spline / Fiber mesh
# Original script by Liero and Atom
# https://blenderartists.org/forum/showthread.php?331750-Fiber-Mesh-Emulation
# ------------------------------------------------------------
def noise(var=1):
    rand = Vector((r.gauss(0,1), r.gauss(0,1), r.gauss(0,1)))
    vec = rand.normalized() * var
    return vec


def bounce_spline(obj,
                number=1000,
                ang_noise=0.25,
                offset=0.0,
                extra=50,
                active_face=False):

    dist, points = 1000, []
    poly = obj.data.polygons

    if active_face:
        try:
            n = poly.active
        except:
            print("No active face selected")
            pass
    else:
        n = r.randint(0, len(poly)-1)

    end = poly[n].normal.copy() * -1
    start = poly[n].center
    points.append(start + offset * end)

    for i in range(number):
        for ray in range(extra + 1):
            end += noise(ang_noise)
            try:
                foo, hit, nor, index = obj.ray_cast(start, end * dist)
            except:
                index = -1
            if index != -1:
                start = hit - nor / 10000
                end = end.reflect(nor).normalized()
                points.append(hit + offset * nor)
                break
        if index == -1:
            return points
    return points


# ------------------------------------------------------------

class BounceSpline(bpy.types.Operator):
    bl_idname = "object.add_bounce_spline"
    bl_label = "BounceSpline"
    bl_description="Fill selected mesh with a bounce spline"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    random_seed = bpy.props.IntProperty(
                name="Random seed",
                default=1,
                min=0,
                description="Random seed number"
                )
    bounce_number = bpy.props.IntProperty(
                name="Bounces",
                default=500,
                min=1,
                max=99999,
                soft_max=9999,
                description="Number of Bounces"
                )
    ang_noise = bpy.props.FloatProperty(
                name="Angular noise",
                default=0.25,
                min=0.0,
                description="Add some noise to ray direction"
                )
    offset = bpy.props.FloatProperty(
                name="Offset",
                default=0.0,
                description="Use normal direction to offset spline"
                )
    extra = bpy.props.IntProperty(
                name="Extra",
                default=50,
                min=0,
                max=1000,
                soft_min=0,
                soft_max=500,
                description="Number of extra tries if it fails to hit mesh"
                )
    active_face = bpy.props.BoolProperty(
                name="Active face",
                default=False,
                description = "Starts from active face or a random one"
                )
    spline_type = bpy.props.EnumProperty(
                name="Spline type",
                default='BEZIER',
                description="Spline type",
                items=[('POLY', 'Poly', 'POLY'),
                        ('BEZIER', 'Bezier', 'BEZIER')]
                )
    spline_resolution = bpy.props.IntProperty(
                name="Resolution u",
                default=12,
                min=0,
                max=64,
                description="Curve resolution u"
                )
    bevel = bpy.props.FloatProperty(
                name="Bevel radius",
                default=0.0,
                min=0.0,
                precision=3,
                description="Bevel depth"
                )

    bevel_res = bpy.props.IntProperty(
                name="Bevel resolution",
                default=0,
                min=0,
                max=32,
                description="Bevel resolution"
                )
    spline_random_radius = bpy.props.FloatProperty(
                name="Random bevel radius",
                default=0.0,
                min=0.0,
                description="Random radius amount"
                )
    x_ray = bpy.props.BoolProperty(
                name="X-Ray",
                default=True,
                description = "Make the object draw in front of others"
                )
    refresh = bpy.props.BoolProperty(
                name="Refresh",
                description="Refresh spline",
                default=False
                )
    auto_refresh = bpy.props.BoolProperty(
                name="Auto",
                description="Auto refresh spline",
                default=True
                )

    @classmethod
    def poll(self, context):
        ob = context.active_object
        return ((ob is not None) and
                (ob.type == 'MESH') and
                (context.mode == 'OBJECT'))


    def invoke(self, context, event):
        self.refresh = True
        return self.execute(context)


    def execute(self, context):
        if not self.refresh:
            return {'PASS_THROUGH'}

        undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False

        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        obj = context.active_object

        if self.random_seed:
            use_random_seed(self.random_seed)

        points = bounce_spline(obj,
                        self.bounce_number,
                        self.ang_noise,
                        self.offset,
                        self.extra,
                        self.active_face)

        add_curve_object(points,
                        obj.matrix_world,
                        self.x_ray,
                        self.spline_type,
                        self.spline_resolution,
                        self.bevel,
                        self.bevel_res,
                        self.spline_random_radius)

        if self.auto_refresh is False:
            self.refresh = False

        context.user_preferences.edit.use_global_undo = undo
        return {'FINISHED'}


    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)

        row.prop(self, 'x_ray', toggle=True)
        row.separator()
        if self.auto_refresh is False:
            self.refresh = False
        elif self.auto_refresh is True:
            self.refresh = True
        row.prop(self, 'auto_refresh', toggle=True, icon='AUTO', text="")
        row.prop(self, 'refresh', toggle=True, icon='FILE_REFRESH', text="")
        row.separator()
        properties = row.operator('object.add_bounce_spline', text="Add New")
        col.separator()
        col = layout.column(align=True)
        row = col.row(align=True)
        col.prop(self, 'bounce_number')
        col.prop(self, 'ang_noise')
        col.prop(self, 'offset')
        col.prop(self, 'extra')
        col.prop(self, 'random_seed')
        col.separator()
        col.prop(self, 'active_face', toggle=False)
        col = layout.column(align=True)
        col.prop(self, 'spline_type')
        col.separator()
        col.prop(self, 'spline_resolution')
        col.prop(self, 'bevel')
        if self.spline_type == 'BEZIER':
            col.prop(self, 'spline_random_radius')
        col.prop(self, 'bevel_res')


# ------------------------------------------------------------
# Tools Panel > Misc
# ------------------------------------------------------------

class SplinePanel( bpy.types.Panel ):
    bl_space_type = "VIEW_3D"
    bl_context = "objectmode"
    bl_region_type = "TOOLS"
    bl_label = "Add Spline to Mesh"
    bl_category = "Create"
    bl_options = {'DEFAULT_CLOSED'}

    def draw( self, context ):
        scn = context.scene
        layout = self.layout
        col = self.layout.column()
        col.operator(SpiroFitSpline.bl_idname, icon="FORCE_MAGNETIC")
        col.operator(BounceSpline.bl_idname, icon="FORCE_HARMONIC")

# ------------------------------------------------------------ # icon="CURVE_DATA"
# Menu: Add > Curve >
# ------------------------------------------------------------

'''
def menu_func(self, context):
    self.layout.operator(SpiroFitSpline.bl_idname, icon="PLUGIN")
    self.layout.operator(BounceSpline.bl_idname, icon="PLUGIN")
'''

# ------------------------------------------------------------
# Register
# ------------------------------------------------------------

def register():
    bpy.utils.register_class(SpiroFitSpline)
    bpy.utils.register_class(BounceSpline)
    bpy.utils.register_class(SplinePanel)
    #bpy.types.INFO_MT_curve_add.append(menu_func)

def unregister():
    bpy.utils.unregister_class(SpiroFitSpline)
    bpy.utils.unregister_class(BounceSpline)
    bpy.utils.unregister_class(SplinePanel)
    #bpy.types.INFO_MT_curve_add.remove(menu_func)

if __name__ == "__main__":
    register()
