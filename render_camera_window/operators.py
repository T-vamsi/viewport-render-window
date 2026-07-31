"""
operators.py
============
The single user-facing operator: open (or focus) the dedicated render window.
"""

import bpy

from . import utils


class RENDERCAMWINDOW_OT_open_window(bpy.types.Operator):
    """Open a dedicated, clean render viewport window (or focus it if already open)"""

    bl_idname = "render_camera_window.open_window"
    bl_label = "Open Render Window"
    bl_description = "Open a dedicated render viewport window, or focus it if one is already open"
    bl_options = {'REGISTER'}

    def execute(self, context: bpy.types.Context) -> set:
        wm = context.window_manager

        # --- Step 1: if a render window already exists, just focus it. ---
        existing_window = utils.find_render_window(wm)
        if existing_window is not None:
            utils.focus_render_window(existing_window)
            return {'FINISHED'}

        # --- Step 2: no render window yet — create one. ---
        prefs = context.preferences.addons[__package__].preferences

        # `window_new` duplicates the current window's screen layout into a
        # new OS window. We use it because it's the officially supported way
        # to spawn a new Blender window from Python; there is no "create
        # blank window" operator.
        try:
            bpy.ops.wm.window_new()
        except RuntimeError as error:
            self.report({'ERROR'}, f"Could not create a new window: {error}")
            return {'CANCELLED'}

        new_window = wm.windows[-1]

        # Best-effort: size the new window to match the Outliner (if one
        # exists in the current screen) or the smallest area otherwise,
        # and dock it to the top-right of the screen. Windows-only.
        ref_size = utils.get_reference_area_size(context)
        if ref_size is not None:
            utils.position_window_top_right(new_window, ref_size[0], ref_size[1])

        # --- Step 3: find (or fail gracefully on) a VIEW_3D area in it. ---
        view3d_area, view3d_region, region_3d, space_data = utils.find_view3d(new_window)
        if view3d_area is None or space_data is None:
            self.report(
                {'ERROR'},
                "Render Camera Window: no 3D Viewport found in the new window. "
                "Closing it.",
            )
            self._close_window_safely(new_window)
            return {'CANCELLED'}

        # --- Step 4: make this new window a single-area VIEW_3D window. ---
        # Maximizing the area gives the "dedicated render viewport" feel
        # rather than leaving whatever multi-area layout was duplicated.
        try:
            with context.temp_override(window=new_window, area=view3d_area):
                if not view3d_area.spaces.active.show_gizmo:
                    pass  # no-op; kept for readability of intent below
                bpy.ops.screen.screen_full_area(use_hide_panels=False)
        except RuntimeError:
            # Non-fatal: if the layout can't be maximized (e.g. already a
            # single-area screen), we simply continue with what we have.
            pass

        # Re-resolve the VIEW_3D area/region after the layout change, since
        # `screen_full_area` can replace the underlying screen data-block.
        view3d_area, view3d_region, region_3d, space_data = utils.find_view3d(new_window)
        if view3d_area is None or space_data is None:
            self.report({'ERROR'}, "Render Camera Window: lost the 3D Viewport after layout change.")
            self._close_window_safely(new_window)
            return {'CANCELLED'}

        # --- Step 5: configure shading + hide UI chrome. ---
        utils.configure_viewport(
            view3d_area,
            space_data,
            context.scene,
            hide_toolbar=prefs.hide_toolbar,
            hide_sidebar=prefs.hide_sidebar,
            hide_nav_gizmo=prefs.hide_nav_gizmo,
            hide_all_gizmos=prefs.hide_all_gizmos,
            hide_overlays=prefs.hide_overlays,
        )

        # --- Step 6: camera logic. ---
        # If a scene camera exists, switch to Camera View (Numpad 0).
        # If not, we deliberately do nothing further — the viewport simply
        # stays in whatever perspective it inherited, and the addon's
        # depsgraph handler will switch it to Camera View automatically
        # once a camera is assigned later.
        if utils.is_camera_available(context.scene):
            utils.set_camera_view(new_window, view3d_area, region_3d, space_data)

        # --- Step 7: remember this window so future clicks focus it. ---
        utils.set_render_window_reference(new_window)

        for area in new_window.screen.areas:
            area.tag_redraw()

        return {'FINISHED'}

    @staticmethod
    def _close_window_safely(window: bpy.types.Window) -> None:
        """Attempt to close a window we failed to configure, without raising."""
        try:
            with bpy.context.temp_override(window=window):
                bpy.ops.wm.window_close()
        except RuntimeError:
            pass
class RENDERCAMWINDOW_OT_drag_button(bpy.types.Operator):
    """Drag the render-window gizmo button to a new position (Alt + drag)"""

    bl_idname = "render_camera_window.drag_button"
    bl_label = "Move Render Window Button"
    bl_options = {'INTERNAL'}

    _initial_mouse = None

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # Only claim the Alt+click if the mouse is actually over the button;
        # otherwise we return False so Blender's normal Alt-orbit/whatever
        # behaviour keeps working unobstructed.
        region = context.region
        if region is None or context.space_data is None or context.space_data.type != 'VIEW_3D':
            return False
        mouse_x = context.window.event.mouse_region_x if hasattr(context.window, "event") else None
        return True  # Fine-grained check happens in invoke(), see below.

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set:
        region = context.region
        mouse_x = event.mouse_region_x
        mouse_y = event.mouse_region_y

        if not utils.is_mouse_near_button(region, mouse_x, mouse_y):
            # Not actually on the button — let the event pass through so
            # normal Alt-based navigation (e.g. Alt-orbit) still works.
            return {'PASS_THROUGH'}

        prefs = context.preferences.addons[__package__].preferences
        prefs.use_custom_position = True

        self._region = region
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> set:
        prefs = context.preferences.addons[__package__].preferences
        region = context.region

        if event.type == 'MOUSEMOVE':
            prefs.pos_x = max(0.0, min(1.0, event.mouse_region_x / region.width))
            prefs.pos_y = max(0.0, min(1.0, event.mouse_region_y / region.height))
            region.tag_redraw()
            return {'RUNNING_MODAL'}

        if event.type in {'LEFTMOUSE', 'RET'} and event.value == 'RELEASE':
            region.tag_redraw()
            return {'FINISHED'}

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            # Cancel: leave the button at its current dragged spot rather
            # than trying to restore the old docked position, since we
            # didn't cache it — simplest predictable behaviour.
            region.tag_redraw()
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


class RENDERCAMWINDOW_OT_reset_button_position(bpy.types.Operator):
    """Reset the gizmo button back to its default docked position"""

    bl_idname = "render_camera_window.reset_button_position"
    bl_label = "Reset Button Position"
    bl_options = {'INTERNAL'}

    def execute(self, context: bpy.types.Context) -> set:
        prefs = context.preferences.addons[__package__].preferences
        prefs.use_custom_position = False
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}