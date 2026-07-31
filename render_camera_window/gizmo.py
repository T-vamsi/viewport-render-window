"""
gizmo.py
========
A persistent GizmoGroup that draws a native-looking camera button in every
3D Viewport, docked under the Perspective/Orthographic overlay text by
default, or freely positioned if the user has dragged it (Alt + drag).
"""

import bpy
from bpy.types import GizmoGroup

from . import utils


class RENDERCAMWINDOW_GGT_button(GizmoGroup):
    """Persistent viewport button that opens the dedicated render window."""

    bl_idname = "RENDERCAMWINDOW_GGT_button"
    bl_label = "Render Camera Window Button"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SCALE'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.space_data is not None and context.space_data.type == 'VIEW_3D'

    def setup(self, context: bpy.types.Context) -> None:
        gz = self.gizmos.new("GIZMO_GT_button_2d")
        gz.icon = 'CAMERA_DATA'
        gz.draw_options = {'BACKDROP', 'OUTLINE'}
        gz.use_grab_cursor = False
        gz.use_draw_modal = False   # don't draw the "in-progress drag" style overlay
        gz.use_tooltip = True       # keep the tooltip, but this also avoids the
                                     # gizmo being treated as a continuously-draggable value

        theme = context.preferences.themes[0].view_3d
        gz.color = theme.header[:3] if hasattr(theme, "header") else (0.15, 0.15, 0.15)
        gz.alpha = 0.65
        gz.color_highlight = (0.35, 0.65, 1.0)
        gz.alpha_highlight = 0.9
        gz.scale_basis = 10.0

        gz.target_set_operator("render_camera_window.open_window")

        self._button = gz

    def refresh(self, context: bpy.types.Context) -> None:
        """Reposition the button: docked under the Perspective/Orthographic
        label by default, or at its dragged position if the user moved it.
        """
        region = context.region
        if region is None:
            return

        prefs = _get_prefs(context)
        ui_scale = context.preferences.system.ui_scale
        button_size = prefs.button_size * ui_scale
        radius = button_size / 2.0

        if prefs.use_custom_position:
            # Freely dragged position, stored normalized so it scales
            # correctly with window resizes.
            x = prefs.pos_x * region.width
            y = prefs.pos_y * region.height
        else:
            # Docked default: top-middle of the viewport, just below the
            # header — clear of both the Perspective/Orthographic label
            # (top-left) and the navigation gizmo (top-right), and it
            # re-centers automatically on resize since x is derived from
            # region.width every refresh rather than a fixed pixel value.
            top_padding = 40.0 * ui_scale  # clears the header bar
            x = region.width / 2.0
            y = region.height - top_padding

        self._button.matrix_basis = _translation_matrix(x, y)
        self._button.scale_basis = radius

        # Record where we put it so the drag operator can hit-test it.
        utils.set_button_screen_position(region, x, y, radius)

    def draw_prepare(self, context: bpy.types.Context) -> None:
        self.refresh(context)


def _translation_matrix(x: float, y: float):
    from mathutils import Matrix
    return Matrix.Translation((x, y, 0.0))


def _get_prefs(context: bpy.types.Context):
    return context.preferences.addons[__package__].preferences