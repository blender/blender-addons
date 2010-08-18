import bpy


def create_and_link_mesh(name, faces, points):
    '''
    Create a blender mesh and object called name from a list of
    *points* and *faces* and link it in the current scene.
    '''

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], faces)

    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.objects.link(ob)

    # update mesh to allow proper display
    mesh.update()


def faces_from_mesh(ob, apply_modifier=False, triangulate=True):
    '''
    From an object, return a generator over a list of faces.

    Each faces is a list of his vertexes. Each vertex is a tuple of
    his coordinate.

    apply_modifier
        Apply the preview modifier to the returned liste

    triangulate
        Split the quad into two triangles
    '''

    # get the modifiers
    mesh = ob.create_mesh(bpy.context.scene,
                          True, "PREVIEW") if apply_modifier else ob.data

    def iter_face_index():
        '''
        From a list of faces, return the face triangulated if needed.
        '''
        for face in mesh.faces:
            if triangulate and len(face.vertices) == 4:
                yield face.vertices[:3]
                yield face.vertices[2:] + [face.vertices[0]]
            else:
                yield list(face.vertices)

    return ([tuple(ob.matrix_world * mesh.vertices[index].co)
             for index in indexes] for indexes in iter_face_index())
