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


# -----------------------------------------------------------------------------
# copied from bullet 2.8
def areVerticesBehindPlane(planeNormal, vertices, margin):
    planeNormal_xyz_dot = planeNormal.xyz.dot  # speedup
    for i, N1 in enumerate(vertices):
        dist = planeNormal_xyz_dot(N1) + planeNormal[3] - margin
        if dist > 0.0:
            return False
    return True


def notExist(planeEquation, planeEquations):
    for N1 in planeEquations:
        if planeEquation.dot(N1) > 0.999:
            return False
    return True


def getPlaneEquationsFromVertices(vertices):
    planeEquationsOut = []
    for i, N1 in enumerate(vertices):
        for j in range(i + 1, len(vertices)):
            N2 = vertices[j]
            for k in range(j + 1, len(vertices)):
                N3 = vertices[k]
                # btVector3 planeEquation,edge0,edge1;
                edge0 = N2 - N1
                edge1 = N3 - N1
                normalSign = 1.0
                for normalSign in (1.0, -1.0):
                    planeEquation = normalSign * edge0.cross(edge1)
                    if planeEquation.length_squared > 0.0001:
                        planeEquation.normalize()
                        if notExist(planeEquation, planeEquationsOut):
                            planeEquation.resize_4d()
                            planeEquation[3] = -planeEquation.xyz.dot(N1)

                            # check if inside, and replace supportingVertexOut if needed
                            if areVerticesBehindPlane(planeEquation, vertices, 0.01):
                                planeEquationsOut.append(planeEquation)
    return planeEquationsOut

# end bullet copy
# ---------------

T = [0.0]
# phymecutils.c
def getVerticesInsidePlanes(planes, verticesOut, planeIndicesOut):
    if 1:
        import mathutils
        r = mathutils.geometry.points_in_planes(planes)
        verticesOut[:] = r[0]
        #planeIndicesOut[:] = r[1]
        planeIndicesOut.clear()
        planeIndicesOut.update(set(r[1]))
        # print(verticesOut)
        return
    
    # populates verticesOut
    # std::set<int>& planeIndicesOut
    # Based on btGeometryUtil.cpp (Gino van den Bergen / Erwin Coumans)
    tt = time.time()
    verticesOut[:] = []
    planeIndicesOut.clear()

    for i in range(len(planes)):
        N1 = planes[i]
        for j in range(i + 1, len(planes)):
            N2 = planes[j]
            n1n2 = N1.xyz.cross(N2.xyz)
            if n1n2.length_squared > 0.0001:
                for k in range(j + 1, len(planes)):
                    N3 = planes[k]
                    n2n3 = N2.xyz.cross(N3.xyz)
                    n3n1 = N3.xyz.cross(N1.xyz)
                    if (n2n3.length_squared > 0.0001) and (n3n1.length_squared > 0.0001):
                        quotient = N1.xyz.dot(n2n3)
                        if abs(quotient) > 0.0001:
                            potentialVertex = (n2n3 * N1[3] + n3n1 * N2[3] + n1n2 * N3[3]) * (-1.0 / quotient)

                            ok = True
                            for l in range(len(planes)):
                                NP = planes[l]
                                if NP.xyz.dot(potentialVertex) + NP[3] > 0.000001:
                                    ok = False
                                    break

                            if ok == True:
                                # vertex (three plane intersection) inside all planes
                                verticesOut.append(potentialVertex)
                                planeIndicesOut |= {i, j, k}
    T[0] += time.time() - tt


def points_as_bmesh_cells(verts, points):
    """Generator for bmesh hull"""

    cells = []

    sortedVoronoiPoints = [p for p in points]

    planeIndices = set()

    vertices = []

    # each convex hull is one bmesh
    if 0:
        convexPlanes = getPlaneEquationsFromVertices(verts)
    elif 0:
        # Faster for large meshes...
        convexPlanes = []

        # get the convex hull
        import bmesh
        bm = bmesh.new()
        for v in verts:
            bm_vert = bm.verts.new(v)
            bm_vert.tag = True
        bmesh.ops.convex_hull(bm, {'TAG'})

        # offset a tiny bit
        bm.normal_update()
        for v in bm.verts:
            v.co += v.normal * 0.01

        # collect the planes
        for f in bm.faces:
            v0, v1, v2 = [v.co for v in f.verts[0:3]]
            plane = (v1 - v0).cross(v2 - v0).normalized()
            plane.resize_4d()
            plane[3] = -plane.xyz.dot(v0)
            convexPlanes.append(plane)
        bm.free()
    elif 0:
        # get 4 planes
        xa = [v[0] for v in verts]
        ya = [v[1] for v in verts]
        za = [v[2] for v in verts]

        xr = min(xa), max(xa)
        yr = min(ya), max(ya)
        zr = min(za), max(za)

        verts_tmp = []
        from mathutils import Vector
        for xi in (0, 1):
            for yi in (0, 1):
                for zi in (0, 1):
                    verts_tmp.append(Vector((xr[xi], yr[yi], zr[zi])))

        convexPlanes = getPlaneEquationsFromVertices(verts_tmp)
        aaa = "\n".join(sorted([repr(v.to_tuple(5)).replace("-0.0", "0.0") for v in convexPlanes]))
        print(aaa)
    else:
        
        xa = [v[0] for v in verts]
        ya = [v[1] for v in verts]
        za = [v[2] for v in verts]
        
        xmin, xmax = min(xa), max(xa)
        ymin, ymax = min(ya), max(ya)
        zmin, zmax = min(za), max(za)
        from mathutils import Vector
        convexPlanes = [
            Vector((+1.0, 0.0, 0.0, -abs(xmax))),
            Vector((-1.0, 0.0, 0.0, -abs(xmin))),
            Vector((0.0, +1.0, 0.0, -abs(ymax))),
            Vector((0.0, -1.0, 0.0, -abs(ymin))),
            Vector((0.0, 0.0, +1.0, -abs(zmax))),
            Vector((0.0, 0.0, -1.0, -abs(zmin))),
            ]
        
        aaa = "\n".join(sorted([repr(v.to_tuple(5)) for v in convexPlanes]))
        print(aaa)

    for i, curVoronoiPoint in enumerate(points):
        planes = [None] * len(convexPlanes)
        for j in range(len(convexPlanes)):
            planes[j] = convexPlanes[j].copy()
            planes[j][3] += planes[j].xyz.dot(curVoronoiPoint)
        maxDistance = 10000000000.0  # a big value!

        sortedVoronoiPoints.sort(key=lambda p: (p - curVoronoiPoint).length_squared)
        # sortedVoronoiPoints.reverse()
        # XXX need to reverse?

        for j in range(1, len(points)):
            normal = sortedVoronoiPoints[j] - curVoronoiPoint
            nlength = normal.length
            if nlength > maxDistance:
                break

            plane = normal.normalized()
            plane.resize_4d()
            plane[3] = -nlength / 2.0
            planes.append(plane.copy())
            getVerticesInsidePlanes(planes, vertices, planeIndices)
            if len(vertices) == 0:
                break
            numPlaneIndices = len(planeIndices)
            if numPlaneIndices != len(planes):
                #'''
                planeIndicesIter = list(sorted(planeIndices))
                for k in range(numPlaneIndices):
                    if k != planeIndicesIter[k]:
                        planes[k] = planes[planeIndicesIter[k]].copy()
                planes[numPlaneIndices:] = []
                #'''
                #planes[:] = [planes[k] for k in planeIndices]

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


if __name__ == "__main__"
    import time
    t = time.time()
    main()

    print("%.5f sec" % (time.time() - t))
    print("%.5f aa" % T[0])
