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

# Another Noise Tool - Landscape  Redraw - Regenerate
# Jim Hazevoet


# ------------------------------------------------------------
# import modules
import bpy

from .ant_functions import (
        noise_gen,
        grid_gen,
        sphere_gen,
        create_mesh_object,
        store_properties,
        )

# ------------------------------------------------------------
# Do refresh - redraw
class AntLandscapeRefresh(bpy.types.Operator):
    bl_idname = "mesh.ant_landscape_refresh"
    bl_label = "Refresh"
    bl_description = "Refresh landscape with current settings"
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(cls, context):
        ob = bpy.context.active_object
        return (ob.ant_landscape and not ob.ant_landscape['sphere_mesh'])


    def execute(self, context):
        # turn off undo
        undo = bpy.context.user_preferences.edit.use_global_undo
        bpy.context.user_preferences.edit.use_global_undo = False

        # ant object items
        obj = bpy.context.active_object

        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.object.mode_set(mode = 'OBJECT')

        if obj and obj.ant_landscape.keys():
            ob = obj.ant_landscape
            obi = ob.items()
            #print("Refresh A.N.T. Landscape Grid")
            #for k in obi.keys():
            #    print(k, "-", obi[k])
            prop = []
            for i in range(len(obi)):
                prop.append(obi[i][1])

            # redraw verts
            mesh = obj.data

            if ob['use_vgroup']:
                vertex_group = obj.vertex_groups.active
                if vertex_group:
                    for v in mesh.vertices:
                        v.co[2] = 0
                        v.co[2] = vertex_group.weight(v.index) * noise_gen(v.co, prop)
            else:
                for v in mesh.vertices:
                    v.co[2] = 0
                    v.co[2] = noise_gen(v.co, prop)
            mesh.update()
        else:
            pass

        # restore pre operator undo state
        context.user_preferences.edit.use_global_undo = undo

        return {'FINISHED'}


# ------------------------------------------------------------
# Do regenerate
class AntLandscapeRegenerate(bpy.types.Operator):
    bl_idname = "mesh.ant_landscape_regenerate"
    bl_label = "Regenerate"
    bl_description = "Regenerate landscape with current settings"
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(cls, context):
        return bpy.context.active_object.ant_landscape


    def execute(self, context):

        # turn off undo
        undo = bpy.context.user_preferences.edit.use_global_undo
        bpy.context.user_preferences.edit.use_global_undo = False

        scene = bpy.context.scene
        # ant object items
        obj = bpy.context.active_object

        if obj and obj.ant_landscape.keys():
            ob = obj.ant_landscape
            obi = ob.items()
            #print("Regenerate A.N.T. Landscape Grid")
            #for k in obi.keys():
            #    print(k, "-", obi[k])
            ant_props = []
            for i in range(len(obi)):
                ant_props.append(obi[i][1])

            new_name = ob.ant_terrain_name

            # Main function, create landscape mesh object
            if ob['sphere_mesh']:
                # sphere
                verts, faces = sphere_gen(
                        ob['subdivision_y'],
                        ob['subdivision_x'],
                        ob['tri_face'],
                        ob['mesh_size'],
                        ant_props,
                        False,
                        0.0
                        )
                new_ob = create_mesh_object(context, verts, [], faces, new_name).object
                if ob['remove_double']:
                    new_ob.select = True
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=False)
                    bpy.ops.object.mode_set(mode = 'OBJECT')
            else:
                # grid
                verts, faces = grid_gen(
                        ob['subdivision_x'],
                        ob['subdivision_y'],
                        ob['tri_face'],
                        ob['mesh_size_x'],
                        ob['mesh_size_y'],
                        ant_props,
                        False,
                        0.0
                        )
                new_ob = create_mesh_object(context, verts, [], faces, new_name).object

            new_ob.select = True

            if ob['smooth_mesh']:
                bpy.ops.object.shade_smooth()

            # Landscape Material
            if ob['land_material'] != "" and ob['land_material'] in bpy.data.materials:
                mat = bpy.data.materials[ob['land_material']]
                bpy.context.object.data.materials.append(mat)

            # Water plane
            if ob['water_plane']:
                if ob['sphere_mesh']:
                    # sphere
                    verts, faces = sphere_gen(
                            ob['subdivision_y'],
                            ob['subdivision_x'],
                            ob['tri_face'],
                            ob['mesh_size'],
                            ant_props,
                            ob['water_plane'],
                            ob['water_level']
                            )
                    wobj = create_mesh_object(context, verts, [], faces, new_name+"_plane").object
                    if ob['remove_double']:
                        wobj.select = True
                        bpy.ops.object.mode_set(mode = 'EDIT')
                        bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=False)
                        bpy.ops.object.mode_set(mode = 'OBJECT')
                else:
                    # grid
                    verts, faces = grid_gen(
                            2,
                            2,
                            ob['tri_face'],
                            ob['mesh_size_x'],
                            ob['mesh_size_y'],
                            ant_props,
                            ob['water_plane'],
                            ob['water_level']
                            )
                    wobj = create_mesh_object(context, verts, [], faces, new_name+"_plane").object

                wobj.select = True

                if ob['smooth_mesh']:
                    bpy.ops.object.shade_smooth()

                # Water Material
                if ob['water_material'] != "" and ob['water_material'] in bpy.data.materials:
                    mat = bpy.data.materials[ob['water_material']]
                    bpy.context.object.data.materials.append(mat)

            # Loc Rot Scale
            if ob['water_plane']:
                wobj.location = obj.location
                wobj.rotation_euler = obj.rotation_euler
                wobj.scale = obj.scale
                wobj.select = False


            new_ob.location = obj.location
            new_ob.rotation_euler = obj.rotation_euler
            new_ob.scale = obj.scale

            # Store props
            new_ob = store_properties(ob, new_ob)

            # Delete old object
            new_ob.select = False
            
            obj.select = True
            scene.objects.active = obj
            bpy.ops.object.delete(use_global=False)
            #scene.update()

            # Select landscape and make active
            new_ob.select = True
            scene.objects.active = new_ob

            # restore pre operator undo state
            context.user_preferences.edit.use_global_undo = undo

        return {'FINISHED'}
