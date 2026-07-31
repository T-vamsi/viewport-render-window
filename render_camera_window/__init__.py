import bpy

from . import utils
from . import operators
from . import gizmo
from . import preferences


def _on_depsgraph_update_post(scene, depsgraph):
    wm = bpy.context.window_manager
    render_window = utils.find_render_window(wm)
    if render_window is None:
        return
    if scene.camera is None:
        return
    view3d_area, view3d_region, region_3d, space_data = utils.find_view3d(render_window)
    if view3d_area is None or region_3d is None:
        return
    if region_3d.view_perspective != 'CAMERA':
        utils.set_camera_view(render_window, view3d_area, region_3d, space_data)


_CLASSES = (
    preferences.RenderCameraWindowPreferences,
    operators.RENDERCAMWINDOW_OT_open_window,
    operators.RENDERCAMWINDOW_OT_drag_button,
    operators.RENDERCAMWINDOW_OT_reset_button_position,
    gizmo.RENDERCAMWINDOW_GGT_button,
)

_addon_keymaps = []


def register() -> None:
    for cls in _CLASSES:
        bpy.utils.register_class(cls)

    if _on_depsgraph_update_post not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update_post)

    # Keymap: Alt + Left-click in the 3D Viewport tries to grab the button.
    # The operator's own invoke() immediately PASS_THROUGHs if the click
    # wasn't actually on the button, so normal Alt-navigation is untouched.
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')
        kmi = km.keymap_items.new(
            operators.RENDERCAMWINDOW_OT_drag_button.bl_idname,
            type='LEFTMOUSE',
            value='PRESS',
            alt=True,
        )
        _addon_keymaps.append((km, kmi))


def unregister() -> None:
    for km, kmi in _addon_keymaps:
        km.keymap_items.remove(kmi)
    _addon_keymaps.clear()

    if _on_depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update_post)

    utils.clean_dead_window_reference(bpy.context.window_manager if bpy.context else None)

    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)