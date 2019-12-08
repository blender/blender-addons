# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# -----------------------------------------------------------------------
# Author: Alan Odom (Clockmender), Rune Morling (ermo) Copyright (c) 2019
# -----------------------------------------------------------------------
#
import bpy
from bpy.types import Operator
from math import pi
from mathutils import Quaternion
from .pdt_functions import euler_to_quaternion


class PDT_OT_ViewRot(Operator):
    """Rotate View using X Y Z Absolute Rotations."""

    bl_idname = "pdt.viewrot"
    bl_label = "Rotate View"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """View Rotation by Absolute Values.

        Rotations are converted to 3x3 Quaternion Rotation Matrix.
        This is an Absolute Rotation, not an Incremental Orbit.

        Args:
            context: Blender bpy.context instance.

        Notes:
            Uses pg.rotation_coords scene variables

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
        if len(areas) > 0:
            roll_value = euler_to_quaternion(
                pg.rotation_coords.x * pi / 180,
                pg.rotation_coords.y * pi / 180,
                pg.rotation_coords.z * pi / 180
            )
            areas[0].spaces.active.region_3d.view_rotation = roll_value
        return {"FINISHED"}


class PDT_OT_vRotL(Operator):
    """Orbit View to Left by Angle."""

    bl_idname = "pdt.viewleft"
    bl_label = "Rotate Left"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """View Orbit Left by Delta Value.

        Orbits view to the left about its vertical axis

        Args:
            context: Blender bpy.context instance.

        Notes:
            Uses pg.vrotangle scene variable

        Returns: Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
        if len(areas) > 0:
            bpy.ops.view3d.view_orbit(angle=(pg.vrotangle * pi / 180), type="ORBITLEFT")
        return {"FINISHED"}


class PDT_OT_vRotR(Operator):
    """Orbit View to Right by Angle."""

    bl_idname = "pdt.viewright"
    bl_label = "Rotate Right"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """View Orbit Right by Delta Value.

        Orbits view to the right about its vertical axis

        Args:
            context: Blender bpy.context instance.

        Notes:
            Uses pg.vrotangle scene variable

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
        if len(areas) > 0:
            bpy.ops.view3d.view_orbit(angle=(pg.vrotangle * pi / 180), type="ORBITRIGHT")
        return {"FINISHED"}


class PDT_OT_vRotU(Operator):
    """Orbit View to Up by Angle."""

    bl_idname = "pdt.viewup"
    bl_label = "Rotate Up"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """View Orbit Up by Delta Value.

        Orbits view up about its horizontal axis

        Args:
            context: Blender bpy.context instance.

        Notes:
            Uses pg.vrotangle scene variable

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
        if len(areas) > 0:
            bpy.ops.view3d.view_orbit(angle=(pg.vrotangle * pi / 180), type="ORBITUP")
        return {"FINISHED"}


class PDT_OT_vRotD(Operator):
    """Orbit View to Down by Angle."""

    bl_idname = "pdt.viewdown"
    bl_label = "Rotate Down"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """View Orbit Down by Delta Value.

        Orbits view down about its horizontal axis

        Args:
            context: Blender bpy.context instance.

        Notes:
            Uses pg.vrotangle scene variable

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
        if len(areas) > 0:
            bpy.ops.view3d.view_orbit(angle=(pg.vrotangle * pi / 180), type="ORBITDOWN")
        return {"FINISHED"}


class PDT_OT_vRoll(Operator):
    """Roll View by Angle."""

    bl_idname = "pdt.viewroll"
    bl_label = "Roll View"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """View Roll by Delta Value.

        Rolls view about its normal axis

        Args:
            context: Blender bpy.context instance.

        Notes:
            Uses pg.vrotangle scene variable

        Returns:
            Status Set.
        """

        scene = context.scene
        pg = scene.pdt_pg
        areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
        if len(areas) > 0:
            bpy.ops.view3d.view_roll(angle=(pg.vrotangle * pi / 180), type="ANGLE")
        return {"FINISHED"}


class PDT_OT_viso(Operator):
    """Isometric View."""

    bl_idname = "pdt.viewiso"
    bl_label = "Isometric View"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Set Isometric View.

        Set view orientation to Isometric

        Args:
            context: Blender bpy.context instance.

        Returns:
            Status Set.
        """

        areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
        if len(areas) > 0:
            # Try working this out in your head!
            areas[0].spaces.active.region_3d.view_rotation = Quaternion(
                (0.8205, 0.4247, -0.1759, -0.3399)
            )
        return {"FINISHED"}
