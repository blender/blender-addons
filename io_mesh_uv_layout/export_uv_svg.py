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

# <pep8-80 compliant>

import bpy


from xml.sax.saxutils import escape
from os.path import basename


class Export_UV_SVG:
    def begin(self, fw, image_size, opacity):

        self.fw = fw
        self.image_width = image_size[0]
        self.image_height = image_size[1]
        self.opacity = opacity

        fw('<?xml version="1.0" standalone="no"?>\n')
        fw('<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" \n')
        fw('  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')
        fw('<svg width="%d" height="%d" viewBox="0 0 %d %d"\n' %
           (self.image_width, self.image_height, self.image_width, self.image_height))
        fw('     xmlns="http://www.w3.org/2000/svg" version="1.1">\n')
        desc = ("%r, (Blender %s)" %
                (basename(bpy.data.filepath), bpy.app.version_string))
        fw('<desc>%s</desc>\n' % escape(desc))

    def build(self, mesh, face_iter_func):
        self.fw('<g>\n')
        desc = ("Mesh: %s" % (mesh.name))
        self.fw('<desc>%s</desc>\n' % escape(desc))

        # svg colors
        fill_settings = []
        fill_default = 'fill="grey"'
        for mat in mesh.materials if mesh.materials else [None]:
            if mat:
                fill_settings.append('fill="rgb(%d, %d, %d)"' %
                                     tuple(int(c * 255) for c in mat.diffuse_color))
            else:
                fill_settings.append(fill_default)

        polys = mesh.polygons
        for i, uvs in face_iter_func():
            try:  # rare cases material index is invalid.
                fill = fill_settings[polys[i].material_index]
            except IndexError:
                fill = fill_default

            self.fw('<polygon stroke="black" stroke-width="1"')
            if self.opacity > 0.0:
                self.fw(' %s fill-opacity="%.2g"' % (fill, self.opacity))

            self.fw(' points="')

            for j, uv in enumerate(uvs):
                x, y = uv[0], 1.0 - uv[1]
                self.fw('%.3f,%.3f ' % (x * self.image_width, y * self.image_height))
            self.fw('" />\n')

        self.fw('</g>\n')

    def end(self):
        self.fw('\n')
        self.fw('</svg>\n')
