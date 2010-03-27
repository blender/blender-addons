# add_mesh_gem.py Copyright (C) 2010, Dreampainter
#
# add gem to the blender 2.50 add->mesh menu
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_addon_info = {
    'name': 'Add Mesh: Gem',
    'author': 'Dreampainter',
    'version': '1.1',
    'blender': (2, 5, 3),
    'location': 'View3D > Add > Mesh ',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/Add_Mesh/Add_Gem',
    'category': 'Add Mesh'}


import bpy


# Stores the values of a list of properties in a
# property group (named like the operator) in the object.
# Always replaces any existing property group with the same name!
# @todo: Should we do this in EDIT Mode? Sounds dangerous.
def obj_store_recall_properties(ob, op, prop_list):
    if ob and op and prop_list:
        #print("Storing recall data for operator: " + op.bl_idname)  # DEBUG

        # Store new recall properties.
        prop_list['recall_op'] = op.bl_idname
        ob['recall'] = prop_list


# Apply view rotation to objects if "Align To" for new objects
# was set to "VIEW" in the User Preference.
def apply_view_rotation(context, ob):
    align = bpy.context.user_preferences.edit.object_align

    if (context.space_data.type == 'VIEW_3D'
        and align == 'VIEW'):
            view3d = context.space_data
            region = view3d.region_3d
            viewMatrix = region.view_matrix
            rot = viewMatrix.rotation_part()
            ob.rotation_euler = rot.invert().to_euler()


def createObject(context, verts, faces, name, edit):
    '''Creates Meshes & Objects for the given lists of vertices and faces.'''

    scene = context.scene

    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Add the geometry to the mesh.
    #mesh.add_geometry(len(verts), 0, len(faces))
    #mesh.verts.foreach_set("co", unpack_list(verts))
    #mesh.faces.foreach_set("verts_raw", unpack_face_list(faces))

    # To quote the documentation:
    # "Make a mesh from a list of verts/edges/faces Until we have a nicer
    #  way to make geometry, use this."
    # http://www.blender.org/documentation/250PythonDoc/
    # bpy.types.Mesh.html#bpy.types.Mesh.from_pydata
    mesh.from_pydata(verts, [], faces)

    # Deselect all objects.
    bpy.ops.object.select_all(action='DESELECT')

    # Update mesh geometry after adding stuff.
    mesh.update()

    if edit:
        # Recreate geometry of existing object
        obj_act = context.active_object
        ob_new = obj_act

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')

        ob_new.data = mesh

        ob_new.selected = True

    else:
        # Create new object
        ob_new = bpy.data.objects.new(name, mesh)

        # Link new object to the given scene and select it.
        scene.objects.link(ob_new)
        ob_new.selected = True

        # Place the object at the 3D cursor location.
        ob_new.location = scene.cursor_location

        obj_act = scene.objects.active

        apply_view_rotation(context, ob_new)

    if obj_act and obj_act.mode == 'EDIT':
        if not edit:
            # We are in EditMode, switch to ObjectMode.
            bpy.ops.object.mode_set(mode='OBJECT')

            # Select the active object as well.
            obj_act.selected = True

            # Apply location of new object.
            scene.update()

            # Join new object into the active.
            bpy.ops.object.join()

            # Switching back to EditMode.
            bpy.ops.object.mode_set(mode='EDIT')

    else:
        # We are in ObjectMode.
        # Make the new object the active one.
        scene.objects.active = ob_new

    return ob_new


def add_gem(r1, r2, seg, h1, h2):
    """
    r1 = pavillion radius
    r2 = crown radius
    seg = number of segments
    h1 = pavillion height
    h2 = crown height
    Generates the vertices and faces of the gem
    """
    from math import cos, sin, pi

    verts = []

    tot_verts = 2 + 4 * seg
    tot_faces = 6 * seg
    a = 2 * pi / seg               # angle between segments
    offset = a / 2.0               # middle between segments

    r3 = ((r1 + r2) / 2.0) / cos(offset)  # middle of crown
    r4 = (r1 / 2.0) / cos(offset)  # middle of pavillion
    h3 = h2 / 2.0                  # middle of crown height
    h4 = -h1 / 2.0                 # middle of pavillion height

    verts.append((0, 0, -h1))
    verts.append((0, 0, h2))

    for i in range(seg):
        s1 = sin(i * a)
        s2 = sin(offset + i * a)
        c1 = cos(i * a)
        c2 = cos(offset + i * a)
        verts.append((r4 * s1, r4 * c1, h4))
        verts.append((r1 * s2, r1 * c2, 0))
        verts.append((r3 * s1, r3 * c1, h3))
        verts.append((r2 * s2, r2 * c2, h2))

    faces = []

    for index in range(seg):
        i = index * 4
        j = ((index + 1) % seg) * 4
        faces.append([0, j + 2, i + 3, i + 2])
        faces.append([i + 3, j + 2, j + 3, i + 3])
        faces.append([i + 3, j + 3, j + 4, i + 3])
        faces.append([i + 3, j + 4, i + 5, i + 4])
        faces.append([i + 5, j + 4, j + 5, i + 5])
        faces.append([i + 5, j + 5, 1, i + 5])

    return verts, faces, tot_verts, tot_faces


from bpy.props import IntProperty, FloatProperty, BoolProperty


class AddGem(bpy.types.Operator):
    """Add a diamond gem"""
    bl_idname = "mesh.primitive_gem_add"
    bl_label = "Add Gem"
    bl_description = "Create an offset faceted gem."
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name="",
        description="",
        default=False,
        options={'HIDDEN'})
    segments = IntProperty(name="Segments",
        description="Longitudial segmentation",
        min=3,
        max=265,
        default=8,)
    pav_radius = FloatProperty(name="Radius",
           description="Radius of the gem",
           min=0.01,
           max=100.0,
           default=1.0)
    crown_radius = FloatProperty(name="Table Radius",
           description="Radius of the table(top).",
           min=0.01,
           max=100.0,
           default=0.6)
    crown_height = FloatProperty(name="Table height",
           description="Height of the top half.",
           min=0.01,
           max=100.0,
           default=0.35)
    pav_height = FloatProperty(name="Pavillion height",
           description="Height of bottom half.",
           min=0.01,
           max=100.0,
           default=0.8)

    def execute(self, context):
        props = self.properties

        # create mesh
        verts, faces, nV, nF = add_gem(self.properties.pav_radius,
               props.crown_radius,
               props.segments,
               props.pav_height,
               props.crown_height)

        obj = createObject(context, verts, faces, "Gem", props.edit)

        # Store 'recall' properties in the object.
        recall_prop_list = {
            "edit": True,
            "segments": props.segments,
            "pav_radius": props.pav_radius,
            "crown_radius": props.crown_radius,
            "pav_height": props.pav_height,
            "crown_height": props.crown_height}
        obj_store_recall_properties(obj, self, recall_prop_list)

        return {'FINISHED'}

# register all operators and panels


menu_func = (lambda self, context: self.layout.operator(AddGem.bl_idname,
                                        text="Gem", icon='PLUGIN'))


def register():
    bpy.types.register(AddGem)
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.unregister(AddGem)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)
    # Remove "Gem" menu from the "Add Mesh" menu.
    #space_info.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
