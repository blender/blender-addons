# Copyright (c) 2012 Jorge Hernandez - Melendez

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

# TODO : translate comments, prop names into English, add missing tooltips

bl_info = {
    "name": "Rope Creator",
    "description": "Dynamic rope (with cloth) creator",
    "author": "Jorge Hernandez - Melenedez",
    "version": (0, 2),
    "blender": (2, 7, 3),
    "location": "Left Toolbar > ClothRope",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"
}


import bpy
from bpy.types import Operator
from bpy.props import (
        BoolProperty,
        FloatProperty,
        IntProperty,
        )


def desocultar(quien):
    if quien == "todo":
        for ob in bpy.data.objects:
            ob.hide = False
    else:
        bpy.data.objects[quien].hide = False


def deseleccionar_todo():
    bpy.ops.object.select_all(action='DESELECT')


def seleccionar_todo():
    bpy.ops.object.select_all(action='SELECT')


def salir_de_editmode():
    if bpy.context.mode == "EDIT" or bpy.context.mode == "EDIT_CURVE" or bpy.context.mode == "EDIT_MESH":
        bpy.ops.object.mode_set(mode='OBJECT')

# Clear scene:


def reset_scene():
    desocultar("todo")
    # el play back al principio
    bpy.ops.screen.frame_jump(end=False)
    try:
        salir_de_editmode()
    except:
        pass
    area = bpy.context.area
    # en el outliner expando todo para poder seleccionar los emptys hijos
    old_type = area.type
    area.type = 'OUTLINER'
    bpy.ops.outliner.expanded_toggle()
    area.type = old_type
    # vuelvo al contexto donde estaba
    seleccionar_todo()
    bpy.ops.object.delete(use_global=False)


def entrar_en_editmode():
    if bpy.context.mode == "OBJECT":
        bpy.ops.object.mode_set(mode='EDIT')


def select_all_in_edit_mode(ob):
    if ob.mode != 'EDIT':
        entrar_en_editmode()
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    salir_de_editmode()
    for v in ob.data.vertices:
        if not v.select:
            v.select = True
    entrar_en_editmode()
    # bpy.ops.mesh.select_all(action="SELECT")


def deselect_all_in_edit_mode(ob):
    if ob.mode != 'EDIT':
        entrar_en_editmode()
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    salir_de_editmode()
    for v in ob.data.vertices:
        if not v.select:
            v.select = False
    entrar_en_editmode()


def which_vertex_are_selected(ob):
    for v in ob.data.vertices:
        if v.select:
            print(str(v.index))
            print("el vertice " + str(v.index) + " esta seleccionado")


def seleccionar_por_nombre(nombre):
    scn = bpy.context.scene
    bpy.data.objects[nombre].select = True
    scn.objects.active = bpy.data.objects[nombre]


def deseleccionar_por_nombre(nombre):
    # scn = bpy.context.scene
    bpy.data.objects[nombre].select = False


def crear_vertices(ob):
    ob.data.vertices.add(1)
    ob.data.update


def borrar_elementos_seleccionados(tipo):
    if tipo == "vertices":
        bpy.ops.mesh.delete(type='VERT')


def tab_editmode():
    bpy.ops.object.editmode_toggle()


def obtener_coords_vertex_seleccionados():
    coordenadas_de_vertices = []
    for ob in bpy.context.selected_objects:
        print(ob.name)
        if ob.type == 'MESH':
            for v in ob.data.vertices:
                if v.select:
                    coordenadas_de_vertices.append([v.co[0], v.co[1], v.co[2]])
            return coordenadas_de_vertices[0]


def crear_locator(pos):
    bpy.ops.object.empty_add(
                type='PLAIN_AXES', radius=1, view_align=False,
                location=(pos[0], pos[1], pos[2]),
                layers=(True, False, False, False, False, False, False,
                        False, False, False, False, False, False, False,
                        False, False, False, False, False, False)
                )


def extruir_vertices(longitud, cuantos_segmentos):
    bpy.ops.mesh.extrude_region_move(
                MESH_OT_extrude_region={"mirror": False},
                TRANSFORM_OT_translate={
                        "value": (longitud / cuantos_segmentos, 0, 0),
                        "constraint_axis": (True, False, False),
                        "constraint_orientation": 'GLOBAL', "mirror": False,
                        "proportional": 'DISABLED', "proportional_edit_falloff": 'SMOOTH',
                        "proportional_size": 1, "snap": False, "snap_target": 'CLOSEST',
                        "snap_point": (0, 0, 0), "snap_align": False, "snap_normal": (0, 0, 0),
                        "gpencil_strokes": False, "texture_space": False,
                        "remove_on_cancel": False, "release_confirm": False
                        }
                )


def select_all_vertex_in_curve_bezier(bc):
    for i in range(len(bc.data.splines[0].points)):
        bc.data.splines[0].points[i].select = True


def deselect_all_vertex_in_curve_bezier(bc):
    for i in range(len(bc.data.splines[0].points)):
        bc.data.splines[0].points[i].select = False


def ocultar_relationships():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].show_relationship_lines = False


class ClothRope(Operator):
    bl_idname = "clot.rope"
    bl_label = "Rope Cloth"

    ropelenght = IntProperty(
                    name="longitud",
                    default=5
                    )
    ropesegments = IntProperty(
                    name="rsegments",
                    default=5
                    )
    qcr = IntProperty(
                    name="qualcolr",
                    min=1, max=20,
                    default=20
                    )
    substeps = IntProperty(
                    name="rsubsteps",
                    min=4, max=80,
                    default=50
                    )
    resrope = IntProperty(
                    name="resr",
                    default=5
                    )
    radiusrope = FloatProperty(
                    name="radius",
                    min=0.04, max=1,
                    default=0.04
                    )
    hide_emptys = BoolProperty(
                    name="hemptys",
                    default=False
                    )

    def execute(self, context):
        # add new scene
        bpy.ops.scene.new(type="NEW")
        scene = bpy.context.scene
        scene.name = "Test Rope"
        seleccionar_todo()
        longitud = self.ropelenght
        # para que desde el primer punto hasta el ultimo, entre
        # medias tenga x segmentos debo sumarle 1 a la cantidad:
        cuantos_segmentos = self.ropesegments + 1
        calidad_de_colision = self.qcr
        substeps = self.substeps
        deseleccionar_todo()
        # creamos el empty que sera el padre de todo
        bpy.ops.object.empty_add(
                        type='SPHERE', radius=1, view_align=False, location=(0, 0, 0),
                        layers=(True, False, False, False, False, False, False, False,
                                False, False, False, False, False, False, False, False,
                                False, False, False, False)
                        )
        ob = bpy.context.selected_objects[0]
        ob.name = "Rope"
        deseleccionar_todo()
        # creamos un plano y lo borramos
        bpy.ops.mesh.primitive_plane_add(
                            radius=1, view_align=False, enter_editmode=False, location=(0, 0, 0),
                            layers=(True, False, False, False, False, False, False, False, False,
                                    False, False, False, False, False, False, False, False,
                                    False, False, False)
                            )
        ob = bpy.context.selected_objects[0]
        # renombrar:
        ob.name = "cuerda"
        entrar_en_editmode()  # entramos en edit mode
        select_all_in_edit_mode(ob)
        # seleccionar_todo() # ya viene por default seleccionado
        borrar_elementos_seleccionados("vertices")
        salir_de_editmode()  # salimos de edit mode
        crear_vertices(ob)  # creamos un vertex
        # creando el grupo Group para el PIN
        # Group contiene los vertices del pin y Group.001 contiene la linea unica principal
        entrar_en_editmode()  # entramos en edit mode
        bpy.ops.object.vertex_group_add()  # creamos un grupo
        select_all_in_edit_mode(ob)
        bpy.ops.object.vertex_group_assign()  # y lo asignamos
        # los hooks van a la curva no a la guia poligonal...
        # creo el primer hook sin necesidad de crear luego el locator a mano:
        # bpy.ops.object.hook_add_newob()
        salir_de_editmode()  # salimos de edit mode
        ob.vertex_groups[0].name = "Pin"
        deseleccionar_todo()
        seleccionar_por_nombre("cuerda")
        # hago los extrudes del vertice:
        for i in range(cuantos_segmentos):
            entrar_en_editmode()
            extruir_vertices(longitud, cuantos_segmentos)
            # y los ELIMINO del grupo PIN
            bpy.ops.object.vertex_group_remove_from()
            # obtengo la direccion para lego crear el locator en su posicion
            pos = obtener_coords_vertex_seleccionados()
            # los hooks van a la curva no a la guia poligonal...
            # creo el hook sin necesidad de crear el locator a mano:
            # bpy.ops.object.hook_add_newob()
            salir_de_editmode()  # salimos de edit mode
            # creo el locator en su sitio
            crear_locator(pos)
            deseleccionar_todo()
            seleccionar_por_nombre("cuerda")
        deseleccionar_todo()
        seleccionar_por_nombre("cuerda")
        # vuelvo a seleccionar la cuerda
        entrar_en_editmode()
        pos = obtener_coords_vertex_seleccionados()  # y obtenemos su posicion
        salir_de_editmode()
        # creamos el ultimo locator
        crear_locator(pos)
        deseleccionar_todo()
        seleccionar_por_nombre("cuerda")
        entrar_en_editmode()  # entramos en edit mode
        bpy.ops.object.vertex_group_add()  # CREANDO GRUPO GUIA MAESTRA
        select_all_in_edit_mode(ob)
        bpy.ops.object.vertex_group_assign()  # y lo asignamos
        ob.vertex_groups[1].name = "Guide_rope"
        # extruimos la curva para que tenga un minimo grosor para colisionar
        bpy.ops.mesh.extrude_region_move(
                        MESH_OT_extrude_region={"mirror": False},
                        TRANSFORM_OT_translate={
                                "value": (0, 0.005, 0), "constraint_axis": (False, True, False),
                                "constraint_orientation": 'GLOBAL', "mirror": False,
                                "proportional": 'DISABLED', "proportional_edit_falloff": 'SMOOTH',
                                "proportional_size": 1, "snap": False, "snap_target": 'CLOSEST',
                                "snap_point": (0, 0, 0), "snap_align": False, "snap_normal": (0, 0, 0),
                                "gpencil_strokes": False, "texture_space": False,
                                "remove_on_cancel": False, "release_confirm": False
                                }
                        )
        bpy.ops.object.vertex_group_remove_from()
        deselect_all_in_edit_mode(ob)
        salir_de_editmode()
        bpy.ops.object.modifier_add(type='CLOTH')
        bpy.context.object.modifiers["Cloth"].settings.use_pin_cloth = True
        bpy.context.object.modifiers["Cloth"].settings.vertex_group_mass = "Pin"
        bpy.context.object.modifiers["Cloth"].collision_settings.collision_quality = calidad_de_colision
        bpy.context.object.modifiers["Cloth"].settings.quality = substeps
        # DUPLICAMOS para convertir a curva:
        # selecciono los vertices que forman parte del grupo Group.001
        seleccionar_por_nombre("cuerda")
        entrar_en_editmode()
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        salir_de_editmode()
        gi = ob.vertex_groups["Guide_rope"].index  # get group index
        for v in ob.data.vertices:
            for g in v.groups:
                if g.group == gi:  # compare with index in VertexGroupElement
                    v.select = True
        entrar_en_editmode()
        # ya tenemos la guia seleccionada:
        # la duplicamos:
        bpy.ops.mesh.duplicate_move(
                        MESH_OT_duplicate={"mode": 1},
                        TRANSFORM_OT_translate={
                                "value": (0, 0, 0), "constraint_axis": (False, False, False),
                                "constraint_orientation": 'GLOBAL', "mirror": False,
                                "proportional": 'DISABLED', "proportional_edit_falloff": 'SMOOTH',
                                "proportional_size": 1, "snap": False, "snap_target": 'CLOSEST',
                                "snap_point": (0, 0, 0), "snap_align": False, "snap_normal": (0, 0, 0),
                                "gpencil_strokes": False, "texture_space": False,
                                "remove_on_cancel": False, "release_confirm": False
                                }
                        )
        # separamos por seleccion:
        bpy.ops.mesh.separate(type='SELECTED')
        salir_de_editmode()
        deseleccionar_todo()
        seleccionar_por_nombre("cuerda.001")
        # a la nueva curva copiada le quitamos el cloth:
        bpy.ops.object.modifier_remove(modifier="Cloth")
        # la convertimos en curva:
        bpy.ops.object.convert(target='CURVE')
        # todos los emptys:
        emptys = []
        for eo in bpy.data.objects:
            if eo.type == 'EMPTY':
                if eo.name != "Rope":
                    emptys.append(eo)
        # print(emptys)
        # cuantos puntos tiene la becier:
        # len(bpy.data.objects['cuerda.001'].data.splines[0].points)
        # seleccionar y deseleccionar:
        bc = bpy.data.objects['cuerda.001']
        n = 0
        for e in emptys:
            deseleccionar_todo()
            seleccionar_por_nombre(e.name)
            seleccionar_por_nombre(bc.name)
            entrar_en_editmode()
            deselect_all_vertex_in_curve_bezier(bc)
            bc.data.splines[0].points[n].select = True
            bpy.ops.object.hook_add_selob(use_bone=False)
            salir_de_editmode()
            n = n + 1
        # entrar_en_editmode()
        ob = bpy.data.objects['cuerda']
        n = 0
        for e in emptys:
            deseleccionar_todo()
            seleccionar_por_nombre(e.name)
            seleccionar_por_nombre(ob.name)
            entrar_en_editmode()
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            salir_de_editmode()
            for v in ob.data.vertices:
                if v.select:
                    v.select = False
            ob.data.vertices[n].select = True
            entrar_en_editmode()
            bpy.ops.object.vertex_parent_set()
            # deselect_all_in_edit_mode(ob)
            salir_de_editmode()
            n = n + 1

        # ocultar los emptys:
        # for e in emptys:
            deseleccionar_todo()
        # emparentando todo al empty esferico:
        seleccionar_por_nombre("cuerda.001")
        seleccionar_por_nombre("cuerda")
        seleccionar_por_nombre("Rope")
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
        deseleccionar_todo()
        # display que no muestre las relaciones
        ocultar_relationships()
        seleccionar_por_nombre("cuerda.001")
        # cuerda curva settings:
        bpy.context.object.data.fill_mode = 'FULL'
        bpy.context.object.data.bevel_depth = self.radiusrope
        bpy.context.object.data.bevel_resolution = self.resrope

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=310)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column()
        col.label("Rope settings:")
        rowsub0 = col.row()
        rowsub0.prop(self, "ropelenght", text='Length')
        rowsub0.prop(self, "ropesegments", text='Segments')
        rowsub0.prop(self, "radiusrope", text='Radius')

        col.label("Quality Settings:")
        col.prop(self, "resrope", text='Resolution curve')
        col.prop(self, "qcr", text='Quality Collision')
        col.prop(self, "substeps", text='Substeps')


class BallRope(Operator):
    bl_idname = "ball.rope"
    bl_label = "Rope Ball"

    # defaults rope ball
    ropelenght2 = IntProperty(
                    name="longitud",
                    default=10
                    )
    ropesegments2 = IntProperty(
                    name="rsegments",
                    min=0, max=999,
                    default=6
                    )
    radiuscubes = FloatProperty(
                    name="radius",
                    default=0.5
                    )
    radiusrope = FloatProperty(
                    name="radius",
                    default=0.4
                    )
    worldsteps = IntProperty(
                    name="worldsteps",
                    min=60, max=1000,
                    default=250
                    )
    solveriterations = IntProperty(
                    name="solveriterations",
                    min=10, max=100,
                    default=50
                    )
    massball = IntProperty(
                    name="massball",
                    default=1
                    )
    resrope = IntProperty(
                    name="resolucion",
                    default=4
                    )
    grados = FloatProperty(
                    name="grados",
                    default=45
                    )
    separacion = FloatProperty(
                    name="separacion",
                    default=0.1
                    )
    hidecubes = BoolProperty(
                    name="hidecubes",
                    default=False
                    )

    def execute(self, context):
        world_steps = self.worldsteps
        solver_iterations = self.solveriterations
        longitud = self.ropelenght2
        # hago un + 2 para que los segmentos sean los que hay entre los dos extremos...
        segmentos = self.ropesegments2 + 2
        offset_del_suelo = 1
        offset_del_suelo_real = (longitud / 2) + (segmentos / 2)
        radio = self.radiuscubes
        radiorope = self.radiusrope
        masa = self.massball
        resolucion = self.resrope
        rotrope = self.grados
        separation = self.separacion
        hidecubeslinks = self.hidecubes
        # add new scene
        bpy.ops.scene.new(type="NEW")
        scene = bpy.context.scene
        scene.name = "Test Ball"
        # suelo:
        bpy.ops.mesh.primitive_cube_add(
                            radius=1, view_align=False, enter_editmode=False, location=(0, 0, 0),
                            layers=(True, False, False, False, False, False, False, False, False,
                                    False, False, False, False, False, False, False, False,
                                    False, False, False)
                            )
        bpy.context.object.scale.x = 10 + longitud
        bpy.context.object.scale.y = 10 + longitud
        bpy.context.object.scale.z = 0.05
        bpy.context.object.name = "groundplane"
        bpy.ops.rigidbody.objects_add(type='PASSIVE')
        # creamos el primer cubo:
        cuboslink = []
        n = 0
        for i in range(segmentos):
            # si es 0 le digo que empieza desde 1
            if i == 0:
                i = offset_del_suelo
            else:  # si no es 0 les tengo que sumar uno para que no se pisen al empezar el primero desde 1
                i = i + offset_del_suelo
            separacion = longitud * 2 / segmentos  # distancia entre los cubos link
            bpy.ops.mesh.primitive_cube_add(
                        radius=1, view_align=False, enter_editmode=False,
                        location=(0, 0, i * separacion),
                        layers=(True, False, False, False, False, False, False, False,
                                False, False, False, False, False, False, False, False,
                                False, False, False, False)
                        )
            bpy.ops.rigidbody.objects_add(type='ACTIVE')
            bpy.context.object.name = "CubeLink"
            if n != 0:
                bpy.context.object.draw_type = 'WIRE'
                bpy.context.object.hide_render = True
            n += 1
            bpy.context.object.scale.z = (longitud * 2) / (segmentos * 2) - separation
            bpy.context.object.scale.x = radio
            bpy.context.object.scale.y = radio
            cuboslink.append(bpy.context.object)
        for i in range(len(cuboslink)):
            deseleccionar_todo()
            if i != len(cuboslink) - 1:
                nombre1 = cuboslink[i]
                nombre2 = cuboslink[i + 1]
                seleccionar_por_nombre(nombre1.name)
                seleccionar_por_nombre(nombre2.name)
                bpy.ops.rigidbody.connect()
        seleccionar_por_nombre
        for i in range(segmentos - 1):
            if i == 0:
                seleccionar_por_nombre("Constraint")
            else:
                if i <= 9 and i > 0:
                    seleccionar_por_nombre("Constraint.00" + str(i))
                else:
                    if i <= 99 and i > 9:
                        seleccionar_por_nombre("Constraint.0" + str(i))
                    else:
                        if i <= 999 and i > 99:
                            seleccionar_por_nombre("Constraint." + str(i))
            for c in bpy.context.selected_objects:
                c.rigid_body_constraint.type = 'POINT'
        deseleccionar_todo()

        # creamos la curva bezier:
        bpy.ops.curve.primitive_bezier_curve_add(
                        radius=1, view_align=False, enter_editmode=False, location=(0, 0, 0),
                        layers=(True, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False, False, False)
                        )
        bpy.context.object.name = "Cuerda"
        for i in range(len(cuboslink)):
            cubonombre = cuboslink[i].name
            seleccionar_por_nombre(cubonombre)
            seleccionar_por_nombre("Cuerda")
            x = cuboslink[i].location[0]
            y = cuboslink[i].location[1]
            z = cuboslink[i].location[2]
            # si es 0 le digo que empieza desde 1 es el offset desde el suelo...
            if i == 0:
                i = offset_del_suelo
            else:  # si no es 0 les tengo que sumar uno para que no se pisen al empezar el primero desde 1
                i = i + offset_del_suelo
            salir_de_editmode()
            # entrar_en_editmode()
            tab_editmode()
            if i == 1:
                # selecciono todos los vertices y los  borro
                select_all_vertex_in_curve_bezier(bpy.data.objects["Cuerda"])
                bpy.ops.curve.delete(type='VERT')
                # creamos el primer vertice:
                bpy.ops.curve.vertex_add(location=(x, y, z))
            else:
                # extruimos el resto:
                bpy.ops.curve.extrude_move(
                            CURVE_OT_extrude={"mode": 'TRANSLATION'},
                            TRANSFORM_OT_translate={
                                "value": (0, 0, z / i),
                                "constraint_axis": (False, False, True),
                                "constraint_orientation": 'GLOBAL', "mirror": False,
                                "proportional": 'DISABLED', "proportional_edit_falloff": 'SMOOTH',
                                "proportional_size": 1, "snap": False, "snap_target": 'CLOSEST',
                                "snap_point": (0, 0, 0), "snap_align": False, "snap_normal": (0, 0, 0),
                                "gpencil_strokes": False, "texture_space": False,
                                "remove_on_cancel": False, "release_confirm": False
                                }
                            )
            bpy.ops.object.hook_add_selob(use_bone=False)
            salir_de_editmode()
            bpy.context.object.data.bevel_resolution = resolucion
            deseleccionar_todo()

        # creando la esfera ball:
        deseleccionar_todo()
        seleccionar_por_nombre(cuboslink[0].name)
        entrar_en_editmode()
        z = cuboslink[0].scale.z + longitud / 2
        bpy.ops.view3d.snap_cursor_to_selected()
        bpy.ops.mesh.primitive_uv_sphere_add(
                        view_align=False, enter_editmode=False,
                        layers=(True, False, False, False, False, False, False,
                                False, False, False, False, False, False, False,
                                False, False, False, False, False, False)
                        )
        bpy.ops.transform.translate(
                        value=(0, 0, -z + 2), constraint_axis=(False, False, True),
                        constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED',
                        proportional_edit_falloff='SMOOTH', proportional_size=1
                        )
        bpy.ops.transform.resize(
                        value=(longitud / 2, longitud / 2, longitud / 2),
                        constraint_axis=(False, False, False),
                        constraint_orientation='GLOBAL',
                        mirror=False, proportional='DISABLED',
                        proportional_edit_falloff='SMOOTH', proportional_size=1
                        )
        deselect_all_in_edit_mode(cuboslink[0])
        salir_de_editmode()
        bpy.ops.object.shade_smooth()
        bpy.context.object.rigid_body.mass = masa
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

        # lo subo todo para arriba un poco mas:
        seleccionar_todo()
        deseleccionar_por_nombre("groundplane")
        bpy.ops.transform.translate(
                        value=(0, 0, offset_del_suelo_real),
                        constraint_axis=(False, False, True),
                        constraint_orientation='GLOBAL', mirror=False,
                        proportional='DISABLED', proportional_edit_falloff='SMOOTH',
                        proportional_size=1
                        )

        deseleccionar_todo()
        seleccionar_por_nombre(cuboslink[-1].name)
        bpy.ops.rigidbody.objects_add(type='PASSIVE')

        bpy.context.scene.rigidbody_world.steps_per_second = world_steps
        bpy.context.scene.rigidbody_world.solver_iterations = solver_iterations

        # para mover todo desde el primero de arriba:
        seleccionar_por_nombre(cuboslink[-1].name)
        bpy.ops.view3d.snap_cursor_to_selected()
        seleccionar_todo()
        deseleccionar_por_nombre("groundplane")
        deseleccionar_por_nombre(cuboslink[-1].name)
        bpy.context.space_data.pivot_point = 'CURSOR'
        bpy.ops.transform.rotate(
                            value=rotrope, axis=(1, 0, 0),
                            constraint_axis=(True, False, False),
                            constraint_orientation='GLOBAL',
                            mirror=False, proportional='DISABLED',
                            proportional_edit_falloff='SMOOTH',
                            proportional_size=1
                            )
        bpy.context.space_data.pivot_point = 'MEDIAN_POINT'
        deseleccionar_todo()

        seleccionar_por_nombre("Cuerda")
        bpy.context.object.data.fill_mode = 'FULL'
        bpy.context.object.data.bevel_depth = radiorope
        for ob in bpy.data.objects:
            if ob.name != cuboslink[0].name:
                if ob.name.find("CubeLink") >= 0:
                    deseleccionar_todo()
                    seleccionar_por_nombre(ob.name)
                    if hidecubeslinks:
                        bpy.context.object.hide = True
        ocultar_relationships()
        deseleccionar_todo()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=310)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column()
        col.label("Rope settings:")
        rowsub0 = col.row()
        rowsub0.prop(self, "hidecubes", text='Hide Link Cubes')
        rowsub1 = col.row()
        rowsub1.prop(self, "ropelenght2", text='Length')
        rowsub1.prop(self, "ropesegments2", text='Segments')
        rowsub2 = col.row()
        rowsub2.prop(self, "radiuscubes", text='Radius Link Cubes')
        rowsub2.prop(self, "radiusrope", text='Radius Rope')
        rowsub3 = col.row()
        rowsub3.prop(self, "grados", text='Degrees')
        rowsub3.prop(self, "separacion", text='Separation Link Cubes')

        col.label("Quality Settings:")
        col.prop(self, "resrope", text='Resolution Rope')
        col.prop(self, "massball", text='Ball Mass')
        col.prop(self, "worldsteps", text='World Steps')
        col.prop(self, "solveriterations", text='Solver Iterarions')


# Register

def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
