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

def RemoveFbxNodes(objekti):
    Node_Tree = objekti.active_material.node_tree
    for node in Node_Tree.nodes:
        if node.type != 'OUTPUT_MATERIAL':
            Node_Tree.nodes.remove(node)
        else:
            output = node
            output.location = 340,400
    Prin_mat = Node_Tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    Prin_mat.location = 13, 375

    Node_Tree.links.new(Prin_mat.outputs[0], output.inputs[0])

def readtexturefolder(objekti,is_new): #read textures from texture file

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
    uusin_mat = materiaali_muutos
    if(is_new == True and objekti.coat3D.obj_mat == ''):
        obj_coat.obj_mat = (objekti.coat3D.applink_name + '_' + objekti.data.uv_layers[0].name)
    elif (objekti.coat3D.obj_mat == ''):
        obj_coat.obj_mat = (objekti.coat3D.applink_name + '_' + uusin_mat)

    new_name = obj_coat.obj_mat + '_'
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

    coat3D = bpy.context.scene.coat3D

    if(objekti.active_material.use_nodes == False):
        objekti.active_material.use_nodes = True
    act_material = objekti.active_material.node_tree
    main_material = objekti.active_material.node_tree
    applink_group_node = False

    #ensimmaiseksi kaydaan kaikki image nodet lapi ja tarkistetaan onko nimi 3DC alkunen jos on niin reload

    for node in act_material.nodes:
        if(node.name == '3DC_Applink' and node.type == 'GROUP'):
            applink_group_node = True
            act_material = node.node_tree
            break


    for node in act_material.nodes:
        if(node.type == 'TEX_IMAGE'):
            if(node.name == '3DC_color'):
                print('halloo helsinki')
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
    if(applink_group_node == False and coat3D.creategroup):
        group_tree = bpy.data.node_groups.new('3DC_Applink', 'ShaderNodeTree')
        applink_tree = act_material.nodes.new('ShaderNodeGroup')
        applink_tree.name = '3DC_Applink'
        applink_tree.node_tree = group_tree
        applink_tree.location = -400, 300
        act_material = group_tree
        notegroup = act_material.nodes.new('NodeGroupOutput')

    main_mat = main_material.nodes['Material Output']
    if(main_mat.inputs['Surface'].is_linked == True):
        glue_mat = main_mat.inputs['Surface'].links[0].from_node
        if(glue_mat.inputs.find('Base Color') == -1):
            input_color = glue_mat.inputs.find('Color')
        else:
            input_color = glue_mat.inputs.find('Base Color')
        input_index = 0
        #Color
        if(bring_color == True and texcoat['color'] != []):
            node = act_material.nodes.new('ShaderNodeTexImage')
            node.name = '3DC_color'
            if (texcoat['color']):
                node.image = bpy.data.images.load(texcoat['color'][0])
            if(coat3D.createnodes):
                curvenode = act_material.nodes.new('ShaderNodeRGBCurve')
                curvenode.name = '3DC_RGBCurve'
                huenode = act_material.nodes.new('ShaderNodeHueSaturation')
                huenode.name = '3DC_HueSaturation'
                act_material.links.new(huenode.outputs[0], glue_mat.inputs[input_color])
                act_material.links.new(curvenode.outputs[0], huenode.inputs[4])
                act_material.links.new(node.outputs[0], curvenode.inputs[1])
                node.location = -990, 530
                curvenode.location = -660, 480
                huenode.location = -337, 335
                if(coat3D.creategroup):
                    act_material.links.new(huenode.outputs[0], notegroup.inputs[input_index])
                    group_tree.outputs[input_index].name = 'Color'
                    main_material.links.new(applink_tree.outputs[input_index], glue_mat.inputs[input_color])
                    input_index += 1
            else:
                if (coat3D.creategroup):
                    node.location = -400, 400
                    act_material.links.new(node.outputs[0], notegroup.inputs[input_index])
                    if (input_color != -1):
                        main_material.links.new(applink_tree.outputs[input_index], glue_mat.inputs[input_color])
                    input_index += 1

                else:
                    node.location = -400,400
                    if (input_color != -1):
                        act_material.links.new(node.outputs[0], glue_mat.inputs[input_color])

        #Metalness
        if(bring_metalness == True and texcoat['metalness'] != []):
            node = act_material.nodes.new('ShaderNodeTexImage')
            node.name='3DC_metalness'
            input_color = glue_mat.inputs.find('Metallic')
            if(texcoat['metalness']):
                node.image = bpy.data.images.load(texcoat['metalness'][0])
                node.color_space = 'NONE'
            if (coat3D.createnodes):
                curvenode = act_material.nodes.new('ShaderNodeRGBCurve')
                curvenode.name = '3DC_RGBCurve'
                huenode = act_material.nodes.new('ShaderNodeHueSaturation')
                huenode.name = '3DC_HueSaturation'
                act_material.links.new(huenode.outputs[0], glue_mat.inputs[input_color])
                act_material.links.new(curvenode.outputs[0], huenode.inputs[4])
                act_material.links.new(node.outputs[0], curvenode.inputs[1])
                node.location = -994, 119
                curvenode.location = -668, 113
                huenode.location = -345, 118
                if (coat3D.creategroup):
                    act_material.links.new(huenode.outputs[0], notegroup.inputs[input_index])
                    group_tree.outputs[input_index].name = 'Metalness'
                    main_material.links.new(applink_tree.outputs[input_index], glue_mat.inputs[input_color])
                    input_index += 1
            else:
                if (coat3D.creategroup):
                    node.location = -830, 160
                    act_material.links.new(node.outputs[0], notegroup.inputs[input_index])
                    if (input_color != -1):
                        main_material.links.new(applink_tree.outputs[input_index], glue_mat.inputs[input_color])
                        input_index += 1
                else:
                    node.location = -830, 160
                    if (input_color != -1):
                        act_material.links.new(node.outputs[0], glue_mat.inputs[input_color])

        #Roughness
        if(bring_roughness == True and texcoat['rough'] != []):
            node = act_material.nodes.new('ShaderNodeTexImage')
            node.name='3DC_roughness'
            input_color = glue_mat.inputs.find('Roughness')
            if(texcoat['rough']):
                node.image = bpy.data.images.load(texcoat['rough'][0])
                node.color_space = 'NONE'
            if (coat3D.createnodes):
                curvenode = act_material.nodes.new('ShaderNodeRGBCurve')
                curvenode.name = '3DC_RGBCurve'
                huenode = act_material.nodes.new('ShaderNodeHueSaturation')
                huenode.name = '3DC_HueSaturation'
                act_material.links.new(huenode.outputs[0], glue_mat.inputs[input_color])
                act_material.links.new(curvenode.outputs[0], huenode.inputs[4])
                act_material.links.new(node.outputs[0], curvenode.inputs[1])
                node.location = -1000, -276
                curvenode.location = -670, -245
                huenode.location = -340, -100
                if (coat3D.creategroup):
                    act_material.links.new(huenode.outputs[0], notegroup.inputs[input_index])
                    group_tree.outputs[input_index].name = 'Roughness'
                    main_material.links.new(applink_tree.outputs[input_index], glue_mat.inputs[input_color])
                    input_index += 1
            else:
                if (coat3D.creategroup):
                    node.location = -550, 0
                    act_material.links.new(node.outputs[0], notegroup.inputs[input_index])
                    if (input_color != -1):
                        main_material.links.new(applink_tree.outputs[input_index], glue_mat.inputs[input_color])
                        input_index += 1
                else:
                    node.location = -550, 0
                    if (input_color != -1):
                        act_material.links.new(node.outputs[0], glue_mat.inputs[input_color])

        #Normal map
        if(bring_normal == True and texcoat['nmap'] != []):
            node = act_material.nodes.new('ShaderNodeTexImage')
            normal_node = act_material.nodes.new('ShaderNodeNormalMap')
            node.location = -600,-670
            normal_node.location = -300,-300
            node.name='3DC_normal'
            normal_node.name='3DC_normalnode'
            if(texcoat['nmap']):
                node.image = bpy.data.images.load(texcoat['nmap'][0])
                node.color_space = 'NONE'
            input_color = glue_mat.inputs.find('Normal')
            act_material.links.new(node.outputs[0], normal_node.inputs[1])
            act_material.links.new(normal_node.outputs[0], glue_mat.inputs[input_color])
            if (coat3D.creategroup):
                act_material.links.new(normal_node.outputs[0], notegroup.inputs[input_index])
                main_material.links.new(applink_tree.outputs[input_index], glue_mat.inputs[input_color])
                input_index += 1



def matlab(mat_list, objekti, scene,is_new):

    ''' FBX Materials: remove all nodes and create princibles node'''
    if(is_new):
        RemoveFbxNodes(objekti)

    '''Main Loop for Texture Update'''
    #checkmaterial(mat_list, objekti)
    readtexturefolder(objekti,is_new)

    return('FINISHED')
