import bpy

import bmesh, mathutils, random
from random import gauss
from math import radians
from mathutils import Euler, Vector

import addon_utils

# ---------------------Crack-------------------
# Cell fracture and post-process:
def makeFracture(child_verts=False, division=100, noise=0.00, scaleX=1.00, scaleY=1.00, scaleZ=1.00, recursion=0, margin=0.001):
    # Get active object name and active layer.
    active_name = bpy.context.scene.objects.active.name
    active_layer = bpy.context.scene.active_layer
    
    # source method of whether use child verts.
    if child_verts == True:
      crack_source = 'VERT_CHILD'
    else:
      crack_source = 'PARTICLE_OWN'
    
    bpy.ops.object.add_fracture_cell_objects(source={crack_source}, source_limit=division, source_noise=noise,
        cell_scale=(scaleX, scaleY, scaleZ), recursion=recursion, recursion_source_limit=8, recursion_clamp=250, recursion_chance=0.25, recursion_chance_select='SIZE_MIN',
        use_smooth_faces=False, use_sharp_edges=False, use_sharp_edges_apply=True, use_data_match=True, use_island_split=True,
        margin=margin, material_index=0, use_interior_vgroup=False, mass_mode='VOLUME', mass=1, use_recenter=True, use_remove_original=True, use_layer_index=0, use_layer_next=False,
        group_name="", use_debug_points=False, use_debug_redraw=True, use_debug_bool=False)

    _makeJoin(active_name, active_layer)

# Join fractures into an object.
def _makeJoin(active_name, active_layer):
    # Get object by name.
    #bpy.context.scene.layers[active_layer+1] = True
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_pattern(pattern=active_name + '_cell*')
    fractures = bpy.context.selected_objects
    
    # Execute join.
    bpy.context.scene.objects.active = fractures[0]
    fractures[0].select = True
    bpy.ops.object.join()
    
    # Change name.
    bpy.context.scene.objects.active.name = active_name + '_crack'
    
    # Change origin.
    bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')
    
    # Turn off the layer where original object is.
    #bpy.context.scene.layers[active_layer] = False

# Add modifier and setting.
def addModifiers():
    bpy.ops.object.modifier_add(type='DECIMATE')
    decimate = bpy.context.object.modifiers[-1]
    decimate.name = 'DECIMATE_crackit'
    decimate.ratio = 0.4
    
    bpy.ops.object.modifier_add(type='SUBSURF')
    subsurf = bpy.context.object.modifiers[-1]
    subsurf.name = 'SUBSURF_crackit'
    
    bpy.ops.object.modifier_add(type='SMOOTH')
    smooth = bpy.context.object.modifiers[-1]
    smooth.name = 'SMOOTH_crackit'



# --------------multi extrude--------------------
# var1=random offset, var2=random rotation, var3=random scale.
def multiExtrude(off=0.1, rotx=0, roty=0, rotz=0, sca=1.0, var1=0.01, var2=0.3, var3=0.3, num=1, ran=0):
    obj = bpy.context.object
    data, om =  obj.data, obj.mode
    bpy.context.tool_settings.mesh_select_mode = [False, False, True]

    # bmesh operations
    bpy.ops.object.mode_set()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    sel = [f for f in bm.faces if f.select]

    # faces loop
    for i, of in enumerate(sel):
        rot = _vrot(r=i, ran=ran, rotx=rotx, var2=var2, roty=roty, rotz=rotz)
        off = _vloc(r=i, ran=ran, off=off, var1=var1)
        of.normal_update()

        # extrusion loop
        for r in range(num):
            nf = of.copy()
            nf.normal_update()
            no = nf.normal.copy()
            ce = nf.calc_center_bounds()
            s = _vsca(r=i+r, ran=ran, var3=var3, sca=sca)

            for v in nf.verts:
                v.co -= ce
                v.co.rotate(rot)
                v.co += ce + no * off
                v.co = v.co.lerp(ce, 1 - s)

            # extrude code from TrumanBlending
            for a, b in zip(of.loops, nf.loops):
                sf = bm.faces.new((a.vert, a.link_loop_next.vert, \
                    b.link_loop_next.vert, b.vert))
                sf.normal_update()

            bm.faces.remove(of)
            of = nf

    for v in bm.verts: v.select = False
    for e in bm.edges: e.select = False
    bm.to_mesh(obj.data)
    obj.data.update()

    if not len(sel):
        self.report({'INFO'}, "Select one or more faces...")
    return{'FINISHED'}

def _vloc(r, ran, off, var1):
    random.seed(ran + r)
    return off * (1 + random.gauss(0, var1 / 3))

def _vrot(r, ran, rotx, var2, roty, rotz):
    random.seed(ran + r)
    return Euler((radians(rotx) + random.gauss(0, var2 / 3), \
        radians(roty) + random.gauss(0, var2 / 3), \
        radians(rotz) + random.gauss(0, var2 / 3)), 'XYZ')

def _vsca(r, ran, sca, var3):
    random.seed(ran + r)
    return sca * (1 + random.gauss(0, var3 / 3))

# centroide de una seleccion de vertices
def _centro(ver):
    vvv = [v for v in ver if v.select]
    if not vvv or len(vvv) == len(ver): return ('error')
    x = sum([round(v.co[0],4) for v in vvv]) / len(vvv)
    y = sum([round(v.co[1],4) for v in vvv]) / len(vvv)
    z = sum([round(v.co[2],4) for v in vvv]) / len(vvv)
    return (x,y,z)

# recuperar el estado original del objeto
def _volver(obj, copia, om, msm, msv):
    for i in copia: obj.data.vertices[i].select = True
    bpy.context.tool_settings.mesh_select_mode = msm
    for i in range(len(msv)):
        obj.modifiers[i].show_viewport = msv[i]



# --------------Material preset--------------------------
def appendMaterial(addon_path, material_name):
    # Load material from the addon directory.
    file_path = _makeFilePath(addon_path=addon_path)
    bpy.ops.wm.append(filename=material_name, directory=file_path)
    
    # If material is loaded some times, select the last-loaded material.
    last_material = _getAppendedMaterial(material_name)
    mat = bpy.data.materials[last_material]
    
    # Apply Only one material in the material slot.
    for m in bpy.context.object.data.materials:
        bpy.ops.object.material_slot_remove()
    bpy.context.object.data.materials.append(mat)

# Make file path of addon.
def _makeFilePath(addon_path):
    material_folder = "/materials"
    blend_file = "/materials1.blend"
    category = "\\Material\\"
    
    file_path = addon_path + material_folder + blend_file + category
    return file_path

# Get last-loaded material, such as ~.002.
def _getAppendedMaterial(material_name):
    # Get material name list.
    material_names = [m.name for m in bpy.data.materials if material_name in m.name]
    # Return last material in the sorted order.
    material_names.sort()
    return material_names[-1]
