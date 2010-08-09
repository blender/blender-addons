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


import bpy
import mathutils
from bpy.props import *
from add_mesh_BoltFactory.createMesh import *
from add_mesh_BoltFactory.preset_utils import *



##------------------------------------------------------------
# calculates the matrix for the new object
# depending on user pref
def align_matrix(context):
    loc = mathutils.TranslationMatrix(context.scene.cursor_location)
    obj_align = context.user_preferences.edit.object_align
    if (context.space_data.type == 'VIEW_3D'
        and obj_align == 'VIEW'):
        rot = context.space_data.region_3d.view_matrix.rotation_part().invert().resize4x4()
    else:
        rot = mathutils.Matrix()
    align_matrix = loc * rot
    return align_matrix



class add_mesh_bolt(bpy.types.Operator):
    ''''''
    bl_idname = 'add_mesh_bolt'
    bl_label = "Add Bolt"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "adds many types of Bolts"
    
    align_matrix = mathutils.Matrix()
    MAX_INPUT_NUMBER = 50
    
    #Model Types
    Model_Type_List = [('bf_Model_Bolt','BOLT','Bolt Model'),
                        ('bf_Model_Nut','NUT','Nut Model')]
    bf_Model_Type = EnumProperty( attr='bf_Model_Type',
            name='Model',
            description='Choose the type off model you would like',
            items = Model_Type_List, default = 'bf_Model_Bolt')

    #Head Types
    Model_Type_List = [('bf_Head_Hex','HEX','Hex Head'),
                        ('bf_Head_Cap','CAP','Cap Head'),
                        ('bf_Head_Dome','DOME','Dome Head'),
                        ('bf_Head_Pan','PAN','Pan Head')]
    bf_Head_Type = EnumProperty( attr='bf_Head_Type',
            name='Head',
            description='Choose the type off Head you would like',
            items = Model_Type_List, default = 'bf_Head_Hex')
    
    #Bit Types
    Bit_Type_List = [('bf_Bit_None','NONE','No Bit Type'),
                    ('bf_Bit_Allen','ALLEN','Allen Bit Type'),
                    ('bf_Bit_Philips','PHILLIPS','Phillips Bit Type')]
    bf_Bit_Type = EnumProperty( attr='bf_Bit_Type',
            name='Bit Type',
            description='Choose the type of bit to you would like',
            items = Bit_Type_List, default = 'bf_Bit_None')
            
    #Nut Types
    Nut_Type_List = [('bf_Nut_Hex','HEX','Hex Nut'),
                    ('bf_Nut_Lock','LOCK','Lock Nut')]
    bf_Nut_Type = EnumProperty( attr='bf_Nut_Type',
            name='Nut Type',
            description='Choose the type of nut you would like',
            items = Nut_Type_List, default = 'bf_Nut_Hex')
            
    #Shank Types    
    bf_Shank_Length = FloatProperty(attr='bf_Shank_Length',
            name='Shank Length', default = 0,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER, 
            description='Length of the unthreaded shank')
            
    bf_Shank_Dia = FloatProperty(attr='bf_Shank_Dia',
            name='Shank Dia', default = 3,
            min = 0, soft_min = 0,max = MAX_INPUT_NUMBER,
            description='Diameter of the shank')
            
    bf_Phillips_Bit_Depth = FloatProperty(attr='bf_Phillips_Bit_Depth',
            name='Bit Depth', default = 0, #set in execute
            options = {'HIDDEN'}, #gets calculated in execute
            min = 0, soft_min = 0,max = MAX_INPUT_NUMBER,
            description='Depth of the Phillips Bit')

    bf_Allen_Bit_Depth = FloatProperty(attr='bf_Allen_Bit_Depth',
            name='Bit Depth', default = 1.5,
            min = 0, soft_min = 0,max = MAX_INPUT_NUMBER,
            description='Depth of the Allen Bit')
            
    bf_Allen_Bit_Flat_Distance = FloatProperty( attr='bf_Allen_Bit_Flat_Distance',
            name='Flat Dist', default = 2.5,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Flat Distance of the Allen Bit')
    
    bf_Hex_Head_Height = FloatProperty( attr='bf_Hex_Head_Height',
            name='Head Height', default = 2,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Height of the Hex Head')

    bf_Hex_Head_Flat_Distance = FloatProperty( attr='bf_Hex_Head_Flat_Distance',
            name='Flat Dist', default = 5.5,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Flat Distance of the Hex Head')

    bf_Cap_Head_Height = FloatProperty( attr='bf_Cap_Head_Height',
            name='Head Height', default = 5.5,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Height of the Cap Head')

    bf_Cap_Head_Dia = FloatProperty( attr='bf_Cap_Head_Dia',
            name='Head Dia', default = 3,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Diameter of the Cap Head')

    bf_Dome_Head_Dia = FloatProperty( attr='bf_Dome_Head_Dia',
            name='Dome Head Dia', default = 5.6,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Length of the unthreaded shank')

    bf_Pan_Head_Dia = FloatProperty( attr='bf_Pan_Head_Dia',
            name='Pan Head Dia', default = 5.6,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Diameter of the Pan Head')

    bf_Philips_Bit_Dia = FloatProperty(attr='bf_Philips_Bit_Dia',
            name='Bit Dia', default = 0, #set in execute
            options = {'HIDDEN'}, #gets calculated in execute
            min = 0, soft_min = 0,max = MAX_INPUT_NUMBER,
            description='Diameter of the Philips Bit')
    
    bf_Thread_Length = FloatProperty( attr='bf_Thread_Length',
            name='Thread Length', default = 6,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Length of the Thread')

    bf_Major_Dia = FloatProperty( attr='bf_Major_Dia',
            name='Major Dia', default = 3,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Outside diameter of the Thread')

    bf_Pitch = FloatProperty( attr='bf_Pitch',
            name='Pitch', default = 0.35,
            min = 0.1, soft_min = 0.1, max = 7.0,
            description='Pitch if the thread')

    bf_Minor_Dia = FloatProperty( attr='bf_Minor_Dia',
            name='Minor Dia', default = 0, #set in execute
            options = {'HIDDEN'}, #gets calculated in execute
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Inside diameter of the Thread')
            
    bf_Crest_Percent = IntProperty( attr='bf_Crest_Percent',
            name='Crest Percent', default = 10,
            min = 1, soft_min = 1, max = 90,
            description='Percent of the pitch that makes up the Crest')

    bf_Root_Percent = IntProperty( attr='bf_Root_Percent',
            name='Root Percent', default = 10,
            min = 1, soft_min = 1, max = 90,
            description='Percent of the pitch that makes up the Root')

    bf_Hex_Nut_Height = FloatProperty( attr='bf_Hex_Nut_Height',
            name='Hex Nut Height', default = 2.4,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Height of the Hex Nut')

    bf_Hex_Nut_Flat_Distance = FloatProperty( attr='bf_Hex_Nut_Flat_Distance',
            name='Hex Nut Flat Dist', default = 5.5,
            min = 0, soft_min = 0, max = MAX_INPUT_NUMBER,
            description='Flat distance of the Hex Nut')

    presets, presetsPath = getPresets()

    bf_presets = EnumProperty(attr='bf_presets',
            name='Preset',
            description="Use Preset from File",
            default='M3.py',
            items=presets)

    last_preset = None


    def draw(self, context):
        props = self.properties
        layout = self.layout
        col = layout.column()
        
        #ENUMS
        col.prop(props, 'bf_Model_Type')
        col.prop(props, 'bf_presets')
        col.separator()
        #Shank
        if props.bf_Model_Type == 'bf_Model_Bolt':
            col.label(text='Shank')
            col.prop(props, 'bf_Shank_Length')
            col.prop(props, 'bf_Shank_Dia')
            col.separator()
        #Head
        if props.bf_Model_Type == 'bf_Model_Bolt':
            col.prop(props, 'bf_Head_Type')
            if props.bf_Head_Type == 'bf_Head_Hex':
                col.prop(props, 'bf_Hex_Head_Height')
                col.prop(props, 'bf_Hex_Head_Flat_Distance')
            elif props.bf_Head_Type == 'bf_Head_Cap':
                col.prop(props,'bf_Cap_Head_Height')
                col.prop(props,'bf_Cap_Head_Dia')
            elif props.bf_Head_Type == 'bf_Head_Dome':
                col.prop(props,'bf_Dome_Head_Dia')
            elif props.bf_Head_Type == 'bf_Head_Pan':
                col.prop(props,'bf_Pan_Head_Dia')
            col.separator()
        #Bit
        if props.bf_Model_Type == 'bf_Model_Bolt':
            col.prop(props, 'bf_Bit_Type')
            if props.bf_Bit_Type == 'bf_Bit_None':
                DoNothing = 1;
            elif props.bf_Bit_Type == 'bf_Bit_Allen':
                 col.prop(props,'bf_Allen_Bit_Depth')
                 col.prop(props,'bf_Allen_Bit_Flat_Distance')
            elif props.bf_Bit_Type == 'bf_Bit_Philips':
                col.prop(props,'bf_Phillips_Bit_Depth')
                col.prop(props,'bf_Philips_Bit_Dia')
            col.separator()
        #Thread
        col.label(text='Thread')
        if props.bf_Model_Type == 'bf_Model_Bolt':
            col.prop(props,'bf_Thread_Length')
        col.prop(props,'bf_Major_Dia')
        col.prop(props,'bf_Minor_Dia')
        col.prop(props,'bf_Pitch')
        col.prop(props,'bf_Crest_Percent')
        col.prop(props,'bf_Root_Percent')
        #Nut
        if props.bf_Model_Type == 'bf_Model_Nut':
            col.prop(props, 'bf_Nut_Type')
            col.prop(props,'bf_Hex_Nut_Height')
            col.prop(props,'bf_Hex_Nut_Flat_Distance')


    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return context.scene != None

    ##### EXECUTE #####
    def execute(self, context):
    
        #print('EXECUTING...')
        props = self.properties

        if not self.last_preset or props.bf_presets != self.last_preset:
            #print('setting Preset', props.bf_presets)
            setProps(props, props.bf_presets, self.presetsPath)

            self.last_preset = props.bf_presets


        props.bf_Phillips_Bit_Depth = float(Get_Phillips_Bit_Height(props.bf_Philips_Bit_Dia))
        props.bf_Philips_Bit_Dia = props.bf_Pan_Head_Dia*(1.82/5.6)
        props.bf_Minor_Dia = props.bf_Major_Dia - (1.082532 * props.bf_Pitch)
        
        Create_New_Mesh(props, context, self.align_matrix)

        return {'FINISHED'}
        
    ##### INVOKE #####
    def invoke(self, context, event):
        #print('\n___________START_____________')
        # store creation_matrix
        self.align_matrix = align_matrix(context)
        self.execute(context)

        return {'FINISHED'}
