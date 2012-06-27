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


def points_as_bmesh_cells(verts, points):
    import mathutils
    from mathutils import Vector

    cells = []

    sortedVoronoiPoints = [p for p in points]
    plane_indices = []
    vertices = []

    # there are many ways we could get planes - convex hull for eg
    # but it ends up fastest if we just use bounding box
    if 1:
        xa = [v[0] for v in verts]
        ya = [v[1] for v in verts]
        za = [v[2] for v in verts]
        
        xmin, xmax = min(xa), max(xa)
        ymin, ymax = min(ya), max(ya)
        zmin, zmax = min(za), max(za)
        convexPlanes = [
            Vector((+1.0, 0.0, 0.0, -abs(xmax))),
            Vector((-1.0, 0.0, 0.0, -abs(xmin))),
            Vector((0.0, +1.0, 0.0, -abs(ymax))),
            Vector((0.0, -1.0, 0.0, -abs(ymin))),
            Vector((0.0, 0.0, +1.0, -abs(zmax))),
            Vector((0.0, 0.0, -1.0, -abs(zmin))),
            ]

    for i, curVoronoiPoint in enumerate(points):
        planes = [None] * len(convexPlanes)
        for j in range(len(convexPlanes)):
            planes[j] = convexPlanes[j].copy()
            planes[j][3] += planes[j].xyz.dot(curVoronoiPoint)
        maxDistance = 10000000000.0  # a big value!

        sortedVoronoiPoints.sort(key=lambda p: (p - curVoronoiPoint).length_squared)

        for j in range(1, len(points)):
            normal = sortedVoronoiPoints[j] - curVoronoiPoint
            nlength = normal.length
            if nlength > maxDistance:
                break

            plane = normal.normalized()
            plane.resize_4d()
            plane[3] = -nlength / 2.0
            planes.append(plane)
            
            vertices[:], plane_indices[:] = mathutils.geometry.points_in_planes(planes)
            if len(vertices) == 0:
                break

            if len(plane_indices) != len(planes):
                planes[:] = [planes[k] for k in plane_indices]

            maxDistance = vertices[0].length
            for k in range(1, len(vertices)):
                distance = vertices[k].length
                if maxDistance < distance:
                    maxDistance = distance
            maxDistance *= 2.0

        if len(vertices) == 0:
            continue

        cells.append((curVoronoiPoint, vertices[:]))
        vertices[:] = []

    return cells


# --- run ---
# b ~/phys.blend -b --python cell_test.py

def main():
    import bpy
    import sys
    #points = [v.co.copy() for v in bpy.data.objects["points"].data.vertices]

    sys.path.append("/media/data/blender-svn/blender-phymec/phymec_tools")

    import phymec_tools as pt
    pt.voro_add_points(100)
    #pt.physics_voronoi_shatter(pt.voro_points(particles=True),True)
    #return

    points = []
    points.extend([p.location for p in bpy.data.objects["verts"].particle_systems[0].particles])

    verts = [v.co.copy() for v in bpy.data.objects["verts"].data.vertices]

    cells = points_as_bmesh_cells(verts, points)
    for cent, cell in cells:
        me = bpy.data.meshes.new(name="Blah")
        ob = bpy.data.objects.new(name="Blah", object_data=me)
        bpy.context.scene.objects.link(ob)
        bpy.context.scene.objects.active = ob
        ob.location = cent

        # create the convex hulls
        import bmesh
        bm = bmesh.new()
        for i, v in enumerate(cell):
            bm_vert = bm.verts.new(v)
            bm_vert.tag = True
        
        import mathutils
        bm.transform(mathutils.Matrix.Translation((+100.0, +100.0, +100.0))) # BUG IN BLENDER
        bmesh.ops.remove_doubles(bm, {'TAG'}, 0.0001)
        bmesh.ops.convex_hull(bm, {'TAG'})
        bm.transform(mathutils.Matrix.Translation((-100.0, -100.0, -100.0))) # BUG IN BLENDER
        
        bm.to_mesh(me)
        bm.free()

    print(len(cells))


if __name__ == "__main__":
    import time
    t = time.time()
    main()

    print("%.5f sec" % (time.time() - t))
