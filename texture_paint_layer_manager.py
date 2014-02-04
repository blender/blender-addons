bl_info = {
    "name": "Texture Paint Layer Manager",
    "author": "Michael Wiliamson",
    "version": (1, 0),
    "blender": (2, 57, 0),
    "location": "Texture Paint > Properties > Texture Paint Layers Panels",
    "description": "Adds a layer manager for image based texture slots in paint and quick add layer tools",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/3D_interaction/Texture_paint_layers",
    "tracker_url": "https://developer.blender.org/T26789",
    "category": "Paint"}
        
        
import bpy
from bpy.props import*
import os
from bpy_extras.io_utils import ImportHelper


#-------------------------------------------

def load_a_brush(context, filepath):
    if os.path.isdir(filepath):
        return
        
    else:

        try:
            fn = bpy.path.display_name_from_filepath(filepath)
            #create image and load...
            img = bpy.data.images.load(filepath)
            img.use_fake_user =True
            
            #create a texture
            tex = bpy.data.textures.new(name =fn, type='IMAGE')
            tex.use_fake_user =True
            #tex.use_calculate_alpha = True
            
            #link the img to the texture
            tex.image = img
            
        except:
            print(f,'is not image?')

    return {'FINISHED'}




class load_single_brush(bpy.types.Operator, ImportHelper):
    """Load an image as a brush texture"""
    bl_idname = "texture.load_single_brush"  
    bl_label = "Load Image as Brush"


    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        return load_a_brush(context, self.filepath)

#-------------------------------------------

def loadbrushes(context, filepath):
    if os.path.isdir(filepath):
        directory = filepath
        
    else:
        #is a file, find parent directory    
        li = filepath.split(os.sep)
        directory = filepath.rstrip(li[-1])
        
        
    files = os.listdir(directory)
    for f in files:
        try:
            fn = f[3:]
            #create image and load...
            img = bpy.data.images.load(filepath = directory +os.sep + f)
            img.use_fake_user =True
            
            #create a texture
            tex = bpy.data.textures.new(name =fn, type='IMAGE')
            tex.use_fake_user =True
            #tex.use_calculate_alpha = True
            
            #link the img to the texture
            tex.image = img
            
        except:
            print(f,'is not image?')
            continue
    return {'FINISHED'}




class ImportBrushes(bpy.types.Operator, ImportHelper):
    """Load a directory of images as brush textures"""
    bl_idname = "texture.load_brushes"  
    bl_label = "Load brushes directory"


    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        return loadbrushes(context, self.filepath)

#-------------------------------------------------------------------

class OBJECT_PT_LoadBrushes(bpy.types.Panel):
    bl_label = "Load Brush images"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "texturepaint"
    
    @classmethod
    def poll(cls, context):
        return (context.sculpt_object or context.image_paint_object)
    
    def draw(self, context):
        layout = self.layout

        layout.operator('texture.load_brushes')
        layout.operator('texture.load_single_brush')


#======================================================================





class OBJECT_PT_Texture_paint_layers(bpy.types.Panel):
    bl_label = "Texture Paint Layers"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    #bl_context = "texturepaint"
    
    @classmethod
    def poll(cls, context):
        return (context.image_paint_object)
    
    def draw(self, context):
        layout = self.layout

        ob = bpy.context.image_paint_object
        if ob:
            mat = ob.active_material
            if not mat:
                row = layout.row() 
                row.label(' Add a Material first!', icon = 'ERROR')
            else:
                row = layout.row()
                row.template_list("UI_UL_list", "texture_paint_layers", ob, "material_slots", ob,
                                  "active_material_index", rows=2 )

                #list Paintable textures
                #TODO add filter for channel type
                i = -1
                for t in mat.texture_slots:
                    i+=1
                    try:
                        if t.texture.type =='IMAGE':                
                            row = layout.row(align= True)                
                            if t.texture == mat.active_texture:
                                ai =  'BRUSH_DATA'
                            else:
                                ai = 'BLANK1'
                            row.operator('object.set_active_paint_layer', 
                                text = "", icon = ai).tex_index =i   
                            row.prop(t.texture,'name', text = "")
            
        
                            #Visibility
                            if t.use:
                                ic = 'RESTRICT_VIEW_OFF'
                            else:
                                ic = 'RESTRICT_VIEW_ON'
                            row.prop(t,'use', text = "",icon = ic)
                    except:
                        continue
    
            
    


            
            ts = mat.texture_slots[mat.active_texture_index]
    
            if ts:
                row = layout.row()

    
                
                
                col = layout.column(align =True)
                col.label('Active Properties:', icon = 'BRUSH_DATA') 
                    
                #use if rather than elif... can be mapped to multiple things                                   
                if ts.use_map_diffuse:
                    col.prop(ts,'diffuse_factor', slider = True)
                if ts.use_map_color_diffuse:
                    col.prop(ts,'diffuse_color_factor', slider = True)
                if ts.use_map_alpha:
                    col.prop(ts,'alpha_factor', slider = True)
                if ts.use_map_translucency:
                    col.prop(ts,'translucency_factor', slider = True)
                if ts.use_map_specular:
                    col.prop(ts,'specular_factor', slider = True)
                if ts.use_map_color_spec:
                    col.prop(ts,'specular_color_factor', slider = True)
                if ts.use_map_hardness:
                    col.prop(ts,'hardness_factor', slider = True)
                    
                if ts.use_map_normal:
                    col.prop(ts,'normal_factor', slider = True)
                if ts.use_map_warp:
                    col.prop(ts,'warp_factor', slider = True)
                if ts.use_map_displacement:
                    col.prop(ts,'displacement_factor', slider = True)  
                    
                if ts.use_map_ambient:
                    col.prop(ts,'ambient_factor', slider = True)               
                if ts.use_map_emit:
                    col.prop(ts,'emit_factor', slider = True)                  
                if ts.use_map_mirror:
                    col.prop(ts,'mirror_factor', slider = True)    
                if ts.use_map_raymir:
                    col.prop(ts,'raymir_factor', slider = True)    
                 
                                    
                col.prop(ts,'blend_type',text='')   
        
            else:
                row=layout.row()
                row.label('No paint layers in material', icon = 'ERROR')        

#            
#        row = layout.row()
#        row.label('')              
#        row = layout.row()
#        row.label('WIP: Use the X to delete!:')                  
#        row = layout.row()                 
#        row.template_ID(mat, "active_texture", new="texture.new") 


class OBJECT_PT_Texture_paint_add(bpy.types.Panel):
    bl_label = "Add Paint Layers"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    #bl_context = "texturepaint"
    
    @classmethod
    def poll(cls, context):
        return (context.image_paint_object)

    def draw(self, context):
        layout = self.layout

        ob = bpy.context.image_paint_object
        if ob:
            mat = ob.active_material
            
            if mat:  
                col = layout.column(align =True)
        
                col.operator('object.add_paint_layer',
                    text = "Add Color").ttype = 'COLOR' 
                col.operator('object.add_paint_layer',
                    text = "Add Bump").ttype = 'NORMAL'
                    
                col = layout.column(align =True)
                col.operator('object.add_paint_layer',
                    text = "Add Specular").ttype = 'SPECULAR'
                col.operator('object.add_paint_layer',
                    text = "Add Spec Col").ttype = 'SPEC_COL'
                col.operator('object.add_paint_layer',
                    text = "Add Hardness").ttype = 'HARDNESS' 
                    
                col = layout.column(align =True)    
                col.operator('object.add_paint_layer',
                    text = "Add Alpha").ttype = 'ALPHA' 
                col.operator('object.add_paint_layer',
                    text = "Add Translucency").ttype = 'TRANSLUCENCY'
                    
#                col = layout.column(align =True)                      
#                col.operator('object.add_paint_layer',
#                    text = "Add Mirror").ttype = 'MIRROR' 
#                col.operator('object.add_paint_layer',
#                    text = "Add Ray Mirror").ttype = 'RAY_MIRROR'   
                    
                col = layout.column(align =True)                      
                col.operator('object.add_paint_layer',
                    text = "Add Emit").ttype = 'EMIT' 
                col.operator('object.add_paint_layer',
                    text = "Add Diffuse").ttype = 'DIFFUSE'   
                col.operator('object.add_paint_layer',
                    text = "Add Ambient").ttype = 'AMBIENT' 
                                        
            else:
                layout.label(' Add a Material first!', icon = 'ERROR')
        
        

def main(context,tn):
    #tn is the index of the texture in the active material
    ob = context.active_object
    me = ob.data
    mat = ob.active_material
    mat.active_texture_index = tn    
    ts = mat.texture_slots[tn]

    #make sure it's visible
    ts.use = True

    #Mesh use UVs?
    if not me.uv_textures:
        bpy.ops.mesh.uv_texture_add()
        
    # texture Slot uses UVs?
    if ts.texture_coords  == 'UV':
        if ts.uv_layer:
            uvtex = me.uv_textures[ts.uv_layer]
        
        else:
            uvtex = me.uv_textures.active
            me.uv_textures.active= uvtex
    else:
        ts.texture_coords ='UV'
        uvtex = me.uv_textures.active
        
        
    uvtex = uvtex.data.values()
    
    
    #get image from texture slot
    img = ts.texture.image
    
    #get material index
    m_id = ob.active_material_index 

    if img:
        for f in me.polygons:  
            if f.material_index == m_id:
                uvtex[f.index].image = img

            

    else:
        for f in me.polygons:  
            if f.material_index == m_id:
                uvtex[f.index].image = None
 
    me.update()







class set_active_paint_layer(bpy.types.Operator):
    """"""
    bl_idname = "object.set_active_paint_layer"
    bl_label = "set_active_paint_layer"
    tex_index = IntProperty(name = 'tex_index', 
        description = "", default = 0)

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        tn = self.tex_index
        main(context, tn)
        return {'FINISHED'}



def add_image_kludge(iname = 'grey', iwidth = 256, iheight = 256, 
        icolor = (0.5,0.5,0.5,1.0), nfloat = False):
    #evil kludge to get index of new image created using bpy.ops
    #store current images
    tl =[]
    for i in bpy.data.images:
        tl.append(i.name)
    
    
    #create a new image

    bpy.ops.image.new(name =iname,width =iwidth,height =iheight, 
            color = icolor, float = nfloat)
        
    #find its creation index
    it = 0
    for i in bpy.data.images:
        if i.name not in tl:
            return(bpy.data.images[it])
            break
        it += 1
        
    
def add_paint(context, size =2048, typ = 'NORMAL'):
    
    ob = bpy.context.object
    mat = ob.active_material
    ts = mat.texture_slots.add()
    ifloat = False

    if typ =='NORMAL':
        color =(0.5,0.5,0.5,1.0)
        iname = 'Bump'
        ifloat = True
    elif typ =='COLOR':
        iname ='Color'
        color = (1.0,1.0,1.0,0.0)

    elif typ =='ALPHA':
        iname ='Alpha'
        color = (1.0,1.0,1.0,0.0)                  
    else:
        color =(0.0,0.0,0.0,1.0)
        iname = typ.capitalize()
        
#    bn = bpy.context.blend_data.filepath.split(bpy.utils._os.sep)[-1]
#    bn = bn.replace('.blend', '')
    bn = ob.name
    
    iname = bn +'_' + iname 
      
    tex = bpy.data.textures.new(name = iname, type = 'IMAGE')
    ts.texture = tex
    img = add_image_kludge(iname = typ, 
        iwidth = size,iheight = size, icolor= color, nfloat = ifloat)
    tex.image = img
    
    if typ == 'COLOR':
        ts.use_map_color_diffuse =True

        
    elif typ == 'NORMAL':
        ts.use_map_normal = True
        ts.use_map_color_diffuse =False
        ts.normal_factor = -1
        ts.bump_method='BUMP_MEDIUM_QUALITY'
        ts.bump_objectspace='BUMP_OBJECTSPACE'
        
    elif typ == 'SPECULAR':
        ts.use_map_specular = True
        ts.use_map_color_diffuse =False
        ts.use_rgb_to_intensity = True
        #ts.blend_type = 'MULTIPLY'
        
    elif typ == 'EMIT':
        ts.use_map_emit = True
        ts.use_map_color_diffuse =False
        ts.use_rgb_to_intensity = True
        
    elif typ == 'ALPHA':
        mat.use_transparency = True
        ts.use_map_alpha = True
        ts.use_map_color_diffuse =False
        ts.use_rgb_to_intensity = True
        ts.blend_type = 'MULTIPLY'
        
    elif typ == 'SPEC_COL':
        ts.use_map_color_spec = True
        ts.use_map_color_diffuse =False
        ts.use_rgb_to_intensity = True
        
    elif typ == 'HARDNESS':
        ts.use_map_hardness = True
        ts.use_map_color_diffuse =False
        ts.use_rgb_to_intensity = True        
        
    elif typ == 'DIFFUSE':
        ts.use_map_diffuse = True
        ts.use_map_color_diffuse =False
        ts.use_rgb_to_intensity = True         

    elif typ == 'TRANSLUCENCY':
        ts.use_map_translucency = True
        ts.use_map_color_diffuse =False
        ts.use_rgb_to_intensity = True 

    elif typ == 'AMBIENT':
        ts.use_map_ambient = True
        ts.use_map_color_diffuse =False
        ts.use_rgb_to_intensity = True
         
    elif typ == 'MIRROR':
        ts.use_map_mirror = True
        ts.use_map_color_diffuse =False
        ts.use_rgb_to_intensity = True 
                        
    elif typ == 'RAY_MIRROR':
        mat.raytrace_mirror.use = True
        ts.use_map_ray_mirror = True
        ts.use_map_color_diffuse =False
        ts.use_rgb_to_intensity = True 
                                               
    #set new texture slot to active
    i = 0
    ts_index = None
    for t in mat.texture_slots:
        if t == ts:
            
            ts_index = i
            break
        i += 1
    if ts_index != None:
        mat.active_texture_index = ts_index
    
    #set the texfaces using this material.
        main(context,ts_index)
    
    
    
    

class add_paint_layer(bpy.types.Operator):
    """"""
    bl_idname = "object.add_paint_layer"
    bl_label = "Add Paint Layer"
    ttype = StringProperty(name ='ttype',default ='NORMAL')
    
    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        ttype = self.ttype
        add_paint(context,typ= ttype)
        return {'FINISHED'}
        



#----------------------------------------------
def save_painted(ts):
    #generated images don't  have a path 
    #so don't get saved with "save_dirty"
    #ts is a texture slot object.
    
    sep = bpy.utils._os.sep
    if ts:
        if ts.texture.type =='IMAGE':
            i = ts.texture.image
            if i.source =='GENERATED':
                if i.is_dirty:
                    name = ts.name
                    if i.file_format =='PNG':
                        name = name + '.png'
                    elif i.file_format =='TARGA':   
                        name = name +'.tga' 
                        
                    bpy.context.scene.render.image_settings.color_mode = 'RGBA'                          
                    fp = bpy.path.abspath('//textures' + sep + name)
                    try:
                        i.save_render(fp)
                        i.source = 'FILE'
                        if bpy.context.user_preferences.filepaths.use_relative_paths:
                            # can't always find the relative path (between drive letters on windows)
                            try:
                                i.filepath = bpy.path.relpath(fp)
                            except ValueError:
                                i.filepath = fp
                        else:
                            i.filepath = fp
                        i.name = name
                    except:
                        print("something wrong with", fp)
    #THAT'S THE GENERATED FILES saved, pathed and reloaded
    #now save other painted textures
    bpy.ops.image.save_dirty()



def save_active_paint():
    #for materials in current object
    ob = bpy.context.object
    for m in ob.material_slots:
        for ts in m.material.texture_slots:
            save_painted(ts)
    return {'FINISHED'}                          

def save_all_paint():
    #for all materials
    for m in bpy.data.materials:
        for ts in m.texture_slots:
            save_painted(ts)      
    return {'FINISHED'}   
            
            
class save_all_generated(bpy.types.Operator):
    """Saves painted layers to disc"""
    bl_idname = "paint.save_all_generated" 
     
    bl_label = "SAVE PAINT LAYERS"


    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        return save_active_paint()




#-----------------------------------
class OBJECT_PT_SavePainted(bpy.types.Panel):
    bl_label = "Save All Painted"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    #bl_context = "texturepaint"
    
    @classmethod
    def poll(cls, context):
        return (context.image_paint_object)
    
    def draw(self, context):
        self.layout.operator('paint.save_all_generated')        
        
def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
