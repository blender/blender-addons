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

# <pep8 compliant>

# Script copyright (C) Blender Foundation 2012

def cell_fracture_objects(context, obj, method={'OTHER'}):

    #assert(method in {'OTHER', 'PARTICLES'})
    
    from . import fracture_cell_calc

    points = []

    if 'PARTICLES' in method:
        points.extend([p.location.copy()
                         for psys in obj.particle_systems
                         for p in psys.particles])

    if 'OTHER' in method:
        for obj_other in context.selected_objects:
            if obj_other.type == 'MESH':
                mesh = obj_other.data
                matrix = obj_other.matrix_world.copy()
                points.extend([matrix * v.co for v in mesh.vertices])


    mesh = obj.data
    matrix = obj.matrix_world.copy()
    verts = [matrix * v.co for v in mesh.vertices]

    cells = fracture_cell_calc.points_as_bmesh_cells(verts, points)
    
    # some hacks here :S
    import bmesh

    scene = context.scene
    cell_name = obj.name + "_cell"
    
    objects = []
    
    for center_point, cell_points in cells:
        mesh = bpy.data.meshes.new(name=cell_name)
        obj_cell = bpy.data.objects.new(name=cell_name, object_data=mesh)
        scene.objects.link(obj_cell)
        # scene.objects.active = obj_cell
        obj_cell.location = center_point

        # create the convex hulls
        bm = bmesh.new()
        for i, co in enumerate(cell_points):
            bm_vert = bm.verts.new(co)
            bm_vert.tag = True

        import mathutils
        bm.transform(mathutils.Matrix.Translation((+100.0, +100.0, +100.0))) # BUG IN BLENDER
        bmesh.ops.remove_doubles(bm, {'TAG'}, 0.0001)
        bmesh.ops.convex_hull(bm, {'TAG'})
        bm.transform(mathutils.Matrix.Translation((-100.0, -100.0, -100.0))) # BUG IN BLENDER
        
        bm.to_mesh(me)
        bm.free()

        objects.append(obj_cell)
    
    return obj_cell




def cell_fracture_boolean(context, obj, objects):
    scene = context.scene
    for obj_cell in objects:
        mod = obj_cell.modifiers.new(type='BOOLEAN')
        mod.object = boolobj
        mod.operation = 'INTERSECT'
        
        mesh_new = obj_cell.to_mesh(scene, apply_modifiers=True)
        mesh_old = obj_cell.data
        obj_cell.data = mesh_new

        # remove if not valid
        if not mesh_old.users:
            bpy.data.meshes.remove(mesh_old)
        if not mesh_new.verts:
            scene.objects.unlink(obj_cell)
            if not obj_cell.users:
                bpy.data.objects.remove(obj_cell)
                if not mesh_new.users:
                    bpy.data.meshes.remove(mesh_old)
        obj_cell.select = True

