extends Control
## Demo screen for the project Theme (#21).
##
## Renders the honeyblot caps / HoneyPigeon faces over the Isle of Lore 2 panel
## chrome and tints the swatch row from the named Wada Sanzo palette colors so the
## theme wiring is verified end to end rather than hard-coded per node.

const PALETTE_TYPE := &"Palette"

@onready var _swatches: HBoxContainer = %Swatches


func _ready() -> void:
	for entry: Node in _swatches.get_children():
		var rect := entry.get_node_or_null("Swatch") as ColorRect
		if rect == null:
			continue
		var color_name := StringName(entry.name)
		if has_theme_color(color_name, PALETTE_TYPE):
			rect.color = get_theme_color(color_name, PALETTE_TYPE)
