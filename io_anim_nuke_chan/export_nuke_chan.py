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

""" This script is an exporter to the nuke's .chan files.
It takes the currently active object and writes it's transformation data
into a text file with .chan extension."""

from mathutils import Matrix
from math import radians, degrees, atan2


def save_chan(context, filepath, y_up, rot_ord):

    # get the active scene and object
    scene = context.scene
    obj = context.active_object
    camera = obj.data if obj.type == 'CAMERA' else None

    # get the range of an animation
    f_start = scene.frame_start
    f_end = scene.frame_end

    # prepare the correcting matrix
    rot_mat = Matrix.Rotation(radians(-90.0), 4, 'X').to_4x4()

    filehandle = open(filepath, 'w')
    fw = filehandle.write

    # iterate the frames
    for frame in range(f_start, f_end, 1):

        # set the current frame
        scene.frame_set(frame)

        # get the objects world matrix
        mat = obj.matrix_world.copy()

        # if the setting is proper use the rotation matrix
        # to flip the Z and Y axis
        if y_up:
            mat = rot_mat * mat

        # create the first component of a new line, the frame number
        fw("%i\t" % frame)

        # create transform component
        t = mat.to_translation()
        fw("%f\t%f\t%f\t" % t[:])

        # create rotation component
        r = mat.to_euler(rot_ord)

        fw("%f\t%f\t%f\t" % (degrees(r[0]), degrees(r[1]), degrees(r[2])))

        # if we have a camera, add the focal length
        if camera:
            sensor_x = camera.sensor_width
            sensor_y = camera.sensor_height
            cam_lens = camera.lens

            # calculate the vertical field of view
            # we know the vertical size of (virtual) sensor, the focal length
            # of the camera so all we need to do is to feed this data to
            # atan2 function whitch returns the degree (in radians) of
            # an angle formed by a triangle with two legs of a given lengths
            vfov = degrees(atan2(sensor_y / 2, cam_lens)) * 2.0
            fw("%f" % vfov)

        fw("\n")

    # after the whole loop close the file
    filehandle.close()

    return {'FINISHED'}
