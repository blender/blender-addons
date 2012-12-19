#(c) 2010 Michael Williamson (michaelw)
#ported from original by Michael Williamsn
#
#tested r28370
#
#
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
    "name": "Material Utils",
    "author": "michaelw",
    "version": (1, 4),
    "blender": (2, 62, 0),
    "location": "View3D > Q key",
    "description": "Menu of material tools (assign, select..)  in the 3D View",
    "warning": "Buggy, Broken in Cycles mode",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/3D interaction/Materials Utils",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"
                   "func=detail&aid=22140",
    "category": "Material"}

"""
This script has several functions and operators... grouped for convenience
* assign material:
    offers the user a list of ALL the materials in the blend file and an
    additional "new" entry the chosen material will be assigned to all the
    selected objects in object mode.

    in edit mode the selected polygons get the selected material applied.

    if the user chose "new" the new material can be renamed using the
    "last operator" section of the toolbox.
    After assigning the material "clean material slots" and
    "material to texface" are auto run to keep things tidy
    (see description bellow)


* select by material
    in object mode this offers the user a menu of all materials in the blend
    file any objects using the selected material will become selected, any
    objects without the material will be removed from selection.

    in edit mode:  the menu offers only the materials attached to the current
    object. It will select the polygons that use the material and deselect those
    that do not.

* clean material slots
    for all selected objects any empty material slots or material slots with
    materials that are not used by the mesh polygons will be removed.

* Any un-used materials and slots will be removed
"""


import bpy
from bpy.props import*


def replace_material(m1, m2, all_objects=False):
    # replace material named m1 with material named m2
    # m1 is the name of original material
    # m2 is the name of the material to replace it with
    # 'all' will replace throughout the blend file

    matorg = bpy.data.materials.get(m1)
    matrep = bpy.data.materials.get(m2)

    if matorg and matrep:
        #store active object
        scn = bpy.context.scene
        ob_active = bpy.context.active_object

        if all_objects:
            objs = bpy.data.objects

        else:
            objs = bpy.context.selected_editable_objects

        for ob in objs:
            if ob.type == 'MESH':
                scn.objects.active = ob

                for m in ob.material_slots.values():
                    if m.material == matorg:
                        m.material = matrep
                        # don't break the loop as the material can be
                        # ref'd more than once

    else:
        print('no match to replace')


def select_material_by_name(find_mat_name):
    #in object mode selects all objects with material find_mat_name
    #in edit mode selects all polygons with material find_mat_name

    find_mat = bpy.data.materials.get(find_mat_name)

    if find_mat is None:
        return

    #check for editmode
    editmode = False

    scn = bpy.context.scene

    #set selection mode to polygons
    scn.tool_settings.mesh_select_mode = False, False, True

    actob = bpy.context.active_object
    if actob.mode == 'EDIT':
        editmode = True
        bpy.ops.object.mode_set()

    if not editmode:
        objs = bpy.data.objects
        for ob in objs:
            if ob.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
                ms = ob.material_slots.values()
                for m in ms:
                    if m.material == find_mat:
                        ob.select = True
                        # the active object may not have the mat!
                        # set it to one that does!
                        scn.objects.active = ob
                        break
                    else:
                        ob.select = False

            #deselect non-meshes
            else:
                ob.select = False

    else:
        #it's editmode, so select the polygons
        ob = actob
        ms = ob.material_slots.values()

        #same material can be on multiple slots
        slot_indeces = []
        i = 0
        # found = False  # UNUSED
        for m in ms:
            if m.material == find_mat:
                slot_indeces.append(i)
                # found = True  # UNUSED
            i += 1
        me = ob.data
        for f in me.polygons:
            if f.material_index in slot_indeces:
                f.select = True
            else:
                f.select = False
        me.update()
    if editmode:
        bpy.ops.object.mode_set(mode='EDIT')


def mat_to_texface():
    # assigns the first image in each material to the polygons in the active
    # uvlayer for all selected objects

    #check for editmode
    editmode = False

    actob = bpy.context.active_object
    if actob.mode == 'EDIT':
        editmode = True
        bpy.ops.object.mode_set()

    for ob in bpy.context.selected_editable_objects:
        if ob.type == 'MESH':
            #get the materials from slots
            ms = ob.material_slots.values()

            #build a list of images, one per material
            images = []
            #get the textures from the mats
            for m in ms:
                gotimage = False
                textures = m.material.texture_slots.values()
                if len(textures) >= 1:
                    for t in textures:
                        if t != None:
                            tex = t.texture
                            if tex.type == 'IMAGE':
                                img = tex.image
                                images.append(img)
                                gotimage = True
                                break

                if not gotimage:
                    print('noimage on', m.name)
                    images.append(None)

            # now we have the images
            # applythem to the uvlayer

            me = ob.data
            #got uvs?
            if not me.uv_textures:
                scn = bpy.context.scene
                scn.objects.active = ob
                bpy.ops.mesh.uv_texture_add()
                scn.objects.active = actob

            #get active uvlayer
            for t in  me.uv_textures:
                if t.active:
                    uvtex = t.data.values()
                    for f in me.polygons:
                        #check that material had an image!
                        if images[f.material_index] != None:
                            uvtex[f.index].image = images[f.material_index]
                        else:
                            uvtex[f.index].image = None

            me.update()

    if editmode:
        bpy.ops.object.mode_set(mode='EDIT')


def assignmatslots(ob, matlist):
    #given an object and a list of material names
    #removes all material slots form the object
    #adds new ones for each material in matlist
    #adds the materials to the slots as well.

    scn = bpy.context.scene
    ob_active = bpy.context.active_object
    scn.objects.active = ob

    for s in ob.material_slots:
        bpy.ops.object.material_slot_remove()

    # re-add them and assign material
    i = 0
    for m in matlist:
        mat = bpy.data.materials[m]
        ob.data.materials.append(mat)
        i += 1

    # restore active object:
    scn.objects.active = ob_active


def cleanmatslots():
    #check for edit mode
    editmode = False
    actob = bpy.context.active_object
    if actob.mode == 'EDIT':
        editmode = True
        bpy.ops.object.mode_set()

    objs = bpy.context.selected_editable_objects

    for ob in objs:
        if ob.type == 'MESH':
            mats = ob.material_slots.keys()

            #check the polygons on the mesh to build a list of used materials
            usedMatIndex = []  # we'll store used materials indices here
            faceMats = []
            me = ob.data
            for f in me.polygons:
                #get the material index for this face...
                faceindex = f.material_index

                #indices will be lost: Store face mat use by name
                currentfacemat = mats[faceindex]
                faceMats.append(currentfacemat)

                # check if index is already listed as used or not
                found = 0
                for m in usedMatIndex:
                    if m == faceindex:
                        found = 1
                        #break

                if found == 0:
                #add this index to the list
                    usedMatIndex.append(faceindex)

            #re-assign the used mats to the mesh and leave out the unused
            ml = []
            mnames = []
            for u in usedMatIndex:
                ml.append(mats[u])
                #we'll need a list of names to get the face indices...
                mnames.append(mats[u])

            assignmatslots(ob, ml)

            # restore face indices:
            i = 0
            for f in me.polygons:
                matindex = mnames.index(faceMats[i])
                f.material_index = matindex
                i += 1

    if editmode:
        bpy.ops.object.mode_set(mode='EDIT')


def assign_mat(matname="Default"):
    # get active object so we can restore it later
    actob = bpy.context.active_object

    # check if material exists, if it doesn't then create it
    found = False
    for m in bpy.data.materials:
        if m.name == matname:
            target = m
            found = True
            break
    if not found:
        target = bpy.data.materials.new(matname)

    # if objectmode then set all polygons
    editmode = False
    allpolygons = True
    if actob.mode == 'EDIT':
        editmode = True
        allpolygons = False
        bpy.ops.object.mode_set()

    objs = bpy.context.selected_editable_objects

    for ob in objs:
        # set the active object to our object
        scn = bpy.context.scene
        scn.objects.active = ob

        if ob.type in {'CURVE', 'SURFACE', 'FONT', 'META'}:
            found = False
            i = 0
            for m in bpy.data.materials:
                if m.name == matname:
                    found = True
                    index = i
                    break
                i += 1
                if not found:
                    index = i - 1
            targetlist = [index]
            assignmatslots(ob, targetlist)

        elif ob.type == 'MESH':
            # check material slots for matname material
            found = False
            i = 0
            mats = ob.material_slots
            for m in mats:
                if m.name == matname:
                    found = True
                    index = i
                    #make slot active
                    ob.active_material_index = i
                    break
                i += 1

            if not found:
                index = i
                #the material is not attached to the object
                ob.data.materials.append(target)

            #now assign the material:
            me = ob.data
            if allpolygons:
                for f in me.polygons:
                    f.material_index = index
            elif allpolygons == False:
                for f in me.polygons:
                    if f.select:
                        f.material_index = index
            me.update()

    #restore the active object
    bpy.context.scene.objects.active = actob
    if editmode:
        bpy.ops.object.mode_set(mode='EDIT')


def check_texture(img, mat):
    #finds a texture from an image
    #makes a texture if needed
    #adds it to the material if it isn't there already

    tex = bpy.data.textures.get(img.name)

    if tex is None:
        tex = bpy.data.textures.new(name=img.name, type='IMAGE')

    tex.image = img

    #see if the material already uses this tex
    #add it if needed
    found = False
    for m in mat.texture_slots:
        if m and m.texture == tex:
            found = True
            break
    if not found and mat:
        mtex = mat.texture_slots.add()
        mtex.texture = tex
        mtex.texture_coords = 'UV'
        mtex.use_map_color_diffuse = True


def texface_to_mat():
    # editmode check here!
    editmode = False
    ob = bpy.context.object
    if ob.mode == 'EDIT':
        editmode = True
        bpy.ops.object.mode_set()

    for ob in bpy.context.selected_editable_objects:

        faceindex = []
        unique_images = []

        # get the texface images and store indices
        if (ob.data.uv_textures):
            for f in ob.data.uv_textures.active.data:
                if f.image:
                    img = f.image
                    #build list of unique images
                    if img not in unique_images:
                        unique_images.append(img)
                    faceindex.append(unique_images.index(img))

                else:
                    img = None
                    faceindex.append(None)

        # check materials for images exist; create if needed
        matlist = []
        for i in unique_images:
            if i:
                try:
                    m = bpy.data.materials[i.name]
                except:
                    m = bpy.data.materials.new(name=i.name)
                    continue

                finally:
                    matlist.append(m.name)
                    # add textures if needed
                    check_texture(i, m)

        # set up the object material slots
        assignmatslots(ob, matlist)

        #set texface indices to material slot indices..
        me = ob.data

        i = 0
        for f in faceindex:
            if f != None:
                me.polygons[i].material_index = f
            i += 1
    if editmode:
        bpy.ops.object.mode_set(mode='EDIT')

def remove_materials():

	for ob in bpy.data.objects:
		print (ob.name)
		try:
			bpy.ops.object.material_slot_remove()
			print ("removed material from " + ob.name)
		except:
			print (ob.name + " does not have materials.")
# -----------------------------------------------------------------------------
# operator classes:

class VIEW3D_OT_texface_to_material(bpy.types.Operator):
    """Create texture materials for images assigned in UV editor"""
    bl_idname = "view3d.texface_to_material"
    bl_label = "MW Texface Images to Material/Texture"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        if context.selected_editable_objects:
            texface_to_mat()
            return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "No editable selected objects, could not finish")
            return {'CANCELLED'}


class VIEW3D_OT_assign_material(bpy.types.Operator):
    """Assign a material to the selection"""
    bl_idname = "view3d.assign_material"
    bl_label = "MW Assign Material"
    bl_options = {'REGISTER', 'UNDO'}

    matname = StringProperty(
            name='Material Name',
            description='Name of Material to Assign',
            default="",
            maxlen=63,
            )

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        mn = self.matname
        print(mn)
        assign_mat(mn)
        cleanmatslots()
        mat_to_texface()
        return {'FINISHED'}


class VIEW3D_OT_clean_material_slots(bpy.types.Operator):
    """Removes any material slots from selected objects """ \
    """that are not used by the mesh"""
    bl_idname = "view3d.clean_material_slots"
    bl_label = "MW Clean Material Slots"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        cleanmatslots()
        return {'FINISHED'}


class VIEW3D_OT_material_to_texface(bpy.types.Operator):
    """Transfer material assignments to UV editor"""
    bl_idname = "view3d.material_to_texface"
    bl_label = "MW Material Images to Texface"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        mat_to_texface()
        return {'FINISHED'}

class VIEW3D_OT_material_remove(bpy.types.Operator):
    """Remove all material slots from active objects"""
    bl_idname = "view3d.material_remove"
    bl_label = "Remove All Material Slots"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        remove_materials()
        return {'FINISHED'}


class VIEW3D_OT_select_material_by_name(bpy.types.Operator):
    """Select geometry with this material assigned to it"""
    bl_idname = "view3d.select_material_by_name"
    bl_label = "MW Select Material By Name"
    bl_options = {'REGISTER', 'UNDO'}
    matname = StringProperty(
            name='Material Name',
            description='Name of Material to Select',
            maxlen=63,
            )

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        mn = self.matname
        select_material_by_name(mn)
        return {'FINISHED'}


class VIEW3D_OT_replace_material(bpy.types.Operator):
    """Replace a material by name"""
    bl_idname = "view3d.replace_material"
    bl_label = "MW Replace Material"
    bl_options = {'REGISTER', 'UNDO'}

    matorg = StringProperty(
            name='Material to Replace',
            description="Name of Material to Assign",
            maxlen=63,
            )
    matrep = StringProperty(name="Replacement material",
            description='Name of Material to Assign',
            maxlen=63,
            )
    all_objects = BoolProperty(
            name="All objects",
            description="Replace for all objects in this blend file",
            default=True,
            )

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        m1 = self.matorg
        m2 = self.matrep
        all = self.all_objects
        replace_material(m1, m2, all)
        return {'FINISHED'}


# -----------------------------------------------------------------------------
# menu classes

class VIEW3D_MT_master_material(bpy.types.Menu):
    bl_label = "Material Utils Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.menu("VIEW3D_MT_assign_material", icon='ZOOMIN')
        layout.menu("VIEW3D_MT_select_material", icon='HAND')
        layout.separator()
        layout.operator("view3d.clean_material_slots",
                        text="Clean Material Slots",
                        icon='CANCEL')
        layout.operator("view3d.material_remove",
                        text="Remove Material Slots",
                        icon='CANCEL')
        layout.operator("view3d.material_to_texface",
                        text="Material to Texface",
                        icon='MATERIAL_DATA')
        layout.operator("view3d.texface_to_material",
                        text="Texface to Material",
                        icon='MATERIAL_DATA')

        layout.separator()
        layout.operator("view3d.replace_material",
                        text='Replace Material',
                        icon='ARROW_LEFTRIGHT')


class VIEW3D_MT_assign_material(bpy.types.Menu):
    bl_label = "Assign Material"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        for material_name in bpy.data.materials.keys():
            layout.operator("view3d.assign_material",
                text=material_name,
                icon='MATERIAL_DATA').matname = material_name

        layout.operator("view3d.assign_material",
                        text="Add New",
                        icon='ZOOMIN')


class VIEW3D_MT_select_material(bpy.types.Menu):
    bl_label = "Select by Material"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        ob = context.object
        layout.label
        if ob.mode == 'OBJECT':
            #show all used materials in entire blend file
            for material_name, material in bpy.data.materials.items():
                if material.users > 0:
                    layout.operator("view3d.select_material_by_name",
                                    text=material_name,
                                    icon='MATERIAL_DATA',
                                    ).matname = material_name

        elif ob.mode == 'EDIT':
            #show only the materials on this object
            mats = ob.material_slots.keys()
            for m in mats:
                layout.operator("view3d.select_material_by_name",
                    text=m,
                    icon='MATERIAL_DATA').matname = m


def register():
    bpy.utils.register_module(__name__)

    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new('wm.call_menu', 'Q', 'PRESS')
        kmi.properties.name = "VIEW3D_MT_master_material"


def unregister():
    bpy.utils.unregister_module(__name__)

    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps["3D View"]
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu':
                if kmi.properties.name == "VIEW3D_MT_master_material":
                    km.keymap_items.remove(kmi)
                    break

if __name__ == "__main__":
    register()
