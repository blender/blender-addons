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
    'description': 'Export cameras, selected objects & camera solution 3D Markers to Adobe After Effects CS3 and above',
    'author': 'Bartek Skorupa',
    'version': (0, 6, 0),
    'blender': (2, 6, 1),
    'location': 'File > Export > Adobe After Effects (.jsx)',
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Import-Export/Adobe_After_Effects",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=29858",
    'category': 'Import-Export',
    }


import bpy
import datetime
from math import pi
from mathutils import Matrix


# create list of static blender's data
def get_comp_data(context):
    scene = context.scene
    aspect_x = scene.render.pixel_aspect_x
    aspect_y = scene.render.pixel_aspect_y
    aspect = aspect_x / aspect_y
    start = scene.frame_start
    end = scene.frame_end
    active_cam_frames = get_active_cam_for_each_frame(scene, start, end)
    fps = scene.render.fps

    return {
        'scn': scene,
        'width': scene.render.resolution_x,
        'height': scene.render.resolution_y,
        'aspect': aspect,
        'fps': fps,
        'start': start,
        'end': end,
        'duration': (end - start + 1.0) / fps,
        'active_cam_frames': active_cam_frames,
        'curframe': scene.frame_current,
        }

# create list of active camera for each frame in case active camera is set by markers
def get_active_cam_for_each_frame(scene, start, end):
    active_cam_frames = []
    sorted_markers = []
    markers = scene.timeline_markers
    if markers:
        for marker in markers:
            if marker.camera:
                sorted_markers.append([marker.frame, marker])
        sorted_markers = sorted(sorted_markers)
        
        for i, marker in enumerate (sorted_markers):
            cam = marker[1].camera
            if i is 0 and marker[0] > start:
                start_range = start
            else:
                start_range = sorted_markers[i][0]
            if len(sorted_markers) > i + 1:
                end_range = sorted_markers[i+1][0] - 1
            else:
                end_range = end
            for i in range(start_range, end_range + 1):
                active_cam_frames.append(cam)
    if not active_cam_frames:
        if scene.camera:
            # in this case active_cam_frames array will have legth of 1. This will indicate that there is only one active cam in all frames
            active_cam_frames.append(scene.camera)

    return(active_cam_frames)    

# create managable list of selected objects
def get_selected(context):
    cameras = []  # list of selected cameras
    solids = []  # list of all selected meshes that can be exported as AE's solids
    lights = []  # list of all selected lamps that can be exported as AE's lights
    nulls = []  # list of all selected objects exept cameras (will be used to create nulls in AE)
    obs = context.selected_objects

    for ob in obs:
        if ob.type == 'CAMERA':
            cameras.append([ob, convert_name(ob.name)])

        elif is_plane(ob):
            # not ready yet. is_plane(object) returns False in all cases. This is temporary
            solids.append([ob, convert_name(ob.name)])
            
        elif ob.type == 'LAMP':
            # not ready yet. Lamps will be exported as nulls. This is temporary
            nulls.append([ob, convert_name(ob.name)])

        else:
            nulls.append([ob, convert_name(ob.name)])

    selection = {
        'cameras': cameras,
        'solids': solids,
        'lights': lights,
        'nulls': nulls,
        }

    return selection

# check if object is plane and can be exported as AE's solid
def is_plane(object):
    # work in progress. Not ready yet
    return False

# convert names of objects to avoid errors in AE.
def convert_name(name):
    name = "_" + name

    if name[0].isdigit():
        name = "_" + name
        
    name = bpy.path.clean_name(name)
    name = name.replace("-", "_")

    return name


# get object's blender's location rotation and scale and return AE's Position, Rotation/Orientation and scale
# this function will be called for every object for every frame
def convert_transform_matrix(matrix, width, height, aspect, x_rot_correction=False):

    # get blender location for ob
    b_loc_x, b_loc_y, b_loc_z = matrix.to_translation()
    b_rot_x, b_rot_y, b_rot_z = matrix.to_euler()
    b_scale_x, b_scale_y, b_scale_z = matrix.to_scale()

    # get blender rotation for ob
    if x_rot_correction:
        b_rot_x = b_rot_x / pi * 180.0 - 90.0
    else:
        b_rot_x = b_rot_x / pi * 180.0
    b_rot_y = b_rot_y / pi * 180.0
    b_rot_z = b_rot_z / pi * 180.0

    # convert to AE Position Rotation and Scale
    # Axes in AE are different. AE's X is blender's X, AE's Y is negative Blender's Z, AE's Z is Blender's Y
    x = (b_loc_x * 100.0) / aspect + width / 2.0  # calculate AE's X position
    y = (-b_loc_z * 100.0) + (height / 2.0)  # calculate AE's Y position
    z = b_loc_y * 100.0  # calculate AE's Z position
    # Using AE's rotation combined with AE's orientation allows to compensate for different euler rotation order.
    rx = b_rot_x  # calculate AE's X rotation. Will become AE's RotationX property
    ry = -b_rot_z  # calculate AE's Y rotation. Will become AE's OrientationY property
    rz = b_rot_y  # calculate AE's Z rotation. Will become AE's OrentationZ property
    sx = b_scale_x * 100.0  # scale of 1.0 is 100% in AE
    sy = b_scale_z * 100.0  # scale of 1.0 is 100% in AE
    sz = b_scale_y * 100.0  # scale of 1.0 is 100% in AE

    return x, y, z, rx, ry, rz, sx, sy, sz

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
    if camera.data.sensor_fit == 'VERTICAL':
        sensor = camera.data.sensor_height
        dimension = height
    else:
        sensor = camera.data.sensor_width
        dimension = width
    
    zoom = camera.data.lens * dimension / sensor * aspect

    return zoom

# convert object bundle's matrix. Not ready yet. Temporarily not active
#def get_ob_bundle_matrix_world(cam_matrix_world, bundle_matrix):
#    matrix = cam_matrix_basis
#    return matrix


# jsx script for AE creation
def write_jsx_file(file, data, selection, include_active_cam, include_selected_cams, include_selected_objects, include_cam_bundles, include_rotation, include_scale):

    print("\n---------------------------\n- Export to After Effects -\n---------------------------")
    #store the current frame to restore it at the enf of export
    curframe = data['curframe']
    #create array which will contain all keyframes values
    js_data = {
        'times': '',
        'cameras': {},
        'solids': {},
        'lights': {},
        'nulls': {},
        'bundles_cam': {},
        'bundles_ob': {},  # not ready yet
        }

    # create structure for active camera/cameras
    active_cam_name = ''
    if include_active_cam and data['active_cam_frames'] != []:
        # check if more that one active cam exist (true if active cams set by markers)
        if len(data['active_cam_frames']) is 1:
            name_ae = convert_name(data['active_cam_frames'][0].name)  # take name of the only active camera in scene
        else:
            name_ae = 'Active_Camera'
        active_cam_name = name_ae  # store name to be used when creating keyframes for active cam.
        js_data['cameras'][name_ae] = {
            'position': '',
            'pointOfInterest': '',
            'orientation': '',
            'rotationX': '',
            'zoom': '',
            }

    # create camera structure for selected cameras
    if include_selected_cams:
        for i, cam in enumerate(selection['cameras']):  # more than one camera can be selected
            if cam[1] != active_cam_name:
                name_ae = selection['cameras'][i][1]
                js_data['cameras'][name_ae] = {
                    'position': '',
                    'pointOfInterest': '',
                    'orientation': '',
                    'rotationX': '',
                    'zoom': '',
                    }
    
    # create structure for solids. Not ready yet. Temporarily not active
#    for i, obj in enumerate(selection['solids']):
#        name_ae = selection['solids'][i][1]
#        js_data['solids'][name_ae] = {
#            'position': '',
#            'orientation': '',
#            'rotationX': '',
#            'scale': '',
#            }

    # create structure for lights. Not ready yet. Temporarily not active
#    for i, obj in enumerate(selection['lights']):
#        name_ae = selection['lights'][i][1]
#        js_data['nulls'][name_ae] = {
#            'position': '',
#            'orientation': '',
#            'rotationX': '',
#            'scale': '',
#            }

    
    # create structure for nulls
    for i, obj in enumerate(selection['nulls']):  # nulls representing blender's obs except cameras, lamps and solids
        if include_selected_objects:
            name_ae = selection['nulls'][i][1]
            js_data['nulls'][name_ae] = {
                'position': '',
                'orientation': '',
                'rotationX': '',
                'scale': '',
                }

    # create structure for cam bundles including positions (cam bundles don't move)
    if include_cam_bundles:
        # go through each selected Camera and active cameras
        selected_cams = []
        active_cams = []
        if include_active_cam:
            active_cams = data['active_cam_frames']
        if include_selected_cams:
            for cam in selection['cameras']:
                selected_cams.append(cam[0])
        # list of cameras that will be checked for 'CAMERA SOLVER'
        cams = list(set.union(set(selected_cams), set(active_cams)))

        for cam in cams:
            # go through each constraints of this camera
            for constraint in cam.constraints:
                # does the camera have a Camera Solver constraint
                if constraint.type == 'CAMERA_SOLVER':
                    # Which movie clip does it use ?
                    if constraint.use_active_clip:
                        clip = data['scn'].active_clip
                    else:
                        clip = constraint.clip

                    # go through each tracking point
                    for track in clip.tracking.tracks:
                        # Does this tracking point have a bundle (has its 3D position been solved)
                        if track.has_bundle:
                            # get the name of the tracker
                            name_ae = convert_name(str(cam.name) + '__' + str(track.name))
                            js_data['bundles_cam'][name_ae] = {
                                'position': '',
                                }
                            # bundles are in camera space. Transpose to world space
                            matrix = Matrix.Translation(cam.matrix_basis.copy() * track.bundle)
                            # convert the position into AE space
                            ae_transform = convert_transform_matrix(matrix, data['width'], data['height'], data['aspect'], x_rot_correction=False)
                            js_data['bundles_cam'][name_ae]['position'] += '[%f,%f,%f],' % (ae_transform[0], ae_transform[1], ae_transform[2])                            


    # get all keyframes for each object and store in dico
    for frame in range(data['start'], data['end'] + 1):
        print("working on frame: " + str(frame))
        data['scn'].frame_set(frame)

        # get time for this loop
        js_data['times'] += '%f ,' % ((frame - data['start']) / data['fps'])

        # keyframes for active camera/cameras
        if include_active_cam and data['active_cam_frames'] != []:
            if len(data['active_cam_frames']) == 1:
                cur_cam_index = 0
            else:
                cur_cam_index = frame - data['start']
            active_cam = data['active_cam_frames'][cur_cam_index]
            # get cam name
            name_ae = active_cam_name
            # convert cam transform properties to AE space
            ae_transform = convert_transform_matrix(active_cam.matrix_world.copy(), data['width'], data['height'], data['aspect'], x_rot_correction=True)
            # convert Blender's lens to AE's zoom in pixels
            zoom = convert_lens(active_cam, data['width'], data['height'], data['aspect'])
            # store all values in dico
            js_data['cameras'][name_ae]['position'] += '[%f,%f,%f],' % (ae_transform[0], ae_transform[1], ae_transform[2])
            js_data['cameras'][name_ae]['pointOfInterest'] += '[%f,%f,%f],' % (ae_transform[0], ae_transform[1], ae_transform[2])
            js_data['cameras'][name_ae]['orientation'] += '[%f,%f,%f],' % (0, ae_transform[4], ae_transform[5])
            js_data['cameras'][name_ae]['rotationX'] += '%f ,' % (ae_transform[3])
            js_data['cameras'][name_ae]['zoom'] += '[%f],' % (zoom)

        # keyframes for selected cameras
        if include_selected_cams:
            for i, cam in enumerate(selection['cameras']):
                if cam[1] != active_cam_name:
                    # get cam name
                    name_ae = selection['cameras'][i][1]
                    # convert cam transform properties to AE space
                    ae_transform = convert_transform_matrix(cam[0].matrix_world.copy(), data['width'], data['height'], data['aspect'], x_rot_correction=True)
                    # convert Blender's lens to AE's zoom in pixels
                    zoom = convert_lens(cam[0], data['width'], data['height'], data['aspect'])
                    # store all values in dico
                    js_data['cameras'][name_ae]['position'] += '[%f,%f,%f],' % (ae_transform[0], ae_transform[1], ae_transform[2])
                    js_data['cameras'][name_ae]['pointOfInterest'] += '[%f,%f,%f],' % (ae_transform[0], ae_transform[1], ae_transform[2])
                    js_data['cameras'][name_ae]['orientation'] += '[%f,%f,%f],' % (0, ae_transform[4], ae_transform[5])
                    js_data['cameras'][name_ae]['rotationX'] += '%f ,' % (ae_transform[3])
                    js_data['cameras'][name_ae]['zoom'] += '[%f],' % (zoom)
    
    
        # keyframes for all solids. Not ready yet. Temporarily not active
#        for i, ob in enumerate(selection['solids']):
#            #get object name
#            name_ae = selection['solids'][i][1]
#            #convert ob position to AE space


        # keyframes for all lights. Not ready yet. Temporarily not active
#        for i, ob in enumerate(selection['lights']):
#            #get object name
#            name_ae = selection['lights'][i][1]
#            #convert ob position to AE space


        # keyframes for all nulls
        if include_selected_objects:
            for i, ob in enumerate(selection['nulls']):
                # get object name
                name_ae = selection['nulls'][i][1]
                # convert ob transform properties to AE space
                ae_transform = convert_transform_matrix(ob[0].matrix_world.copy(), data['width'], data['height'], data['aspect'], x_rot_correction=False)
                # store all values in dico
                js_data['nulls'][name_ae]['position'] += '[%f,%f,%f],' % (ae_transform[0], ae_transform[1], ae_transform[2])
                if include_rotation:
                    js_data['nulls'][name_ae]['orientation'] += '[%f,%f,%f],' % (0, ae_transform[4], ae_transform[5])
                    js_data['nulls'][name_ae]['rotationX'] += '%f ,' % (ae_transform[3])
                if include_scale:
                    js_data['nulls'][name_ae]['scale'] += '[%f,%f,%f],' % (ae_transform[6], ae_transform[7], ae_transform[8])

        # keyframes for all object bundles. Not ready yet.
        #
        #
        #

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

    # wrap in function
    jsx_file.write("function compFromBlender(){\n")
    # create new comp
    jsx_file.write('\nvar compName = prompt("Blender Comp\'s Name \\nEnter Name of newly created Composition","BlendComp","Composition\'s Name");')
    jsx_file.write('if (compName){')
    jsx_file.write('\nvar newComp = app.project.items.addComp(compName, %i, %i, %f, %f, %i);\n\n\n' %
                   (data['width'], data['height'], data['aspect'], data['duration'], data['fps']))

    # create camera bundles (nulls)
    jsx_file.write('// **************  CAMERA 3D MARKERS  **************\n\n\n')
    for i, obj in enumerate(js_data['bundles_cam']):
        name_ae = obj
        jsx_file.write('var %s = newComp.layers.addNull();\n' % (name_ae))
        jsx_file.write('%s.threeDLayer = true;\n' % name_ae)
        jsx_file.write('%s.source.name = "%s";\n' % (name_ae, name_ae))
        jsx_file.write('%s.property("position").setValue(%s);\n\n\n' % (name_ae, js_data['bundles_cam'][obj]['position']))
    
    # create object bundles (not ready yet)

    # create objects (nulls)
    jsx_file.write('// **************  OBJECTS  **************\n\n\n')
    for i, obj in enumerate(js_data['nulls']):
        name_ae = obj
        jsx_file.write('var %s = newComp.layers.addNull();\n' % (name_ae))
        jsx_file.write('%s.threeDLayer = true;\n' % name_ae)
        jsx_file.write('%s.source.name = "%s";\n' % (name_ae, name_ae))
        jsx_file.write('%s.property("position").setValuesAtTimes([%s],[%s]);\n' % (name_ae, js_data['times'], js_data['nulls'][obj]['position']))
        if include_rotation:
            jsx_file.write('%s.property("orientation").setValuesAtTimes([%s],[%s]);\n' % (name_ae, js_data['times'], js_data['nulls'][obj]['orientation']))
            jsx_file.write('%s.property("rotationX").setValuesAtTimes([%s],[%s]);\n' % (name_ae, js_data['times'], js_data['nulls'][obj]['rotationX']))
            jsx_file.write('%s.property("rotationY").setValue(0);\n' % name_ae)
            jsx_file.write('%s.property("rotationZ").setValue(0);\n\n\n' % name_ae)
        if include_scale:
            jsx_file.write('%s.property("scale").setValuesAtTimes([%s],[%s]);\n\n\n' % (name_ae, js_data['times'], js_data['nulls'][obj]['scale']))

    # create solids (not ready yet)

    # create lights (not ready yet)

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

    jsx_file.write('\n}else{alert ("Exit Import Blender animation data \\nNo Comp\'s name has been chosen","EXIT")};')
    jsx_file.write("}\n\n\n")
    jsx_file.write('app.beginUndoGroup("Import Blender animation data");\n')
    jsx_file.write('compFromBlender();\n')
    jsx_file.write('app.endUndoGroup();\n\n\n')
    jsx_file.close()

    data['scn'].frame_set(curframe)  # set current frame of animation in blender to state before export

##########################################
# DO IT
##########################################


def main(file, context, include_active_cam, include_selected_cams, include_selected_objects, include_cam_bundles, include_rotation, include_scale):
    data = get_comp_data(context)
    selection = get_selected(context)
    write_jsx_file(file, data, selection, include_active_cam, include_selected_cams, include_selected_objects, include_cam_bundles, include_rotation, include_scale)
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
    
    include_active_cam = BoolProperty(
            name = "Active Camera",
            description = "Include Active Camera Data",
            default = True,
            )
    include_selected_cams = BoolProperty(
            name = "Selected Cameras",
            description = "Add Selected Cameras Data",
            default = True,
            )
    include_selected_objects = BoolProperty(
            name = "Selected Objects",
            description = "Add Selected Objects Data",
            default = True,
            )
    include_rotation = BoolProperty(
            name = "Rotation",
            description  ="Include rotation of selected objects",
            default = True,
            )
    include_scale = BoolProperty(
            name = "Scale",
            description = "Include scale of selected object",
            default = True,
            )
    include_cam_bundles = BoolProperty(
            name = "Camera 3D Markers",
            description = "Include 3D Markers of Camera Motion Solution for selected cameras",
            default = True,
            )
#    include_ob_bundles = BoolProperty(
#            name = "Objects 3D Markers",
#            description = "Include 3D Markers of Object Motion Solution for selected cameras",
#            default = True,
#            )

    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label('Include Cameras and Objects:')
        box.prop(self, 'include_active_cam')
        box.prop(self, 'include_selected_cams')
        box.prop(self, 'include_selected_objects')
        box.label("Include Objects' Properties:")
        box.prop(self, 'include_rotation')
        box.prop(self, 'include_scale')
        box.label("Include Tracking Data:")
        box.prop(self, 'include_cam_bundles')
#        box.prop(self, 'include_ob_bundles')

    @classmethod
    def poll(cls, context):
        active = context.active_object
        selected = context.selected_objects
        camera = context.scene.camera
        ok = selected or camera
        return ok

    def execute(self, context):
        return main(self.filepath, context, self.include_active_cam, self.include_selected_cams, self.include_selected_objects, self.include_cam_bundles, self.include_rotation, self.include_scale)


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