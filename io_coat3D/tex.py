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

    if(is_new == True):
        files_dir = os.path.dirname(os.path.abspath(objekti.coat3D.applink_address))
    else:
        files_dir = os.path.dirname(os.path.abspath(objekti.coat3D.applink_address))
        files_dir = files_dir.replace('3DC2Blender' + os.sep + 'Objects','3DC2Blender' + os.sep + 'Textures')
    files = os.listdir(files_dir)
    materiaali_muutos = objekti.active_material.name
    uusin_mat = materiaali_muutos.replace('Material.','Material_')
    for i in files:
        if(i.startswith(obj_coat.applink_name + '_' + uusin_mat)):
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
            node.location = -600,200
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
            node.location = -600,-270
            normal_node.location = -300,-170
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


    """
    print('tassa tietoo')
    print(mat_list,objekti,scene,export)

    coat3D = bpy.context.scene.coat3D
    coa = objekti.coat3D
    print(coat3D,coa)

    if(bpy.context.scene.render.engine == 'VRAY_RENDER' or bpy.context.scene.render.engine == 'VRAY_RENDER_PREVIEW'):
        vray = True
    else:
        vray = False

    take_color = 0
    take_spec = 0
    take_normal = 0
    take_disp = 0

    bring_color = 1
    bring_spec = 1
    bring_normal = 1
    bring_disp = 1
    
    texcoat = {}
    texcoat['color'] = []
    texcoat['specular'] = []
    texcoat['nmap'] = []
    texcoat['disp'] = []
    texu = []

    if(export):
        objekti.coat3D.objpath = export
        nimi = os.path.split(export)[1]
        osoite = os.path.dirname(export) + os.sep #pitaa ehka muuttaa
        for mate in objekti.material_slots:
            for tex_slot in mate.material.texture_slots:
                if(hasattr(tex_slot,'texture')):
                    if(tex_slot.texture.type == 'IMAGE'):
                        if tex_slot.texture.image is not None:
                            tex_slot.texture.image.reload()
    else:
        if(os.sys.platform == 'win32'):
            osoite = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'Textures' + os.sep
        else:
            osoite = os.path.expanduser("~") + os.sep + '3DC2Blender' + os.sep + 'Textures' + os.sep
    ki = os.path.split(coa.applink_name)[1]
    ko = os.path.splitext(ki)[0]
    just_nimi = ko + '_'
    just_nimi_len = len(just_nimi)
    print('terve:' + coa.applink_name)

    if(len(objekti.material_slots) != 0):
        for obj_tex in objekti.active_material.texture_slots:
            if(hasattr(obj_tex,'texture')):
                if(obj_tex.texture.type == 'IMAGE'):
                    if(obj_tex.use_map_color_diffuse):
                        bring_color = 0;
                    if(obj_tex.use_map_specular):
                        bring_spec = 0;
                    if(obj_tex.use_map_normal):
                        bring_normal = 0;
                    if(obj_tex.use_map_displacement):
                        bring_disp = 0;

    files = os.listdir(osoite)
    for i in files:
        tui = i[:just_nimi_len]
        if(tui == just_nimi):
            texu.append(i)

    for yy in texu:
        minimi = (yy.rfind('_'))+1
        maksimi = (yy.rfind('.'))
        tex_name = yy[minimi:maksimi]
        koko = ''
        koko += osoite
        koko += yy
        texcoat[tex_name].append(koko)

    if((texcoat['color'] or texcoat['nmap'] or texcoat['disp'] or texcoat['specular']) and (len(objekti.material_slots)) == 0):
        materials_old = bpy.data.materials.keys()
        bpy.ops.material.new()
        materials_new = bpy.data.materials.keys()
        new_ma = list(set(materials_new).difference(set(materials_old)))
        new_mat = new_ma[0]
        ki = bpy.data.materials[new_mat]
        objekti.data.materials.append(ki)

    if(bring_color == 1 and texcoat['color']):
        index = find_index(objekti)
        tex = bpy.ops.Texture
        objekti.active_material.texture_slots.create(index)
        total_mat = len(objekti.active_material.texture_slots.items())
        useold = ''

        for seekco in bpy.data.textures:
            if((seekco.name[:5] == 'Color') and (seekco.users_material == ())):
                useold = seekco


        if(useold == ''):

            textures_old = bpy.data.textures.keys()
            bpy.data.textures.new('Color',type='IMAGE')
            textures_new = bpy.data.textures.keys()
            name_te = list(set(textures_new).difference(set(textures_old)))
            name_tex = name_te[0]

            bpy.ops.image.new(name=name_tex)
            bpy.data.images[name_tex].filepath = texcoat['color'][0]
            bpy.data.images[name_tex].source = 'FILE'

            objekti.active_material.texture_slots[index].texture = bpy.data.textures[name_tex]
            objekti.active_material.texture_slots[index].texture.image = bpy.data.images[name_tex]

            if(objekti.data.uv_textures.active):
                objekti.active_material.texture_slots[index].texture_coords = 'UV'
                objekti.active_material.texture_slots[index].uv_layer = objekti.data.uv_textures.active.name

            objekti.active_material.texture_slots[index].texture.image.reload()


        elif(useold != ''):

            objekti.active_material.texture_slots[index].texture = useold
            objekti.active_material.texture_slots[index].texture.image = bpy.data.images[useold.name]
            objekti.active_material.texture_slots[index].texture.image.filepath = texcoat['color'][0]
            if(objekti.data.uv_textures.active):
                objekti.active_material.texture_slots[index].texture_coords = 'UV'
                objekti.active_material.texture_slots[index].uv_layer = objekti.data.uv_textures.active.name


    if(bring_normal == 1 and texcoat['nmap']):
        index = find_index(objekti)
        tex = bpy.ops.Texture
        objekti.active_material.texture_slots.create(index)
        total_mat = len(objekti.active_material.texture_slots.items())
        useold = ''

        for seekco in bpy.data.textures:
            if((seekco.name[:6] == 'Normal') and (seekco.users_material == ())):
                useold = seekco

        if(useold == ''):

            textures_old = bpy.data.textures.keys()
            bpy.data.textures.new('Normal',type='IMAGE')
            textures_new = bpy.data.textures.keys()
            name_te = list(set(textures_new).difference(set(textures_old)))
            name_tex = name_te[0]

            bpy.ops.image.new(name=name_tex)
            bpy.data.images[name_tex].filepath = texcoat['nmap'][0]
            bpy.data.images[name_tex].source = 'FILE'

            objekti.active_material.texture_slots[index].texture = bpy.data.textures[name_tex]
            objekti.active_material.texture_slots[index].texture.image = bpy.data.images[name_tex]

            if(objekti.data.uv_textures.active):
                objekti.active_material.texture_slots[index].texture_coords = 'UV'
                objekti.active_material.texture_slots[index].uv_layer = objekti.data.uv_textures.active.name

            objekti.active_material.texture_slots[index].use_map_color_diffuse = False
            objekti.active_material.texture_slots[index].use_map_normal = True

            objekti.active_material.texture_slots[index].texture.image.reload()
            if(vray):
                bpy.data.textures[name_tex].vray_slot.BRDFBump.map_type = 'TANGENT'

            else:
                bpy.data.textures[name_tex].use_normal_map = True
                objekti.active_material.texture_slots[index].normal_map_space = 'TANGENT'
                objekti.active_material.texture_slots[index].normal_factor = 1



        elif(useold != ''):

            objekti.active_material.texture_slots[index].texture = useold
            objekti.active_material.texture_slots[index].texture.image = bpy.data.images[useold.name]
            objekti.active_material.texture_slots[index].texture.image.filepath = texcoat['nmap'][0]
            if(objekti.data.uv_textures.active):
                objekti.active_material.texture_slots[index].texture_coords = 'UV'
                objekti.active_material.texture_slots[index].uv_layer = objekti.data.uv_textures.active.name
            objekti.active_material.texture_slots[index].use_map_color_diffuse = False
            objekti.active_material.texture_slots[index].use_map_normal = True
            objekti.active_material.texture_slots[index].normal_factor = 1


    if(bring_spec == 1 and texcoat['specular']):

        index = find_index(objekti)

        objekti.active_material.texture_slots.create(index)
        useold = ''

        for seekco in bpy.data.textures:
            if((seekco.name[:8] == 'Specular') and (seekco.users_material == ())):
                useold = seekco

        if(useold == ''):

            textures_old = bpy.data.textures.keys()
            bpy.data.textures.new('Specular',type='IMAGE')
            textures_new = bpy.data.textures.keys()
            name_te = list(set(textures_new).difference(set(textures_old)))
            name_tex = name_te[0]

            bpy.ops.image.new(name=name_tex)
            bpy.data.images[name_tex].filepath = texcoat['specular'][0]
            bpy.data.images[name_tex].source = 'FILE'

            objekti.active_material.texture_slots[index].texture = bpy.data.textures[name_tex]
            objekti.active_material.texture_slots[index].texture.image = bpy.data.images[name_tex]

            if(objekti.data.uv_textures.active):
                objekti.active_material.texture_slots[index].texture_coords = 'UV'
                objekti.active_material.texture_slots[index].uv_layer = objekti.data.uv_textures.active.name

            objekti.active_material.texture_slots[index].use_map_color_diffuse = False
            objekti.active_material.texture_slots[index].use_map_specular = True

            objekti.active_material.texture_slots[index].texture.image.reload()


        elif(useold != ''):

            objekti.active_material.texture_slots[index].texture = useold
            objekti.active_material.texture_slots[index].texture.image = bpy.data.images[useold.name]
            objekti.active_material.texture_slots[index].texture.image.filepath = texcoat['specular'][0]
            if(objekti.data.uv_textures.active):
                objekti.active_material.texture_slots[index].texture_coords = 'UV'
                objekti.active_material.texture_slots[index].uv_layer = objekti.data.uv_textures.active.name
            objekti.active_material.texture_slots[index].use_map_color_diffuse = False
            objekti.active_material.texture_slots[index].use_map_specular = True

    if(bring_disp == 1 and texcoat['disp']):

        index = find_index(objekti)


        objekti.active_material.texture_slots.create(index)
        useold = ''

        for seekco in bpy.data.textures:
            if((seekco.name[:12] == 'Displacement') and (seekco.users_material == ())):
                useold = seekco

        if useold == "":

            textures_old = bpy.data.textures.keys()
            bpy.data.textures.new('Displacement',type='IMAGE')
            textures_new = bpy.data.textures.keys()
            name_te = list(set(textures_new).difference(set(textures_old)))
            name_tex = name_te[0]

            bpy.ops.image.new(name=name_tex)
            bpy.data.images[name_tex].filepath = texcoat['disp'][0]
            bpy.data.images[name_tex].source = 'FILE'

            objekti.active_material.texture_slots[index].texture = bpy.data.textures[name_tex]
            objekti.active_material.texture_slots[index].texture.image = bpy.data.images[name_tex]

            if(objekti.data.uv_textures.active):
                objekti.active_material.texture_slots[index].texture_coords = 'UV'
                objekti.active_material.texture_slots[index].uv_layer = objekti.data.uv_textures.active.name

            objekti.active_material.texture_slots[index].use_map_color_diffuse = False
            objekti.active_material.texture_slots[index].use_map_displacement = True

            objekti.active_material.texture_slots[index].texture.image.reload()


        elif(useold != ''):

            objekti.active_material.texture_slots[index].texture = useold
            objekti.active_material.texture_slots[index].texture.image = bpy.data.images[useold.name]
            objekti.active_material.texture_slots[index].texture.image.filepath = texcoat['disp'][0]
            if(objekti.data.uv_textures.active):
                objekti.active_material.texture_slots[index].texture_coords = 'UV'
                objekti.active_material.texture_slots[index].uv_layer = objekti.data.uv_textures.active.name
            objekti.active_material.texture_slots[index].use_map_color_diffuse = False
            objekti.active_material.texture_slots[index].use_map_displacement = True

        if(vray):
            objekti.active_material.texture_slots[index].texture.use_interpolation = False
            objekti.active_material.texture_slots[index].displacement_factor = 0.05


        else:
            disp_modi = ''
            for seek_modi in objekti.modifiers:
                if(seek_modi.type == 'DISPLACE'):
                    disp_modi = seek_modi
                    break
            if(disp_modi):
                disp_modi.texture = objekti.active_material.texture_slots[index].texture
                if(objekti.data.uv_textures.active):
                    disp_modi.texture_coords = 'UV'
                    disp_modi.uv_layer = objekti.data.uv_textures.active.name
            else:
                objekti.modifiers.new('Displace',type='DISPLACE')
                objekti.modifiers['Displace'].texture = objekti.active_material.texture_slots[index].texture
                if(objekti.data.uv_textures.active):
                    objekti.modifiers['Displace'].texture_coords = 'UV'
                    objekti.modifiers['Displace'].uv_layer = objekti.data.uv_textures.active.name
    """
    return('FINISHED')
