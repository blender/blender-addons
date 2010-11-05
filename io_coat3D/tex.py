import bpy
import os
import filecmp


def objname(path):

    path2 = os.path.dirname(path) + os.sep
    print("kalle:%s"%path2)
    pituus = len(path2)
    nimi = path[pituus:]

    return nimi

def justname(name):
    monesko = name.rfind('.')
    justname = name[:monesko]
    return justname

def setgallery():
    newname =''
    tex_name =[]
    index_tex = 0
    for tt in bpy.data.textures:
        tex_name.append(tt.name)
    return tex_name

def find_index(objekti):
        luku = 0
        for tex in objekti.active_material.texture_slots:
                if(not(hasattr(tex,'texture'))):
                        break
                luku = luku +1
                

        return luku

def gettex(mat_list, objekti, scene,export):

    coat3D = bpy.context.scene.coat3D
    
    if(bpy.context.scene.render.engine == 'VRAY_RENDER' or bpy.context.scene.render.engine == 'VRAY_RENDER_PREVIEW'):
        vray = True
    else:
        vray = False
    
        
    
    take_color = 0;
    take_spec = 0;
    take_normal = 0;
    take_disp = 0;
    
    bring_color = 1;
    bring_spec = 1;
    bring_normal = 1;
    bring_disp = 1;

    texcoat = {}
    texcoat['color'] = []
    texcoat['specular'] = []
    texcoat['nmap'] = []
    texcoat['disp'] = []
    texu = []

    if(export):
        objekti.coat3D.objpath = export
        nimi = objname(export)
        osoite = os.path.dirname(export) + os.sep
        for mate in objekti.material_slots:
            for tex_slot in mate.material.texture_slots:
                if(hasattr(tex_slot,'texture')):
                    if(tex_slot.texture.type == 'IMAGE'):
                                                tex_slot.texture.image.reload()
    else:
        nimi = objname(coat3D.objectdir)
        osoite = os.path.dirname(coat3D.objectdir) + os.sep
    just_nimi = justname(nimi)
    just_nimi += '_'
    just_nimi_len = len(just_nimi)
        
    
    if(len(objekti.material_slots) != 0):
        for obj_tex in objekti.active_material.texture_slots:
            if(hasattr(obj_tex,'texture')):
                if(obj_tex.texture):
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
        #date = os.path.getmtime(texcoat[tex_name][0])

    if((texcoat['color'] or texcoat['nmap'] or texcoat['disp'] or texcoat['specular']) and (len(objekti.material_slots)) == 0):
        new_mat = ("%s_Material"%(objekti.name))
        bpy.data.materials.new(new_mat)
        ki = bpy.data.materials[new_mat]
        objekti.data.materials.append(ki)
        
        
            
    if(bring_color == 1 and texcoat['color']):
        name_tex ='Color_'
        num = []

        index = find_index(objekti)
        

        tex = bpy.ops.Texture
        objekti.active_material.texture_slots.create(index)
        total_mat = len(objekti.active_material.texture_slots.items())
        useold = ''
        
        for seekco in bpy.data.textures:
            if((seekco.name[:6] == 'Color_') and (seekco.users_material == ())):
                useold = seekco



        if(useold == ''):

            tex_name = setgallery()

            for num_tex in tex_name:
                if(num_tex[:6] == 'Color_'):
                    num.append(num_tex)
            luku_tex = len(num)
            name_tex = ('Color_%s'%(luku_tex))

            bpy.ops.image.new(name=name_tex)
            bpy.data.images[name_tex].filepath = texcoat['color'][0]
            bpy.data.images[name_tex].source = 'FILE'
            

            bpy.data.textures.new(name_tex,type='IMAGE')
            objekti.active_material.texture_slots[index].texture = bpy.data.textures[name_tex]
            objekti.active_material.texture_slots[index].texture.image = bpy.data.images[name_tex]
        
            if(objekti.data.uv_textures.active):
                objekti.active_material.texture_slots[index].texture_coords = 'UV'
                objekti.active_material.texture_slots[index].uv_layer = objekti.data.uv_textures.active.name

            objekti.active_material.texture_slots[index].texture.image.reload()
            

        elif(useold != ''):
            
            objekti.active_material.texture_slots[index].texture = useold
            objekti.active_material.texture_slots[index].texture.image.filepath = texcoat['color'][0]
            if(objekti.data.uv_textures.active):
                objekti.active_material.texture_slots[index].texture_coords = 'UV'
                objekti.active_material.texture_slots[index].uv_layer = objekti.data.uv_textures.active.name
    
    if(bring_normal == 1 and texcoat['nmap']):
        name_tex ='Normal_'
        num = []
        
        index = find_index(objekti)
        

        tex = bpy.ops.Texture
        objekti.active_material.texture_slots.create(index)
        total_mat = len(objekti.active_material.texture_slots.items())
        useold = ''
        
        for seekco in bpy.data.textures:
            if((seekco.name[:7] == 'Normal_') and (seekco.users_material == ())):
                useold = seekco

        

        if(useold == ''):

            tex_name = setgallery()

            for num_tex in tex_name:
                if(num_tex[:7] == 'Normal_'):
                    num.append(num_tex)
            luku_tex = len(num)
            name_tex = ('Normal_%s'%(luku_tex))

            bpy.ops.image.new(name=name_tex)
            bpy.data.images[name_tex].filepath = texcoat['nmap'][0]
            bpy.data.images[name_tex].source = 'FILE'
            

            bpy.data.textures.new(name_tex,type='IMAGE')
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
                bpy.data.textures[name_tex].normal_space = 'TANGENT'
            

        elif(useold != ''):
            
            objekti.active_material.texture_slots[index].texture = useold
            objekti.active_material.texture_slots[index].texture.image.filepath = texcoat['nmap'][0]
            if(objekti.data.uv_textures.active):
                objekti.active_material.texture_slots[index].texture_coords = 'UV'
                objekti.active_material.texture_slots[index].uv_layer = objekti.data.uv_textures.active.name
            objekti.active_material.texture_slots[index].use_map_color_diffuse = False
            objekti.active_material.texture_slots[index].use_map_normal = True


    if(bring_spec == 1 and texcoat['specular']):
        name_tex ='Specular_'
        num = []

        index = find_index(objekti)
        

        tex = bpy.ops.Texture
        objekti.active_material.texture_slots.create(index)
        total_mat = len(objekti.active_material.texture_slots.items())
        useold = ''
        
        for seekco in bpy.data.textures:
            if((seekco.name[:9] == 'Specular_') and (seekco.users_material == ())):
                useold = seekco

        


        if(useold == ''):

            tex_name = setgallery()

            for num_tex in tex_name:
                if(num_tex[:9] == 'Specular_'):
                    num.append(num_tex)
            luku_tex = len(num)
            name_tex = ('Specular_%s'%(luku_tex))

            bpy.ops.image.new(name=name_tex)
            bpy.data.images[name_tex].filepath = texcoat['specular'][0]
            bpy.data.images[name_tex].source = 'FILE'
            

            bpy.data.textures.new(name_tex,type='IMAGE')
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
            objekti.active_material.texture_slots[index].texture.image.filepath = texcoat['specular'][0]
            if(objekti.data.uv_textures.active):
                objekti.active_material.texture_slots[index].texture_coords = 'UV'
                objekti.active_material.texture_slots[index].uv_layer = objekti.data.uv_textures.active.name
            objekti.active_material.texture_slots[index].use_map_color_diffuse = False
            objekti.active_material.texture_slots[index].use_map_specular = True

    if(bring_disp == 1 and texcoat['disp']):
        name_tex ='Displacement_'
        num = []

        index = find_index(objekti)
        

        tex = bpy.ops.Texture
        objekti.active_material.texture_slots.create(index)
        total_mat = len(objekti.active_material.texture_slots.items())
        useold = ''
        
        for seekco in bpy.data.textures:
            if((seekco.name[:13] == 'Displacement_') and (seekco.users_material == ())):
                useold = seekco

        


        if(useold == ''):

            tex_name = setgallery()

            for num_tex in tex_name:
                if(num_tex[:13] == 'Displacement_'):
                    num.append(num_tex)
            luku_tex = len(num)
            name_tex = ('Displacement_%s'%(luku_tex))

            bpy.ops.image.new(name=name_tex)
            bpy.data.images[name_tex].filepath = texcoat['disp'][0]
            bpy.data.images[name_tex].source = 'FILE'
            

            bpy.data.textures.new(name_tex,type='IMAGE')
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

    return('FINISHED')
