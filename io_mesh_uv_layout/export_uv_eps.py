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


class Export_UV_EPS:
    def begin(self, fw, image_size, opacity):

        self.fw = fw
        self.image_width = image_size[0]
        self.image_height = image_size[1]
        self.opacity = opacity

        fw("%!PS-Adobe-3.0 EPSF-3.0\n")
        fw("%%%%Creator: Blender %s\n" % bpy.app.version_string)
        fw("%%Pages: 1\n")
        fw("%%Orientation: Portrait\n")
        fw("%%%%BoundingBox: 0 0 %d %d\n" % (self.image_width, self.image_height))
        fw("%%%%HiResBoundingBox: 0.0 0.0 %.4f %.4f\n" %
           (self.image_width, self.image_height))
        fw("%%EndComments\n")
        fw("%%Page: 1 1\n")
        fw("0 0 translate\n")
        fw("1.0 1.0 scale\n")
        fw("0 0 0 setrgbcolor\n")
        fw("[] 0 setdash\n")
        fw("1 setlinewidth\n")
        fw("1 setlinejoin\n")
        fw("1 setlinecap\n")

    def build(self, mesh, face_iter_func):
        polys = mesh.polygons

        if self.opacity > 0.0:
            for i, mat in enumerate(mesh.materials if mesh.materials else [None]):
                self.fw("/DRAW_%d {" % i)
                self.fw("gsave\n")
                if mat:
                    color = tuple((1.0 - ((1.0 - c) * self.opacity))
                                  for c in mat.diffuse_color)
                else:
                    color = 1.0, 1.0, 1.0
                self.fw("%.3g %.3g %.3g setrgbcolor\n" % color)
                self.fw("fill\n")
                self.fw("grestore\n")
                self.fw("0 setgray\n")
                self.fw("} def\n")

            # fill
            for i, uvs in face_iter_func():
                self.fw("newpath\n")
                for j, uv in enumerate(uvs):
                    uv_scale = (uv[0] * self.image_width, uv[1] * self.image_height)
                    if j == 0:
                        self.fw("%.5f %.5f moveto\n" % uv_scale)
                    else:
                        self.fw("%.5f %.5f lineto\n" % uv_scale)

                self.fw("closepath\n")
                self.fw("DRAW_%d\n" % polys[i].material_index)

        # stroke only
        for i, uvs in face_iter_func():
            self.fw("newpath\n")
            for j, uv in enumerate(uvs):
                uv_scale = (uv[0] * self.image_width, uv[1] * self.image_height)
                if j == 0:
                    self.fw("%.5f %.5f moveto\n" % uv_scale)
                else:
                    self.fw("%.5f %.5f lineto\n" % uv_scale)

            self.fw("closepath\n")
            self.fw("stroke\n")

    def end(self):
        self.fw("showpage\n")
        self.fw("%%EOF\n")
