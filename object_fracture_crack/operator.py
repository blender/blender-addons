import bpy
from . import crack_it

# Class for input and execution settings.
class FractureOperation(bpy.types.Operator):

    bl_idname = 'mesh.crackit_fracture' # Access by bpy.ops.mesh.crackit_fracture.
    bl_label = "Crack It!" # Label of button on menu.
    bl_description = "Make crack by cell fracture addon."
    bl_options = {'REGISTER', 'UNDO'}

    # Input after execution------------------------
    #  Reference by self.~ in execute().
    
    # -----------------------------------------
    
    '''
    @classmethod
    def poll(cls, context):
     return (context.object is not None)
     
    '''

    def execute(self, context):
        sce = context.scene

        crack_it.makeFracture(child_verts=sce.crackit_fracture_childverts, division=sce.crackit_fracture_div,
                            scaleX=sce.crackit_fracture_scalex, scaleY=sce.crackit_fracture_scaley, scaleZ=sce.crackit_fracture_scalez,
                            margin=sce.crackit_fracture_margin)
        crack_it.addModifiers()
        crack_it.multiExtrude(off=sce.crackit_extrude_offset,
                            var2=sce.crackit_extrude_random, var3=sce.crackit_extrude_random)
        bpy.ops.object.shade_smooth()
        return {'FINISHED'}

# Apply material preset.
class MaterialOperation(bpy.types.Operator):

    bl_idname = 'mesh.crackit_material' # Access by bpy.ops.mesh.crackit_material.
    bl_label = "Apply Material" # Label of button on menu.
    bl_description = "Apply a preset material"
    bl_options = {'REGISTER', 'UNDO'}

    # Input after execution------------------------
    #  Reference by self.~ in execute().
    
    # -----------------------------------------
    
    '''
    @classmethod
    def poll(cls, context):
     return (context.object is not None)
     
    '''

    def execute(self, context):
        sce = context.scene

        crack_it.appendMaterial(addon_path=sce.crackit_material_addonpath, material_name=sce.crackit_material_preset)
        return {'FINISHED'}

# Menu settings.
class crackitPanel(bpy.types.Panel):
    bl_label = "Crack it!" # title.
    bl_idname = 'crack_it' # id to reference.
    bl_space_type = 'VIEW_3D' # 3Dview.
    bl_region_type = 'TOOLS' # make menu on tool shelf.
    bl_category = 'Create' # Tab name on tool shelf.
    bl_context = (('objectmode')) # Mode to show the menu.
    
    # Menu.
    def draw(self, context):
         obj = context.object
         sce = context.scene
         layout = self.layout
         
         # Crack input
         box = layout.box()
         row = box.row()
         row.label("Crack")
         # Warning if fracture cell addon is not enabled.
         if 'object_fracture_cell' not in bpy.context.user_preferences.addons.keys():
             row = box.row()
             row.label("Note: Please enable 'Object: Cell Fracture' addon!")
         row = box.row()
         row.prop(sce, 'crackit_fracture_childverts')
         row = box.row()
         row.prop(sce, 'crackit_fracture_scalex') # bpy.types.Scene.crackit_fracture_scalex.
         row = box.row()
         row.prop(sce, 'crackit_fracture_scaley')
         row = box.row()
         row.prop(sce, 'crackit_fracture_scalez')
         row = box.row()
         row.prop(sce, 'crackit_fracture_div') 
         row = box.row()
         row.prop(sce, 'crackit_fracture_margin')
         row = box.row()
         row.prop(sce, 'crackit_extrude_offset')
         row = box.row()
         row.prop(sce, 'crackit_extrude_random')
         row = box.row()
         row.operator(FractureOperation.bl_idname) # Execute button.
         
         # material Preset:
         box = layout.box()
         row = box.row()
         row.label("Material Preset")
         row = box.row()
         row.prop(sce, 'crackit_material_preset')
         row = box.row()
         row.operator(MaterialOperation.bl_idname) # Execute button.