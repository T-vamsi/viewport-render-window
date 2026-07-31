# Render Camera Window

A Blender 4.x addon that provides a dedicated rendered viewport with a single click. It automatically configures a clean render preview, making it easier to animate, light, and review scenes without repeatedly setting up a new viewport.

> **Status:** 🚧 Work in Progress

---

## Overview

Render Camera Window is designed to simplify the workflow of creating a dedicated render preview in Blender.

Instead of manually opening another viewport, switching to Rendered mode, entering Camera View, and hiding interface elements every time, the addon performs these steps automatically with a single click.

---

## Features

### Current

* Create a dedicated render viewport window.
* Automatically switch to **Rendered** shading.
* Use the active scene camera when available.
* Fall back to Perspective View when no camera exists.
* Automatically hide:

  * Toolbar
  * Sidebar
  * Navigation Gizmo
  * Viewport Gizmos
* Lightweight and built for Blender 4.x.

### Planned

* Viewport gizmo positioned near the Navigation Gizmo.
* Detect and reuse an existing render window.
* Automatic camera synchronization.
* Multi-monitor support.
* User preferences.
* Customizable viewport settings.
* Blender Extension support.

---

## Why This Addon?

Many Blender users repeatedly perform the same setup:

* Open a new window.
* Change it to a 3D Viewport.
* Switch to Rendered mode.
* Enter Camera View.
* Hide overlays and UI.

This addon automates that workflow into a single action.

---

## Installation

### Install as an Add-on

1. Download or clone this repository.
2. Open Blender.
3. Go to:

```text
Edit → Preferences → Add-ons → Install
```

4. Select the addon ZIP (or the addon folder if appropriate).
5. Enable **Render Camera Window**.

---

## Usage

1. Open any Blender project.
2. Click the addon button (or viewport gizmo once implemented).
3. A dedicated render window is created.

### If the scene has an active camera

* Camera View is enabled automatically.
* Rendered shading is activated.

### If the scene has no camera

* The render window still opens.
* The viewport remains in Perspective View.

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

* Blender 4.0 or newer
* Python (included with Blender)

---

## Contributing

Contributions are welcome.

If you discover a bug, have an idea for a new feature, or want to improve the code, feel free to open an issue or submit a pull request.

---

## License

This project is licensed under the **Apache License 2.0**. See the `LICENSE` file for details.

> **Note:** Blender addons interact with Blender's Python API. Before distributing the addon through Blender-specific platforms, ensure your chosen license aligns with Blender's licensing requirements.

---

## Author

**Vamsi Turaga**

If this project helps you, consider giving the repository a ⭐ to support its development.
