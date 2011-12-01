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
    "name": "PDB Atomic Blender",
    "description": "Loading and manipulating atoms from PDB files",
    "author": "Clemens Barth",
    "version": (1,0),
    "blender": (2,6),
    "api": 31236,
    "location": "File -> Import -> PDB (.pdb), Panel: View 3D - Tools",
    "warning": "",
    "wiki_url": "http://development.root-1.de/Atomic_Blender.php",
    "tracker_url": "http://projects.blender.org/tracker/"
                   "index.php?func=detail&aid=29226&group_id=153&atid=468",
    "category": "Import-Export"
}


import bpy
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper
from bpy.props import (StringProperty,
                       BoolProperty,
                       EnumProperty,
                       IntProperty,
                       FloatProperty)


# TODO, allow reload
from . import import_pdb

# -----------------------------------------------------------------------------
#                                                                           GUI

# The panel, which is loaded after the file has been
# chosen via the menu 'File -> Import'
class CLASS_atom_pdb_panel(Panel):
    bl_label       = "PDB - Atomic Blender"
    #bl_space_type  = "PROPERTIES"
    #bl_region_type = "WINDOW"
    #bl_context     = "physics"
    # This could be also an option ... :
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOL_PROPS"

    # This 'poll thing' has taken 3 hours of a hard search and understanding.
    # I explain it in the following from my point of view:
    #
    # Before this class is entirely treaten (here: drawing the panel) the
    # poll method is called first. Basically, some conditions are
    # checked before other things in the class are done afterwards. If a
    # condition is not valid, one returns 'False' such that nothing further
    # is done. 'True' means: 'Go on'
    #
    # In the case here, it is verified if the ATOM_PDB_FILEPATH variable contains
    # a name. If not - and this is the case directly after having started the
    # script - the panel does not appear because 'False' is returned. However,
    # as soon as a file has been chosen, the panel appears because
    # ATOM_PDB_FILEPATH contains a name.
    #
    # Please, correct me if I'm wrong.
    @classmethod
    def poll(self, context):
        if import_pdb.ATOM_PDB_FILEPATH == "":
            return False
        else:
            return True

    def draw(self, context):
        layout = self.layout
        scn    = bpy.context.scene

        row = layout.row()
        row.label(text="Custom data file")
        row = layout.row()
        col = row.column()
        col.prop(scn, "atom_pdb_datafile")
        col.operator("atom_pdb.datafile_apply")
        row = layout.row()
        col = row.column(align=True)
        col.prop(scn, "atom_pdb_PDB_file")

        layout.separator()

        row = layout.row()
        col = row.column(align=True)
        col.prop(scn, "use_atom_pdb_mesh")
        col.prop(scn, "atom_pdb_mesh_azimuth")
        col.prop(scn, "atom_pdb_mesh_zenith")


        col = row.column(align=True)
        col.label(text="Scaling factors")
        col.prop(scn, "atom_pdb_scale_ballradius")
        col.prop(scn, "atom_pdb_scale_distances")
        row = layout.row()
        col = row.column()
        col.prop(scn, "use_atom_pdb_sticks")
        col = row.column(align=True)
        col.prop(scn, "atom_pdb_sticks_sectors")
        col.prop(scn, "atom_pdb_sticks_radius")

        row = layout.row()
        row.prop(scn, "use_atom_pdb_center")

        row = layout.row()
        col = row.column()
        col.prop(scn, "use_atom_pdb_cam")
        col.prop(scn, "use_atom_pdb_lamp")
        col = row.column()
        col.operator("atom_pdb.button_reload")

        # TODO, use lanel() instead
        col.prop(scn, "atom_pdb_number_atoms")

        layout.separator()

        row = layout.row()
        row.operator("atom_pdb.button_distance")
        row.prop(scn, "atom_pdb_distance")
        layout.separator()

        row = layout.row()
        row.label(text="All changes concern:")
        row = layout.row()
        row.prop(scn, "atom_pdb_radius_how")

        row = layout.row()
        row.label(text="1. Change type of radii")
        row = layout.row()
        row.prop(scn, "atom_pdb_radius_type")

        row = layout.row()
        row.label(text="2. Change atom radii in pm")
        row = layout.row()
        row.prop(scn, "atom_pdb_radius_pm_name")
        row = layout.row()
        row.prop(scn, "atom_pdb_radius_pm")

        row = layout.row()
        row.label(text="3. Change atom radii by scale")
        row = layout.row()
        col = row.column()
        col.prop(scn, "atom_pdb_radius_all")
        col = row.column(align=True)
        col.operator( "atom_pdb.radius_all_bigger" )
        col.operator( "atom_pdb.radius_all_smaller" )

        if bpy.context.mode == 'EDIT_MESH':

            layout.separator()
            row = layout.row()
            row.operator( "atom_pdb.separate_atom" )


class CLASS_atom_pdb_IO(bpy.types.PropertyGroup):

    def Callback_radius_type(self, context):
        scnn = bpy.context.scene
        import_pdb.DEF_atom_pdb_radius_type(
                scnn.atom_pdb_radius_type,
                scnn.atom_pdb_radius_how,
                )

    def Callback_radius_pm(self, context):
        scnn = bpy.context.scene
        import_pdb.DEF_atom_pdb_radius_pm(
                scnn.atom_pdb_radius_pm_name,
                scnn.atom_pdb_radius_pm,
                scnn.atom_pdb_radius_how,
                )

    # In the file dialog window
    scn = bpy.types.Scene
    scn.use_atom_pdb_cam = BoolProperty(
        name="Camera", default=False,
        description="Do you need a camera?")
    scn.use_atom_pdb_lamp = BoolProperty(
        name="Lamp", default=False,
        description = "Do you need a lamp?")
    scn.use_atom_pdb_mesh = BoolProperty(
        name = "Mesh balls", default=False,
        description = "Do you want to use mesh balls instead of NURBS?")
    scn.atom_pdb_mesh_azimuth = IntProperty(
        name = "Azimuth", default=32, min=0,
        description = "Number of sectors (azimuth)")
    scn.atom_pdb_mesh_zenith = IntProperty(
        name = "Zenith", default=32, min=0,
        description = "Number of sectors (zenith)")
    scn.atom_pdb_scale_ballradius = FloatProperty(
        name = "Balls", default=1.0, min=0.0,
        description = "Scale factor for all atom radii")
    scn.atom_pdb_scale_distances = FloatProperty (
        name = "Distances", default=1.0, min=0.0,
        description = "Scale factor for all distances")
    scn.use_atom_pdb_center = BoolProperty(
        name = "Object to origin", default=True,
        description = "Shall the object first put into the global origin "
        "before applying the offsets on the left?")
    scn.use_atom_pdb_sticks = BoolProperty(
        name="Use sticks", default=False,
        description="Do you want to display also the sticks?")
    scn.atom_pdb_sticks_sectors = IntProperty(
        name = "Sector", default=20, min=0,
        description="Number of sectors of a stick")
    scn.atom_pdb_sticks_radius = FloatProperty(
        name = "Radius", default=0.1, min=0.0,
        description ="Radius of a stick")
    scn.atom_pdb_atomradius = EnumProperty(
        name="Type of radius",
        description="Choose type of atom radius",
        items=(('0', "Pre-defined", "Use pre-defined radius"),
               ('1', "Atomic", "Use atomic radius"),
               ('2', "van der Waals", "Use van der Waals radius")),
               default='0',)

    # In the panel
    scn.atom_pdb_datafile = StringProperty(
        name = "", description="Path to your custom data file",
        maxlen = 256, default = "", subtype='FILE_PATH')
    scn.atom_pdb_PDB_file = StringProperty(
        name = "Path to file", default="",
        description = "Path of the PDB file")
    # TODO, remove this property, its used for display only!
    scn.atom_pdb_number_atoms = StringProperty(name="",
        default="Number", description = "This output shows "
        "the number of atoms which have been loaded")
    scn.atom_pdb_distance = StringProperty(
        name="", default="Distance (A)",
        description="Distance of 2 objects in Angstrom")
    scn.atom_pdb_radius_how = EnumProperty(
        name="",
        description="Which objects shall be modified?",
        items=(('ALL_ACTIVE',"all active objects", "in the current layer"),
               ('ALL_IN_LAYER',"all"," in active layer(s)")),
               default='ALL_ACTIVE',)
    scn.atom_pdb_radius_type = EnumProperty(
        name="Type",
        description="Which type of atom radii?",
        items=(('0',"predefined", "Use pre-defined radii"),
               ('1',"atomic", "Use atomic radii"),
               ('2',"van der Waals","Use van der Waals radii")),
               default='0',update=Callback_radius_type)
    scn.atom_pdb_radius_pm_name = StringProperty(
        name="", default="Atom name",
        description="Put in the name of the atom (e.g. Hydrogen)")
    scn.atom_pdb_radius_pm = FloatProperty(
        name="", default=100.0, min=0.0,
        description="Put in the radius of the atom (in pm)",
        update=Callback_radius_pm)
    scn.atom_pdb_radius_all = FloatProperty(
        name="Scale", default = 1.05, min=1.0,
        description="Put in the scale factor")


# Button loading a custom data file
class CLASS_atom_pdb_datafile_apply(Operator):
    bl_idname = "atom_pdb.datafile_apply"
    bl_label = "Apply"
    bl_description = "Use color and radii values stored in a custom file"

    def execute(self, context):
        scn    = bpy.context.scene

        if scn.atom_pdb_datafile == "":
            return {'FINISHED'}

        import_pdb.DEF_atom_pdb_custom_datafile(scn.atom_pdb_datafile)

        # TODO, move this into 'import_pdb' and call the function
        for obj in bpy.context.selected_objects:
            if len(obj.children) != 0:
                child = obj.children[0]
                if child.type == "SURFACE" or child.type  == "MESH":
                    for element in import_pdb.ATOM_PDB_ELEMENTS:
                        if element.name in obj.name:
                            child.scale = (element.radii[0],) * 3
                            child.active_material.diffuse_color = element.color
            else:
                if obj.type == "SURFACE" or obj.type == "MESH":
                    for element in import_pdb.ATOM_PDB_ELEMENTS:
                        if element.name in obj.name:
                            obj.scale = (element.radii[0],) * 3
                            obj.active_material.diffuse_color = element.color

        return {'FINISHED'}


# Button for measuring the distance of the active objects
class CLASS_atom_pdb_separate_atom(Operator):
    bl_idname = "atom_pdb.separate_atom"
    bl_label = "Separate atom"
    bl_description = "Separate the atom you have chosen"

    def execute(self, context):
        scn    = bpy.context.scene

        # Get first all important properties from the atom which the user
        # has chosen: location, color, scale
        obj = bpy.context.edit_object
        name = obj.name
        loc_obj_vec = obj.location
        scale = obj.children[0].scale
        material = obj.children[0].active_material

        # Separate the vertex from the main mesh and create a new mesh.
        bpy.ops.mesh.separate()
        new_object = bpy.context.scene.objects[0]
        # Keep in mind the coordinates <= We only need this
        loc_vec = new_object.data.vertices[0].co

        # And now, switch to the OBJECT mode such that we can ...
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        # ... delete the new mesh including the separated vertex
        bpy.ops.object.select_all(action='DESELECT')
        new_object.select = True
        bpy.ops.object.delete()  # TODO, use scene.objects.unlink()

        # Create a new atom/vacancy at the position of the old atom
        current_layers=bpy.context.scene.layers

        if "Vacancy" not in name:
            if scn.use_atom_pdb_mesh == False:
                bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                                    view_align=False, enter_editmode=False,
                                    location=loc_vec+loc_obj_vec,
                                    rotation=(0.0, 0.0, 0.0),
                                    layers=current_layers)
            else:
                bpy.ops.mesh.primitive_uv_sphere_add(
                                segments=scn.atom_pdb_mesh_azimuth,
                                ring_count=scn.atom_pdb_mesh_zenith,
                                size=1, view_align=False, enter_editmode=False,
                                location=loc_vec+loc_obj_vec,
                                rotation=(0, 0, 0),
                                layers=current_layers)
        else:
            bpy.ops.mesh.primitive_cube_add(
                               view_align=False, enter_editmode=False,
                               location=loc_vec+loc_obj_vec,
                               rotation=(0.0, 0.0, 0.0),
                               layers=current_layers)

        new_atom = bpy.context.scene.objects.active
        # Scale, material and name it.
        new_atom.scale = scale
        new_atom.active_material = material
        new_atom.name = name + "_sep"

        # Switch back into the 'Edit mode' because we would like to seprate
        # other atoms may be (more convinient)
        new_atom.select = False
        obj.select = True
        bpy.context.scene.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        return {'FINISHED'}


# Button for measuring the distance of the active objects
class CLASS_atom_pdb_distance_button(Operator):
    bl_idname = "atom_pdb.button_distance"
    bl_label = "Measure ..."
    bl_description = "Measure the distance between two objects"

    def execute(self, context):
        scn    = bpy.context.scene
        dist   = import_pdb.DEF_atom_pdb_distance()

        if dist != "N.A.":
           # The string length is cut, 3 digits after the first 3 digits
           # after the '.'. Append also "Angstrom".
           # Remember: 1 Angstrom = 10^(-10) m
           pos    = str.find(dist, ".")
           dist   = dist[:pos+4]
           dist   = dist + " A"

        # Put the distance into the string of the output field.
        scn.atom_pdb_distance = dist
        return {'FINISHED'}


# Button for increasing the radii of all atoms
class CLASS_atom_pdb_radius_all_bigger_button(Operator):
    bl_idname = "atom_pdb.radius_all_bigger"
    bl_label = "Bigger ..."
    bl_description = "Increase the radii of the atoms"

    def execute(self, context):
        scn = bpy.context.scene
        import_pdb.DEF_atom_pdb_radius_all(
                scn.atom_pdb_radius_all,
                scn.atom_pdb_radius_how,
                )
        return {'FINISHED'}


# Button for decreasing the radii of all atoms
class CLASS_atom_pdb_radius_all_smaller_button(Operator):
    bl_idname = "atom_pdb.radius_all_smaller"
    bl_label = "Smaller ..."
    bl_description = "Decrease the radii of the atoms"

    def execute(self, context):
        scn = bpy.context.scene
        import_pdb.DEF_atom_pdb_radius_all(
                1.0/scn.atom_pdb_radius_all,
                scn.atom_pdb_radius_how,
                )
        return {'FINISHED'}


# The button for loading the atoms and creating the scene
class CLASS_atom_pdb_load_button(Operator):
    bl_idname = "atom_pdb.button_reload"
    bl_label = "RELOAD"
    bl_description = "Load the structure again"

    def execute(self, context):
        scn = bpy.context.scene

        azimuth    = scn.atom_pdb_mesh_azimuth
        zenith     = scn.atom_pdb_mesh_zenith
        bradius    = scn.atom_pdb_scale_ballradius
        bdistance  = scn.atom_pdb_scale_distances
        radiustype = scn.atom_pdb_atomradius
        center     = scn.use_atom_pdb_center
        sticks     = scn.use_atom_pdb_sticks
        ssector    = scn.atom_pdb_sticks_sectors
        sradius    = scn.atom_pdb_sticks_radius
        cam        = scn.use_atom_pdb_cam
        lamp       = scn.use_atom_pdb_lamp
        mesh       = scn.use_atom_pdb_mesh
        datafile   = scn.atom_pdb_datafile

        # Execute main routine an other time ... from the panel
        atom_number = import_pdb.DEF_atom_pdb_main(
                mesh, azimuth, zenith, bradius,
                radiustype, bdistance, sticks,
                ssector, sradius, center, cam, lamp, datafile,
                )
        scn.atom_pdb_number_atoms = str(atom_number) + " atoms"

        return {'FINISHED'}


# This is the class for the file dialog.
class ImportPDB(Operator, ImportHelper):
    bl_idname = "import_mesh.pdb"
    bl_label  = "Import Protein Data Bank (*.pdb)"

    filename_ext = ".pdb"
    filter_glob  = StringProperty(default="*.pdb", options={'HIDDEN'},)

    def draw(self, context):
        layout = self.layout
        scn = bpy.context.scene

        row = layout.row()
        row.prop(scn, "use_atom_pdb_cam")
        row.prop(scn, "use_atom_pdb_lamp")
        row = layout.row()
        col = row.column()
        col.prop(scn, "use_atom_pdb_mesh")
        col = row.column(align=True)
        col.prop(scn, "atom_pdb_mesh_azimuth")
        col.prop(scn, "atom_pdb_mesh_zenith")

        row = layout.row()
        col = row.column()
        col.label(text="Scaling factors")
        col = row.column(align=True)
        col.prop(scn, "atom_pdb_scale_ballradius")
        col.prop(scn, "atom_pdb_scale_distances")
        row = layout.row()
        col = row.column()
        col.prop(scn, "use_atom_pdb_sticks")
        col = row.column(align=True)
        col.prop(scn, "atom_pdb_sticks_sectors")
        col.prop(scn, "atom_pdb_sticks_radius")

        row = layout.row()
        row.prop(scn, "use_atom_pdb_center")

        row = layout.row()
        row.prop(scn, "atom_pdb_atomradius")

    def execute(self, context):
        scn = bpy.context.scene

        # This is in order to solve this strange 'relative path' thing.
        import_pdb.ATOM_PDB_FILEPATH = bpy.path.abspath(self.filepath)

        scn.atom_pdb_PDB_file = import_pdb.ATOM_PDB_FILEPATH

        azimuth    = scn.atom_pdb_mesh_azimuth
        zenith     = scn.atom_pdb_mesh_zenith
        bradius    = scn.atom_pdb_scale_ballradius
        bdistance  = scn.atom_pdb_scale_distances
        radiustype = scn.atom_pdb_atomradius
        center     = scn.use_atom_pdb_center
        sticks     = scn.use_atom_pdb_sticks
        ssector    = scn.atom_pdb_sticks_sectors
        sradius    = scn.atom_pdb_sticks_radius
        cam        = scn.use_atom_pdb_cam
        lamp       = scn.use_atom_pdb_lamp
        mesh       = scn.use_atom_pdb_mesh
        datafile   = scn.atom_pdb_datafile

        # Execute main routine
        atom_number = import_pdb.DEF_atom_pdb_main(
                mesh, azimuth, zenith, bradius,
                radiustype, bdistance, sticks,
                ssector, sradius, center, cam, lamp, datafile)

        scn.atom_pdb_number_atoms = str(atom_number) + " atoms"

        return {'FINISHED'}


# The entry into the menu 'file -> import'
def menu_func(self, context):
    self.layout.operator(ImportPDB.bl_idname, text="Protein Data Bank (.pdb)")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == "__main__":

    register()
