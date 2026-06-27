extends Node2D

## Assembles a small patch of isometric terrain from the curated Kenney
## "Isometric Miniature" tiles under res://assets/terrain/.
##
## Tile geometry: every tile is 256x512 px with a 256x128 diamond footprint
## bottom-anchored to the image. One grid step therefore shifts a (centered)
## sprite by half a diamond: HALF_W horizontally and HALF_H vertically.
##
## Drawing is back-to-front (by row + col). A full floor tile is laid in every
## cell first, then any raised/special feature for that cell is drawn on top --
## so short tiles (stairs, half blocks, slabs) never reveal the background
## underneath them.

const TILES_DIR := "res://assets/terrain/"
const GRID := 7
const HALF_W := 128.0
const HALF_H := 64.0

# Wada Sanzo combo 282 (see docs/art_direction.md). The flat floor tiles ship a
# near-white beige, so multiply-modulation reproduces these hues faithfully.
const MAPLE := Color("c59f6b")  # base ground
const COBALT_GREEN := Color("96d1aa")  # accent ground tile
const EUGENIA_RED := Color("da525d")  # accent ground tile
const LILAC := Color("b984af")  # accent ground tile

# Cell -> modulate for the ground layer (every cell gets a floor tile).
var _ground := {}
# Cell -> [base_name, facing] for raised / special features drawn on top. These
# keep a warm Maple tint so the whole built structure reads as one earthy mass.
var _features := {}


func _ready() -> void:
	_build_layout()
	_assemble()
	_frame_camera()


func _build_layout() -> void:
	for row in range(GRID):
		for col in range(GRID):
			_ground[Vector2i(col, row)] = MAPLE

	# Palette accent tiles scattered across the flat ground (think objective
	# markers on the world map -- see docs/wireframes.md).
	_ground[Vector2i(1, 1)] = COBALT_GREEN
	_ground[Vector2i(5, 1)] = LILAC
	_ground[Vector2i(1, 5)] = LILAC
	_ground[Vector2i(0, 6)] = EUGENIA_RED
	_ground[Vector2i(6, 0)] = EUGENIA_RED
	_ground[Vector2i(5, 5)] = COBALT_GREEN

	# A small raised plateau (2x2 full blocks) with a stair leading up to it and
	# a half-step + slope giving the height variation some shape.
	_features[Vector2i(3, 2)] = ["block", "N"]
	_features[Vector2i(4, 2)] = ["block", "N"]
	_features[Vector2i(3, 3)] = ["block", "N"]
	_features[Vector2i(4, 3)] = ["block", "N"]
	_features[Vector2i(3, 4)] = ["stairs", "N"]
	_features[Vector2i(4, 4)] = ["blockHalf", "N"]
	# A free-standing ramp on open ground, to show the slope tile clearly.
	_features[Vector2i(1, 4)] = ["slope", "E"]


func _assemble() -> void:
	var cells := _ground.keys()
	# Back-to-front: smaller (col + row) is drawn first (tie-break by col keeps
	# it stable). This is the painter's order for a single-height iso grid.
	cells.sort_custom(
		func(a: Vector2i, b: Vector2i) -> bool:
			var da := a.x + a.y
			var db := b.x + b.y
			if da == db:
				return a.x < b.x
			return da < db
	)

	for cell: Vector2i in cells:
		_add_tile("floor", "N", cell, _ground[cell])
		if _features.has(cell):
			var f: Array = _features[cell]
			_add_tile(f[0], f[1], cell, MAPLE)


func _add_tile(base: String, facing: String, cell: Vector2i, mod: Color) -> void:
	var tex := _load_tile(base, facing)
	if tex == null:
		return
	var spr := Sprite2D.new()
	spr.texture = tex
	spr.centered = true
	spr.modulate = mod
	spr.position = _cell_to_world(cell)
	add_child(spr)


func _cell_to_world(cell: Vector2i) -> Vector2:
	return Vector2((cell.x - cell.y) * HALF_W, (cell.x + cell.y) * HALF_H)


func _load_tile(base: String, facing: String) -> Texture2D:
	var path := "%s%s_%s.png" % [TILES_DIR, base, facing]
	if not ResourceLoader.exists(path):
		push_warning("terrain_demo: missing tile %s" % path)
		return null
	return load(path) as Texture2D


func _frame_camera() -> void:
	var cam := Camera2D.new()
	# Centre on the patch. The diamond footprint sits below a sprite's origin,
	# so nudge the camera down to centre the visible ground.
	cam.position = Vector2(0.0, float(GRID - 1) * HALF_H + 150.0)
	cam.zoom = Vector2(0.5, 0.5)
	add_child(cam)
	cam.make_current()
