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
    "name": "3D-Coat Applink",
    "author": "Kalle-Samuli Riihikoski (haikalle)",
    "version": (3, 5, 22),
    "blender": (2, 80, 0),
    "location": "Scene > 3D-Coat Applink",
    "description": "Transfer data between 3D-Coat/Blender",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Import-Export/3dcoat_applink",
    "category": "Import-Export",
}


if "bpy" in locals():
    import importlib
    importlib.reload(coat)
    importlib.reload(tex)
else:
    from . import tex

from io_coat3D import tex
import os
import ntpath
import re

import time
import bpy
from bpy.types import PropertyGroup
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatVectorProperty,
        StringProperty,
        PointerProperty,
        )


bpy.coat3D = dict()
bpy.coat3D['active_coat'] = ''
bpy.coat3D['status'] = 0

def folder_size(path):

    tosi = True
    while tosi:
        list_of_files = []
        for file in os.listdir(path):
            list_of_files.append(path + os.sep + file)

        if len(list_of_files) >= 400:
            oldest_file = min(list_of_files, key=os.path.getctime)
            os.remove(os.path.abspath(oldest_file))
        else:
            tosi = False

def set_exchange_folder():
    platform = os.sys.platform
    coat3D = bpy.context.scene.coat3D
    Blender_export = ""

    if(platform == 'win32'):
        exchange = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3D-CoatV4' + os.sep +'Exchange'
        if not(os.path.isdir(exchange)):
            exchange = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3D-CoatV3' + os.sep +'Exchange'
    else:
        exchange = os.path.expanduser("~") + os.sep + '3D-CoatV4' + os.sep + 'Exchange'
        if not(os.path.isdir(exchange)):
            exchange = os.path.expanduser("~") + os.sep + '3D-CoatV3' + os.sep + 'Exchange'
    if(not(os.path.isdir(exchange))):
        exchange = coat3D.exchangedir

    if(os.path.isdir(exchange)):
        bpy.coat3D['status'] = 1
        if(platform == 'win32'):
            exchange_path = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
            applink_folder = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender'
            if(not(os.path.isdir(applink_folder))):
                os.makedirs(applink_folder)
        else:
            exchange_path = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
            applink_folder = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender'
            if(not(os.path.isdir(applink_folder))):
                os.makedirs(applink_folder)
        file = open(exchange_path, "w")
        file.write("%s"%(coat3D.exchangedir))
        file.close()

    else:
        if(platform == 'win32'):
            exchange_path = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
        else:
            exchange_path = os.path.expanduser("~") + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
        if(os.path.isfile(exchange_path)):
            ex_path =''

            ex_pathh = open(exchange_path)
            for line in ex_pathh:
                ex_path = line
                break
            ex_pathh.close()

            if(os.path.isdir(ex_path) and ex_path.rfind('Exchange') >= 0):
                exchange = ex_path
                bpy.coat3D['status'] = 1
            else:
                bpy.coat3D['status'] = 0
        else:
            bpy.coat3D['status'] = 0
    if(bpy.coat3D['status'] == 1):
        Blender_folder = ("%s%sBlender"%(exchange,os.sep))
        Blender_export = Blender_folder
        path3b_now = exchange
        path3b_now += ('last_saved_3b_file.txt')
        Blender_export += ('%sexport.txt'%(os.sep))

        if(not(os.path.isdir(Blender_folder))):
            os.makedirs(Blender_folder)
            Blender_folder = os.path.join(Blender_folder,"run.txt")
            file = open(Blender_folder, "w")
            file.close()
    return exchange

def set_working_folders():
    platform = os.sys.platform
    coat3D = bpy.context.scene.coat3D
    if(platform == 'win32'):
        folder_objects = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'ApplinkObjects'
        if(not(os.path.isdir(folder_objects))):
            os.makedirs(folder_objects)
    else:
        folder_objects = os.path.expanduser("~") + os.sep + '3DC2Blender' + os.sep + 'ApplinkObjects'
        if(not(os.path.isdir(folder_objects))):
            os.makedirs(folder_objects)

    return folder_objects

def make_texture_list(texturefolder):
    texturefolder += ('%stextures.txt'%(os.sep))
    texturelist = []

    if (os.path.isfile(texturefolder)):
        texturefile = open(texturefolder)
        index = 0
        for line in texturefile:
            if line != '' and index == 0:
                objekti = line
                index += 1
            elif index == 1:
                material = line
                index += 1
            elif index == 2:
                type = line
                index += 1
            elif index == 3:
                address = line
                texturelist.append([objekti,material,type,address])
                index = 0
        texturefile.close()
    return texturelist

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
        coat3D = bpy.context.scene.coat3D
        if(bpy.context.active_object):
            coa = bpy.context.active_object.coat3D

        if(bpy.coat3D['status'] == 0 and not(os.path.isdir(coat3D.exchangedir))):
            bpy.coat3D['active_coat'] = set_exchange_folder()
            row = layout.row()
            row.label(text="Applink didn't find your 3d-Coat/Excahnge folder.")
            row = layout.row()
            row.label("Please select it before using Applink.")
            row = layout.row()
            row.prop(coat3D,"exchangedir",text="")

        else:
            #Here you add your GUI
            row = layout.row()
            row.prop(coat3D,"type",text = "")
            row = layout.row()
            colL = row.column()
            colR = row.column()

            colR.operator("export_applink.pilgway_3d_coat", text="Transfer")
            colL.operator("import_applink.pilgway_3d_coat", text="Update")



class SCENE_OT_export(bpy.types.Operator):
    bl_idname = "export_applink.pilgway_3d_coat"
    bl_label = "Export your custom property"
    bl_description = "Export your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):

        for mesh in bpy.data.meshes:
            if (mesh.users == 0 and mesh.coat3D.name == '3DC'):
                bpy.data.meshes.remove(mesh)

        for material in bpy.data.materials:
            if (material.users == 1 and material.coat3D.name == '3DC'):
                bpy.data.materials.remove(material)

        export_ok = False
        coat3D = bpy.context.scene.coat3D

        if (bpy.context.selected_objects == []):
            return {'FINISHED'}
        else:
            for objec in bpy.context.selected_objects:
                if objec.type == 'MESH':
                    export_ok = True
            if (export_ok == False):
                return {'FINISHED'}

        if(coat3D.exchange_found == False):
            return {'FINISHED'}

        activeobj = bpy.context.active_object.name
        checkname = ''
        coa = bpy.context.active_object.coat3D
        coat3D.exchangedir = set_exchange_folder()


        folder_objects = set_working_folders()
        folder_size(folder_objects)


        importfile = coat3D.exchangedir
        texturefile = coat3D.exchangedir
        importfile += ('%simport.txt'%(os.sep))
        texturefile += ('%stextures.txt'%(os.sep))

        looking = True
        object_index = 0

        while(looking == True):
            checkname = folder_objects + os.sep + activeobj
            checkname = ("%s%.2d.dae"%(checkname,object_index))
            if(os.path.isfile(checkname)):
                object_index += 1
            else:
                looking = False
                coa.applink_name = ("%s%.2d"%(activeobj,object_index))
                coa.applink_address = checkname

        matindex = 0
        for objekti in bpy.context.selected_objects:
            if(objekti.material_slots.keys() == []):
                newmat = bpy.data.materials.new('Material')
                objekti.data.materials.append(newmat)
                matindex += 1

        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        #bpy.ops.object.transforms_to_deltas(mode='ROT')

        bpy.ops.wm.collada_export(filepath=coa.applink_address, selected=True,
                                  apply_modifiers=False, sort_by_name=True, use_blender_profile=False, triangulate=False)

        file = open(importfile, "w")
        file.write("%s"%(checkname))
        file.write("\n%s"%(checkname))
        file.write("\n[%s]"%(coat3D.type))
        file.close()
        group_index = -1.0

        for objekti in bpy.context.selected_objects:
            nimi = ''
            for koko in bpy.context.selected_objects:
                nimi += koko.data.name + ':::'
            objekti.coat3D.applink_group = nimi
            objekti.coat3D.applink_address = coa.applink_address
            objekti.coat3D.applink_name = coa.applink_name
            objekti.coat3D.applink_firsttime = True
            objekti.coat3D.objecttime = str(os.path.getmtime(objekti.coat3D.applink_address))
            objekti.data.coat3D.name = '3DC'

            if(objekti.material_slots.keys() != []):
                for material in objekti.material_slots:
                    if material.material.use_nodes == True:
                        for node in material.material.node_tree.nodes:
                            if(node.name.startswith('3DC_') == True):
                                material.material.node_tree.nodes.remove(node)



        return {'FINISHED'}

class SCENE_OT_import(bpy.types.Operator):
    bl_idname = "import_applink.pilgway_3d_coat"
    bl_label = "import your custom property"
    bl_description = "import your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):

        for mesh in bpy.data.meshes:
            if(mesh.users == 0 and mesh.coat3D.name == '3DC'):
                bpy.data.meshes.remove(mesh)

        for material in bpy.data.materials:
            img_list = []
            if (material.users == 1 and material.coat3D.name == '3DC'):
                if material.use_nodes == True:
                    for node in material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.name.startswith('3DC'):
                            img_list.append(node.image)
                if img_list != []:
                    for del_img in img_list:
                        bpy.data.images.remove(del_img)

                bpy.data.materials.remove(material)

        coat3D = bpy.context.scene.coat3D
        coat = bpy.coat3D
        coat3D.exchangedir = set_exchange_folder()

        texturelist = make_texture_list(coat3D.exchangedir)
        for texturepath in texturelist:
            for image in bpy.data.images:
                if(image.filepath == texturepath[3]):
                    bpy.data.images.remove(image)


        Blender_folder = ("%s%sBlender"%(coat3D.exchangedir,os.sep))
        Blender_export = Blender_folder
        path3b_now = coat3D.exchangedir
        path3b_now += ('last_saved_3b_file.txt')
        Blender_export += ('%sexport.txt'%(os.sep))
        new_applink_address = 'False'
        new_object = False
        if(os.path.isfile(Blender_export)):
            obj_pathh = open(Blender_export)
            new_object = True
            for line in obj_pathh:
                new_applink_address = line
                break
            obj_pathh.close()

            for scene_objects in bpy.context.collection.objects:
                if(scene_objects.type == 'MESH'):
                    if(scene_objects.coat3D.applink_address == new_applink_address):
                        new_object = False

        exportfile = coat3D.exchangedir
        exportfile += ('%sBlender' % (os.sep))
        exportfile += ('%sexport.txt' % (os.sep))
        if (os.path.isfile(exportfile)):
            os.remove(exportfile)



        if(new_object == False):

            #Blender -> 3DC -> Blender workflow
            #First check if objects needs to be imported, if imported it will then delete extra mat and objs.

            old_materials = bpy.data.materials.keys()
            old_objects = bpy.data.objects.keys()
            old_images = bpy.data.images.keys()
            image_list = []
            object_list = []
            import_list = []
            mesh_del_list = []
            for objekti in bpy.context.scene.collection.all_objects:
                if (objekti.type == 'MESH'):
                    object_list.append(objekti.name)
                    obj_coat = objekti.coat3D
                    if(obj_coat.applink_address != ''):
                        if (obj_coat.objecttime != str(os.path.getmtime(obj_coat.applink_address))):
                            obj_coat.dime = objekti.dimensions
                            obj_coat.import_mesh = True
                            obj_coat.objecttime = str(os.path.getmtime(obj_coat.applink_address))
                            if(obj_coat.applink_address not in import_list):
                                import_list.append(obj_coat.applink_address)
            if(import_list):
                for list in import_list:
                    bpy.ops.wm.collada_import(filepath=list)
                bpy.ops.object.select_all(action='DESELECT')

                new_materials = bpy.data.materials.keys()
                new_objects = bpy.data.objects.keys()
                new_images = bpy.data.images.keys()

                diff_mat = [i for i in new_materials if i not in old_materials]
                diff_objects = [i for i in new_objects if i not in old_objects]
                diff_images = [i for i in new_images if i not in old_images]

                for mark_mesh in diff_objects:
                    bpy.data.objects[mark_mesh].data.coat3D.name = '3DC'
                for c_index in diff_mat:
                    bpy.data.materials.remove(bpy.data.materials[c_index])
                for i in diff_images:
                    bpy.data.images.remove(bpy.data.images[i])

            #The main Applink Object Loop

            for oname in object_list:
                objekti = bpy.data.objects[oname]
                if(objekti.coat3D.import_mesh):
                    objekti.coat3D.import_mesh = False
                    objekti.select_set('SELECT')

                    if (objekti.coat3D.applink_export == False):
                        find_name = objekti.data.name + '-mesh'
                        find_name = find_name.replace('.', '_')
                    else:


                        new_name = objekti.data.name
                        name_boxs = new_name.split('.')
                        if len(name_boxs) > 1:
                            if len(name_boxs[-1]) == 3:
                                luku = int(name_boxs[-1])
                                luku +=1
                                uusi_nimi = ("%s.%.3d" % (new_name[:-4], luku))
                                find_name = uusi_nimi
                        else:
                            find_name = objekti.data.name
                            tosi = True
                            luku = 1
                            find_name = ("%s.%.3d" % (objekti.data.name, luku))
                            loyty = False
                            while tosi:
                                for obj in bpy.data.meshes:
                                    if (obj.name == find_name):
                                        loyty = True
                                        break
                                if(loyty == True):
                                    luku += 1
                                    find_name = ("%s.%.3d" % (objekti.data.name, luku))
                                    loyty = False
                                else:
                                    find_name = ("%s.%.3d" % (objekti.data.name, luku-1))
                                    tosi = False







                    for proxy_objects in diff_objects:
                        if (bpy.data.objects[proxy_objects].data.name == find_name):
                            obj_proxy = bpy.data.objects[proxy_objects]
                            break

                    exportfile = coat3D.exchangedir
                    path3b_n = coat3D.exchangedir
                    path3b_n += ('last_saved_3b_file.txt')
                    exportfile += ('%sBlender' % (os.sep))
                    exportfile += ('%sexport.txt'%(os.sep))
                    if(os.path.isfile(exportfile)):
                        export_file = open(exportfile)
                        for line in export_file:
                            if line.rfind('.3b'):
                                coat['active_coat'] = line
                        export_file.close()
                        os.remove(exportfile)


                    obj_names = objekti.coat3D.applink_group
                    obj_list = obj_names.split(':::')
                    applinks = []
                    mat_list = []
                    obj_list.pop()

                    use_smooth = objekti.data.polygons[0].use_smooth

                    if(objekti.material_slots):
                        act_mat = objekti.active_material
                        for obj_mat in objekti.material_slots:
                            mat_list.append(obj_mat.material)

                    bpy.ops.object.select_all(action='DESELECT')
                    obj_proxy.select_set('SELECT')

                    bpy.ops.object.select_all(action='TOGGLE')

                    if(coat3D.importlevel):
                        obj_proxy.select = True
                        obj_proxy.modifiers.new(name='temp',type='MULTIRES')
                        objekti.select = True
                        bpy.ops.object.multires_reshape(modifier=multires_name)
                        bpy.ops.object.select_all(action='TOGGLE')
                        multires_on = False
                    else:

                        #scene.objects.active = obj_proxy HACKKI
                        obj_proxy.select_set('SELECT')

                        obj_data = objekti.data.id_data
                        objekti.data = obj_proxy.data.id_data
                        objekti.data.id_data.name = obj_data.name
                        if(bpy.data.meshes[obj_data.name].users == 0):
                            bpy.data.meshes.remove(obj_data)


                    #tärkee että saadaan oikein käännettyä objekt

                    objekti.select_set('SELECT')
                    bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')
                    objekti.data.materials.pop()
                    for mat in mat_list:
                        objekti.data.materials.append(mat)

                    if (use_smooth):
                        for data_mesh in objekti.data.polygons:
                            data_mesh.use_smooth = True

                        bpy.ops.object.select_all(action='DESELECT')

                    if(os.path.isfile(path3b_n)):
                        path3b_fil = open(path3b_n)
                        for lin in path3b_fil:
                            objekti.coat3D.path3b = lin
                        path3b_fil.close()
                        os.remove(path3b_n)

                    if(coat3D.importmesh and not(os.path.isfile(objekti.coat3D.applink_address))):
                        coat3D.importmesh = False


                    objekti.select_set('SELECT')
                    if(coat3D.importtextures):
                        is_new = False
                        tex.matlab(mat_list,objekti,bpy.context.scene,is_new)
                    objekti.select_set('DESELECT')

            bpy.ops.object.select_all(action='DESELECT')
            if(import_list):
                for del_obj in diff_objects:
                    bpy.context.collection.all_objects[del_obj].select_set('SELECT')
                    bpy.ops.object.delete()

            #This is a hack to make textures to update propery

            for material in bpy.data.materials:
                if material.use_nodes == True:
                    for node in material.node_tree.nodes:
                        if (node.name).startswith('3DC'):
                            node.location = node.location

        else:

            # 3DC -> Blender workflow

            for old_obj in bpy.context.collection.objects:
                old_obj.coat3D.applink_old = True

            coat3D = bpy.context.scene.coat3D
            scene = context.scene
            Blender_folder = ("%s%sBlender"%(coat3D.exchangedir,os.sep))
            Blender_export = Blender_folder
            path3b_now = coat3D.exchangedir
            path3b_now += ('last_saved_3b_file.txt')
            Blender_export += ('%sexport.txt'%(os.sep))
            mat_list = []
            nimi = ''

            old_materials = bpy.data.materials.keys()
            old_objects = bpy.data.objects.keys()

            bpy.ops.wm.collada_import(filepath=new_applink_address)

            new_materials = bpy.data.materials.keys()
            new_objects = bpy.data.objects.keys()

            diff_mat = [i for i in new_materials if i not in old_materials]
            diff_objects = [i for i in new_objects if i not in old_objects]

            for mark_mesh in diff_mat:
                bpy.data.materials[mark_mesh].coat3D.name = '3DC'
                bpy.data.materials[mark_mesh].use_fake_user = True
            laskuri = 0
            for c_index in diff_objects:
                bpy.data.objects[c_index].data.coat3D.name = '3DC'
                bpy.data.objects[c_index].material_slots[0].material = bpy.data.materials[diff_mat[laskuri]]
                laskuri += 1

            bpy.ops.object.select_all(action='DESELECT')
            for new_obj in bpy.context.collection.objects:

                if(new_obj.coat3D.applink_old == False):
                    nimi += new_obj.data.name + ':::'
                    new_obj.select_set('SELECT')
                    #bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')
                    new_obj.rotation_euler = (0, 0, 0)
                    new_obj.scale = (1, 1, 1)
                    new_obj.coat3D.applink_firsttime = False
                    new_obj.select_set('DESELECT')
                    new_obj.coat3D.applink_address = new_applink_address
                    new_obj.coat3D.objecttime = str(os.path.getmtime(new_obj.coat3D.applink_address))
                    splittext = ntpath.basename(new_applink_address)
                    new_obj.coat3D.applink_name = splittext.split('.')[0]
                    new_obj.coat3D.applink_export = True
                    for material in bpy.data.materials:
                        if(new_obj.name == material.name):
                            new_obj.material_slots[0].material = material
                            break

                    # bpy.ops.object.transforms_to_deltas(mode='ROT')

                    mat_list.append(new_obj.material_slots[0].material)
                    is_new = True
                    tex.matlab(mat_list, new_obj, bpy.context.scene, is_new)

            for new_obj in bpy.context.collection.objects:
                if(new_obj.coat3D.applink_old == False):
                    new_obj.coat3D.applink_group = nimi
                    new_obj.coat3D.applink_old = True



            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
            bpy.ops.object.select_all(action='DESELECT')
            if (os.path.isfile(Blender_export)):
                os.remove(Blender_export)
            for material in bpy.data.materials:
                if material.use_nodes == True:
                    for node in material.node_tree.nodes:
                        if (node.name).startswith('3DC'):
                            node.location = node.location


        return {'FINISHED'}



from bpy import *
from mathutils import Vector, Matrix

# 3D-Coat Dynamic Menu
class VIEW3D_MT_Coat_Dynamic_Menu(bpy.types.Menu):
    bl_label = "3D-Coat Applink Menu"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'

        ob = context
        if ob.mode == 'OBJECT':
            if(len(context.selected_objects) > 0):
                layout.operator("import_applink.pilgway_3d_coat", text="Update Scene")
                layout.separator()

                layout.operator("export_applink.pilgway_3d_coat", text="Transfer selected object(s) into 3D-Coat")
                layout.separator()
            else:
                layout.operator("import_applink.pilgway_3d_coat", text="Update")
                layout.separator()



class VIEW3D_MT_ImportMenu(bpy.types.Menu):
    bl_label = "Import Settings"

    def draw(self, context):
        layout = self.layout
        coat3D = bpy.context.scene.coat3D
        settings = context.tool_settings
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.prop(coat3D,"importmesh")
        layout.prop(coat3D,"importmod")
        layout.prop(coat3D,"smooth_on")
        layout.prop(coat3D,"importtextures")

class VIEW3D_MT_ExportMenu(bpy.types.Menu):
    bl_label = "Export Settings"

    def draw(self, context):
        layout = self.layout
        coat3D = bpy.context.scene.coat3D
        settings = context.tool_settings

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("view3d.copybuffer", icon="COPY_ID")

        layout.prop(coat3D,"exportover")
        if(coat3D.exportover):
           layout.prop(coat3D,"exportmod")

class VIEW3D_MT_ExtraMenu(bpy.types.Menu):
    bl_label = "Extra"

    def draw(self, context):
        layout = self.layout
        coat3D = bpy.context.scene.coat3D
        settings = context.tool_settings
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("import_applink.pilgway_3d_deltex",text="Delete all Textures")
        layout.separator()

class ObjectCoat3D(PropertyGroup):
    objpath: StringProperty(
        name="Object_Path"
    )
    applink_address: StringProperty(
        name="Object_Applink_address"
    )
    applink_name: StringProperty(
        name="Applink object name"
    )
    applink_group: StringProperty(
        name="Applink group"
    )
    applink_firsttime: BoolProperty(
        name="FirstTime",
        description="FirstTime",
        default=True
    )
    import_mesh: BoolProperty(
        name="ImportMesh",
        description="ImportMesh",
        default=False
    )
    applink_old: BoolProperty(
        name="OldObject",
        description="Old Object",
        default=False
    )
    applink_export: BoolProperty(
        name="FirstTime",
        description="Object is from 3d-ocat",
        default=False
    )
    objecttime: StringProperty(
        name="ObjectTime",
        subtype="FILE_PATH"
    )
    path3b: StringProperty(
        name="3B Path",
        subtype="FILE_PATH"
    )
    dime: FloatVectorProperty(
        name="dime",
        description="Dimension"
    )


class SceneCoat3D(PropertyGroup):
    defaultfolder: StringProperty(
        name="FilePath",
        subtype="DIR_PATH",
    )
    cursor_loc: FloatVectorProperty(
        name="Cursor_loc",
        description="location"
    )
    exchangedir: StringProperty(
        name="FilePath",
        subtype="DIR_PATH"
    )
    exchangefolder: StringProperty(
        name="FilePath",
        subtype="DIR_PATH"
    )
    wasactive: StringProperty(
        name="Pass active object",
    )
    import_box: BoolProperty(
        name="Import window",
        description="Allows to skip import dialog",
        default=True
    )
    exchange_found: BoolProperty(
        name="Exchange Found",
        description="Alert if Exchange folder is not found",
        default=True
    )
    export_box: BoolProperty(
        name="Export window",
        description="Allows to skip export dialog",
        default=True
    )
    export_color: BoolProperty(
        name="Export color",
        description="Export color texture",
        default=True
    )
    export_spec: BoolProperty(
        name="Export specular",
        description="Export specular texture",
        default=True
    )
    export_normal: BoolProperty(
        name="Export Normal",
        description="Export normal texture",
        default=True
    )
    export_disp: BoolProperty(
        name="Export Displacement",
        description="Export displacement texture",
        default=True
    )
    export_position: BoolProperty(
        name="Export Source Position",
        description="Export source position",
        default=True
    )
    export_zero_layer: BoolProperty(
        name="Export from Layer 0",
        description="Export mesh from Layer 0",
        default=True
    )
    export_coarse: BoolProperty(
        name="Export Coarse",
        description="Export Coarse",
        default=True
    )
    exportfile: BoolProperty(
        name="No Import File",
        description="Add Modifiers and export",
        default=False
    )
    importmod: BoolProperty(
        name="Remove Modifiers",
        description="Import and add modifiers",
        default=False
    )
    exportmod: BoolProperty(
        name="Modifiers",
        description="Export modifiers",
        default=False
    )
    export_pos: BoolProperty(
        name="Remember Position",
        description="Remember position",
        default=True
    )
    importtextures: BoolProperty(
        name="Bring Textures",
        description="Import Textures",
        default=True
    )
    importlevel: BoolProperty(
        name="Multires. Level",
        description="Bring Specific Multires Level",
        default=False
    )
    exportover: BoolProperty(
        name="Export Obj",
        description="Import Textures",
        default=False
    )
    importmesh: BoolProperty(
        name="Mesh",
        description="Import Mesh",
        default=True
    )

    # copy location

    loca: FloatVectorProperty(
        name="location",
        description="Location",
        subtype="XYZ",
        default=(0.0, 0.0, 0.0)
    )
    rota: FloatVectorProperty(
        name="location",
        description="Location",
        subtype="EULER",
        default=(0.0, 0.0, 0.0)
    )
    scal: FloatVectorProperty(
        name="location",
        description="Location",
        subtype="XYZ",
        default=(0.0, 0.0, 0.0)
    )
    dime: FloatVectorProperty(
        name="dimension",
        description="Dimension",
        subtype="XYZ",
        default=(0.0, 0.0, 0.0)
    )
    type: EnumProperty(
        name="Export Type",
        description="Different Export Types",
        items=(("ppp", "Per-Pixel Painting", ""),
               ("mv", "Microvertex Painting", ""),
               ("ptex", "Ptex Painting", ""),
               ("uv", "UV-Mapping", ""),
               ("ref", "Reference Mesh", ""),
               ("retopo", "Retopo mesh as new layer", ""),
               ("vox", "Mesh As Voxel Object", ""),
               ("alpha", "Mesh As New Pen Alpha", ""),
               ("prim", "Mesh As Voxel Primitive", ""),
               ("curv", "Mesh As a Curve Profile", ""),
               ("autopo", "Mesh For Auto-retopology", ""),
               ),
        default="ppp"
    )
class MeshCoat3D(PropertyGroup):
    applink_address: StringProperty(
        name="ApplinkAddress",
        subtype="APPLINK_ADDRESS",
    )
class MaterialCoat3D(PropertyGroup):
    name: StringProperty(
        name="ApplinkAddress",
        subtype="APPLINK_ADDRESS",
    )


classes = (
    #ObjectButtonsPanel,
    SCENE_PT_Main,
    SCENE_OT_export,
    SCENE_OT_import,
    VIEW3D_MT_Coat_Dynamic_Menu,
    #VIEW3D_MT_ImportMenu,
    #VIEW3D_MT_ExportMenu,
    #VIEW3D_MT_ExtraMenu,
    ObjectCoat3D,
    SceneCoat3D,
    MeshCoat3D,
    MaterialCoat3D,
    )

def register():
    bpy.coat3D = dict()
    bpy.coat3D['active_coat'] = ''
    bpy.coat3D['status'] = 0
    bpy.coat3D['kuva'] = 1

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Object.coat3D = PointerProperty(type=ObjectCoat3D)
    bpy.types.Scene.coat3D = PointerProperty(type=SceneCoat3D)
    bpy.types.Mesh.coat3D = PointerProperty(type=MeshCoat3D)
    bpy.types.Material.coat3D = PointerProperty(type=MaterialCoat3D)

    kc = bpy.context.window_manager.keyconfigs.addon

    if kc:
        km = kc.keymaps.new(name="Object Mode")
        kmi = km.keymap_items.new('wm.call_menu', 'Q', 'PRESS')
        kmi.properties.name = "VIEW3D_MT_Coat_Dynamic_Menu"



def unregister():

    import bpy
    from bpy.utils import unregister_class

    del bpy.types.Object.coat3D
    del bpy.types.Scene.coat3D
    del bpy.types.Mesh.coat3D
    del bpy.coat3D

    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.get('Object Mode')
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu':
                if kmi.properties.name == "VIEW3D_MT_Coat_Dynamic_Menu":
                    km.keymap_items.remove(kmi)

    for cls in reversed(classes):
        unregister_class(cls)
