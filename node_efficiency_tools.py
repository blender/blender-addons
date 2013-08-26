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
    'name': "Nodes Efficiency Tools",
    'author': "Bartek Skorupa",
    'version': (2, 33),
    'blender': (2, 6, 8),
    'location': "Node Editor Properties Panel (Ctrl-SPACE)",
    'description': "Nodes Efficiency Tools",
    'warning': "",
    'wiki_url': "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Nodes_Efficiency_Tools",
    'tracker_url': "http://projects.blender.org/tracker/index.php?func=detail&aid=33543&group_id=153&atid=469",
    'category': "Node",
    }

import bpy
from bpy.types import Operator, Panel, Menu
from bpy.props import FloatProperty, EnumProperty, BoolProperty
from mathutils import Vector

#################
# rl_outputs:
# list of outputs of Input Render Layer
# with attributes determinig if pass is used,
# and MultiLayer EXR outputs names and corresponding render engines
#
# rl_outputs entry = (render_pass, rl_output_name, exr_output_name, in_internal, in_cycles)
rl_outputs = (
    ('use_pass_ambient_occlusion', 'AO', 'AO', True, True),
    ('use_pass_color', 'Color', 'Color', True, False),
    ('use_pass_combined', 'Image', 'Combined', True, True),
    ('use_pass_diffuse', 'Diffuse', 'Diffuse', True, False),
    ('use_pass_diffuse_color', 'Diffuse Color', 'DiffCol', False, True),
    ('use_pass_diffuse_direct', 'Diffuse Direct', 'DiffDir', False, True),
    ('use_pass_diffuse_indirect', 'Diffuse Indirect', 'DiffInd', False, True),
    ('use_pass_emit', 'Emit', 'Emit', True, False),
    ('use_pass_environment', 'Environment', 'Env', True, False),
    ('use_pass_glossy_color', 'Glossy Color', 'GlossCol', False, True),
    ('use_pass_glossy_direct', 'Glossy Direct', 'GlossDir', False, True),
    ('use_pass_glossy_indirect', 'Glossy Indirect', 'GlossInd', False, True),
    ('use_pass_indirect', 'Indirect', 'Indirect', True, False),
    ('use_pass_material_index', 'IndexMA', 'IndexMA', True, True),
    ('use_pass_mist', 'Mist', 'Mist', True, False),
    ('use_pass_normal', 'Normal', 'Normal', True, True),
    ('use_pass_object_index', 'IndexOB', 'IndexOB', True, True),
    ('use_pass_reflection', 'Reflect', 'Reflect', True, False),
    ('use_pass_refraction', 'Refract', 'Refract', True, False),
    ('use_pass_shadow', 'Shadow', 'Shadow', True, True),
    ('use_pass_specular', 'Specular', 'Spec', True, False),
    ('use_pass_subsurface_color', 'Subsurface Color', 'SubsurfaceCol', False, True),
    ('use_pass_subsurface_direct', 'Subsurface Direct', 'SubsurfaceDir', False, True),
    ('use_pass_subsurface_indirect', 'Subsurface Indirect', 'SubsurfaceInd', False, True),
    ('use_pass_transmission_color', 'Transmission Color', 'TransCol', False, True),
    ('use_pass_transmission_direct', 'Transmission Direct', 'TransDir', False, True),
    ('use_pass_transmission_indirect', 'Transmission Indirect', 'TransInd', False, True),
    ('use_pass_uv', 'UV', 'UV', True, True),
    ('use_pass_vector', 'Speed', 'Vector', True, True),
    ('use_pass_z', 'Z', 'Depth', True, True),
    )
# list of blend types of "Mix" nodes in a form that can be used as 'items' for EnumProperty.
blend_types = [
    ('MIX', 'Mix', 'Mix Mode'),
    ('ADD', 'Add', 'Add Mode'),
    ('MULTIPLY', 'Multiply', 'Multiply Mode'),
    ('SUBTRACT', 'Subtract', 'Subtract Mode'),
    ('SCREEN', 'Screen', 'Screen Mode'),
    ('DIVIDE', 'Divide', 'Divide Mode'),
    ('DIFFERENCE', 'Difference', 'Difference Mode'),
    ('DARKEN', 'Darken', 'Darken Mode'),
    ('LIGHTEN', 'Lighten', 'Lighten Mode'),
    ('OVERLAY', 'Overlay', 'Overlay Mode'),
    ('DODGE', 'Dodge', 'Dodge Mode'),
    ('BURN', 'Burn', 'Burn Mode'),
    ('HUE', 'Hue', 'Hue Mode'),
    ('SATURATION', 'Saturation', 'Saturation Mode'),
    ('VALUE', 'Value', 'Value Mode'),
    ('COLOR', 'Color', 'Color Mode'),
    ('SOFT_LIGHT', 'Soft Light', 'Soft Light Mode'),
    ('LINEAR_LIGHT', 'Linear Light', 'Linear Light Mode'),
    ]
# list of operations of "Math" nodes in a form that can be used as 'items' for EnumProperty.
operations = [
    ('ADD', 'Add', 'Add Mode'),
    ('MULTIPLY', 'Multiply', 'Multiply Mode'),
    ('SUBTRACT', 'Subtract', 'Subtract Mode'),
    ('DIVIDE', 'Divide', 'Divide Mode'),
    ('SINE', 'Sine', 'Sine Mode'),
    ('COSINE', 'Cosine', 'Cosine Mode'),
    ('TANGENT', 'Tangent', 'Tangent Mode'),
    ('ARCSINE', 'Arcsine', 'Arcsine Mode'),
    ('ARCCOSINE', 'Arccosine', 'Arccosine Mode'),
    ('ARCTANGENT', 'Arctangent', 'Arctangent Mode'),
    ('POWER', 'Power', 'Power Mode'),
    ('LOGARITHM', 'Logatithm', 'Logarithm Mode'),
    ('MINIMUM', 'Minimum', 'Minimum Mode'),
    ('MAXIMUM', 'Maximum', 'Maximum Mode'),
    ('ROUND', 'Round', 'Round Mode'),
    ('LESS_THAN', 'Less Than', 'Less Thann Mode'),
    ('GREATER_THAN', 'Greater Than', 'Greater Than Mode'),
    ]
# in BatchChangeNodes additional types/operations in a form that can be used as 'items' for EnumProperty.
navs = [
    ('CURRENT', 'Current', 'Leave at current state'),
    ('NEXT', 'Next', 'Next blend type/operation'),
    ('PREV', 'Prev', 'Previous blend type/operation'),
    ]
# list of mixing shaders
merge_shaders_types = ('MIX', 'ADD')
# list of regular shaders. Entry: (identified, type, name for humans). Will be used in SwapShaders and menus.
# Keeping mixed case to avoid having to translate entries when adding new nodes in SwapNodes.
regular_shaders = (
    ('ShaderNodeBsdfDiffuse', 'BSDF_DIFFUSE', 'Diffuse BSDF'),
    ('ShaderNodeBsdfGlossy', 'BSDF_GLOSSY', 'Glossy BSDF'),
    ('ShaderNodeBsdfTransparent', 'BSDF_TRANSPARENT', 'Transparent BSDF'),
    ('ShaderNodeBsdfRefraction', 'BSDF_REFRACTION', 'Refraction BSDF'),
    ('ShaderNodeBsdfGlass', 'BSDF_GLASS', 'Glass BSDF'),
    ('ShaderNodeBsdfTranslucent', 'BSDF_TRANSLUCENT', 'Translucent BSDF'),
    ('ShaderNodeBsdfAnisotropic', 'BSDF_ANISOTROPIC', 'Anisotropic BSDF'),
    ('ShaderNodeBsdfVelvet', 'BSDF_VELVET', 'Velvet BSDF'),
    ('ShaderNodeBsdfToon', 'BSDF_TOON', 'Toon BSDF'),
    ('ShaderNodeSubsurfaceScattering', 'SUBSURFACE_SCATTERING', 'Subsurface Scattering'),
    ('ShaderNodeEmission', 'EMISSION', 'Emission'),
    ('ShaderNodeBackground', 'BACKGROUND', 'Background'),
    ('ShaderNodeAmbientOcclusion', 'AMBIENT_OCCLUSION', 'Ambient Occlusion'),
    ('ShaderNodeHoldout', 'HOLDOUT', 'Holdout'),
    )
merge_shaders = (
    ('ShaderNodeMixShader', 'MIX_SHADER', 'Mix Shader'),
    ('ShaderNodeAddShader', 'ADD_SHADER', 'Add Shader'),
    )

def get_nodes_links(context):
    space = context.space_data
    tree = space.node_tree
    nodes = tree.nodes
    links = tree.links
    active = nodes.active
    context_active = context.active_node
    # check if we are working on regular node tree or node group is currently edited.
    # if group is edited - active node of space_tree is the group
    # if context.active_node != space active node - it means that the group is being edited.
    # in such case we set "nodes" to be nodes of this group, "links" to be links of this group
    # if context.active_node == space.active_node it means that we are not currently editing group
    is_main_tree = True
    if active:
        is_main_tree = context_active == active
    if not is_main_tree:  # if group is currently edited
        tree = active.node_tree
        nodes = tree.nodes
        links = tree.links

    return nodes, links


class NodeToolBase:
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None


class MergeNodes(Operator, NodeToolBase):
    bl_idname = "node.merge_nodes"
    bl_label = "Merge Nodes"
    bl_description = "Merge Selected Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    mode = EnumProperty(
            name="mode",
            description="All possible blend types and math operations",
            items=blend_types + [op for op in operations if op not in blend_types],
            )
    merge_type = EnumProperty(
            name="merge type",
            description="Type of Merge to be used",
            items=(
                ('AUTO', 'Auto', 'Automatic Output Type Detection'),
                ('SHADER', 'Shader', 'Merge using ADD or MIX Shader'),
                ('MIX', 'Mix Node', 'Merge using Mix Nodes'),
                ('MATH', 'Math Node', 'Merge using Math Nodes'),
                ),
            )

    def execute(self, context):
        tree_type = context.space_data.node_tree.type
        if tree_type == 'COMPOSITING':
            node_type = 'CompositorNode'
        elif tree_type == 'SHADER':
            node_type = 'ShaderNode'
        nodes, links = get_nodes_links(context)
        mode = self.mode
        merge_type = self.merge_type
        selected_mix = []  # entry = [index, loc]
        selected_shader = []  # entry = [index, loc]
        selected_math = []  # entry = [index, loc]

        for i, node in enumerate(nodes):
            if node.select and node.outputs:
                if merge_type == 'AUTO':
                    for (type, types_list, dst) in (
                            ('SHADER', merge_shaders_types, selected_shader),
                            ('RGBA', [t[0] for t in blend_types], selected_mix),
                            ('VALUE', [t[0] for t in operations], selected_math),
                            ):
                        output_type = node.outputs[0].type
                        valid_mode = mode in types_list
                        # When mode is 'MIX' use mix node for both 'RGBA' and 'VALUE' output types.
                        # Cheat that output type is 'RGBA',
                        # and that 'MIX' exists in math operations list.
                        # This way when selected_mix list is analyzed:
                        # Node data will be appended even though it doesn't meet requirements.
                        if output_type != 'SHADER' and mode == 'MIX':
                            output_type = 'RGBA'
                            valid_mode = True
                        if output_type == type and valid_mode:
                            dst.append([i, node.location.x, node.location.y])
                else:
                    for (type, types_list, dst) in (
                            ('SHADER', merge_shaders_types, selected_shader),
                            ('MIX', [t[0] for t in blend_types], selected_mix),
                            ('MATH', [t[0] for t in operations], selected_math),
                            ):
                        if merge_type == type and mode in types_list:
                            dst.append([i, node.location.x, node.location.y])
        # When nodes with output kinds 'RGBA' and 'VALUE' are selected at the same time
        # use only 'Mix' nodes for merging.
        # For that we add selected_math list to selected_mix list and clear selected_math.
        if selected_mix and selected_math and merge_type == 'AUTO':
            selected_mix += selected_math
            selected_math = []

        for nodes_list in [selected_mix, selected_shader, selected_math]:
            if nodes_list:
                count_before = len(nodes)
                # sort list by loc_x - reversed
                nodes_list.sort(key=lambda k: k[1], reverse=True)
                # get maximum loc_x
                loc_x = nodes_list[0][1] + 350.0
                nodes_list.sort(key=lambda k: k[2], reverse=True)
                loc_y = nodes_list[len(nodes_list) - 1][2]
                offset_y = 40.0
                if nodes_list == selected_shader:
                    offset_y = 150.0
                the_range = len(nodes_list) - 1
                do_hide = True
                if len(nodes_list) == 1:
                    the_range = 1
                    do_hide = False
                for i in range(the_range):
                    if nodes_list == selected_mix:
                        add_type = node_type + 'MixRGB'
                        add = nodes.new(add_type)
                        add.blend_type = mode
                        add.show_preview = False
                        add.hide = do_hide
                        first = 1
                        second = 2
                        add.width_hidden = 100.0
                    elif nodes_list == selected_math:
                        add_type = node_type + 'Math'
                        add = nodes.new(add_type)
                        add.operation = mode
                        add.hide = do_hide
                        first = 0
                        second = 1
                        add.width_hidden = 100.0
                    elif nodes_list == selected_shader:
                        if mode == 'MIX':
                            add_type = node_type + 'MixShader'
                            add = nodes.new(add_type)
                            first = 1
                            second = 2
                            add.width_hidden = 100.0
                        elif mode == 'ADD':
                            add_type = node_type + 'AddShader'
                            add = nodes.new(add_type)
                            first = 0
                            second = 1
                            add.width_hidden = 100.0
                    add.location = loc_x, loc_y
                    loc_y += offset_y
                    add.select = True
                count_adds = i + 1
                count_after = len(nodes)
                index = count_after - 1
                first_selected = nodes[nodes_list[0][0]]
                # "last" node has been added as first, so its index is count_before.
                last_add = nodes[count_before]
                # add links from last_add to all links 'to_socket' of out links of first selected.
                for fs_link in first_selected.outputs[0].links:
                    # Prevent cyclic dependencies when nodes to be marged are linked to one another.
                    # Create list of invalid indexes.
                    invalid_i = [n[0] for n in (selected_mix + selected_math + selected_shader)]
                    # Link only if "to_node" index not in invalid indexes list.
                    if fs_link.to_node not in [nodes[i] for i in invalid_i]:
                        links.new(last_add.outputs[0], fs_link.to_socket)
                # add link from "first" selected and "first" add node
                links.new(first_selected.outputs[0], nodes[count_after - 1].inputs[first])
                # add links between added ADD nodes and between selected and ADD nodes
                for i in range(count_adds):
                    if i < count_adds - 1:
                        links.new(nodes[index - 1].inputs[first], nodes[index].outputs[0])
                    if len(nodes_list) > 1:
                        links.new(nodes[index].inputs[second], nodes[nodes_list[i + 1][0]].outputs[0])
                    index -= 1
                # set "last" of added nodes as active
                nodes.active = last_add
                for i, x, y in nodes_list:
                    nodes[i].select = False

        return {'FINISHED'}


class BatchChangeNodes(Operator, NodeToolBase):
    bl_idname = "node.batch_change"
    bl_label = "Batch Change"
    bl_description = "Batch Change Blend Type and Math Operation"
    bl_options = {'REGISTER', 'UNDO'}

    blend_type = EnumProperty(
            name="Blend Type",
            items=blend_types + navs,
            )
    operation = EnumProperty(
            name="Operation",
            items=operations + navs,
            )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        blend_type = self.blend_type
        operation = self.operation
        for node in context.selected_nodes:
            if node.type == 'MIX_RGB':
                if not blend_type in [nav[0] for nav in navs]:
                    node.blend_type = blend_type
                else:
                    if blend_type == 'NEXT':
                        index = [i for i, entry in enumerate(blend_types) if node.blend_type in entry][0]
                        #index = blend_types.index(node.blend_type)
                        if index == len(blend_types) - 1:
                            node.blend_type = blend_types[0][0]
                        else:
                            node.blend_type = blend_types[index + 1][0]

                    if blend_type == 'PREV':
                        index = [i for i, entry in enumerate(blend_types) if node.blend_type in entry][0]
                        if index == 0:
                            node.blend_type = blend_types[len(blend_types) - 1][0]
                        else:
                            node.blend_type = blend_types[index - 1][0]

            if node.type == 'MATH':
                if not operation in [nav[0] for nav in navs]:
                    node.operation = operation
                else:
                    if operation == 'NEXT':
                        index = [i for i, entry in enumerate(operations) if node.operation in entry][0]
                        #index = operations.index(node.operation)
                        if index == len(operations) - 1:
                            node.operation = operations[0][0]
                        else:
                            node.operation = operations[index + 1][0]

                    if operation == 'PREV':
                        index = [i for i, entry in enumerate(operations) if node.operation in entry][0]
                        #index = operations.index(node.operation)
                        if index == 0:
                            node.operation = operations[len(operations) - 1][0]
                        else:
                            node.operation = operations[index - 1][0]

        return {'FINISHED'}


class ChangeMixFactor(Operator, NodeToolBase):
    bl_idname = "node.factor"
    bl_label = "Change Factor"
    bl_description = "Change Factors of Mix Nodes and Mix Shader Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    # option: Change factor.
    # If option is 1.0 or 0.0 - set to 1.0 or 0.0
    # Else - change factor by option value.
    option = FloatProperty()

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        option = self.option
        selected = []  # entry = index
        for si, node in enumerate(nodes):
            if node.select:
                if node.type in {'MIX_RGB', 'MIX_SHADER'}:
                    selected.append(si)

        for si in selected:
            fac = nodes[si].inputs[0]
            nodes[si].hide = False
            if option in {0.0, 1.0}:
                fac.default_value = option
            else:
                fac.default_value += option

        return {'FINISHED'}


class NodesCopySettings(Operator):
    bl_idname = "node.copy_settings"
    bl_label = "Copy Settings"
    bl_description = "Copy Settings of Active Node to Selected Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if (space.type == 'NODE_EDITOR' and
                space.node_tree is not None and
                context.active_node is not None and
                context.active_node.type is not 'FRAME'
                ):
            valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        selected = [n for n in nodes if n.select]
        reselect = []  # duplicated nodes will be selected after execution
        active = nodes.active
        if active.select:
            reselect.append(active)

        for node in selected:
            if node.type == active.type and node != active:
                # duplicate active, relink links as in 'node', append copy to 'reselect', delete node
                bpy.ops.node.select_all(action='DESELECT')
                nodes.active = active
                active.select = True
                bpy.ops.node.duplicate()
                copied = nodes.active
                # Copied active should however inherit some properties from 'node'
                attributes = (
                    'hide', 'show_preview', 'mute', 'label',
                    'use_custom_color', 'color', 'width', 'width_hidden',
                    )
                for attr in attributes:
                    setattr(copied, attr, getattr(node, attr))
                # Handle scenario when 'node' is in frame. 'copied' is in same frame then.
                if copied.parent:
                    bpy.ops.node.parent_clear()
                locx = node.location.x
                locy = node.location.y
                # get absolute node location
                parent = node.parent
                while parent:
                    locx += parent.location.x
                    locy += parent.location.y
                    parent = parent.parent
                copied.location = [locx, locy]
                # reconnect links from node to copied
                for i, input in enumerate(node.inputs):
                    if input.links:
                        link = input.links[0]
                        links.new(link.from_socket, copied.inputs[i])
                for out, output in enumerate(node.outputs):
                    if output.links:
                        out_links = output.links
                        for link in out_links:
                            links.new(copied.outputs[out], link.to_socket)
                bpy.ops.node.select_all(action='DESELECT')
                node.select = True
                bpy.ops.node.delete()
                reselect.append(copied)
            else:  # If selected wasn't copied, need to reselect it afterwards.
                reselect.append(node)
        # clean up
        bpy.ops.node.select_all(action='DESELECT')
        for node in reselect:
            node.select = True
        nodes.active = active

        return {'FINISHED'}


class NodesCopyLabel(Operator, NodeToolBase):
    bl_idname = "node.copy_label"
    bl_label = "Copy Label"
    bl_options = {'REGISTER', 'UNDO'}

    option = EnumProperty(
            name="option",
            description="Source of name of label",
            items=(
                ('FROM_ACTIVE', 'from active', 'from active node',),
                ('FROM_NODE', 'from node', 'from node linked to selected node'),
                ('FROM_SOCKET', 'from socket', 'from socket linked to selected node'),
                )
            )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        option = self.option
        active = nodes.active
        if option == 'FROM_ACTIVE':
            if active:
                src_label = active.label
                for node in [n for n in nodes if n.select and nodes.active != n]:
                    node.label = src_label
        elif option == 'FROM_NODE':
            selected = [n for n in nodes if n.select]
            for node in selected:
                for input in node.inputs:
                    if input.links:
                        src = input.links[0].from_node
                        node.label = src.label
                        break
        elif option == 'FROM_SOCKET':
            selected = [n for n in nodes if n.select]
            for node in selected:
                for input in node.inputs:
                    if input.links:
                        src = input.links[0].from_socket
                        node.label = src.name
                        break

        return {'FINISHED'}


class NodesClearLabel(Operator, NodeToolBase):
    bl_idname = "node.clear_label"
    bl_label = "Clear Label"
    bl_options = {'REGISTER', 'UNDO'}

    option = BoolProperty()

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        for node in [n for n in nodes if n.select]:
            node.label = ''

        return {'FINISHED'}

    def invoke(self, context, event):
        if self.option:
            return self.execute(context)
        else:
            return context.window_manager.invoke_confirm(self, event)


class NodesAddTextureSetup(Operator):
    bl_idname = "node.add_texture"
    bl_label = "Texture Setup"
    bl_description = "Add Texture Node Setup to Selected Shaders"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.tree_type == 'ShaderNodeTree' and space.node_tree is not None:
                valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        active = nodes.active
        valid = False
        if active:
            if active.select:
                if active.type in {
                        'BSDF_ANISOTROPIC',
                        'BSDF_DIFFUSE',
                        'BSDF_GLOSSY',
                        'BSDF_GLASS',
                        'BSDF_REFRACTION',
                        'BSDF_TRANSLUCENT',
                        'BSDF_TRANSPARENT',
                        'BSDF_VELVET',
                        'EMISSION',
                        'AMBIENT_OCCLUSION',
                        }:
                    if not active.inputs[0].is_linked:
                        valid = True
        if valid:
            locx = active.location.x
            locy = active.location.y
            tex = nodes.new('ShaderNodeTexImage')
            tex.location = [locx - 200.0, locy + 28.0]
            map = nodes.new('ShaderNodeMapping')
            map.location = [locx - 490.0, locy + 80.0]
            coord = nodes.new('ShaderNodeTexCoord')
            coord.location = [locx - 700, locy + 40.0]
            active.select = False
            nodes.active = tex

            links.new(tex.outputs[0], active.inputs[0])
            links.new(map.outputs[0], tex.inputs[0])
            links.new(coord.outputs[2], map.inputs[0])

        return {'FINISHED'}


class NodesAddReroutes(Operator, NodeToolBase):
    bl_idname = "node.add_reroutes"
    bl_label = "Add Reroutes"
    bl_description = "Add Reroutes to Outputs"
    bl_options = {'REGISTER', 'UNDO'}

    option = EnumProperty(
            name="option",
            items=[
                ('ALL', 'to all', 'Add to all outputs'),
                ('LOOSE', 'to loose', 'Add only to loose outputs'),
                ('LINKED', 'to linked', 'Add only to linked outputs'),
                ]
            )

    def execute(self, context):
        tree_type = context.space_data.node_tree.type
        option = self.option
        nodes, links = get_nodes_links(context)
        # output valid when option is 'all' or when 'loose' output has no links
        valid = False
        post_select = []  # nodes to be selected after execution
        # create reroutes and recreate links
        for node in [n for n in nodes if n.select]:
            if node.outputs:
                x = node.location.x
                y = node.location.y
                width = node.width
                # unhide 'REROUTE' nodes to avoid issues with location.y
                if node.type == 'REROUTE':
                    node.hide = False
                # When node is hidden - width_hidden not usable.
                # Hack needed to calculate real width
                if node.hide:
                    bpy.ops.node.select_all(action='DESELECT')
                    helper = nodes.new('NodeReroute')
                    helper.select = True
                    node.select = True
                    # resize node and helper to zero. Then check locations to calculate width
                    bpy.ops.transform.resize(value=(0.0, 0.0, 0.0))
                    width = 2.0 * (helper.location.x - node.location.x)
                    # restore node location
                    node.location = x, y
                    # delete helper
                    node.select = False
                    # only helper is selected now
                    bpy.ops.node.delete()
                x = node.location.x + width + 20.0
                if node.type != 'REROUTE':
                    y -= 35.0
                y_offset = -22.0
                loc = x, y
            reroutes_count = 0  # will be used when aligning reroutes added to hidden nodes
            for out_i, output in enumerate(node.outputs):
                pass_used = False  # initial value to be analyzed if 'R_LAYERS'
                # if node is not 'R_LAYERS' - "pass_used" not needed, so set it to True
                if node.type != 'R_LAYERS':
                    pass_used = True
                else:  # if 'R_LAYERS' check if output represent used render pass
                    node_scene = node.scene
                    node_layer = node.layer
                    # If output - "Alpha" is analyzed - assume it's used. Not represented in passes.
                    if output.name == 'Alpha':
                        pass_used = True
                    else:
                        # check entries in global 'rl_outputs' variable
                        for render_pass, out_name, exr_name, in_internal, in_cycles in rl_outputs:
                            if output.name == out_name:
                                pass_used = getattr(node_scene.render.layers[node_layer], render_pass)
                                break
                if pass_used:
                    valid = ((option == 'ALL') or
                             (option == 'LOOSE' and not output.links) or
                             (option == 'LINKED' and output.links))
                    # Add reroutes only if valid, but offset location in all cases.
                    if valid:
                        n = nodes.new('NodeReroute')
                        nodes.active = n
                        for link in output.links:
                            links.new(n.outputs[0], link.to_socket)
                        links.new(output, n.inputs[0])
                        n.location = loc
                        post_select.append(n)
                    reroutes_count += 1
                    y += y_offset
                    loc = x, y
            # disselect the node so that after execution of script only newly created nodes are selected
            node.select = False
            # nicer reroutes distribution along y when node.hide
            if node.hide:
                y_translate = reroutes_count * y_offset / 2.0 - y_offset - 35.0
                for reroute in [r for r in nodes if r.select]:
                    reroute.location.y -= y_translate
            for node in post_select:
                node.select = True

        return {'FINISHED'}


class NodesSwap(Operator, NodeToolBase):
    bl_idname = "node.swap_nodes"
    bl_label = "Swap Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    option = EnumProperty(
            items=[
                ('CompositorNodeSwitch', 'Switch', 'Switch'),
                ('NodeReroute', 'Reroute', 'Reroute'),
                ('NodeMixRGB', 'Mix Node', 'Mix Node'),
                ('NodeMath', 'Math Node', 'Math Node'),
                ('CompositorNodeAlphaOver', 'Alpha Over', 'Alpha Over'),
                ('ShaderNodeMixShader', 'Mix Shader', 'Mix Shader'),
                ('ShaderNodeAddShader', 'Add Shader', 'Add Shader'),
                ('ShaderNodeBsdfDiffuse', 'Diffuse BSDF', 'Diffuse BSDF'),
                ('ShaderNodeBsdfGlossy', 'Glossy BSDF', 'Glossy BSDF'),
                ('ShaderNodeBsdfTransparent', 'Transparent BSDF', 'Transparent BSDF'),
                ('ShaderNodeBsdfRefraction', 'Refraction BSDF', 'Refraction BSDF'),
                ('ShaderNodeBsdfGlass', 'Glass BSDF', 'Glass BSDF'),
                ('ShaderNodeBsdfTranslucent', 'Translucent BSDF', 'Translucent BSDF'),
                ('ShaderNodeBsdfAnisotropic', 'Anisotropic BSDF', 'Anisotropic BSDF'),
                ('ShaderNodeBsdfVelvet', 'Velvet BSDF', 'Velvet BSDF'),
                ('ShaderNodeBsdfToon', 'Toon BSDF', 'Toon BSDF'),
                ('ShaderNodeSubsurfaceScattering', 'SUBSURFACE_SCATTERING', 'Subsurface Scattering'),
                ('ShaderNodeEmission', 'Emission', 'Emission'),
                ('ShaderNodeBackground', 'Background', 'Background'),
                ('ShaderNodeAmbientOcclusion', 'Ambient Occlusion', 'Ambient Occlusion'),
                ('ShaderNodeHoldout', 'Holdout', 'Holdout'),
                ]
            )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        tree_type = context.space_data.tree_type
        if tree_type == 'CompositorNodeTree':
            prefix = 'Compositor'
        elif tree_type == 'ShaderNodeTree':
            prefix = 'Shader'
        option = self.option
        selected = [n for n in nodes if n.select]
        reselect = []
        mode = None  # will be used to set proper operation or blend type in new Math or Mix nodes.
        # regular_shaders - global list. Entry: (identifier, type, name for humans)
        # example: ('ShaderNodeBsdfTransparent', 'BSDF_TRANSPARENT', 'Transparent BSDF')
        swap_shaders = option in (s[0] for s in regular_shaders)
        swap_merge_shaders = option in (s[0] for s in merge_shaders)
        if swap_shaders or swap_merge_shaders:
            # replace_types - list of node types that can be replaced using selected option
            shaders = regular_shaders + merge_shaders
            replace_types = [type[1] for type in shaders]
            new_type = option
        elif option == 'CompositorNodeSwitch':
            replace_types = ('REROUTE', 'MIX_RGB', 'MATH', 'ALPHAOVER')
            new_type = option
        elif option == 'NodeReroute':
            replace_types = ('SWITCH')
            new_type = option
        elif option == 'NodeMixRGB':
            replace_types = ('REROUTE', 'SWITCH', 'MATH', 'ALPHAOVER')
            new_type = prefix + option
        elif option == 'NodeMath':
            replace_types = ('REROUTE', 'SWITCH', 'MIX_RGB', 'ALPHAOVER')
            new_type = prefix + option
        elif option == 'CompositorNodeAlphaOver':
            replace_types = ('REROUTE', 'SWITCH', 'MATH', 'MIX_RGB')
            new_type = option
        for node in selected:
            if node.type in replace_types:
                hide = node.hide
                if node.type == 'REROUTE':
                    hide = True
                new_node = nodes.new(new_type)
                # if swap Mix to Math of vice-verca - try to set blend type or operation accordingly
                if new_node.type in {'MIX_RGB', 'ALPHAOVER'}:
                    new_node.inputs[0].default_value = 1.0
                    if node.type == 'MATH':
                        if node.operation in [entry[0] for entry in blend_types]:
                            if hasattr(new_node, 'blend_type'):
                                new_node.blend_type = node.operation
                        for i in range(2):
                            new_node.inputs[i+1].default_value = [node.inputs[i].default_value] * 3 + [1.0]
                    elif node.type in {'MIX_RGB', 'ALPHAOVER'}:
                        for i in range(3):
                            new_node.inputs[i].default_value = node.inputs[i].default_value
                elif new_node.type == 'MATH':
                    if node.type in {'MIX_RGB', 'ALPHAOVER'}:
                        if hasattr(node, 'blend_type'):
                            if node.blend_type in [entry[0] for entry in operations]:
                                new_node.operation = node.blend_type
                        for i in range(2):
                            channels = []
                            for c in range(3):
                                channels.append(node.inputs[i+1].default_value[c])
                            new_node.inputs[i].default_value = max(channels)
                old_inputs_count = len(node.inputs)
                new_inputs_count = len(new_node.inputs)
                replace = []  # entries - pairs: old input index, new input index.
                if swap_shaders:
                    for old_i, old_input in enumerate(node.inputs):
                        for new_i, new_input in enumerate(new_node.inputs):
                            if old_input.name == new_input.name:
                                replace.append((old_i, new_i))
                                new_input.default_value = old_input.default_value
                                break
                elif option == 'ShaderNodeAddShader':
                    if node.type == 'ADD_SHADER':
                        replace = ((0, 0), (1, 1))
                    elif node.type == 'MIX_SHADER':
                        replace = ((1, 0), (2, 1))
                elif option == 'ShaderNodeMixShader':
                    if node.type == 'ADD_SHADER':
                        replace = ((0, 1), (1, 2))
                    elif node.type == 'MIX_SHADER':
                        replace = ((1, 1), (2, 2))
                elif new_inputs_count == 1:
                    replace = ((0, 0), )
                elif new_inputs_count == 2:
                    if old_inputs_count == 1:
                        replace = ((0, 0), )
                    elif old_inputs_count == 2:
                        replace = ((0, 0), (1, 1))
                    elif old_inputs_count == 3:
                        replace = ((1, 0), (2, 1))
                elif new_inputs_count == 3:
                    if old_inputs_count == 1:
                        replace = ((0, 1), )
                    elif old_inputs_count == 2:
                        replace = ((0, 1), (1, 2))
                    elif old_inputs_count == 3:
                        replace = ((0, 0), (1, 1), (2, 2))
                if replace:
                    for old_i, new_i in replace:
                        if node.inputs[old_i].links:
                            in_link = node.inputs[old_i].links[0]
                            links.new(in_link.from_socket, new_node.inputs[new_i])
                for out_link in node.outputs[0].links:
                    links.new(new_node.outputs[0], out_link.to_socket)
                for attr in {'location', 'label', 'mute', 'show_preview', 'width_hidden', 'use_clamp'}:
                    if hasattr(node, attr) and hasattr(new_node, attr):
                        setattr(new_node, attr, getattr(node, attr))
                new_node.hide = hide
                nodes.active = new_node
                reselect.append(new_node)
                bpy.ops.node.select_all(action="DESELECT")
                node.select = True
                bpy.ops.node.delete()
            else:
                reselect.append(node)
        for node in reselect:
            node.select = True

        return {'FINISHED'}


class NodesLinkActiveToSelected(Operator):
    bl_idname = "node.link_active_to_selected"
    bl_label = "Link Active Node to Selected"
    bl_options = {'REGISTER', 'UNDO'}

    replace = BoolProperty()
    use_node_name = BoolProperty()
    use_outputs_names = BoolProperty()

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.node_tree is not None and context.active_node is not None:
                if context.active_node.select:
                    valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        replace = self.replace
        use_node_name = self.use_node_name
        use_outputs_names = self.use_outputs_names
        active = nodes.active
        selected = [node for node in nodes if node.select and node != active]
        outputs = []  # Only usable outputs of active nodes will be stored here.
        for out in active.outputs:
            if active.type != 'R_LAYERS':
                outputs.append(out)
            else:
                # 'R_LAYERS' node type needs special handling.
                # outputs of 'R_LAYERS' are callable even if not seen in UI.
                # Only outputs that represent used passes should be taken into account
                # Check if pass represented by output is used.
                # global 'rl_outputs' list will be used for that
                for render_pass, out_name, exr_name, in_internal, in_cycles in rl_outputs:
                    pass_used = False  # initial value. Will be set to True if pass is used
                    if out.name == 'Alpha':
                        # Alpha output is always present. Doesn't have representation in render pass. Assume it's used.
                        pass_used = True
                    elif out.name == out_name:
                        # example 'render_pass' entry: 'use_pass_uv' Check if True in scene render layers
                        pass_used = getattr(active.scene.render.layers[active.layer], render_pass)
                        break
                if pass_used:
                    outputs.append(out)
        doit = True  # Will be changed to False when links successfully added to previous output.
        for out in outputs:
            if doit:
                for node in selected:
                    dst_name = node.name  # Will be compared with src_name if needed.
                    # When node has label - use it as dst_name
                    if node.label:
                        dst_name = node.label
                    valid = True  # Initial value. Will be changed to False if names don't match.
                    src_name = dst_name  # If names not used - this asignment will keep valid = True.
                    if use_node_name:
                        # Set src_name to source node name or label
                        src_name = active.name
                        if active.label:
                            src_name = active.label
                    elif use_outputs_names:
                        src_name = (out.name, )
                        for render_pass, out_name, exr_name, in_internal, in_cycles in rl_outputs:
                            if out.name in {out_name, exr_name}:
                                src_name = (out_name, exr_name)
                    if dst_name not in src_name:
                        valid = False
                    if valid:
                        for input in node.inputs:
                            if input.type == out.type or node.type == 'REROUTE':
                                if replace or not input.is_linked:
                                    links.new(out, input)
                                    if not use_node_name and not use_outputs_names:
                                        doit = False
                                    break

        return {'FINISHED'}


class AlignNodes(Operator, NodeToolBase):
    bl_idname = "node.align_nodes"
    bl_label = "Align nodes"
    bl_options = {'REGISTER', 'UNDO'}

    # option: 'Vertically', 'Horizontally'
    option = EnumProperty(
            name="option",
            description="Direction",
            items=(
                ('AXIS_X', "Align Vertically", 'Align Vertically'),
                ('AXIS_Y', "Aligh Horizontally", 'Aligh Horizontally'),
                )
            )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        selected = []  # entry = [index, loc.x, loc.y, width, height]
        frames_reselect = []  # entry = frame node. will be used to reselect all selected frames
        active = nodes.active
        for i, node in enumerate(nodes):
            if node.select:
                if node.type == 'FRAME':
                    node.select = False
                    frames_reselect.append(i)
                else:
                    locx = node.location.x
                    locy = node.location.y
                    parent = node.parent
                    while parent is not None:
                        locx += parent.location.x
                        locy += parent.location.y
                        parent = parent.parent
                    selected.append([i, locx, locy])
        count = len(selected)
        # add reroute node then scale all to 0.0 and calculate widths and heights of nodes
        if count > 1:  # aligning makes sense only if at least 2 nodes are selected
            helper = nodes.new('NodeReroute')
            helper.select = True
            bpy.ops.transform.resize(value=(0.0, 0.0, 0.0))
            # store helper's location for further calculations
            zero_x = helper.location.x
            zero_y = helper.location.y
            nodes.remove(helper)
            # helper is deleted but its location is stored
            # helper's width and height are 0.0.
            # Check loc of other nodes in relation to helper to calculate their dimensions
            # and append them to entries of "selected"
            total_w = 0.0  # total width of all nodes. Will be calculated later.
            total_h = 0.0  # total height of all nodes. Will be calculated later
            for j, [i, x, y] in enumerate(selected):
                locx = nodes[i].location.x
                locy = nodes[i].location.y
                # take node's parent (frame) into account. Get absolute location
                parent = nodes[i].parent
                while parent is not None:
                        locx += parent.location.x
                        locy += parent.location.y
                        parent = parent.parent
                width = abs((zero_x - locx) * 2.0)
                height = abs((zero_y - locy) * 2.0)
                selected[j].append(width)  # complete selected's entry for nodes[i]
                selected[j].append(height)  # complete selected's entry for nodes[i]
                total_w += width  # add nodes[i] width to total width of all nodes
                total_h += height  # add nodes[i] height to total height of all nodes
            selected_sorted_x = sorted(selected, key=lambda k: (k[1], -k[2]))
            selected_sorted_y = sorted(selected, key=lambda k: (-k[2], k[1]))
            min_x = selected_sorted_x[0][1]  # min loc.x
            min_x_loc_y = selected_sorted_x[0][2]  # loc y of node with min loc x
            min_x_w = selected_sorted_x[0][3]  # width of node with max loc x
            max_x = selected_sorted_x[count - 1][1]  # max loc.x
            max_x_loc_y = selected_sorted_x[count - 1][2]  # loc y of node with max loc.x
            max_x_w = selected_sorted_x[count - 1][3]  # width of node with max loc.x
            min_y = selected_sorted_y[0][2]  # min loc.y
            min_y_loc_x = selected_sorted_y[0][1]  # loc.x of node with min loc.y
            min_y_h = selected_sorted_y[0][4]  # height of node with min loc.y
            min_y_w = selected_sorted_y[0][3]  # width of node with min loc.y
            max_y = selected_sorted_y[count - 1][2]  # max loc.y
            max_y_loc_x = selected_sorted_y[count - 1][1]  # loc x of node with max loc.y
            max_y_w = selected_sorted_y[count - 1][3]  # width of node with max loc.y
            max_y_h = selected_sorted_y[count - 1][4]  # height of node with max loc.y

            if self.option == 'AXIS_Y':  # Horizontally. Equivelent of s -> x -> 0 with even spacing.
                loc_x = min_x
                #loc_y = (max_x_loc_y + min_x_loc_y) / 2.0
                loc_y = (max_y - max_y_h / 2.0 + min_y - min_y_h / 2.0) / 2.0
                offset_x = (max_x - min_x - total_w + max_x_w) / (count - 1)
                for i, x, y, w, h in selected_sorted_x:
                    nodes[i].location.x = loc_x
                    nodes[i].location.y = loc_y + h / 2.0
                    parent = nodes[i].parent
                    while parent is not None:
                        nodes[i].location.x -= parent.location.x
                        nodes[i].location.y -= parent.location.y
                        parent = parent.parent
                    loc_x += offset_x + w
            else:  # if self.option == 'AXIS_Y'
                #loc_x = (max_y_loc_x + max_y_w / 2.0 + min_y_loc_x + min_y_w / 2.0) / 2.0
                loc_x = (max_x + max_x_w / 2.0 + min_x + min_x_w / 2.0) / 2.0
                loc_y = min_y
                offset_y = (max_y - min_y + total_h - min_y_h) / (count - 1)
                for i, x, y, w, h in selected_sorted_y:
                    nodes[i].location.x = loc_x - w / 2.0
                    nodes[i].location.y = loc_y
                    parent = nodes[i].parent
                    while parent is not None:
                        nodes[i].location.x -= parent.location.x
                        nodes[i].location.y -= parent.location.y
                        parent = parent.parent
                    loc_y += offset_y - h

            # reselect selected frames
            for i in frames_reselect:
                nodes[i].select = True
            # restore active node
            nodes.active = active

        return {'FINISHED'}


class SelectParentChildren(Operator, NodeToolBase):
    bl_idname = "node.select_parent_child"
    bl_label = "Select Parent or Children"
    bl_options = {'REGISTER', 'UNDO'}

    option = EnumProperty(
            name="option",
            items=(
                ('PARENT', 'Select Parent', 'Select Parent Frame'),
                ('CHILD', 'Select Children', 'Select members of selected frame'),
                )
            )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        option = self.option
        selected = [node for node in nodes if node.select]
        if option == 'PARENT':
            for sel in selected:
                parent = sel.parent
                if parent:
                    parent.select = True
        else:  # option == 'CHILD'
            for sel in selected:
                children = [node for node in nodes if node.parent == sel]
                for kid in children:
                    kid.select = True

        return {'FINISHED'}


class DetachOutputs(Operator, NodeToolBase):
    bl_idname = "node.detach_outputs"
    bl_label = "Detach Outputs"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        nodes, links = get_nodes_links(context)
        selected = context.selected_nodes
        bpy.ops.node.duplicate_move_keep_inputs()
        new_nodes = context.selected_nodes
        bpy.ops.node.select_all(action="DESELECT")
        for node in selected:
            node.select = True
        bpy.ops.node.delete_reconnect()
        for new_node in new_nodes:
            new_node.select = True
        bpy.ops.transform.translate('INVOKE_DEFAULT')
        
        return {'FINISHED'}


class LinkToOutputNode(Operator, NodeToolBase):
    bl_idname = "node.link_to_output_node"
    bl_label = "Link to Output Node"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if (space.type == 'NODE_EDITOR' and
                space.node_tree is not None and
                context.active_node is not None
                ):
            valid = True
        return valid
    
    def execute(self, context):
        nodes, links = get_nodes_links(context)
        active = nodes.active
        output_node = None
        for node in nodes:
            if (node.type == 'OUTPUT_MATERIAL' or\
                    node.type == 'OUTPUT_WORLD' or\
                    node.type == 'OUTPUT_LAMP' or\
                    node.type == 'COMPOSITE'):
                output_node = node
                break
        if not output_node:
            bpy.ops.node.select_all(action="DESELECT")
            type = context.space_data.tree_type
            if type == 'ShaderNodeTree':
                output_node = nodes.new('ShaderNodeOutputMaterial')
            elif type == 'CompositorNodeTree':
                output_node = nodes.new('CompositorNodeComposite')
            output_node.location = active.location + Vector((300.0, 0.0))
            nodes.active = output_node
        if (output_node and active.outputs):
            output_index = 0
            for i, output in enumerate(active.outputs):
                if output.type == output_node.inputs[0].type:
                    output_index = i
                    break
            links.new(active.outputs[output_index], output_node.inputs[0])

        return {'FINISHED'}


#############################################################
#  P A N E L S
#############################################################

class EfficiencyToolsPanel(Panel, NodeToolBase):
    bl_idname = "NODE_PT_efficiency_tools"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Efficiency Tools (Ctrl-SPACE)"

    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout

        box = layout.box()
        box.menu(MergeNodesMenu.bl_idname)
        if type == 'ShaderNodeTree':
            box.operator(NodesAddTextureSetup.bl_idname, text="Add Image Texture (Ctrl T)")
        box.menu(BatchChangeNodesMenu.bl_idname, text="Batch Change...")
        box.menu(NodeAlignMenu.bl_idname, text="Align Nodes (Shift =)")
        box.menu(CopyToSelectedMenu.bl_idname, text="Copy to Selected (Shift-C)")
        box.operator(NodesClearLabel.bl_idname).option = True
        box.operator(DetachOutputs.bl_idname)
        box.menu(AddReroutesMenu.bl_idname, text="Add Reroutes ( / )")
        box.menu(NodesSwapMenu.bl_idname, text="Swap Nodes (Shift-S)")
        box.menu(LinkActiveToSelectedMenu.bl_idname, text="Link Active To Selected ( \\ )")
        box.operator(LinkToOutputNode.bl_idname)


#############################################################
#  M E N U S
#############################################################

class EfficiencyToolsMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_node_tools_menu"
    bl_label = "Efficiency Tools"

    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout
        layout.menu(MergeNodesMenu.bl_idname, text="Merge Selected Nodes")
        if type == 'ShaderNodeTree':
            layout.operator(NodesAddTextureSetup.bl_idname, text="Add Image Texture with coordinates")
        layout.menu(BatchChangeNodesMenu.bl_idname, text="Batch Change")
        layout.menu(NodeAlignMenu.bl_idname, text="Align Nodes")
        layout.menu(CopyToSelectedMenu.bl_idname, text="Copy to Selected")
        layout.operator(NodesClearLabel.bl_idname).option = True
        layout.operator(DetachOutputs.bl_idname)
        layout.menu(AddReroutesMenu.bl_idname, text="Add Reroutes")
        layout.menu(NodesSwapMenu.bl_idname, text="Swap Nodes")
        layout.menu(LinkActiveToSelectedMenu.bl_idname, text="Link Active To Selected")
        layout.operator(LinkToOutputNode.bl_idname)


class MergeNodesMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_merge_nodes_menu"
    bl_label = "Merge Selected Nodes"

    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout
        if type == 'ShaderNodeTree':
            layout.menu(MergeShadersMenu.bl_idname, text="Use Shaders")
        layout.menu(MergeMixMenu.bl_idname, text="Use Mix Nodes")
        layout.menu(MergeMathMenu.bl_idname, text="Use Math Nodes")


class MergeShadersMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_merge_shaders_menu"
    bl_label = "Merge Selected Nodes using Shaders"

    def draw(self, context):
        layout = self.layout
        for type in merge_shaders_types:
            props = layout.operator(MergeNodes.bl_idname, text=type)
            props.mode = type
            props.merge_type = 'SHADER'


class MergeMixMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_merge_mix_menu"
    bl_label = "Merge Selected Nodes using Mix"

    def draw(self, context):
        layout = self.layout
        for type, name, description in blend_types:
            props = layout.operator(MergeNodes.bl_idname, text=name)
            props.mode = type
            props.merge_type = 'MIX'


class MergeMathMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_merge_math_menu"
    bl_label = "Merge Selected Nodes using Math"

    def draw(self, context):
        layout = self.layout
        for type, name, description in operations:
            props = layout.operator(MergeNodes.bl_idname, text=name)
            props.mode = type
            props.merge_type = 'MATH'


class BatchChangeNodesMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_batch_change_nodes_menu"
    bl_label = "Batch Change Selected Nodes"

    def draw(self, context):
        layout = self.layout
        layout.menu(BatchChangeBlendTypeMenu.bl_idname)
        layout.menu(BatchChangeOperationMenu.bl_idname)


class BatchChangeBlendTypeMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_batch_change_blend_type_menu"
    bl_label = "Batch Change Blend Type"

    def draw(self, context):
        layout = self.layout
        for type, name, description in blend_types:
            props = layout.operator(BatchChangeNodes.bl_idname, text=name)
            props.blend_type = type
            props.operation = 'CURRENT'


class BatchChangeOperationMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_batch_change_operation_menu"
    bl_label = "Batch Change Math Operation"

    def draw(self, context):
        layout = self.layout
        for type, name, description in operations:
            props = layout.operator(BatchChangeNodes.bl_idname, text=name)
            props.blend_type = 'CURRENT'
            props.operation = type


class CopyToSelectedMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_copy_node_properties_menu"
    bl_label = "Copy to Selected"

    def draw(self, context):
        layout = self.layout
        layout.operator(NodesCopySettings.bl_idname, text="Settings from Active")
        layout.menu(CopyLabelMenu.bl_idname)


class CopyLabelMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_copy_label_menu"
    bl_label = "Copy Label"

    def draw(self, context):
        layout = self.layout
        layout.operator(NodesCopyLabel.bl_idname, text="from Active Node's Label").option = 'FROM_ACTIVE'
        layout.operator(NodesCopyLabel.bl_idname, text="from Linked Node's Label").option = 'FROM_NODE'
        layout.operator(NodesCopyLabel.bl_idname, text="from Linked Output's Name").option = 'FROM_SOCKET'


class AddReroutesMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_add_reroutes_menu"
    bl_label = "Add Reroutes"
    bl_description = "Add Reroute Nodes to Selected Nodes' Outputs"

    def draw(self, context):
        layout = self.layout
        layout.operator(NodesAddReroutes.bl_idname, text="to All Outputs").option = 'ALL'
        layout.operator(NodesAddReroutes.bl_idname, text="to Loose Outputs").option = 'LOOSE'
        layout.operator(NodesAddReroutes.bl_idname, text="to Linked Outputs").option = 'LINKED'


class NodesSwapMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_swap_menu"
    bl_label = "Swap Nodes"

    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout
        if type == 'ShaderNodeTree':
            layout.menu(ShadersSwapMenu.bl_idname, text="Swap Shaders")
        layout.operator(NodesSwap.bl_idname, text="Change to Mix Nodes").option = 'NodeMixRGB'
        layout.operator(NodesSwap.bl_idname, text="Change to Math Nodes").option = 'NodeMath'
        if type == 'CompositorNodeTree':
            layout.operator(NodesSwap.bl_idname, text="Change to Alpha Over").option = 'CompositorNodeAlphaOver'
        if type == 'CompositorNodeTree':
            layout.operator(NodesSwap.bl_idname, text="Change to Switches").option = 'CompositorNodeSwitch'
            layout.operator(NodesSwap.bl_idname, text="Change to Reroutes").option = 'NodeReroute'


class ShadersSwapMenu(Menu):
    bl_idname = "NODE_MT_shaders_swap_menu"
    bl_label = "Swap Shaders"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.tree_type == 'ShaderNodeTree' and space.node_tree is not None:
                valid = True
        return valid

    def draw(self, context):
        layout = self.layout
        shaders = merge_shaders + regular_shaders
        for opt, type, txt in shaders:
            layout.operator(NodesSwap.bl_idname, text=txt).option = opt


class LinkActiveToSelectedMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_link_active_to_selected_menu"
    bl_label = "Link Active to Selected"

    def draw(self, context):
        layout = self.layout
        layout.menu(LinkStandardMenu.bl_idname)
        layout.menu(LinkUseNodeNameMenu.bl_idname)
        layout.menu(LinkUseOutputsNamesMenu.bl_idname)


class LinkStandardMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_link_standard_menu"
    bl_label = "To All Selected"

    def draw(self, context):
        layout = self.layout
        props = layout.operator(NodesLinkActiveToSelected.bl_idname, text="Don't Replace Links")
        props.replace = False
        props.use_node_name = False
        props.use_outputs_names = False
        props = layout.operator(NodesLinkActiveToSelected.bl_idname, text="Replace Links")
        props.replace = True
        props.use_node_name = False
        props.use_outputs_names = False


class LinkUseNodeNameMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_link_use_node_name_menu"
    bl_label = "Use Node Name/Label"

    def draw(self, context):
        layout = self.layout
        props = layout.operator(NodesLinkActiveToSelected.bl_idname, text="Don't Replace Links")
        props.replace = False
        props.use_node_name = True
        props.use_outputs_names = False
        props = layout.operator(NodesLinkActiveToSelected.bl_idname, text="Replace Links")
        props.replace = True
        props.use_node_name = True
        props.use_outputs_names = False


class LinkUseOutputsNamesMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_link_use_outputs_names_menu"
    bl_label = "Use Outputs Names"

    def draw(self, context):
        layout = self.layout
        props = layout.operator(NodesLinkActiveToSelected.bl_idname, text="Don't Replace Links")
        props.replace = False
        props.use_node_name = False
        props.use_outputs_names = True
        props = layout.operator(NodesLinkActiveToSelected.bl_idname, text="Replace Links")
        props.replace = True
        props.use_node_name = False
        props.use_outputs_names = True


class NodeAlignMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_node_align_menu"
    bl_label = "Align Nodes"

    def draw(self, context):
        layout = self.layout
        layout.operator(AlignNodes.bl_idname, text="Horizontally").option = 'AXIS_X'
        layout.operator(AlignNodes.bl_idname, text="Vertically").option = 'AXIS_Y'


#############################################################
#  MENU ITEMS
#############################################################

def select_parent_children_buttons(self, context):
    layout = self.layout
    layout.operator(SelectParentChildren.bl_idname, text="Select frame's members (children)").option = 'CHILD'
    layout.operator(SelectParentChildren.bl_idname, text="Select parent frame").option = 'PARENT'

#############################################################
#  REGISTER/UNREGISTER CLASSES AND KEYMAP ITEMS
#############################################################

addon_keymaps = []
# kmi_defs entry: (identifier, key, CTRL, SHIFT, ALT, props)
# props entry: (property name, property value)
kmi_defs = (
    # MERGE NODES
    # MergeNodes with Ctrl (AUTO).
    (MergeNodes.bl_idname, 'NUMPAD_0', True, False, False,
        (('mode', 'MIX'), ('merge_type', 'AUTO'),)),
    (MergeNodes.bl_idname, 'ZERO', True, False, False,
        (('mode', 'MIX'), ('merge_type', 'AUTO'),)),
    (MergeNodes.bl_idname, 'NUMPAD_PLUS', True, False, False,
        (('mode', 'ADD'), ('merge_type', 'AUTO'),)),
    (MergeNodes.bl_idname, 'EQUAL', True, False, False,
        (('mode', 'ADD'), ('merge_type', 'AUTO'),)),
    (MergeNodes.bl_idname, 'NUMPAD_ASTERIX', True, False, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'AUTO'),)),
    (MergeNodes.bl_idname, 'EIGHT', True, False, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'AUTO'),)),
    (MergeNodes.bl_idname, 'NUMPAD_MINUS', True, False, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'AUTO'),)),
    (MergeNodes.bl_idname, 'MINUS', True, False, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'AUTO'),)),
    (MergeNodes.bl_idname, 'NUMPAD_SLASH', True, False, False,
        (('mode', 'DIVIDE'), ('merge_type', 'AUTO'),)),
    (MergeNodes.bl_idname, 'SLASH', True, False, False,
        (('mode', 'DIVIDE'), ('merge_type', 'AUTO'),)),
    (MergeNodes.bl_idname, 'COMMA', True, False, False,
        (('mode', 'LESS_THAN'), ('merge_type', 'MATH'),)),
    (MergeNodes.bl_idname, 'PERIOD', True, False, False,
        (('mode', 'GREATER_THAN'), ('merge_type', 'MATH'),)),
    # MergeNodes with Ctrl Alt (MIX)
    (MergeNodes.bl_idname, 'NUMPAD_0', True, False, True,
        (('mode', 'MIX'), ('merge_type', 'MIX'),)),
    (MergeNodes.bl_idname, 'ZERO', True, False, True,
        (('mode', 'MIX'), ('merge_type', 'MIX'),)),
    (MergeNodes.bl_idname, 'NUMPAD_PLUS', True, False, True,
        (('mode', 'ADD'), ('merge_type', 'MIX'),)),
    (MergeNodes.bl_idname, 'EQUAL', True, False, True,
        (('mode', 'ADD'), ('merge_type', 'MIX'),)),
    (MergeNodes.bl_idname, 'NUMPAD_ASTERIX', True, False, True,
        (('mode', 'MULTIPLY'), ('merge_type', 'MIX'),)),
    (MergeNodes.bl_idname, 'EIGHT', True, False, True,
        (('mode', 'MULTIPLY'), ('merge_type', 'MIX'),)),
    (MergeNodes.bl_idname, 'NUMPAD_MINUS', True, False, True,
        (('mode', 'SUBTRACT'), ('merge_type', 'MIX'),)),
    (MergeNodes.bl_idname, 'MINUS', True, False, True,
        (('mode', 'SUBTRACT'), ('merge_type', 'MIX'),)),
    (MergeNodes.bl_idname, 'NUMPAD_SLASH', True, False, True,
        (('mode', 'DIVIDE'), ('merge_type', 'MIX'),)),
    (MergeNodes.bl_idname, 'SLASH', True, False, True,
        (('mode', 'DIVIDE'), ('merge_type', 'MIX'),)),
    # MergeNodes with Ctrl Shift (MATH)
    (MergeNodes.bl_idname, 'NUMPAD_PLUS', True, True, False,
        (('mode', 'ADD'), ('merge_type', 'MATH'),)),
    (MergeNodes.bl_idname, 'EQUAL', True, True, False,
        (('mode', 'ADD'), ('merge_type', 'MATH'),)),
    (MergeNodes.bl_idname, 'NUMPAD_ASTERIX', True, True, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'MATH'),)),
    (MergeNodes.bl_idname, 'EIGHT', True, True, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'MATH'),)),
    (MergeNodes.bl_idname, 'NUMPAD_MINUS', True, True, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'MATH'),)),
    (MergeNodes.bl_idname, 'MINUS', True, True, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'MATH'),)),
    (MergeNodes.bl_idname, 'NUMPAD_SLASH', True, True, False,
        (('mode', 'DIVIDE'), ('merge_type', 'MATH'),)),
    (MergeNodes.bl_idname, 'SLASH', True, True, False,
        (('mode', 'DIVIDE'), ('merge_type', 'MATH'),)),
    (MergeNodes.bl_idname, 'COMMA', True, True, False,
        (('mode', 'LESS_THAN'), ('merge_type', 'MATH'),)),
    (MergeNodes.bl_idname, 'PERIOD', True, True, False,
        (('mode', 'GREATER_THAN'), ('merge_type', 'MATH'),)),
    # BATCH CHANGE NODES
    # BatchChangeNodes with Alt
    (BatchChangeNodes.bl_idname, 'NUMPAD_0', False, False, True,
        (('blend_type', 'MIX'), ('operation', 'CURRENT'),)),
    (BatchChangeNodes.bl_idname, 'ZERO', False, False, True,
        (('blend_type', 'MIX'), ('operation', 'CURRENT'),)),
    (BatchChangeNodes.bl_idname, 'NUMPAD_PLUS', False, False, True,
        (('blend_type', 'ADD'), ('operation', 'ADD'),)),
    (BatchChangeNodes.bl_idname, 'EQUAL', False, False, True,
        (('blend_type', 'ADD'), ('operation', 'ADD'),)),
    (BatchChangeNodes.bl_idname, 'NUMPAD_ASTERIX', False, False, True,
        (('blend_type', 'MULTIPLY'), ('operation', 'MULTIPLY'),)),
    (BatchChangeNodes.bl_idname, 'EIGHT', False, False, True,
        (('blend_type', 'MULTIPLY'), ('operation', 'MULTIPLY'),)),
    (BatchChangeNodes.bl_idname, 'NUMPAD_MINUS', False, False, True,
        (('blend_type', 'SUBTRACT'), ('operation', 'SUBTRACT'),)),
    (BatchChangeNodes.bl_idname, 'MINUS', False, False, True,
        (('blend_type', 'SUBTRACT'), ('operation', 'SUBTRACT'),)),
    (BatchChangeNodes.bl_idname, 'NUMPAD_SLASH', False, False, True,
        (('blend_type', 'DIVIDE'), ('operation', 'DIVIDE'),)),
    (BatchChangeNodes.bl_idname, 'SLASH', False, False, True,
        (('blend_type', 'DIVIDE'), ('operation', 'DIVIDE'),)),
    (BatchChangeNodes.bl_idname, 'COMMA', False, False, True,
        (('blend_type', 'CURRENT'), ('operation', 'LESS_THAN'),)),
    (BatchChangeNodes.bl_idname, 'PERIOD', False, False, True,
        (('blend_type', 'CURRENT'), ('operation', 'GREATER_THAN'),)),
    (BatchChangeNodes.bl_idname, 'DOWN_ARROW', False, False, True,
        (('blend_type', 'NEXT'), ('operation', 'NEXT'),)),
    (BatchChangeNodes.bl_idname, 'UP_ARROW', False, False, True,
        (('blend_type', 'PREV'), ('operation', 'PREV'),)),
    # LINK ACTIVE TO SELECTED
    # Don't use names, don't replace links (K)
    (NodesLinkActiveToSelected.bl_idname, 'K', False, False, False,
        (('replace', False), ('use_node_name', False), ('use_outputs_names', False),)),
    # Don't use names, replace links (Shift K)
    (NodesLinkActiveToSelected.bl_idname, 'K', False, True, False,
        (('replace', True), ('use_node_name', False), ('use_outputs_names', False),)),
    # Use node name, don't replace links (')
    (NodesLinkActiveToSelected.bl_idname, 'QUOTE', False, False, False,
        (('replace', False), ('use_node_name', True), ('use_outputs_names', False),)),
    # Don't use names, replace links (')
    (NodesLinkActiveToSelected.bl_idname, 'QUOTE', False, True, False,
        (('replace', True), ('use_node_name', True), ('use_outputs_names', False),)),
    (NodesLinkActiveToSelected.bl_idname, 'SEMI_COLON', False, False, False,
        (('replace', False), ('use_node_name', False), ('use_outputs_names', True),)),
    # Don't use names, replace links (')
    (NodesLinkActiveToSelected.bl_idname, 'SEMI_COLON', False, True, False,
        (('replace', True), ('use_node_name', False), ('use_outputs_names', True),)),
    # CHANGE MIX FACTOR
    (ChangeMixFactor.bl_idname, 'LEFT_ARROW', False, False, True, (('option', -0.1),)),
    (ChangeMixFactor.bl_idname, 'RIGHT_ARROW', False, False, True, (('option', 0.1),)),
    (ChangeMixFactor.bl_idname, 'LEFT_ARROW', False, True, True, (('option', -0.01),)),
    (ChangeMixFactor.bl_idname, 'RIGHT_ARROW', False, True, True, (('option', 0.01),)),
    (ChangeMixFactor.bl_idname, 'LEFT_ARROW', True, True, True, (('option', 0.0),)),
    (ChangeMixFactor.bl_idname, 'RIGHT_ARROW', True, True, True, (('option', 1.0),)),
    (ChangeMixFactor.bl_idname, 'NUMPAD_0', True, True, True, (('option', 0.0),)),
    (ChangeMixFactor.bl_idname, 'ZERO', True, True, True, (('option', 0.0),)),
    (ChangeMixFactor.bl_idname, 'NUMPAD_1', True, True, True, (('option', 1.0),)),
    (ChangeMixFactor.bl_idname, 'ONE', True, True, True, (('option', 1.0),)),
    # CLEAR LABEL (Alt L)
    (NodesClearLabel.bl_idname, 'L', False, False, True, (('option', False),)),
    # DETACH OUTPUTS (Alt Shift D)
    (DetachOutputs.bl_idname, 'D', False, True, True, None),
    # LINK TO OUTPUT NODE (O)
    (LinkToOutputNode.bl_idname, 'O', False, False, False, None),
    # SELECT PARENT/CHILDREN
    # Select Children
    (SelectParentChildren.bl_idname, 'RIGHT_BRACKET', False, False, False, (('option', 'CHILD'),)),
    # Select Parent
    (SelectParentChildren.bl_idname, 'LEFT_BRACKET', False, False, False, (('option', 'PARENT'),)),
    # Add Texture Setup
    (NodesAddTextureSetup.bl_idname, 'T', True, False, False, None),
    # Copy Label from active to selected
    (NodesCopyLabel.bl_idname, 'V', False, True, False, (('option', 'FROM_ACTIVE'),)),
    # MENUS
    ('wm.call_menu', 'SPACE', True, False, False, (('name', EfficiencyToolsMenu.bl_idname),)),
    ('wm.call_menu', 'SLASH', False, False, False, (('name', AddReroutesMenu.bl_idname),)),
    ('wm.call_menu', 'NUMPAD_SLASH', False, False, False, (('name', AddReroutesMenu.bl_idname),)),
    ('wm.call_menu', 'EQUAL', False, True, False, (('name', NodeAlignMenu.bl_idname),)),
    ('wm.call_menu', 'BACK_SLASH', False, False, False, (('name', LinkActiveToSelectedMenu.bl_idname),)),
    ('wm.call_menu', 'C', False, True, False, (('name', CopyToSelectedMenu.bl_idname),)),
    ('wm.call_menu', 'S', False, True, False, (('name', NodesSwapMenu.bl_idname),)),
    )


def register():
    bpy.utils.register_module(__name__)
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Node Editor', space_type="NODE_EDITOR")
    for (identifier, key, CTRL, SHIFT, ALT, props) in kmi_defs:
        kmi = km.keymap_items.new(identifier, key, 'PRESS', ctrl=CTRL, shift=SHIFT, alt=ALT)
        if props:
            for prop, value in props:
                setattr(kmi.properties, prop, value)
        addon_keymaps.append((km, kmi))
    # menu items
    bpy.types.NODE_MT_select.append(select_parent_children_buttons)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.NODE_MT_select.remove(select_parent_children_buttons)
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()