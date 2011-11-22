#  ***** BEGIN GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  The Original Code is: all of this file.
#
#  ***** END GPL LICENSE BLOCK *****
#
bl_info = {
    'name': 'Export: Adobe After Effects (.jsx)',
    'description': 'Export selected cameras, objects & bundles to Adobe After Effects CS3 and above',
    'author': 'Bartek Skorupa',
    'version': (0, 58),
    'blender': (2, 6, 0),
    'api': 42052,
    'location': 'File > Export > Adobe After Effects (.jsx)',
    'category': 'Import-Export',
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Import-Export/Adobe_After_Effects"
    }


from math import pi
import bpy
import datetime


# create list of static blender's data
def get_comp_data(context):
    scene = context.scene
    aspect_x = scene.render.pixel_aspect_x
    aspect_y = scene.render.pixel_aspect_y
    aspect = aspect_x / aspect_y
    fps = scene.render.fps

    return {
        'scn': scene,
        'width': scene.render.resolution_x,
        'height': scene.render.resolution_y,
        'aspect': aspect,
        'fps': fps,
        'start': scene.frame_start,
        'end': scene.frame_end,
        'duration': (scene.frame_end - scene.frame_start + 1.0) / fps,
        'curframe': scene.frame_current,
        }


# create managable list of selected objects
# (only selected objects will be analyzed and exported)
def get_selected(context, prefix):
    cameras = []  # list of selected cameras
    cams_names = []  # list of selected cameras' names (prevent from calling "ConvertName(ob)" function too many times)
    nulls = []  # list of all selected objects exept cameras (will be used to create nulls in AE)
    nulls_names = []  # list of above objects names (prevent from calling "ConvertName(ob)" function too many times)
    obs = context.selected_objects

    for ob in obs:
        if ob.type == 'CAMERA':
            cameras.append(ob)
            cams_names.append(convert_name(False, ob, prefix))
        else:
            nulls.append(ob)
            nulls_names.append(convert_name(False, ob, prefix))

    selection = {
        'cameras': cameras,
        'cams_names': cams_names,
        'nulls': nulls,
        'nulls_names': nulls_names,
        }

    return selection


# convert names of objects to avoid errors in AE. Add user specified prefix
def convert_name(is_comp, ob, prefix):
    if is_comp:
        ob_name = prefix + ob
        ob_name = ob_name.replace('"', "_")
    else:
        ob_name = prefix + "_" + ob.name

        if ob_name[0].isdigit():
            ob_name = "_" + ob_name
            
        ob_name = bpy.path.clean_name(ob_name)
        ob_name = ob_name.replace("-", "_")

    return ob_name


# get object's blender's location and rotation and return AE's Position and Rotation/Orientation
# this function will be called for every object for every frame
def convert_pos_rot_matrix(matrix, width, height, aspect, x_rot_correction=False):

    # get blender location for ob
    b_loc_x, b_loc_y, b_loc_z = matrix.to_translation()
    b_rot_x, b_rot_y, b_rot_z = matrix.to_euler()

    # get blender rotation for ob
    if x_rot_correction:
        b_rot_x = b_rot_x / pi * 180.0 - 90.0
    else:
        b_rot_x = b_rot_x / pi * 180.0
    b_rot_y = b_rot_y / pi * 180.0
    b_rot_z = b_rot_z / pi * 180.0

    # convert to AE Position and Rotation
    # Axes in AE are different. AE's X is blender's X, AE's Y is negative Blender's Z, AE's Z is Blender's Y
    x = (b_loc_x * 100.0) / aspect + width / 2.0  # calculate AE's X position
    y = (-b_loc_z * 100.0) + (height / 2.0)  # calculate AE's Y position
    z = b_loc_y * 100.0  # calculate AE's Z position
    rx = b_rot_x  # calculate AE's X rotation. Will become AE's RotationX property
    ry = -b_rot_z  # calculate AE's Y rotation. Will become AE's OrientationY property
    rz = b_rot_y  # calculate AE's Z rotation. Will become AE's OrentationZ property
    # Using AE's rotation combined with AE's orientation allows to compensate for different euler rotation order.

    return x, y, z, rx, ry, rz


def convert_pos_rot(obj, width, height, aspect, x_rot_correction=False):
    matrix = obj.matrix_world.copy()
    return convert_pos_rot_matrix(matrix, width, height, aspect, x_rot_correction)


# get camera's lens and convert to AE's "zoom" value in pixels
# this function will be called for every camera for every frame
#
#
# AE's lens is defined by "zoom" in pixels. Zoom determines focal angle or focal length.
#
# ZOOM VALUE CALCULATIONS:
#
# Given values:
#     - sensor width (camera.data.sensor_width)
#     - sensor height (camera.data.sensor_height)
#     - sensor fit (camera.data.sensor_fit)
#     - lens (blender's lens in mm)
#     - width (width of the composition/scene in pixels)
#     - height (height of the composition/scene in pixels)
#     - PAR (pixel aspect ratio)
#
# Calculations are made using sensor's size and scene/comp dimension (width or height).
# If camera.sensor_fit is set to 'AUTO' or 'HORIZONTAL' - sensor = camera.data.sensor_width, dimension = width.
# If camera.sensor_fit is set to 'VERTICAL' - sensor = camera.data.sensor_height, dimension = height
#
# zoom can be calculated using simple proportions.
#
#                             |
#                           / |
#                         /   |
#                       /     | d
#       s  |\         /       | i
#       e  |  \     /         | m
#       n  |    \ /           | e
#       s  |    / \           | n
#       o  |  /     \         | s
#       r  |/         \       | i
#                       \     | o
#          |     |        \   | n
#          |     |          \ |
#          |     |            |
#           lens |    zoom
#
#    zoom / dimension = lens / sensor   =>
#    zoom = lens * dimension / sensor
#
#    above is true if square pixels are used. If not - aspect compensation is needed, so final formula is:
#    zoom = lens * dimension / sensor * aspect
#
def convert_lens(camera, width, height, aspect):
    if hasattr(camera.data, "sensor_width"):  # Preserve compatibility with versions not supporting camera sensor.
        if camera.data.sensor_fit == 'VERTICAL':
            sensor = camera.data.sensor_height
            dimension = height
        else:
            sensor = camera.data.sensor_width
            dimension = width
    else:
        sensor = 32  # standard blender's sensor size
        dimension = width
    
    zoom = camera.data.lens * dimension / sensor * aspect

    return zoom


# jsx script for AE creation
def write_jsx_file(file, data, selection, export_bundles, comp_name, prefix):
    from mathutils import Matrix

    print("\n---------------------------\n- Export to After Effects -\n---------------------------")
    #store the current frame to restore it at the enf of export
    curframe = data['curframe']
    #create array which will contain all keyframes values
    js_data = {
        'times': '',
        'cameras': {},
        'objects': {},
        }

    # create camera structure
    for i, cam in enumerate(selection['cameras']):  # more than one camera can be selected
        name_ae = selection['cams_names'][i]
        js_data['cameras'][name_ae] = {
            'position': '',
            'pointOfInterest': '',
            'orientation': '',
            'rotationX': '',
            'zoom': '',
            }

    # create object structure
    for i, obj in enumerate(selection['nulls']):  # nulls representing blender's obs except cameras
        name_ae = selection['nulls_names'][i]
        js_data['objects'][name_ae] = {
            'position': '',
            'orientation': '',
            'rotationX': '',
            }

    # get all keyframes for each objects and store into dico
    for frame in range(data['start'], data['end'] + 1):
        print("working on frame: " + str(frame))
        data['scn'].frame_set(frame)

        #get time for this loop
        js_data['times'] += '%f ,' % ((frame - data['start']) / data['fps'])

        # keyframes for all cameras
        for i, cam in enumerate(selection['cameras']):
            #get cam name
            name_ae = selection['cams_names'][i]
            #convert cam position to AE space
            ae_pos_rot = convert_pos_rot(cam, data['width'], data['height'], data['aspect'], x_rot_correction=True)
            #convert Blender's cam zoom to AE's
            zoom = convert_lens(cam, data['width'], data['height'], data['aspect'])
            #store all the value into dico
            js_data['cameras'][name_ae]['position'] += '[%f,%f,%f],' % (ae_pos_rot[0], ae_pos_rot[1], ae_pos_rot[2])
            js_data['cameras'][name_ae]['pointOfInterest'] += '[%f,%f,%f],' % (ae_pos_rot[0], ae_pos_rot[1], ae_pos_rot[2])
            js_data['cameras'][name_ae]['orientation'] += '[%f,%f,%f],' % (0, ae_pos_rot[4], ae_pos_rot[5])
            js_data['cameras'][name_ae]['rotationX'] += '%f ,' % (ae_pos_rot[3])
            js_data['cameras'][name_ae]['zoom'] += '[%f],' % (zoom)

        #keyframes for all nulls
        for i, ob in enumerate(selection['nulls']):
            #get object name
            name_ae = selection['nulls_names'][i]
            #convert ob position to AE space
            ae_pos_rot = convert_pos_rot(ob, data['width'], data['height'], data['aspect'], x_rot_correction=False)
            #store all datas into dico
            js_data['objects'][name_ae]['position'] += '[%f,%f,%f],' % (ae_pos_rot[0], ae_pos_rot[1], ae_pos_rot[2])
            js_data['objects'][name_ae]['orientation'] += '[%f,%f,%f],' % (0, ae_pos_rot[4], ae_pos_rot[5])
            js_data['objects'][name_ae]['rotationX'] += '%f ,' % (ae_pos_rot[3])

    # ---- write JSX file
    jsx_file = open(file, 'w')

    # make the jsx executable in After Effects (enable double click on jsx)
    jsx_file.write('#target AfterEffects\n\n')
    jsx_file.write('/**************************************\n')
    jsx_file.write('Scene : %s\n' % data['scn'].name)
    jsx_file.write('Resolution : %i x %i\n' % (data['width'], data['height']))
    jsx_file.write('Duration : %f\n' % (data['duration']))
    jsx_file.write('FPS : %f\n' % (data['fps']))
    jsx_file.write('Date : %s\n' % datetime.datetime.now())
    jsx_file.write('Exported with io_export_after_effects.py\n')
    jsx_file.write('**************************************/\n\n\n\n')

    #wrap in function
    jsx_file.write("function compFromBlender(){\n")
    # create new comp
    jsx_file.write('\nvar compName = "%s";' % (comp_name))
    jsx_file.write('\nvar newComp = app.project.items.addComp(compName, %i, %i, %f, %f, %i);\n\n\n' %
                   (data['width'], data['height'], data['aspect'], data['duration'], data['fps']))

    # create cameras
    jsx_file.write('// **************  CAMERAS  **************\n\n\n')
    for i, cam in enumerate(js_data['cameras']):  # more than one camera can be selected
        name_ae = cam
        jsx_file.write('var %s = newComp.layers.addCamera("%s",[0,0]);\n' % (name_ae, name_ae))
        jsx_file.write('%s.property("position").setValuesAtTimes([%s],[%s]);\n' % (name_ae, js_data['times'], js_data['cameras'][cam]['position']))
        jsx_file.write('%s.property("pointOfInterest").setValuesAtTimes([%s],[%s]);\n' % (name_ae, js_data['times'], js_data['cameras'][cam]['pointOfInterest']))
        jsx_file.write('%s.property("orientation").setValuesAtTimes([%s],[%s]);\n' % (name_ae, js_data['times'], js_data['cameras'][cam]['orientation']))
        jsx_file.write('%s.property("rotationX").setValuesAtTimes([%s],[%s]);\n' % (name_ae, js_data['times'], js_data['cameras'][cam]['rotationX']))
        jsx_file.write('%s.property("rotationY").setValue(0);\n' % name_ae)
        jsx_file.write('%s.property("rotationZ").setValue(0);\n' % name_ae)
        jsx_file.write('%s.property("zoom").setValuesAtTimes([%s],[%s]);\n\n\n' % (name_ae, js_data['times'], js_data['cameras'][cam]['zoom']))

    # create objects
    jsx_file.write('// **************  OBJECTS  **************\n\n\n')
    for i, obj in enumerate(js_data['objects']):  # more than one camera can be selected
        name_ae = obj
        jsx_file.write('var %s = newComp.layers.addNull();\n' % (name_ae))
        jsx_file.write('%s.threeDLayer = true;\n' % name_ae)
        jsx_file.write('%s.source.name = "%s";\n' % (name_ae, name_ae))
        jsx_file.write('%s.property("position").setValuesAtTimes([%s],[%s]);\n' % (name_ae, js_data['times'], js_data['objects'][obj]['position']))
        jsx_file.write('%s.property("orientation").setValuesAtTimes([%s],[%s]);\n' % (name_ae, js_data['times'], js_data['objects'][obj]['orientation']))
        jsx_file.write('%s.property("rotationX").setValuesAtTimes([%s],[%s]);\n' % (name_ae, js_data['times'], js_data['objects'][obj]['rotationX']))
        jsx_file.write('%s.property("rotationY").setValue(0);\n' % name_ae)
        jsx_file.write('%s.property("rotationZ").setValue(0);\n\n\n' % name_ae)

    # create Bundles
    if export_bundles:

        jsx_file.write('// **************  BUNDLES (3d tracks)  **************\n\n\n')

        #Bundles are linked to MovieClip, so we have to find which MC is linked to our selected camera (if any?)
        mc = ''

        #go through each selected Cameras
        for cam in selection['cameras']:
            #go through each constrains of this camera
            for constrain in cam.constraints:
                #does the camera have a Camera Solver constrain
                if constrain.type == 'CAMERA_SOLVER':
                    #Which movie clip does it use ?
                    if constrain.use_active_clip:
                        mc = data['scn'].active_clip
                    else:
                        mc = constrain.clip

                    #go throuhg each tracking point
                    for track in mc.tracking.tracks:
                        #is this tracking point has a Bundles (does it's 3D position has been solved)
                        if track.has_bundle:
                            # bundle are in camera space, so transpose it to world space
                            matrix = Matrix.Translation(cam.matrix_basis * track.bundle)
                            #convert the position into AE space
                            ae_pos_rot = convert_pos_rot_matrix(matrix, data['width'], data['height'], data['aspect'], x_rot_correction=False)
                            #get the name of the tracker
                            name_ae = convert_name(False, track, prefix)
                            #write JS script for this Bundle
                            jsx_file.write('var %s = newComp.layers.addNull();\n' % name_ae)
                            jsx_file.write('%s.threeDLayer = true;\n' % name_ae)
                            jsx_file.write('%s.source.name = "%s";\n' % (name_ae, name_ae))
                            jsx_file.write('%s.property("position").setValue([%f,%f,%f]);\n\n\n' % (name_ae, ae_pos_rot[0], ae_pos_rot[1], ae_pos_rot[2]))

    jsx_file.write("}\n\n\n")
    jsx_file.write('app.beginUndoGroup("Import Blender animation data");\n')
    jsx_file.write('compFromBlender();\n')
    jsx_file.write('app.endUndoGroup();\n\n\n')
    jsx_file.close()

    data['scn'].frame_set(curframe)  # set current frame of animation in blender to state before export

##########################################
# DO IT
##########################################


def main(file, context, export_bundles, comp_name, prefix):
    data = get_comp_data(context)
    selection = get_selected(context, prefix)
    comp_name = convert_name(True, comp_name, "")
    write_jsx_file(file, data, selection, export_bundles, comp_name, prefix)
    print ("\nExport to After Effects Completed")
    return {'FINISHED'}

##########################################
# ExportJsx class register/unregister
##########################################

from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty


class ExportJsx(bpy.types.Operator, ExportHelper):
    '''Export selected cameras and objects animation to After Effects'''
    bl_idname = "export.jsx"
    bl_label = "Export to Adobe After Effects"
    filename_ext = ".jsx"
    filter_glob = StringProperty(default="*.jsx", options={'HIDDEN'})

    comp_name = StringProperty(
            name="Comp Name",
            description="Name of composition to be created in After Effects",
            default="BlendComp"
            )
    prefix = StringProperty(
            name="Layer's Prefix",
            description="Prefix to use before AE layer's name",
            #default="bl_"
            )
    export_bundles = BoolProperty(
            name="Export Bundles",
            description="Export 3D Tracking points of a selected camera",
            default=False,
            )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        return main(self.filepath, context, self.export_bundles, self.comp_name, self.prefix)


def menu_func(self, context):
    self.layout.operator(ExportJsx.bl_idname, text="Adobe After Effects (.jsx)")


def register():
    bpy.utils.register_class(ExportJsx)
    bpy.types.INFO_MT_file_export.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ExportJsx)
    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()
