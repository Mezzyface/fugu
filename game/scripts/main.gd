extends Control

signal screen_changed(screen_id: String)

const SCREEN_DEFS: Dictionary = {
	"home_hub": {"title": "Home / Hub", "scene": "res://scenes/home_hub.tscn"},
	"banner_select": {"title": "Banner Select", "scene": "res://scenes/banner_select.tscn"},
	"banner_pull": {"title": "Banner / Pull", "scene": "res://scenes/banner_pull.tscn"},
	"run_setup": {"title": "Run Setup", "scene": "res://scenes/run_setup.tscn"},
	"run_progress": {"title": "Run In Progress", "scene": "res://scenes/run_progress.tscn"},
	"run_results": {"title": "Run Results", "scene": "res://scenes/run_results.tscn"},
	"echo_pool": {"title": "Echo Pool", "scene": "res://scenes/echo_pool_screen.tscn"},
	"exchange_event": {"title": "Exchange Event", "scene": "res://scenes/exchange_event.tscn"},
	"relic_forge": {"title": "Relic Forge", "scene": "res://scenes/relic_forge_screen.tscn"},
	"character_collection": {"title": "Character Collection", "scene": "res://scenes/character_collection.tscn"},
}

@onready var _screen_mount: Control = %ScreenMount
@onready var _nav_buttons: VBoxContainer = %NavButtons
@onready var _status_label: Label = %StatusLabel

var current_screen_id: String = ""
var current_screen: Control


func _ready() -> void:
	_build_nav_buttons()
	if GameSession.has_signal("state_changed"):
		GameSession.state_changed.connect(_refresh_status)
	go_to_screen("home_hub")
	_refresh_status()


func screen_ids() -> Array[String]:
	var ids: Array[String] = []
	for screen_id: String in SCREEN_DEFS:
		ids.append(screen_id)
	return ids


func can_go_to_screen(screen_id: String) -> bool:
	return SCREEN_DEFS.has(screen_id)


func go_to_screen(screen_id: String) -> bool:
	if not can_go_to_screen(screen_id):
		push_error("unknown screen %s" % screen_id)
		return false
	var screen := _instantiate_screen(screen_id)
	if screen == null:
		return false
	_clear_screen()
	current_screen_id = screen_id
	current_screen = screen
	_screen_mount.add_child(screen)
	_setup_screen(screen, screen_id)
	screen_changed.emit(screen_id)
	_refresh_status()
	return true


func go_home() -> bool:
	return go_to_screen("home_hub")


func _build_nav_buttons() -> void:
	for child in _nav_buttons.get_children():
		child.queue_free()
	for screen_id: String in screen_ids():
		var button := Button.new()
		button.text = SCREEN_DEFS[screen_id]["title"]
		button.pressed.connect(go_to_screen.bind(screen_id))
		_nav_buttons.add_child(button)


func _instantiate_screen(screen_id: String) -> Control:
	var packed := load(SCREEN_DEFS[screen_id]["scene"]) as PackedScene
	if packed == null:
		push_error("screen scene failed to load: %s" % SCREEN_DEFS[screen_id]["scene"])
		return null
	var instance := packed.instantiate()
	if not instance is Control:
		push_error("screen scene root must be Control: %s" % screen_id)
		instance.queue_free()
		return null
	return instance


func _setup_screen(screen: Control, screen_id: String) -> void:
	if screen.has_method("setup_screen"):
		screen.setup_screen(screen_id, SCREEN_DEFS[screen_id]["title"], GameSession)
	if screen.has_signal("navigation_requested"):
		screen.navigation_requested.connect(go_to_screen)


func _clear_screen() -> void:
	if current_screen != null:
		current_screen.queue_free()
		current_screen = null
	for child in _screen_mount.get_children():
		child.queue_free()


func _refresh_status() -> void:
	_status_label.text = GameSession.currency_summary()
