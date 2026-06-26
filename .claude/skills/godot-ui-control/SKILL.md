---
name: godot-ui-control
description: Godot 4.x UI with Control nodes — anchors, containers, sizing flags, themes, and NinePatchRect for scalable panels/buttons. Use when building menus/HUD/screens, laying out responsive UI, applying a theme, or rendering nine-slice panels and buttons from asset packs.
---

# Godot 4.x UI (Control nodes)

UI is built from **Control** nodes. Layout is driven by **anchors + containers**, not
manual pixel math. Game world uses Node2D/Node3D; UI lives under a `CanvasLayer` or a
`Control` root.

## Containers do the layout — prefer them over hand-placing
- `VBoxContainer` / `HBoxContainer` — stack children.
- `GridContainer`, `MarginContainer`, `CenterContainer`, `PanelContainer`.
- Children expand via **size flags**: `size_flags_horizontal = SIZE_EXPAND_FILL`.
- For a full-screen root, set anchors to Full Rect (anchor preset 15) or use
  `set_anchors_preset(Control.PRESET_FULL_RECT)`.

## NinePatchRect (nine-slice) — scalable panels/buttons without distortion
```gdscript
# In a .tscn: a NinePatchRect with texture = panel.png
# patch_margin_left/top/right/bottom define the non-stretched border (in px)
$Panel.patch_margin_left = 8
$Panel.patch_margin_top = 8
$Panel.patch_margin_right = 8
$Panel.patch_margin_bottom = 8
$Panel.axis_stretch_horizontal = NinePatchRect.AXIS_STRETCH_MODE_STRETCH
```
This is the correct way to use Kenney/Tiny-Swords panel art — never stretch a whole
texture into a box (that's what produced the white/black blobs in the old prototype).
For themed Buttons/Panels, set a `StyleBoxTexture` with the same margins instead.

## Theme
- Create a `Theme` resource; set default font, font sizes, and per-control StyleBoxes.
- Assign it on the UI root (`theme` property); children inherit it.
- Override per-node via theme overrides only when necessary.

## Pitfalls
- Don't set `position`/`size` on a child inside a container — the container overrides it.
- Use `custom_minimum_size` to enforce a minimum.
- Check contrast: text color vs panel background (a real bug in the prototype).

Docs: https://docs.godotengine.org/en/stable/tutorials/ui/index.html
