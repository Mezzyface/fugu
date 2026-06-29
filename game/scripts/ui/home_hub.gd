class_name HomeHubScreen
extends Control
## Screen 01 — Home / Hub (wireframes §01).
##
## The entry / navigation root: a FUGU wordmark, the live currency totals from
## [GameSession] (◆ shards · ✦ essence · ⬡ relic rolls), the current week's
## featured banners (resolved through [method GachaSystem.featured_banners_for_week]),
## and nav buttons that reach every other screen. The screen never navigates
## directly — it emits [signal navigation_requested] and the navigation root
## (`scripts/main.gd`) performs the switch.

## Emitted when a nav button is pressed; the navigation root listens and switches
## screens. Disabled buttons (screens not yet built) never emit.
signal navigation_requested(screen_id: String)

const TITLE_COLOR := Color(0.854902, 0.321569, 0.364706, 1.0)  # eugenia_red
const BODY_COLOR := Color(0.94, 0.94, 0.90, 1.0)
const MUTED_COLOR := Color(0.776471, 0.788235, 0.823529, 1.0)
const FEATURED_COLOR := Color(0.72549, 0.517647, 0.686275, 1.0)  # lilac

## Hub navigation entries as `[label, screen_id]`. An empty screen_id renders a
## disabled button (the screen is not built yet — e.g. Settings).
const NAV_ENTRIES: Array = [
	["Banner", "banner_select"],
	["New Run", "run_setup"],
	["Echo Pool", "echo_pool"],
	["Relic Forge", "relic_forge"],
	["Exchange", "exchange_event"],
	["Collection", "character_collection"],
	["Settings", ""],
]

@export var screen_id: String = "home_hub"
@export var screen_title: String = "Home / Hub"

## The state source. Set by the navigation root via [method setup_screen]; falls
## back to the [GameSession] autoload when the scene is opened standalone.
var session: Node

@onready var _currency_label: Label = %CurrencyLabel
@onready var _featured_title: Label = %FeaturedTitle
@onready var _featured_list: Label = %FeaturedList
@onready var _nav_grid: GridContainer = %NavGrid


func _ready() -> void:
	if session == null:
		session = get_node_or_null("/root/GameSession")
	_build_nav_buttons()
	_connect_session()
	_refresh()


## Navigation-root contract (see `scripts/main.gd`): inject the screen id, title,
## and shared [GameSession] when this screen is mounted.
func setup_screen(p_screen_id: String, p_screen_title: String, p_session: Node) -> void:
	screen_id = p_screen_id
	screen_title = p_screen_title
	session = p_session
	if is_node_ready():
		_connect_session()
		_refresh()


func _connect_session() -> void:
	if session != null and session.has_signal("state_changed"):
		if not session.state_changed.is_connected(_refresh):
			session.state_changed.connect(_refresh)


func _build_nav_buttons() -> void:
	for child in _nav_grid.get_children():
		child.queue_free()
	for entry: Array in NAV_ENTRIES:
		var label: String = entry[0]
		var target: String = entry[1]
		var button := Button.new()
		button.text = label
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.custom_minimum_size = Vector2(0, 52)
		if target == "":
			button.disabled = true
			button.tooltip_text = "Coming soon"
		else:
			button.pressed.connect(_on_nav_pressed.bind(target))
		_nav_grid.add_child(button)


func _on_nav_pressed(target_screen_id: String) -> void:
	navigation_requested.emit(target_screen_id)


func _refresh() -> void:
	if not is_node_ready():
		return
	_currency_label.text = _currency_text()
	_featured_title.text = _featured_title_text()
	_featured_list.text = _featured_list_text()


func _currency_text() -> String:
	if session == null or not session.has_method("currency_totals"):
		return "◆ —   ·   ✦ —   ·   ⬡ —"
	var totals: Dictionary = session.currency_totals()
	return (
		"◆ %d  shards     ·     ✦ %d  essence     ·     ⬡ %d  relic rolls"
		% [totals.get("shards", 0), totals.get("essence", 0), totals.get("relic_rolls", 0)]
	)


func _featured_title_text() -> String:
	var week: int = _current_week()
	var max_week: int = _max_week()
	var count: int = _featured_ids().size()
	return "★ Featured this week — Week %d / %d · %d banners" % [week, max_week, count]


func _featured_list_text() -> String:
	var ids: Array = _featured_ids()
	if ids.is_empty():
		return "No featured banners this week."
	var names: Array[String] = []
	for index in range(ids.size()):
		var banner_id: String = ids[index]
		var display := _character_name(banner_id)
		if index == 0:
			display = "%s  (★ lead)" % display
		names.append(display)
	return "   ·   ".join(names)


func _featured_ids() -> Array:
	if session != null and session.has_method("featured_banner_ids"):
		return session.featured_banner_ids()
	return []


func _character_name(banner_id: String) -> String:
	if session != null and session.has_method("get_character"):
		var character: CharacterDef = session.get_character(banner_id)
		if character != null:
			return character.name
	return banner_id.capitalize()


func _current_week() -> int:
	if session != null and "current_week" in session:
		return session.current_week
	return 1


func _max_week() -> int:
	return 52
