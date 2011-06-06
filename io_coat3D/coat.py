# scene_blend_info.py Copyright (C) 2010, Mariano Hidalgo
#
# Show Information About the Blend.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

import bpy
from bpy.props import *
from io_coat3D import tex
import os
import linecache
import math

bpy.coat3D = dict()
bpy.coat3D['active_coat'] = ''
bpy.coat3D['status'] = 0


class ObjectButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

class SCENE_PT_Main(ObjectButtonsPanel,bpy.types.Panel):
    bl_label = "3D-Coat Applink"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        me = context.scene.objects
        mat_list = []
        import_no = 0
        coat = bpy.coat3D
        coat3D = bpy.context.scene.coat3D
        if(bpy.context.scene.objects.active):
            coa = bpy.context.scene.objects.active.coat3D
        
        if(os.path.isdir(coat3D.exchangedir)):
            foldder = coat3D.exchangedir
            if(foldder.rfind('Exchange') >= 0):
                coat['status'] = 1
            else:
                coat['status'] = 0
        else:
            coat['status'] = 0

        if(coat['status'] == 1):
            Blender_folder = ("%s%sBlender"%(coat3D.exchangedir,os.sep))
            Blender_export = Blender_folder
            path3b_now = coat3D.exchangedir
            path3b_now += ('last_saved_3b_file.txt')
            Blender_export += ('%sexport.txt'%(os.sep))

            if(not(os.path.isdir(Blender_folder))):
                os.makedirs(Blender_folder)
                Blender_folder = os.path.join(Blender_folder,"run.txt")
                file = open(Blender_folder, "w")
                file.close()
        
        #Here you add your GUI 
        row = layout.row()
        row.prop(coat3D,"type",text = "")
        row = layout.row()
        if(context.selected_objects):
            if(context.selected_objects[0].type == 'MESH'):
                row.active = True
            else:
                row.active = False
        else:
            row.active = False

        if(not(bpy.context.selected_objects) and os.path.isfile(Blender_export)):
            row.active = True
            row.operator("import3b_applink.pilgway_3d_coat", text="Bring from 3D-Coat")

        else:
            colL = row.column()
            colR = row.column()
        
            colL.operator("export_applink.pilgway_3d_coat", text="Export")
            colL.label(text="Export Settings:")

            colL.prop(coat3D,"exportover")
            if(coat3D.exportover):
                colL.prop(coat3D,"exportmod")
            colL.prop(coat3D,"exportfile")
            colL.prop(coat3D,"export_pos")
               
            colR.operator("import_applink.pilgway_3d_coat", text="Import")
            colR.label(text="Import Settings:")
            colR.prop(coat3D,"importmesh")
            colR.prop(coat3D,"importmod")
            colR.prop(coat3D,"smooth_on")
            colR.prop(coat3D,"importtextures")
            row = layout.row()
        
        if(bpy.context.selected_objects):
            if(context.selected_objects[0].type == 'MESH'):
                coa = context.selected_objects[0].coat3D
                colL = row.column()
                colR = row.column()
                colL.label(text="Object Path:")
                if(coa.path3b):
                    colR.active = True
                else:
                    colR.active = False
                    
                colR.operator("import_applink.pilgway_3d_coat_3b", text="Load 3b")
                row = layout.row()
                row.prop(coa,"objectdir",text="")
                    
        row = layout.row()
                
        if(context.selected_objects):
            if(context.selected_objects[0].type == 'MESH'):
                coa = bpy.context.selected_objects[0].coat3D
                row = layout.row()
                row.label(text="Texture output folder:")
                row = layout.row()
                row.prop(coa,"texturefolder",text="")
        row = layout.row()
        if(coat['status'] == 0):
            row.label(text="Exchange Folder: not connected")
        else:
            row.label(text="Exchange Folder: connected")        

class SCENE_PT_Settings(ObjectButtonsPanel,bpy.types.Panel):
    bl_label = "Applink Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        coat3D = bpy.context.scene.coat3D
        

        row = layout.row()
        if(bpy.context.selected_objects):
            if(context.selected_objects[0].type == 'MESH'):
                row.active = True
        else:
            row.active = False
        row.operator("import_applink.pilgway_3d_deltex",text="Delete Textures")
        row = layout.row()
        row.label(text="Exchange Folder:")
        row = layout.row()
        row.prop(coat3D,"exchangedir",text="")
        if(bpy.context.scene.objects.active):
            coa = bpy.context.scene.objects.active.coat3D
            row = layout.row()
            row.label(text="3b path:")
            row = layout.row()
            row.prop(coa,"path3b",text="")
            row = layout.row()
            row.label(text="Default Folder:")
            row = layout.row()
            row.prop(coat3D,"defaultfolder",text="")
            
        #colL = row.column()
        #colR = row.column()
        #colL.prop(coat3D,"export_box")
        #colR.prop(coat3D,"import_box")
        #if(not(coat3D.export_box)):
        #    row = layout.row()
        #    colL.label(text="Export settings:")
        #    row = layout.row()
        #    colL = row.column()
        #    colR = row.column()
        #    colL.prop(coat3D,"export_color")
        #    colL.prop(coat3D,"export_spec")
        #    colL.prop(coat3D,"export_normal")
        #    colL.prop(coat3D,"export_disp")
        #    colR.prop(coat3D,"export_position")
        #    colR.prop(coat3D,"export_export_zero_layer")
        #    colR.prop(coat3D,"export_coarse")
        #row = layout.row()
        #colL = row.column()
        #colR = row.column()

        
       
        


class SCENE_OT_export(bpy.types.Operator):
    bl_idname = "export_applink.pilgway_3d_coat"
    bl_label = "Export your custom property"
    bl_description = "Export your custom property"

    
    def invoke(self, context, event):
        checkname = ''
        coat3D = bpy.context.scene.coat3D
        scene = context.scene
        coat3D.export_on = False
        activeobj = bpy.context.active_object.name
        obj = scene.objects[activeobj]
        coa = bpy.context.scene.objects.active.coat3D

        importfile = coat3D.exchangedir
        texturefile = coat3D.exchangedir
        importfile += ('%simport.txt'%(os.sep))
        texturefile += ('%stextures.txt'%(os.sep))
        if(os.path.isfile(texturefile)):
                os.remove(texturefile)
        
        checkname = coa.objectdir
        
        if(coa.objectdir[-4:] != '.obj'):
            checkname += ('%s.obj'%(activeobj))

        if(not(os.path.isfile(checkname)) or coat3D.exportover):
            if(coat3D.export_pos):
                bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)

                bpy.ops.export_scene.obj(filepath=checkname,use_selection=True,
                use_apply_modifiers=coat3D.exportmod,use_blen_objects=False, group_by_material= True,
                use_materials = False,keep_vertex_order = True,axis_forward='Y',axis_up='Z')
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

                coa.export_on = True
            else:
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                coat3D.loca = obj.location
                coat3D.rota = obj.rotation_euler
                coat3D.scal = obj.scale
                obj.location = (0,0,0)
                obj.rotation_euler = (0,0,0)
                obj.scale = (1,1,1)

                bpy.ops.export_scene.obj(filepath=checkname,use_selection=True,
                use_apply_modifiers=coat3D.exportmod,use_blen_objects=False, group_by_material= True,
                use_materials = False,keep_vertex_order = True,axis_forward='Y',axis_up='Z')

                obj.location = coat3D.loca
                obj.rotation_euler = coat3D.rota
                obj.scale = coat3D.scal
                coa.export_on = False
                    


        if(coat3D.exportfile == False):
            file = open(importfile, "w")
            file.write("%s"%(checkname))
            file.write("\n%s"%(checkname))
            file.write("\n[%s]"%(coat3D.type))
            if(coa.texturefolder):
                file.write("\n[TexOutput:%s"%(coa.texturefolder))
            
            
        

            
            file.close()
        coa.objectdir = checkname

        return('FINISHED')


class SCENE_OT_import(bpy.types.Operator):
    bl_idname = "import_applink.pilgway_3d_coat"
    bl_label = "import your custom property"
    bl_description = "import your custom property"
    
    def invoke(self, context, event):
        scene = context.scene
        coat3D = bpy.context.scene.coat3D
        coat = bpy.coat3D
        activeobj = bpy.context.active_object.name
        mat_list = []
        scene.objects[activeobj].select = True
        objekti = scene.objects[activeobj]
        coat3D.loca = objekti.location
        coat3D.rota = objekti.rotation_euler
        coa = bpy.context.scene.objects.active.coat3D

        exportfile = coat3D.exchangedir
        path3b_n = coat3D.exchangedir
        path3b_n += ('last_saved_3b_file.txt')
        exportfile += ('%sexport.txt'%(os.sep))
        if(os.path.isfile(exportfile)):
            export_file = open(exportfile)
            for line in export_file:
                if line.rfind('.3b'):
                    objekti.coat3D.coatpath = line
                    coat['active_coat'] = line
            export_file.close()
            os.remove(exportfile)
            
            
           

        if(objekti.material_slots):
            for obj_mat in objekti.material_slots:
                mat_list.append(obj_mat.material)
            act_mat_index = objekti.active_material_index


        if(coat3D.importmesh and os.path.isfile(coa.objectdir)):
            mtl = coa.objectdir
            mtl = mtl.replace('.obj','.mtl')
            if(os.path.isfile(mtl)):
                os.remove(mtl)

            
            bpy.ops.import_scene.obj(filepath=coa.objectdir,axis_forward='Y',axis_up='Z')
            obj_proxy = scene.objects[0]
            bpy.ops.object.select_all(action='TOGGLE')
            obj_proxy.select = True
            if(coa.export_on):
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                
            bpy.ops.object.transform_apply(rotation=True)
            proxy_mat = obj_proxy.material_slots[0].material
            obj_proxy.data.materials.pop(0)
            proxy_mat.user_clear()
            bpy.data.materials.remove(proxy_mat)
            bpy.ops.object.select_all(action='TOGGLE')
            
          
            
            scene.objects.active = obj_proxy

            obj_data = objekti.data.id_data
            objekti.data = obj_proxy.data.id_data
            if(bpy.data.meshes[obj_data.name].users == 0):
                bpy.data.meshes.remove(obj_data)
                objekti.data.id_data.name = obj_data.name

            obj_proxy.select = True
            bpy.ops.object.delete()
            objekti.select = True
            bpy.context.scene.objects.active = objekti

                
                
    
            if(coat3D.smooth_on):
                bpy.ops.object.shade_smooth()
            else:
                bpy.ops.object.shade_flat()

        if(os.path.isfile(path3b_n)):
            path3b_fil = open(path3b_n)
            for lin in path3b_fil:
                objekti.coat3D.path3b = lin
            path3b_fil.close()
            os.remove(path3b_n)
                
        if(coat3D.importmesh and not(os.path.isfile(coa.objectdir))):
            coat3D.importmesh = False

        if(mat_list and coat3D.importmesh):
            for mat_one in mat_list:
                objekti.data.materials.append(mat_one)
            objekti.active_material_index = act_mat_index
            
        if(mat_list):
            for obj_mate in objekti.material_slots:
                for tex_slot in obj_mate.material.texture_slots:
                    if(hasattr(tex_slot,'texture')):
                        if(tex_slot.texture.type == 'IMAGE'):
                                                        tex_slot.texture.image.reload()
                                                        

        if(coat3D.importmod):
            mod_list = []
            for mod_index in objekti.modifiers:
                objekti.modifiers.remove(mod_index)
                
        
                
        if(coat3D.importtextures):
                        export = ''
                        tex.gettex(mat_list,objekti,scene,export)
        
        return('FINISHED')

class SCENE_OT_import3b(bpy.types.Operator):
    bl_idname = "import3b_applink.pilgway_3d_coat"
    bl_label = "Brings mesh from 3D-Coat"
    bl_description = "Bring 3D-Coat Mesh"

    
    def invoke(self, context, event):

        coat3D = bpy.context.scene.coat3D
        scene = context.scene
        
        Blender_folder = ("%s%sBlender"%(coat3D.exchangedir,os.sep))
        Blender_export = Blender_folder
        path3b_now = coat3D.exchangedir
        path3b_now += ('last_saved_3b_file.txt')
        Blender_export += ('%sexport.txt'%(os.sep))

        import_no = 0
        mat_list = []
        obj_path =''

        obj_pathh = open(Blender_export)
        for line in obj_pathh:
            obj_path = line
            break
        obj_pathh.close()
        export = obj_path
        mod_time = os.path.getmtime(obj_path)
        mtl_list = obj_path.replace('.obj','.mtl')
        if(os.path.isfile(mtl_list)):
            os.remove(mtl_list)
            
        if(os.path.isfile(path3b_now)):
            path3b_file = open(path3b_now)
            for lin in path3b_file:
                path_export = lin
                path_on = 1
            path3b_file.close()
            os.remove(path3b_now)
        else:
            print("ei toimi")
            path_on = 0

        for palikka in bpy.context.scene.objects:
            if(palikka.type == 'MESH'):
                if(palikka.coat3D.objectdir == export):
                    import_no = 1
                    target = palikka
                    break

        if(import_no):
            new_obj = palikka
            import_no = 0
        else:
            bpy.ops.import_scene.obj(filepath=obj_path,axis_forward='Y',axis_up='Z')
            new_obj = scene.objects[0]
            scene.objects[0].coat3D.objectdir = export
            if(path_on):
                scene.objects[0].coat3D.path3b = path_export
            
        os.remove(Blender_export)
        
        bpy.context.scene.objects.active = new_obj

        if(coat3D.smooth_on):
            bpy.ops.object.shade_smooth()
        else:
            bpy.ops.object.shade_flat()

        Blender_tex = ("%s%stextures.txt"%(coat3D.exchangedir,os.sep))
        mat_list.append(new_obj.material_slots[0].material)
        tex.gettex(mat_list, new_obj, scene,export)


        return('FINISHED')

class SCENE_OT_load3b(bpy.types.Operator):
    bl_idname = "import_applink.pilgway_3d_coat_3b"
    bl_label = "Loads 3b linked into object"
    bl_description = "Loads 3b linked into object"

    
    def invoke(self, context, event):
        checkname = ''
        coa = bpy.context.scene.objects.active.coat3D
        if(coa.path3b):
            coat3D = bpy.context.scene.coat3D
            scene = context.scene
            importfile = coat3D.exchangedir
            importfile += ('%simport.txt'%(os.sep))
            
            coat_path = bpy.context.active_object.coat3D.path3b
            
            file = open(importfile, "w")
            file.write("%s"%(coat_path))
            file.write("\n%s"%(coat_path))
            file.write("\n[3B]")
            file.close()


        return('FINISHED')

class SCENE_OT_deltex(bpy.types.Operator):
    bl_idname = "import_applink.pilgway_3d_deltex"  # XXX, name?
    bl_label = "Picks Object's name into path"
    bl_description = "Loads 3b linked into object"

    
    def invoke(self, context, event):
        if(bpy.context.selected_objects):
            if(context.selected_objects[0].type == 'MESH'):
                coat3D = bpy.context.scene.coat3D
                coa = bpy.context.scene.objects.active.coat3D
                scene = context.scene
                nimi = tex.objname(coa.objectdir)
                if(coa.texturefolder):
                    osoite = os.path.dirname(coa.texturefolder) + os.sep
                else:
                    osoite = os.path.dirname(coa.objectdir) + os.sep
                just_nimi = tex.justname(nimi)
                just_nimi += '_'

                files = os.listdir(osoite)
                for i in files:
                    if(i.rfind(just_nimi) >= 0):
                        del_osoite = osoite + i
                        os.remove(del_osoite)
    
        return('FINISHED')

def register():
    bpy.utils.register_module(__name__)

    pass

def unregister():
    bpy.utils.unregister_module(__name__)

    pass

if __name__ == "__main__":
    register()
