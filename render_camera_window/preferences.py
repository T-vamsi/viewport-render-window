"""
preferences.py
===============
Addon preferences: what UI chrome to hide, and how the gizmo button looks.
"""

import bpy


class RenderCameraWindowPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    hide_overlays: bpy.props.BoolProperty(
        name="Hide Overlays",
        description="Hide viewport overlays in the render window",
        default=True,
    )
    hide_toolbar: bpy.props.BoolProperty(
        name="Hide Toolbar",
        default=True,
    )
    hide_sidebar: bpy.props.BoolProperty(
        name="Hide Sidebar",
        default=True,
    )
    hide_nav_gizmo: bpy.props.BoolProperty(
        name="Hide Navigation Gizmo",
        default=True,
    )
    hide_all_gizmos: bpy.props.BoolProperty(
        name="Hide All Gizmos",
        description="Hide all viewport gizmos (including this addon's own button) in the render window",
        default=True,   # was False
    )

    button_size: bpy.props.FloatProperty(
        name="Button Size",
        default=24.0,
        min=12.0,
        max=64.0,
        subtype='PIXEL',
    )

    # --- Position ---------------------------------------------------------
    # The button now defaults to docking under the Perspective/Orthographic
    # overlay text (top-left), but can be freely dragged (Alt + Left-click
    # drag) anywhere in the viewport. Once dragged, `use_custom_position`
    # flips on and `pos_x` / `pos_y` (normalized 0-1 region-space, origin at
    # bottom-left, matching Blender's own region coordinate convention)
    # take over from the docked default.
    use_custom_position: bpy.props.BoolProperty(
        name="Custom Position",
        description="Use a freely-dragged position instead of the default docked position",
        default=False,
    )
    pos_x: bpy.props.FloatProperty(
        name="Position X",
        description="Normalized horizontal position (0 = left edge, 1 = right edge)",
        default=0.5,
        min=0.0,
        max=1.0,
    )
    pos_y: bpy.props.FloatProperty(
        name="Position Y",
        description="Normalized vertical position (0 = bottom edge, 1 = top edge)",
        default=0.95,
        min=0.0,
        max=1.0,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        col = layout.column(heading="Hide In Render Window")
        col.prop(self, "hide_toolbar")
        col.prop(self, "hide_sidebar")
        col.prop(self, "hide_nav_gizmo")
        col.prop(self, "hide_all_gizmos")
        col.prop(self, "hide_overlays")

        layout.separator()

        col = layout.column(heading="Gizmo Button")
        col.prop(self, "button_size")

        layout.separator()

        col = layout.column(heading="Button Position")
        col.prop(self, "use_custom_position")
        sub = col.column()
        sub.enabled = self.use_custom_position
        sub.prop(self, "pos_x")
        sub.prop(self, "pos_y")
        if self.use_custom_position:
            row = col.row()
            row.operator("render_camera_window.reset_button_position", icon='LOOP_BACK')