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
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

import bpy
import os
import re
def find_index(objekti):

    luku = 0
    for tex in objekti.active_material.texture_slots:
        if(not(hasattr(tex,'texture'))):
            break
        luku = luku +1
    return luku

def readtexturefolder(objekti,is_new): #read textures from texture file

    coat3D = bpy.context.scene.coat3D
    obj_coat = objekti.coat3D

    texcoat = {}
    texcoat['color'] = []
    texcoat['metalness'] = []
    texcoat['rough'] = []
    texcoat['nmap'] = []
    texcoat['disp'] = []


    files_dir = os.path.dirname(os.path.abspath(objekti.coat3D.applink_address))
    files = os.listdir(files_dir)
    materiaali_muutos = objekti.active_material.name
    uusin_mat = materiaali_muutos.replace('Material.','Material_')
    new_name = (obj_coat.applink_name + '_' + uusin_mat)
    name_boxs = new_name.split('.')
    if len(name_boxs) > 1:
        if len(name_boxs[-1]) == 3:
            new_name = new_name[:-4]
    for i in files:
        if(i.startswith(new_name)):
            koko_osoite = files_dir + os.sep + i
            listed = re.split(r'[_.]', i)
            tex_name = listed[-2]
            texcoat[tex_name].append(koko_osoite)

    createnodes(objekti, texcoat)

def checkmaterial(mat_list, objekti): #check how many materials object has
    mat_list = []

    for obj_mate in objekti.material_slots:
        if(obj_mate.material.use_nodes == False):
            obj_mate.material.use_nodes = True

def createnodes(objekti,texcoat): #luo nodes palikat ja linkittaa tekstuurit niihin
    bring_color = True #naiden tarkoitus on tsekata onko tarvetta luoda uusi node vai riittaako paivitys
    bring_metalness = True
    bring_roughness = True
    bring_normal = True
    bring_disp = True

    act_material = objekti.active_material
    if(objekti.active_material.use_nodes == False):
        objekti.active_material.use_nodes = True

    #ensimmaiseksi kaydaan kaikki image nodet lapi ja tarkistetaan onko nimi 3DC alkunen jos on niin reload

    for node in act_material.node_tree.nodes:
        if(node.type == 'TEX_IMAGE'):
            if(node.name == '3DC_color'):
                bring_color = False
                node.image.reload()
            elif(node.name == '3DC_metalness'):
                bring_metalness = False
                node.image.reload()
            elif(node.name == '3DC_roughness'):
                bring_roughness = False
                node.image.reload()
            elif(node.name == '3DC_normal'):
                bring_normal = False
                node.image.reload()

    #seuraavaksi lahdemme rakentamaan node tree. Lahdetaan Material Outputista rakentaa

    main_mat = act_material.node_tree.nodes['Material Output']
    if(main_mat.inputs['Surface'].is_linked == True):
        glue_mat = main_mat.inputs['Surface'].links[0].from_node

        #Color
        if(bring_color == True and glue_mat.inputs.find('Base Color') != -1 and texcoat['color'] != []):
            node = act_material.node_tree.nodes.new('ShaderNodeTexImage')
            node.location = -400,400
            node.name='3DC_color'
            if(texcoat['color']):
                node.image = bpy.data.images.load(texcoat['color'][0])
            input_color = glue_mat.inputs.find('Base Color')
            act_material.node_tree.links.new(node.outputs[0], glue_mat.inputs[input_color])

        #Metalness
        if(bring_metalness == True and glue_mat.inputs.find('Metallic') != -1 and texcoat['metalness'] != []):
            node = act_material.node_tree.nodes.new('ShaderNodeTexImage')
            node.location = -830,160
            node.name='3DC_metalness'
            if(texcoat['metalness']):
                node.image = bpy.data.images.load(texcoat['metalness'][0])
                node.color_space = 'NONE'
            input_color = glue_mat.inputs.find('Metallic')
            act_material.node_tree.links.new(node.outputs[0], glue_mat.inputs[input_color])

        #Roughness
        if(bring_roughness == True and glue_mat.inputs.find('Roughness') != -1 and texcoat['rough'] != []):
            node = act_material.node_tree.nodes.new('ShaderNodeTexImage')
            node.location = -550,0
            node.name='3DC_roughness'
            if(texcoat['rough']):
                node.image = bpy.data.images.load(texcoat['rough'][0])
                node.color_space = 'NONE'
            input_color = glue_mat.inputs.find('Roughness')
            act_material.node_tree.links.new(node.outputs[0], glue_mat.inputs[input_color])

        #Normal map
        if(bring_normal == True and glue_mat.inputs.find('Normal') != -1 and texcoat['nmap'] != []):
            node = act_material.node_tree.nodes.new('ShaderNodeTexImage')
            normal_node = act_material.node_tree.nodes.new('ShaderNodeNormalMap')
            node.location = -600,-370
            normal_node.location = -300,-270
            node.name='3DC_normal'
            if(texcoat['nmap']):
                node.image = bpy.data.images.load(texcoat['nmap'][0])
                node.color_space = 'NONE'
            input_color = glue_mat.inputs.find('Normal')
            act_material.node_tree.links.new(node.outputs[0], normal_node.inputs[1])
            act_material.node_tree.links.new(normal_node.outputs[0], glue_mat.inputs[input_color])

        bpy.ops.object.editmode_toggle() #HACKKI joka saa tekstuurit nakymaan heti
        bpy.ops.object.editmode_toggle()



def matlab(mat_list, objekti, scene,is_new):
    #checkmaterial(mat_list, objekti)
    readtexturefolder(objekti,is_new)

    return('FINISHED')
