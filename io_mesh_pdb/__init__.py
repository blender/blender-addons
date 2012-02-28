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
    "version": (1,2),
    "blender": (2,6),
    "api": 31236,
    "location": "File -> Import -> PDB (.pdb), Panel: View 3D - Tools",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Import-Export/PDB",
    "tracker_url": "http://projects.blender.org/tracker/"
                   "index.php?func=detail&aid=29226",
    "category": "Import-Export"
}

import bpy
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import (StringProperty,
                       BoolProperty,
                       EnumProperty,
                       IntProperty,
                       FloatProperty)


# TODO, allow reload
from . import import_pdb
from . import export_pdb


ATOM_PDB_ERROR = ""

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
    #bl_region_type = "TOOLS"
    bl_region_type = "TOOL_PROPS"

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
        row.label(text="Outputs and custom data file")

        box = layout.box()
        row = box.row()
        row.label(text="Custom data file")
        row = box.row()
        col = row.column()
        col.prop(scn, "atom_pdb_datafile")
        col.operator("atom_pdb.datafile_apply")
        row = box.row()
        col = row.column(align=True)
        col.prop(scn, "atom_pdb_PDB_file")

        row = layout.row()
        row.label(text="Reload structure")

        box = layout.box()
        row = box.row()
        col = row.column()
        col.prop(scn, "use_atom_pdb_mesh")
        col = row.column()
        col.label(text="Scaling factors")
        row = box.row()
        col = row.column(align=True)  
        col.active = scn.use_atom_pdb_mesh   
        col.prop(scn, "atom_pdb_mesh_azimuth")
        col.prop(scn, "atom_pdb_mesh_zenith")
        col = row.column(align=True)
        col.prop(scn, "atom_pdb_scale_ballradius")
        col.prop(scn, "atom_pdb_scale_distances")
        row = box.row()
        col = row.column()  
        col.prop(scn, "use_atom_pdb_sticks")
        row = box.row()        
        row.active = scn.use_atom_pdb_sticks
        col = row.column(align=True)
        col.prop(scn, "atom_pdb_sticks_sectors")
        col.prop(scn, "atom_pdb_sticks_radius")
        col = row.column(align=True)        
        col.prop(scn, "use_atom_pdb_sticks_color")        
        col.prop(scn, "use_atom_pdb_sticks_smooth")
        col.prop(scn, "use_atom_pdb_sticks_bonds")
        row = box.row()        
        row.active = scn.use_atom_pdb_sticks
        col = row.column(align=True)
        col = row.column(align=True)
        col.active = scn.use_atom_pdb_sticks and scn.use_atom_pdb_sticks_bonds 
        col.prop(scn, "atom_pdb_sticks_dist")        
        row = box.row()
        row.prop(scn, "use_atom_pdb_center")
        row = box.row()
        col = row.column()
        col.prop(scn, "use_atom_pdb_cam")
        col.prop(scn, "use_atom_pdb_lamp")
        col = row.column()
        col.operator("atom_pdb.button_reload")
        col.prop(scn, "atom_pdb_number_atoms")
        row = box.row()
        row.operator("atom_pdb.button_distance")
        row.prop(scn, "atom_pdb_distance")

        row = layout.row()
        row.label(text="Modify atom radii")
        
        box = layout.box()
        row = box.row()
        row.label(text="All changes concern:")
        row = box.row()
        row.prop(scn, "atom_pdb_radius_how")
        row = box.row()
        row.label(text="1. Change type of radii")
        row = box.row()
        row.prop(scn, "atom_pdb_radius_type")
        row = box.row()
        row.label(text="2. Change atom radii in pm")
        row = box.row()
        row.prop(scn, "atom_pdb_radius_pm_name")
        row = box.row()
        row.prop(scn, "atom_pdb_radius_pm")
        row = box.row()
        row.label(text="3. Change atom radii by scale")
        row = box.row()
        col = row.column()
        col.prop(scn, "atom_pdb_radius_all")
        col = row.column(align=True)
        col.operator( "atom_pdb.radius_all_bigger" )
        col.operator( "atom_pdb.radius_all_smaller" )
        row = box.row()
        row.label(text="4. Show sticks only")
        row = box.row()
        col = row.column()
        col.operator( "atom_pdb.radius_sticks" )

        if bpy.context.mode == 'EDIT_MESH':

            row = layout.row()
            row.label(text="Separate atom")
            box = layout.box()
            row = box.row()
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

    # In the file dialog window - Import
    scn = bpy.types.Scene
    scn.use_atom_pdb_cam = BoolProperty(
        name="Camera", default=False,
        description="Do you need a camera?")
    scn.use_atom_pdb_lamp = BoolProperty(
        name="Lamp", default=False,
        description = "Do you need a lamp?")
    scn.use_atom_pdb_mesh = BoolProperty(
        name = "Mesh balls", default=False,
        description = "Use mesh balls instead of NURBS")
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
        description = "Put the object into the global origin")
    scn.use_atom_pdb_sticks = BoolProperty(
        name="Use sticks", default=True,
        description="Do you want to display the sticks?")
    scn.atom_pdb_sticks_sectors = IntProperty(
        name = "Sector", default=20, min=0,
        description="Number of sectors of a stick")
    scn.atom_pdb_sticks_radius = FloatProperty(
        name = "Radius", default=0.1, min=0.0,
        description ="Radius of a stick")
    scn.use_atom_pdb_sticks_color = BoolProperty(
        name="Color", default=True,
        description="The sticks appear in the color of the atoms")
    scn.use_atom_pdb_sticks_smooth = BoolProperty(
        name="Smooth", default=False,
        description="The sticks are round (sectors are not visible)")     
    scn.use_atom_pdb_sticks_bonds = BoolProperty(
        name="Bonds", default=False,
        description="Show double and tripple bonds.")
    scn.atom_pdb_sticks_dist = FloatProperty(
        name="Distance", default = 1.1, min=1.0, max=3.0,
        description="Distance between sticks measured in stick diameter")        
    scn.atom_pdb_atomradius = EnumProperty(
        name="Type of radius",
        description="Choose type of atom radius",
        items=(('0', "Pre-defined", "Use pre-defined radius"),
               ('1', "Atomic", "Use atomic radius"),
               ('2', "van der Waals", "Use van der Waals radius")),
               default='0',)

    # In the file dialog window - Export
    scn.atom_pdb_export_type = EnumProperty(
        name="Type of Objects",
        description="Choose type of objects",
        items=(('0', "All", "Export all active objects"),
               ('1', "Elements", "Export only those active objects which have a proper element name")),
               default='1',)    
    
    # In the panel
    scn.atom_pdb_datafile = StringProperty(
        name = "", description="Path to your custom data file",
        maxlen = 256, default = "", subtype='FILE_PATH')
    scn.atom_pdb_PDB_file = StringProperty(
        name = "PDB file", default="",
        description = "Path of the PDB file")
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
    bl_description = "Use color and radii values stored in the custom file"

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


# Button for separating single objects from a atom mesh
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
    bl_description = "Measure the distance between two objects (only in Object Mode)"

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


# Button for showing the sticks only - the radii of the atoms downscaled onto
# 90% of the stick radius
class CLASS_atom_pdb_radius_sticks_button(Operator):
    bl_idname = "atom_pdb.radius_sticks"
    bl_label = "Show sticks"
    bl_description = "Show only the sticks (atom radii = stick radii)"

    def execute(self, context):
        global ATOM_PDB_ERROR
        
        scn = bpy.context.scene
                
        result = import_pdb.DEF_atom_pdb_radius_sticks(
                     scn.atom_pdb_sticks_radius * 0.9,
                     scn.atom_pdb_radius_how,
                     )
                     
        if result == False:
            ATOM_PDB_ERROR = "No sticks => no changes"
            bpy.ops.atom_pdb.error_dialog('INVOKE_DEFAULT')
                                          
        return {'FINISHED'}


# The button for reloading the atoms and creating the scene
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
        sticks_col = scn.use_atom_pdb_sticks_color
        sticks_sm  = scn.use_atom_pdb_sticks_smooth
        ssector    = scn.atom_pdb_sticks_sectors
        sradius    = scn.atom_pdb_sticks_radius
        stick_bond = scn.use_atom_pdb_sticks_bonds
        stick_dist = scn.atom_pdb_sticks_dist
        
        cam        = scn.use_atom_pdb_cam
        lamp       = scn.use_atom_pdb_lamp
        mesh       = scn.use_atom_pdb_mesh
        datafile   = scn.atom_pdb_datafile
        
        # Execute main routine an other time ... from the panel
        atom_number = import_pdb.DEF_atom_pdb_main(
                mesh, azimuth, zenith, bradius, radiustype, bdistance, 
                sticks, sticks_col, sticks_sm, stick_bond,
                stick_dist, ssector, sradius, center, cam, lamp, datafile)
        scn.atom_pdb_number_atoms = str(atom_number) + " atoms"

        return {'FINISHED'}


# This is the class for the file dialog.
class ImportPDB(Operator, ImportHelper):
    bl_idname = "import_mesh.pdb"
    bl_label  = "Import Protein Data Bank(*.pdb)"

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
        col.active = scn.use_atom_pdb_mesh
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
        row = layout.row()        
        row.active = scn.use_atom_pdb_sticks
        col = row.column(align=True)
        col.prop(scn, "atom_pdb_sticks_sectors")
        col.prop(scn, "atom_pdb_sticks_radius")
        col = row.column(align=True)        
        col.prop(scn, "use_atom_pdb_sticks_color")        
        col.prop(scn, "use_atom_pdb_sticks_smooth")
        col.prop(scn, "use_atom_pdb_sticks_bonds")
        row = layout.row()        
        row.active = scn.use_atom_pdb_sticks
        col = row.column(align=True)
        col = row.column(align=True)
        col.active = scn.use_atom_pdb_sticks and scn.use_atom_pdb_sticks_bonds 
        col.prop(scn, "atom_pdb_sticks_dist")

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
        sticks_col = scn.use_atom_pdb_sticks_color
        sticks_sm  = scn.use_atom_pdb_sticks_smooth
        ssector    = scn.atom_pdb_sticks_sectors
        sradius    = scn.atom_pdb_sticks_radius
        stick_bond = scn.use_atom_pdb_sticks_bonds
        stick_dist = scn.atom_pdb_sticks_dist
                
        cam        = scn.use_atom_pdb_cam
        lamp       = scn.use_atom_pdb_lamp
        mesh       = scn.use_atom_pdb_mesh
        datafile   = scn.atom_pdb_datafile
        
        # Execute main routine
        atom_number = import_pdb.DEF_atom_pdb_main(
                mesh, azimuth, zenith, bradius, radiustype, bdistance, 
                sticks, sticks_col, sticks_sm, stick_bond,
                stick_dist, ssector, sradius, center, cam, lamp, datafile)

        scn.atom_pdb_number_atoms = str(atom_number) + " atoms"

        return {'FINISHED'}



# This is the class for the file dialog.
class ExportPDB(Operator, ExportHelper):
    bl_idname = "export_mesh.pdb"
    bl_label  = "Export Protein Data Bank(*.pdb)"

    filename_ext = ".pdb"
    filter_glob  = StringProperty(default="*.pdb", options={'HIDDEN'},)

    def draw(self, context):
        layout = self.layout
        scn = bpy.context.scene

        row = layout.row()
        row.prop(scn, "atom_pdb_export_type")

    def execute(self, context):
        scn = bpy.context.scene

        # This is in order to solve this strange 'relative path' thing.
        export_pdb.ATOM_PDB_FILEPATH = bpy.path.abspath(self.filepath)
        export_pdb.DEF_atom_pdb_export(scn.atom_pdb_export_type)

        return {'FINISHED'}



class CLASS_atom_pdb_error_dialog(bpy.types.Operator):
    bl_idname = "atom_pdb.error_dialog"
    bl_label = "Attention !"
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="                          "+ATOM_PDB_ERROR) 
    def execute(self, context):
        print("Atomic Blender - Error: "+ATOM_PDB_ERROR+"\n")
        return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


# The entry into the menu 'file -> import'
def menu_func_import(self, context):
    self.layout.operator(ImportPDB.bl_idname, text="Protein Data Bank (.pdb)")

# The entry into the menu 'file -> export'
def menu_func_export(self, context):
    self.layout.operator(ExportPDB.bl_idname, text="Protein Data Bank (.pdb)")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":

    register()
