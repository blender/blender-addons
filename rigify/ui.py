#====================== BEGIN GPL LICENSE BLOCK ======================
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
#======================= END GPL LICENSE BLOCK ========================

import bpy
from bpy.props import *
from imp import reload
import rigify
from rigify.utils import get_rig_type
from rigify import generate
from rna_prop_ui import rna_idprop_ui_prop_get


class DATA_PT_rigify_buttons(bpy.types.Panel):
    bl_label = "Rigify Buttons"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    #bl_options = {'DEFAULT_OPEN'}

    @classmethod
    def poll(cls, context):
        if not context.armature:
            return False
        #obj = context.object
        #if obj:
        #    return (obj.mode in ('POSE', 'OBJECT', 'EDIT'))
        #return False
        return True

    def draw(self, context):
        C = context
        layout = self.layout
        obj = context.object

        if obj.mode in ('POSE', 'OBJECT'):
            row = layout.row()
            row.operator("pose.rigify_generate", text="Generate")
        elif obj.mode == 'EDIT':
            # Build types list
            collection_name = str(C.scene.rigify_collection).replace(" ", "")

            for i in range(0, len(C.scene.rigify_types)):
                C.scene.rigify_types.remove(0)

            for r in rigify.rig_list:
                collection = r.split('.')[0]
                if collection_name == "All":
                    a = C.scene.rigify_types.add()
                    a.name = r
                elif r.startswith(collection_name + '.'):
                    a = C.scene.rigify_types.add()
                    a.name = r
                elif collection_name == "None" and len(r.split('.')) == 1:
                    a = C.scene.rigify_types.add()
                    a.name = r

            ## Rig collection field
            #row = layout.row()
            #row.prop(C.scene, 'rigify_collection', text="Category")

            # Rig type list
            row = layout.row()
            row.template_list(C.scene, "rigify_types", C.scene, 'rigify_active_type')
            row = layout.row()
            op = row.operator("armature.metarig_sample_add", text="Add sample")
            op.metarig_type = C.scene.rigify_types[C.scene.rigify_active_type].name


class BONE_PT_rigify_buttons(bpy.types.Panel):
    bl_label = "Rigify Type"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"
    #bl_options = {'DEFAULT_OPEN'}

    @classmethod
    def poll(cls, context):
        if not context.armature or not context.active_pose_bone:
            return False
        obj = context.object
        if obj:
            return (obj.mode in ('POSE'))
        return False

    def draw(self, context):
        C = context
        bone = context.active_pose_bone
        collection_name = str(C.scene.rigify_collection).replace(" ", "")
        rig_name = str(context.active_pose_bone.rigify_type).replace(" ", "")

        layout = self.layout

        # Build types list
        for i in range(0, len(C.scene.rigify_types)):
            C.scene.rigify_types.remove(0)

        for r in rigify.rig_list:
            collection = r.split('.')[0]
            if collection_name == "All":
                a = C.scene.rigify_types.add()
                a.name = r
            elif r.startswith(collection_name + '.'):
                a = C.scene.rigify_types.add()
                a.name = r
            elif collection_name == "None" and len(r.split('.')) == 1:
                a = C.scene.rigify_types.add()
                a.name = r

        # Rig type field
        row = layout.row()
        row.prop_search(bone, "rigify_type", C.scene, "rigify_types", text="Rig type:")

        # Rig type parameters / Rig type non-exist alert
        if rig_name != "":
            if len(bone.rigify_parameters) < 1:
                bone.rigify_parameters.add()

            try:
                rig = get_rig_type(rig_name)
                rig.Rig
            except (ImportError, AttributeError):
                row = layout.row()
                box = row.box()
                box.label(text="ALERT: type \"%s\" does not exist!" % rig_name)
            else:
                try:
                    rig.Rig.parameters_ui
                except AttributeError:
                    pass
                else:
                    col = layout.column()
                    col.label(text="Options:")
                    box = layout.box()

                    rig.Rig.parameters_ui(box, C.active_object, bone.name)


#class INFO_MT_armature_metarig_add(bpy.types.Menu):
#    bl_idname = "INFO_MT_armature_metarig_add"
#    bl_label = "Meta-Rig"

#    def draw(self, context):
        #import rigify

        #layout = self.layout
        #layout.operator_context = 'INVOKE_REGION_WIN'

        #for submodule_type in rigify.get_submodule_types():
        #    text = bpy.path.display_name(submodule_type)
        #    layout.operator("pose.metarig_sample_add", text=text, icon='OUTLINER_OB_ARMATURE').metarig_type = submodule_type


def rigify_report_exception(operator, exception):
    import traceback
    import sys
    import os
    # find the module name where the error happened
    # hint, this is the metarig type!
    exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
    fn = traceback.extract_tb(exceptionTraceback)[-1][0]
    fn = os.path.basename(fn)
    fn = os.path.splitext(fn)[0]
    message = []
    if fn.startswith("__"):
        message.append("Incorrect armature...")
    else:
        message.append("Incorrect armature for type '%s'" % fn)
    message.append(exception.message)

    message.reverse()  # XXX - stupid! menu's are upside down!

    operator.report(set(['INFO']), '\n'.join(message))


class Generate(bpy.types.Operator):
    '''Generates a rig from the active metarig armature'''

    bl_idname = "pose.rigify_generate"
    bl_label = "Rigify Generate Rig"

    def execute(self, context):
        reload(generate)

        try:
            generate.generate_rig(context, context.object)
        except rigify.utils.MetarigError as rig_exception:
            rigify_report_exception(self, rig_exception)

        return {'FINISHED'}


class Sample(bpy.types.Operator):
    '''Create a sample metarig to be modified before generating the final rig.'''

    bl_idname = "armature.metarig_sample_add"
    bl_label = "Add a sample metarig for a rig type"

    metarig_type = StringProperty(name="Type", description="Name of the rig type to generate a sample of", maxlen=128, default="")

    def execute(self, context):
        if context.mode == 'EDIT_ARMATURE' and self.metarig_type != "":
            try:
                rig = get_rig_type(self.metarig_type).Rig
                create_sample = rig.create_sample
            except (ImportError, AttributeError):
                print("Rigify: rig type has no sample.")
            else:
                create_sample(context.active_object)
            bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


#menu_func = (lambda self, context: self.layout.menu("INFO_MT_armature_metarig_add", icon='OUTLINER_OB_ARMATURE'))

#import space_info  # ensure the menu is loaded first

def register():
    #bpy.types.register(DATA_PT_rigify_buttons)
    #bpy.types.register(BONE_PT_rigify_buttons)
    #bpy.types.register(Generate)
    #bpy.types.register(Sample)

    #space_info.INFO_MT_armature_add.append(ui.menu_func)
    pass


def unregister():
    #bpy.types.unregister(DATA_PT_rigify_buttons)
    #bpy.types.unregister(BONE_PT_rigify_buttons)
    #bpy.types.unregister(Generate)
    #bpy.types.unregister(Sample)
    pass

