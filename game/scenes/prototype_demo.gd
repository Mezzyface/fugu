extends Node2D

## Showcases the curated Kenney "Prototype Textures" graybox set under
## res://assets/prototype/ -- the documented fallback for any sprite/texture that
## does not yet exist in the real art packs (see docs/art_direction.md, #9).
##
## The source PNGs are a near-neutral light gray, so a multiply-style modulate
## reproduces the Wada Sanzo palette faithfully (same trick as terrain_demo.gd).
## The top row is left raw to show the untinted graybox; the lower rows tint each
## surface with a palette color to show how a placeholder reads in-theme.

const PROTO_DIR := "res://assets/prototype/"
const THUMB_PX := 140.0  # on-screen size of each 1024x1024 source texture

# Wada Sanzo combo 282 (docs/art_direction.md). WHITE leaves the graybox raw.
const EUGENIA_RED := Color("da525d")
const MAPLE := Color("c59f6b")
const COBALT_GREEN := Color("96d1aa")
const LILAC := Color("b984af")

# [file stem, caption, modulate] laid out left-to-right, top-to-bottom in a 3x3.
const SURFACES := [
	["wall", "wall (raw)", Color.WHITE],
	["door", "door (raw)", Color.WHITE],
	["window", "window (raw)", Color.WHITE],
	["grid", "grid", MAPLE],
	["checker", "checker", COBALT_GREEN],
	["grid_diagonal", "diagonal", LILAC],
	["stairs", "stairs", EUGENIA_RED],
	["grid_fine", "fine grid", COBALT_GREEN],
	["crosshair", "crosshair", LILAC],
]

const COLS := 3
const CELL_W := 384.0
const CELL_H := 185.0
const ORIGIN := Vector2(256.0, 195.0)

# The project theme colors text dark for light UI panels; this demo sits on a
# dark backdrop, so override to a light ink for legible captions (art_direction.md
# calls out keeping text high-contrast over its background).
const INK := Color("e6e8ea")


func _ready() -> void:
	_add_titles()
	_build_grid()


func _add_titles() -> void:
	var title := Label.new()
	title.theme_type_variation = &"TitleLabel"
	title.text = "Prototype Textures — graybox fallback"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.position = Vector2(0.0, 36.0)
	title.size = Vector2(1280.0, 50.0)
	title.add_theme_color_override("font_color", INK)
	add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Placeholder for any missing sprite/texture. Tint via modulate (Wada Sanzo 282)."
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle.position = Vector2(0.0, 96.0)
	subtitle.size = Vector2(1280.0, 30.0)
	subtitle.add_theme_color_override("font_color", INK)
	add_child(subtitle)


func _build_grid() -> void:
	for i in SURFACES.size():
		var entry: Array = SURFACES[i]
		var cell := Vector2i(i % COLS, i / COLS)
		var center := ORIGIN + Vector2(cell.x * CELL_W, cell.y * CELL_H)
		_add_surface(entry[0], entry[1], entry[2], center)


func _add_surface(stem: String, caption: String, mod: Color, center: Vector2) -> void:
	var tex := _load_texture(stem)
	if tex == null:
		return
	var spr := Sprite2D.new()
	spr.texture = tex
	spr.centered = true
	spr.modulate = mod
	spr.scale = Vector2.ONE * (THUMB_PX / float(tex.get_width()))
	spr.position = center
	add_child(spr)

	var label := Label.new()
	label.text = caption
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.position = center + Vector2(-100.0, THUMB_PX * 0.5 + 8.0)
	label.size = Vector2(200.0, 28.0)
	label.add_theme_color_override("font_color", INK)
	add_child(label)


func _load_texture(stem: String) -> Texture2D:
	var path := "%s%s.png" % [PROTO_DIR, stem]
	if not ResourceLoader.exists(path):
		push_warning("prototype_demo: missing texture %s" % path)
		return null
	return load(path) as Texture2D
