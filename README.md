# Render Camera Window

A Blender 4.x addon that opens a dedicated rendered viewport window with a single click. The addon automatically uses the active scene camera when available, or falls back to the current perspective view if no camera exists, creating a clean and distraction-free render preview.

---

## Features

* One-click render viewport.
* Opens a dedicated Blender window.
* Automatically switches to **Rendered** viewport shading.
* Uses the active scene camera when available.
* Falls back to Perspective View if no camera exists.
* Hides unnecessary UI elements for a clean preview.
* Designed to feel like a native Blender tool.
* Lightweight and optimized for Blender 4.x.

---

## Planned Features

* Viewport Gizmo below the Navigation Gizmo.
* Prevent duplicate render windows.
* Focus an existing render window instead of creating a new one.
* Optional viewport preferences.
* Multi-monitor support.
* Automatic camera synchronization.
* Extension support for Blender 4.2+.

---

## Installation

### Method 1 – Install as an Add-on

1. Download or clone this repository.
2. Zip the addon folder (if required).
3. Open Blender.
4. Go to:

```text
Edit → Preferences → Add-ons → Install
```

5. Select the ZIP file.
6. Enable **Render Camera Window**.

---

## Usage

After installation:

1. Open any 3D Viewport.
2. Click the **Render Camera Window** button (or viewport gizmo when implemented).
3. A dedicated render window will open.

If the scene contains an active camera:

* The viewport switches to Camera View.
* Rendered shading is enabled automatically.

If no active camera exists:

* The viewport remains in Perspective View.
* Rendered shading is still enabled.

---

## How It Works

The addon:

* Creates a new Blender window.
* Finds a 3D Viewport.
* Configures it automatically.
* Enables Rendered shading.
* Hides unnecessary interface elements.
* Uses the active camera whenever possible.

This eliminates the repetitive process of manually creating a render preview viewport every time you work.

---

## Project Structure

```text
render_camera_window/
│
├── __init__.py
├── operators.py
├── gizmo.py
├── utils.py
├── preferences.py
└── blender_manifest.toml
```

---

## Requirements

* Blender 4.0+
* Python (bundled with Blender)

---

## Roadmap

* [ ] Viewport Gizmo
* [ ] Window Manager
* [ ] Camera Tracking
* [ ] Render Window Reuse
* [ ] Preferences
* [ ] Blender Extension Support
* [ ] Documentation
* [ ] Unit Testing

---

## Contributing

Contributions, feature requests, and bug reports are welcome.

If you have ideas for improving the addon, feel free to open an issue or submit a pull request.

---

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.
---

## Author

Developed by **Vamsi Turaga**.

If you find this project useful, consider giving it a ⭐ on GitHub to support its development.
