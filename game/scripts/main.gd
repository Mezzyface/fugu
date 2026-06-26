extends Control
## Placeholder entry screen for the Fugu project.
##
## This is the scene set as `run/main_scene`. It only displays a title while the
## real gameplay scenes are built out in later tasks.

@onready var _title_label: Label = %TitleLabel


func _ready() -> void:
	_title_label.text = "Fugu"
