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

# <pep8 compliant>

bl_info = {
    "name": "Export Freestyle edges to an .svg format",
    "author": "Folkert de Vries",
    "version": (1, 0),
    "blender": (2, 72, 1),
    "location": "properties > render > SVG Export",
    "description": "Adds the functionality of exporting Freestyle's stylized edges as an .svg file",
    "warning": "",
    "wiki_url": "",
    "category": "Render",
    }

import bpy
import parameter_editor
import itertools
import os

import xml.etree.cElementTree as et

from freestyle.types import (
        StrokeShader,
        Interface0DIterator,
        Operators,
        )
from freestyle.utils import getCurrentScene
from freestyle.functions import GetShapeF1D, CurveMaterialF0D
from freestyle.predicates import (
        AndUP1D,
        ContourUP1D,
        SameShapeIdBP1D,
        NotUP1D,
        QuantitativeInvisibilityUP1D,
        TrueUP1D,
        pyZBP1D,
        )
from freestyle.chainingiterators import ChainPredicateIterator
from parameter_editor import get_dashed_pattern

from bpy.props import (
        BoolProperty,
        EnumProperty,
        PointerProperty,
        )
from bpy.app.handlers import persistent
from collections import OrderedDict
from mathutils import Vector


# use utf-8 here to keep ElementTree happy, end result is utf-16
svg_primitive = """<?xml version="1.0" encoding="ascii" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{:d}" height="{:d}">
</svg>"""


# xml namespaces
namespaces = {
    "inkscape": "http://www.inkscape.org/namespaces/inkscape",
    "svg": "http://www.w3.org/2000/svg",
    }


def render_height(scene):
    return int(scene.render.resolution_y * scene.render.resolution_percentage / 100)


def render_width(scene):
    return int(scene.render.resolution_x * scene.render.resolution_percentage / 100)


class RenderState:
    # Note that this flag is set to False only after the first frame
    # has been written to file.
    is_preview = True


@persistent
def render_init(scene):
    RenderState.is_preview = True


@persistent
def render_write(scene):
    RenderState.is_preview = False


def is_preview_render(scene):
    return RenderState.is_preview or scene.svg_export.mode == 'FRAME'


def create_path(scene):
    """Creates the output path for the svg file"""
    dirname = os.path.dirname(scene.render.frame_path())
    basename = bpy.path.basename(scene.render.filepath)
    if scene.svg_export.mode == 'FRAME':
        frame = "{:04d}".format(scene.frame_current)
    else:
        frame = "{:04d}-{:04d}".format(scene.frame_start, scene.frame_end)
    return os.path.join(dirname, basename + frame + ".svg")


class SVGExport(bpy.types.PropertyGroup):
    """Implements the properties for the SVG exporter"""
    bl_idname = "RENDER_PT_svg_export"

    use_svg_export = BoolProperty(
            name="SVG Export",
            description="Export Freestyle edges to an .svg format",
            )
    split_at_invisible = BoolProperty(
            name="Split at Invisible",
            description="Split the stroke at an invisible vertex",
            )
    object_fill = BoolProperty(
            name="Fill Contours",
            description="Fill the contour with the object's material color",
            )
    mode = EnumProperty(
            name="Mode",
            items=(
                ('FRAME', "Frame", "Export a single frame", 0),
                ('ANIMATION', "Animation", "Export an animation", 1),
                ),
            default='FRAME',
            )
    line_join_type = EnumProperty(
            name="Linejoin",
            items=(
                ('MITTER', "Mitter", "Corners are sharp", 0),
                ('ROUND', "Round", "Corners are smoothed", 1),
                ('BEVEL', "Bevel", "Corners are bevelled", 2),
                ),
            default='ROUND',
            )


class SVGExporterPanel(bpy.types.Panel):
    """Creates a Panel in the render context of the properties editor"""
    bl_idname = "RENDER_PT_SVGExporterPanel"
    bl_space_type = 'PROPERTIES'
    bl_label = "Freestyle SVG Export"
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw_header(self, context):
        self.layout.prop(context.scene.svg_export, "use_svg_export", text="")

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        svg = scene.svg_export
        freestyle = scene.render.layers.active.freestyle_settings

        layout.active = (svg.use_svg_export and freestyle.mode != 'SCRIPT')

        row = layout.row()
        row.prop(svg, "mode", expand=True)

        row = layout.row()
        row.prop(svg, "split_at_invisible")
        row.prop(svg, "object_fill")

        row = layout.row()
        row.prop(svg, "line_join_type", expand=True)


@persistent
def svg_export_header(scene):
    if not (scene.render.use_freestyle and scene.svg_export.use_svg_export):
        return

    # write the header only for the first frame when animation is being rendered
    if not is_preview_render(scene) and scene.frame_current != scene.frame_start:
        return

    # this may fail still. The error is printed to the console.
    with open(create_path(scene), "w") as f:
        f.write(svg_primitive.format(render_width(scene), render_height(scene)))


@persistent
def svg_export_animation(scene):
    """makes an animation of the exported SVG file """
    render = scene.render
    svg = scene.svg_export

    if render.use_freestyle and svg.use_svg_export and not is_preview_render(scene):
        write_animation(create_path(scene), scene.frame_start, render.fps)


def write_animation(filepath, frame_begin, fps):
    """Adds animate tags to the specified file."""
    tree = et.parse(filepath)
    root = tree.getroot()

    linesets = tree.findall(".//svg:g[@inkscape:groupmode='lineset']", namespaces=namespaces)
    for i, lineset in enumerate(linesets):
        name = lineset.get('id')
        frames = lineset.findall(".//svg:g[@inkscape:groupmode='frame']", namespaces=namespaces)
        fills = lineset.findall(".//svg:g[@inkscape:groupmode='fills']", namespaces=namespaces)
        fills = reversed(fills) if fills else itertools.repeat(None, len(frames))

        print("-" * 10, "animate", "-" * 10)

        n_of_frames = len(frames)
        keyTimes = ";".join(str(round(x / n_of_frames, 3)) for x in range(n_of_frames)) + ";1"

        style = {
            'attributeName': 'display',
            'values': "none;" * (n_of_frames - 1) + "inline;none",
            'repeatCount': 'indefinite',
            'keyTimes': keyTimes,
            'dur': str(n_of_frames / fps) + 's',
            }

        print(style)
        print(n_of_frames)

        for j, (frame, fill) in enumerate(zip(frames, fills)):
            id = 'anim_{}_{:06n}'.format(name, j + frame_begin)
            # create animate tag
            frame_anim = et.XML('<animate id="{}" begin="{}s" />'.format(id, (j - n_of_frames) / fps))
            # add per-lineset style attributes
            frame_anim.attrib.update(style)
            # add to the current frame
            frame.append(frame_anim)
            # append the animation to the associated fill as well (if valid)
            if fill is not None:
                fill.append(frame_anim)

    # write SVG to file
    indent_xml(root)
    tree.write(filepath, encoding='ascii', xml_declaration=True)


# - StrokeShaders - #
class SVGPathShader(StrokeShader):
    """Stroke Shader for writing stroke data to a .svg file."""
    def __init__(self, name, style, filepath, res_y, split_at_invisible, frame_current):
        StrokeShader.__init__(self)
        # attribute 'name' of 'StrokeShader' objects is not writable, so _name is used
        self._name = name
        self.filepath = filepath
        self.h = res_y
        self.frame_current = frame_current
        self.elements = []
        self.split_at_invisible = split_at_invisible
        # put style attributes into a single svg path definition
        self.path = '\n<path ' + "".join('{}="{}" '.format(k, v) for k, v in style.items()) + 'd=" M '

    @classmethod
    def from_lineset(cls, lineset, filepath, res_y, split_at_invisible, frame_current, *, name=""):
        """Builds a SVGPathShader using data from the given lineset"""
        name = name or lineset.name
        linestyle = lineset.linestyle
        # extract style attributes from the linestyle and scene
        svg = getCurrentScene().svg_export
        style = {
            'fill': 'none',
            'stroke-width': linestyle.thickness,
            'stroke-linecap': linestyle.caps.lower(),
            'stroke-opacity': linestyle.alpha,
            'stroke': 'rgb({}, {}, {})'.format(*(int(c * 255) for c in linestyle.color)),
            'stroke-linejoin': svg.line_join_type.lower(),
            }
        # get dashed line pattern (if specified)
        if linestyle.use_dashed_line:
            style['stroke-dasharray'] = ",".join(str(elem) for elem in get_dashed_pattern(linestyle))
        # return instance
        return cls(name, style, filepath, res_y, split_at_invisible, frame_current)

    @staticmethod
    def pathgen(stroke, path, height, split_at_invisible, f=lambda v: not v.attribute.visible):
        """Generator that creates SVG paths (as strings) from the current stroke """
        it = iter(stroke)
        # start first path
        yield path
        for v in it:
            x, y = v.point
            yield '{:.3f}, {:.3f} '.format(x, height - y)
            if split_at_invisible and v.attribute.visible is False:
                # end current and start new path;
                yield '" />' + path
                # fast-forward till the next visible vertex
                it = itertools.dropwhile(f, it)
                # yield next visible vertex
                svert = next(it, None)
                if svert is None:
                    break
                x, y = svert.point
                yield '{:.3f}, {:.3f} '.format(x, height - y)
        # close current path
        yield '" />'

    def shade(self, stroke):
        stroke_to_paths = "".join(self.pathgen(stroke, self.path, self.h, self.split_at_invisible)).split("\n")
        # convert to actual XML, check to prevent empty paths
        self.elements.extend(et.XML(elem) for elem in stroke_to_paths if len(elem.strip()) > len(self.path))

    def write(self):
        """Write SVG data tree to file """
        tree = et.parse(self.filepath)
        root = tree.getroot()
        name = self._name

        # make <g> for lineset as a whole (don't overwrite)
        lineset_group = tree.find(".//svg:g[@id='{}']".format(name), namespaces=namespaces)
        if lineset_group is None:
            lineset_group = et.XML('<g/>')
            lineset_group.attrib = {
                'id': name,
                'xmlns:inkscape': namespaces["inkscape"],
                'inkscape:groupmode': 'lineset',
                'inkscape:label': name,
                }
            root.insert(0, lineset_group)

        # make <g> for the current frame
        id = "{}_frame_{:06n}".format(name, self.frame_current)
        frame_group = et.XML("<g/>")
        frame_group.attrib = {'id': id, 'inkscape:groupmode': 'frame', 'inkscape:label': id}
        frame_group.extend(self.elements)
        lineset_group.append(frame_group)

        # write SVG to file
        print("SVG Export: writing to ", self.filepath)
        indent_xml(root)
        tree.write(self.filepath, encoding='ascii', xml_declaration=True)


class SVGFillShader(StrokeShader):
    """Creates SVG fills from the current stroke set"""
    def __init__(self, filepath, height, name):
        StrokeShader.__init__(self)
        # use an ordered dict to maintain input and z-order
        self.shape_map = OrderedDict()
        self.filepath = filepath
        self.h = height
        self._name = name

    def shade(self, stroke, func=GetShapeF1D(), curvemat=CurveMaterialF0D()):
        shape = func(stroke)[0].id.first
        item = self.shape_map.get(shape)
        if len(stroke) > 2:
            if item is not None:
                item[0].append(stroke)
            else:
                # the shape is not yet present, let's create it.
                material = curvemat(Interface0DIterator(stroke))
                *color, alpha = material.diffuse
                self.shape_map[shape] = ([stroke], color, alpha)
        # make the strokes of the second drawing invisible
        for v in stroke:
            v.attribute.visible = False

    @staticmethod
    def pathgen(vertices, path, height):
        yield path
        for point in vertices:
            x, y = point
            yield '{:.3f}, {:.3f} '.format(x, height - y)
        yield 'z" />'  # closes the path; connects the current to the first point

    def write(self):
        """Write SVG data tree to file """
        # initialize SVG
        tree = et.parse(self.filepath)
        root = tree.getroot()
        name = self._name

        # create XML elements from the acquired data
        elems = []
        path = '<path fill-rule="evenodd" stroke="none" fill-opacity="{}" fill="rgb({}, {}, {})"  d=" M '
        for strokes, col, alpha in self.shape_map.values():
            p = path.format(alpha, *(int(255 * c) for c in col))
            for stroke in strokes:
                elems.append(et.XML("".join(self.pathgen((sv.point for sv in stroke), p, self.h))))

        # make <g> for lineset as a whole (don't overwrite)
        lineset_group = tree.find(".//svg:g[@id='{}']".format(name), namespaces=namespaces)
        if lineset_group is None:
            lineset_group = et.XML('<g/>')
            lineset_group.attrib = {
                'id': name,
                'xmlns:inkscape': namespaces["inkscape"],
                'inkscape:groupmode': 'lineset',
                'inkscape:label': name,
                }
            root.insert(0, lineset_group)

        # make <g> for fills
        frame_group = et.XML('<g />')
        frame_group.attrib = {'id': "layer_fills", 'inkscape:groupmode': 'fills', 'inkscape:label': 'fills'}
        # reverse the elements so they are correctly ordered in the image
        frame_group.extend(reversed(elems))
        lineset_group.insert(0, frame_group)

        # write SVG to file
        indent_xml(root)
        tree.write(self.filepath, encoding='ascii', xml_declaration=True)


# - Callbacks - #
class ParameterEditorCallback(object):
    """Object to store callbacks for the Parameter Editor in"""
    def lineset_pre(self, scene, layer, lineset):
        raise NotImplementedError()

    def modifier_post(self, scene, layer, lineset):
        raise NotImplementedError()

    def lineset_post(self, scene, layer, lineset):
        raise NotImplementedError()


class SVGPathShaderCallback(ParameterEditorCallback):
    @classmethod
    def modifier_post(cls, scene, layer, lineset):
        if not (scene.render.use_freestyle and scene.svg_export.use_svg_export):
            return []

        split = scene.svg_export.split_at_invisible
        cls.shader = SVGPathShader.from_lineset(
                lineset, create_path(scene),
                render_height(scene), split, scene.frame_current)
        return [cls.shader]

    @classmethod
    def lineset_post(cls, scene, *args):
        if not (scene.render.use_freestyle and scene.svg_export.use_svg_export):
            return

        cls.shader.write()


class SVGFillShaderCallback(ParameterEditorCallback):
    @staticmethod
    def lineset_post(scene, layer, lineset):
        if not (scene.render.use_freestyle and scene.svg_export.use_svg_export and scene.svg_export.object_fill):
            return

        # reset the stroke selection (but don't delete the already generated strokes)
        Operators.reset(delete_strokes=False)
        # shape detection
        upred = AndUP1D(QuantitativeInvisibilityUP1D(0), ContourUP1D())
        Operators.select(upred)
        # chain when the same shape and visible
        bpred = SameShapeIdBP1D()
        Operators.bidirectional_chain(ChainPredicateIterator(upred, bpred), NotUP1D(QuantitativeInvisibilityUP1D(0)))
        # sort according to the distance from camera
        Operators.sort(pyZBP1D())
        # render and write fills
        shader = SVGFillShader(create_path(scene), render_height(scene), lineset.name)
        Operators.create(TrueUP1D(), [shader, ])
        shader.write()


def indent_xml(elem, level=0, indentsize=4):
    """Prettifies XML code (used in SVG exporter) """
    i = "\n" + level * " " * indentsize
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + " " * indentsize
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent_xml(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    elif level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


classes = (
    SVGExporterPanel,
    SVGExport,
    )


def register():

    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.svg_export = PointerProperty(type=SVGExport)

    # add callbacks
    bpy.app.handlers.render_init.append(render_init)
    bpy.app.handlers.render_write.append(render_write)
    bpy.app.handlers.render_pre.append(svg_export_header)
    bpy.app.handlers.render_complete.append(svg_export_animation)

    # manipulate shaders list
    parameter_editor.callbacks_modifiers_post.append(SVGPathShaderCallback.modifier_post)
    parameter_editor.callbacks_lineset_post.append(SVGPathShaderCallback.lineset_post)
    parameter_editor.callbacks_lineset_post.append(SVGFillShaderCallback.lineset_post)

    # register namespaces
    et.register_namespace("", "http://www.w3.org/2000/svg")
    et.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")
    et.register_namespace("sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")


def unregister():

    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.svg_export

    # remove callbacks
    bpy.app.handlers.render_init.remove(render_init)
    bpy.app.handlers.render_write.remove(render_write)
    bpy.app.handlers.render_pre.remove(svg_export_header)
    bpy.app.handlers.render_complete.remove(svg_export_animation)

    # manipulate shaders list
    parameter_editor.callbacks_modifiers_post.remove(SVGPathShaderCallback.modifier_post)
    parameter_editor.callbacks_lineset_post.remove(SVGPathShaderCallback.lineset_post)
    parameter_editor.callbacks_lineset_post.remove(SVGFillShaderCallback.lineset_post)


if __name__ == "__main__":
    register()
