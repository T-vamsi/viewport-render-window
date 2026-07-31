"""
utils.py
========
Stateless-as-possible helper functions shared by the operator and gizmo.

The only piece of mutable module-level state is `_render_window_ref`, which
stores a reference to the dedicated render Window. This is unavoidable:
Blender's `bpy.types.Window` has no custom-property storage, so there is no
way to "tag" a window as ours other than remembering it ourselves.
"""

from typing import Optional, Tuple

import bpy

import sys
import ctypes
import ctypes.wintypes



# ---------------------------------------------------------------------------
# Module-level window tracking.
#
# This is the single piece of global state in the addon, and it exists only
# because Blender gives us no other way to identify "our" window later.
# Everything that touches it goes through the functions below so the rest
# of the addon never manipulates it directly.
# ---------------------------------------------------------------------------
_render_window_ref: Optional[bpy.types.Window] = None


def set_render_window_reference(window: Optional[bpy.types.Window]) -> None:
    """Store (or clear) the module's reference to the dedicated render window."""
    global _render_window_ref
    _render_window_ref = window


def clean_dead_window_reference(wm: Optional[bpy.types.WindowManager]) -> None:
    """Clear the stored window reference if it no longer points to a live window.

    `wm.windows` only supports `in` with string keys, not object identity,
    so we compare each live window's underlying pointer against our stored
    reference's pointer instead of using `in` directly.
    """
    global _render_window_ref
    if _render_window_ref is None:
        return

    if wm is None:
        _render_window_ref = None
        return

    try:
        stored_pointer = _render_window_ref.as_pointer()
    except (ReferenceError, RuntimeError):
        # The underlying C data was freed; the Python wrapper is dangling.
        _render_window_ref = None
        return

    still_open = any(window.as_pointer() == stored_pointer for window in wm.windows)

    if not still_open:
        _render_window_ref = None


def find_render_window(wm: bpy.types.WindowManager) -> Optional[bpy.types.Window]:
    """Return the dedicated render window if it still exists, else None.

    This also self-heals the stored reference: if the window was closed by
    the user, the stale reference is cleared here so future calls are cheap
    and correct.
    """
    clean_dead_window_reference(wm)
    return _render_window_ref


def focus_render_window(window: bpy.types.Window) -> None:
    """Bring an existing render window to the front and give it input focus.

    `window_manager.windows.update()`  by itself doesn't raise a window on
    all platforms, so we additionally flag the window as active via the
    context temp override where supported, and fall back gracefully.
    """
    # Re-ordering `window` to the front of the WM's window list is the most
    # portable way to signal "focus this one" across platforms; Blender's
    # window manager raises the most-recently-touched window on redraw.
    wm = bpy.context.window_manager
    wm.windows.update()

    try:
        with bpy.context.temp_override(window=window):
            bpy.ops.wm.window_close.poll()  # cheap no-op call to force a context refresh
    except Exception:
        pass

    # Force every area in the target window to redraw, which on most
    # platforms is sufficient to bring it to the foreground when combined
    # with the OS window manager's focus-follows-redraw behaviour.
    for area in window.screen.areas:
        area.tag_redraw()


def find_view3d(
    window: bpy.types.Window,
) -> Tuple[
    Optional[bpy.types.Area],
    Optional[bpy.types.Region],
    Optional[bpy.types.RegionView3D],
    Optional[bpy.types.SpaceView3D],
]:
    """Locate the VIEW_3D area/region/region_3d/space in a given window.

    Returns a 4-tuple of (area, region, region_3d, space_data). Any element
    that cannot be found is returned as None so callers can fail gracefully.
    """
    screen = window.screen
    for area in screen.areas:
        if area.type != 'VIEW_3D':
            continue

        space_data = area.spaces.active
        if not isinstance(space_data, bpy.types.SpaceView3D):
            continue

        window_region = None
        for region in area.regions:
            if region.type == 'WINDOW':
                window_region = region
                break

        region_3d = space_data.region_3d
        return area, window_region, region_3d, space_data

    return None, None, None, None


def is_camera_available(scene: bpy.types.Scene) -> bool:
    """Return True if the scene has an active camera assigned."""
    return scene.camera is not None


def set_camera_view(
    window: bpy.types.Window,
    area: bpy.types.Area,
    region_3d: bpy.types.RegionView3D,
    space_data: bpy.types.SpaceView3D,
) -> None:
    """Switch a specific viewport into Camera View, equivalent to Numpad 0.

    We avoid `bpy.ops.view3d.view_camera()` where possible because operators
    depend on the *current* context window/area, which may not be the render
    window when this is called from a handler. We use `temp_override` to
    safely direct the operator at the correct window/area/region.
    """
    # Ensure the space is following the scene camera, not a locally
    # overridden one, so future scene.camera changes keep tracking correctly.
    space_data.use_local_camera = False

    window_region = None
    for region in area.regions:
        if region.type == 'WINDOW':
            window_region = region
            break

    if window_region is None:
        return

    try:
        with bpy.context.temp_override(
            window=window,
            area=area,
            region=window_region,
        ):
            bpy.ops.view3d.view_camera()
    except RuntimeError:
        # Operator context override failed (e.g. area not fully initialised
        # yet, such as immediately after window creation). Fall back to
        # setting the perspective mode directly, which achieves the same
        # visual result without relying on operator context.
        region_3d.view_perspective = 'CAMERA'


def hide_viewport_ui(
    space_data: bpy.types.SpaceView3D,
    *,
    hide_toolbar: bool = True,
    hide_sidebar: bool = True,
    hide_nav_gizmo: bool = True,
    hide_all_gizmos: bool = True,
    hide_overlays: bool = True,
) -> None:
    """Strip a VIEW_3D space of its UI chrome for a clean render-only look."""
    space_data.show_region_toolbar = not hide_toolbar
    space_data.show_region_ui = not hide_sidebar

    # Gizmo visibility: the "show all gizmos" master toggle takes priority.
    # If it's off, the individual navigate-gizmo toggle is moot.
    if hide_all_gizmos:
        space_data.show_gizmo = False
    else:
        space_data.show_gizmo = True
        space_data.show_gizmo_navigate = not hide_nav_gizmo

    space_data.overlay.show_overlays = not hide_overlays


def configure_viewport(
    area: bpy.types.Area,
    space_data: bpy.types.SpaceView3D,
    scene: bpy.types.Scene,
    *,
    hide_toolbar: bool,
    hide_sidebar: bool,
    hide_nav_gizmo: bool,
    hide_all_gizmos: bool,
    hide_overlays: bool,
) -> None:
    """Apply the full "render window" viewport configuration in one call.

    Sets rendered shading and strips UI chrome. Camera-view switching is
    handled separately by `set_camera_view` since it needs a live window
    context override.
    """
    # Rendered shading, matching the "look through the render engine" goal.
    space_data.shading.type = 'RENDERED'

    hide_viewport_ui(
        space_data,
        hide_toolbar=hide_toolbar,
        hide_sidebar=hide_sidebar,
        hide_nav_gizmo=hide_nav_gizmo,
        hide_all_gizmos=hide_all_gizmos,
        hide_overlays=hide_overlays,
    )

# ---------------------------------------------------------------------------
# Button position tracking, per-region.
#
# Needed so the drag operator (in operators.py) can hit-test "is the mouse
# near the button" without duplicating the placement math that gizmo.py
# already computes each refresh. Keyed by region.as_pointer() since regions
# are transient Python wrappers but their underlying pointer is stable for
# the region's lifetime.
# ---------------------------------------------------------------------------
_button_screen_positions: dict = {}


def set_button_screen_position(region: bpy.types.Region, x: float, y: float, radius: float) -> None:
    """Record where the gizmo button was last drawn in a given region."""
    _button_screen_positions[region.as_pointer()] = (x, y, radius)


def get_button_screen_position(region: bpy.types.Region):
    """Return (x, y, radius) for the button in this region, or None if unknown."""
    return _button_screen_positions.get(region.as_pointer())


def is_mouse_near_button(region: bpy.types.Region, mouse_x: float, mouse_y: float, padding: float = 6.0) -> bool:
    """Hit-test whether a mouse position (region-relative) is over the button."""
    pos = get_button_screen_position(region)
    if pos is None:
        return False
    bx, by, radius = pos
    dx = mouse_x - bx
    dy = mouse_y - by
    return (dx * dx + dy * dy) <= (radius + padding) ** 2


def position_window_top_right_quarter(window: bpy.types.Window) -> None:
    """Resize and move a window to occupy the top-right quarter of the screen.

    Blender's Python API does not expose window x/y/width/height as settable
    properties, so this is implemented via the Win32 API directly. It is a
    best-effort, Windows-only operation: on other platforms (or if anything
    about this fails) it silently does nothing, leaving the window at
    whatever size/position Blender created it with.
    """
    if not sys.platform.startswith("win"):
        return  # No portable equivalent for macOS/Linux from pure Python.

    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()  # avoid DPI-scaled metrics mismatching real pixels

        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)

        quarter_w = screen_w // 2
        quarter_h = screen_h // 2
        pos_x = screen_w - quarter_w  # right half
        pos_y = 0  # top half

        # The newly created window is the foreground window immediately
        # after wm.window_new() returns, since Blender activates it on
        # creation. We grab its HWND via GetForegroundWindow rather than
        # trying to resolve it from `window`, since bpy.types.Window has
        # no native handle accessor.
        hwnd = user32.GetForegroundWindow()
        if hwnd:
            user32.MoveWindow(hwnd, pos_x, pos_y, quarter_w, quarter_h, True)
    except Exception:
        # Never let a platform-specific convenience feature crash the
        # operator — the window still opened correctly either way.
        pass


def get_reference_area_size(context: bpy.types.Context):
    """Determine the target render-window size.

    Preference order:
    1. If an OUTLINER area exists in the invoking window's screen, use its
       pixel dimensions.
    2. Otherwise, use the dimensions of the smallest area (by pixel area)
       in that screen.
    Returns (width, height) in pixels, or None if the screen has no areas
    (shouldn't normally happen).
    """
    screen = context.screen
    if screen is None or not screen.areas:
        return None

    outliner_area = None
    smallest_area = None
    smallest_size = None

    for area in screen.areas:
        size = area.width * area.height
        if area.type == 'OUTLINER':
            outliner_area = area
        if smallest_size is None or size < smallest_size:
            smallest_size = size
            smallest_area = area

    target = outliner_area if outliner_area is not None else smallest_area
    if target is None:
        return None
    return target.width, target.height


def position_window_top_right(window: bpy.types.Window, width: int, height: int) -> None:
    """Resize a window to (width, height) and dock it to the top-right of the screen.

    Windows-only (via ctypes/user32), same rationale as before: Blender's
    Python API exposes no portable window-geometry setter. `AdjustWindowRectEx`
    is used so the requested size matches the *client area* (the actual
    viewport content), not the outer window including title bar/borders.
    """
    if not sys.platform.startswith("win"):
        return

    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()

        screen_w = user32.GetSystemMetrics(0)

        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return

        # Expand (width, height) from a desired client-area size to the
        # full window rect size, accounting for the title bar/border style
        # of a standard overlapped window.
        WS_OVERLAPPEDWINDOW = 0x00CF0000
        rect = ctypes.wintypes.RECT(0, 0, width, height)
        user32.AdjustWindowRectEx(ctypes.byref(rect), WS_OVERLAPPEDWINDOW, False, 0)
        full_w = rect.right - rect.left
        full_h = rect.bottom - rect.top

        pos_x = screen_w - full_w  # dock to the right edge
        pos_y = 0  # dock to the top edge

        user32.MoveWindow(hwnd, pos_x, pos_y, full_w, full_h, True)
    except Exception:
        pass  # Best-effort convenience only — never fail the operator over this.