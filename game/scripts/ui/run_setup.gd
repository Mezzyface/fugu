class_name RunSetupScreen
extends Control

signal navigation_requested(screen_id: String)

const TITLE_COLOR := Color(0.854902, 0.321569, 0.364706, 1.0)
const BODY_COLOR := Color(0.94, 0.94, 0.90, 1.0)
const MUTED_COLOR := Color(0.776471, 0.788235, 0.823529, 1.0)
const FEATURED_COLOR := Color(0.588235, 0.819608, 0.666667, 1.0)
const WARNING_COLOR := Color(0.772549, 0.623529, 0.419608, 1.0)

@export var screen_id: String = "run_setup"
@export var screen_title: String = "Run Setup"

var session: Node
var selected_character_id: String = ""
var selected_route: String = "balanced"
var selected_parents: Array[FrozenEcho] = []
var last_message: String = ""

@onready var _character_selector: OptionButton = %CharacterSelector
@onready var _route_selector: OptionButton = %RouteSelector
@onready var _parent_list: VBoxContainer = %ParentList
@onready var _selected_parents_label: Label = %SelectedParentsLabel
@onready var _route_detail_label: Label = %RouteDetailLabel
@onready var _stats_grid: GridContainer = %StatsGrid
@onready var _instability_label: Label = %InstabilityLabel
@onready var _message_label: Label = %MessageLabel
@onready var _start_button: Button = %StartButton
@onready var _hub_button: Button = %HubButton

var _character_ids: Array[String] = []
var _route_ids: Array[String] = []


func _ready() -> void:
	if session == null:
		session = get_node_or_null("/root/GameSession")
	_character_selector.item_selected.connect(_on_character_selected)
	_route_selector.item_selected.connect(_on_route_selected)
	_start_button.pressed.connect(_on_start_pressed)
	_hub_button.pressed.connect(_on_hub_pressed)
	_connect_session()
	_populate_characters()
	_populate_routes()
	_refresh()


func setup_screen(p_screen_id: String, p_screen_title: String, p_session: Node) -> void:
	screen_id = p_screen_id
	screen_title = p_screen_title
	session = p_session
	if is_node_ready():
		_connect_session()
		_populate_characters()
		_populate_routes()
		_refresh()


func selected_parent_count() -> int:
	return selected_parents.size()


func projected_start() -> Array:
	var character := _selected_character()
	if character == null:
		return [{}, 0, 0]
	return TrainingSimulator.new().start_stats(character, selected_parents)


func _connect_session() -> void:
	if session != null and session.has_signal("state_changed"):
		if not session.state_changed.is_connected(_refresh):
			session.state_changed.connect(_refresh)


func _populate_characters() -> void:
	_character_selector.clear()
	_character_ids.clear()
	if session == null or not ("characters" in session):
		return
	_character_ids.assign((session.characters as Dictionary).keys())
	_character_ids.sort()
	for character_id: String in _character_ids:
		_character_selector.add_item(_character_name(character_id))
	if _character_ids.is_empty():
		selected_character_id = ""
		return
	if not _character_ids.has(selected_character_id):
		selected_character_id = _default_character_id()
	_character_selector.selected = maxi(0, _character_ids.find(selected_character_id))


func _populate_routes() -> void:
	_route_selector.clear()
	_route_ids.clear()
	for route: String in TrainingSimulator.available_routes():
		_route_ids.append(route)
		_route_selector.add_item(_route_label(route))
	if not _route_ids.has(selected_route):
		selected_route = _route_ids[0] if not _route_ids.is_empty() else "balanced"
	_route_selector.selected = maxi(0, _route_ids.find(selected_route))


func _default_character_id() -> String:
	if session != null and session.has_method("featured_banner_ids"):
		var featured: Array = session.featured_banner_ids()
		if not featured.is_empty() and _character_ids.has(featured[0]):
			return featured[0]
	return _character_ids[0]


func _refresh() -> void:
	if not is_node_ready():
		return
	_prune_selected_parents()
	_build_parent_list()
	_refresh_projection()
	_message_label.text = last_message


func _build_parent_list() -> void:
	for child in _parent_list.get_children():
		child.queue_free()
	var records := _parent_records()
	if records.is_empty():
		_parent_list.add_child(_plain_label("No echoes banked yet — run results can bank Frozen Echo parents."))
		return
	var recommended := _recommended_parent_echoes()
	for record: EchoRecord in records:
		var button := Button.new()
		button.text = _parent_button_text(record, recommended.has(record.echo))
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		button.custom_minimum_size = Vector2(0, 62)
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.add_theme_color_override("font_color", FEATURED_COLOR if _has_parent(record.echo) else BODY_COLOR)
		button.pressed.connect(_toggle_parent.bind(record.echo))
		_parent_list.add_child(button)


func _refresh_projection() -> void:
	_selected_parents_label.text = _selected_parent_text()
	_route_detail_label.text = _route_detail_text()
	var projection := projected_start()
	var stats: Dictionary = projection[0]
	var lineage_depth: int = projection[1]
	var instability: int = projection[2]
	_build_stats(stats)
	_instability_label.text = "lineage depth %d · instability ⚠ %d" % [lineage_depth, instability]
	_instability_label.add_theme_color_override("font_color", WARNING_COLOR if instability > 0 else BODY_COLOR)


func _build_stats(stats: Dictionary) -> void:
	for child in _stats_grid.get_children():
		child.queue_free()
	var stat_names: Array = stats.keys()
	stat_names.sort()
	for stat_name: String in stat_names:
		var name_label := _stat_label(stat_name.to_upper(), MUTED_COLOR, 96)
		_stats_grid.add_child(name_label)
		_stats_grid.add_child(_stat_label(_format_stat(stats[stat_name]), BODY_COLOR, 180))


func _toggle_parent(echo: FrozenEcho) -> void:
	var index := selected_parents.find(echo)
	if index != -1:
		selected_parents.remove_at(index)
		last_message = "Parent removed."
	elif selected_parents.size() >= TrainingSimulator.MAX_PARENTS:
		last_message = "Parent cap reached: choose at most %d echoes." % TrainingSimulator.MAX_PARENTS
	else:
		selected_parents.append(echo)
		last_message = "Parent selected."
	_refresh()


func _prune_selected_parents() -> void:
	var available: Array[FrozenEcho] = []
	for record: EchoRecord in _parent_records():
		available.append(record.echo)
	for index in range(selected_parents.size() - 1, -1, -1):
		if not available.has(selected_parents[index]):
			selected_parents.remove_at(index)
	while selected_parents.size() > TrainingSimulator.MAX_PARENTS:
		selected_parents.pop_back()


func _parent_records() -> Array[EchoRecord]:
	if session == null or not ("echo_pool" in session) or session.echo_pool == null:
		return []
	return session.echo_pool.sorted_records("power").slice(0, 8)


func _recommended_parent_echoes() -> Array[FrozenEcho]:
	if session == null or not ("echo_pool" in session) or session.echo_pool == null:
		return []
	return session.echo_pool.best_parents(selected_character_id, TrainingSimulator.MAX_PARENTS)


func _parent_button_text(record: EchoRecord, recommended: bool) -> String:
	var marker := "✓ " if _has_parent(record.echo) else ""
	var tag := " · recommended" if recommended else ""
	return "%s#%d %s · pwr %d · lin %d%s" % [
		marker,
		record.id,
		_character_name(record.echo.source_character_id),
		record.power_score,
		record.echo.lineage_depth,
		tag
	]


func _selected_parent_text() -> String:
	if selected_parents.is_empty():
		return "Parents: none selected · EchoPool best_parents can recommend up to 2."
	var names: Array[String] = []
	for echo: FrozenEcho in selected_parents:
		names.append("%s (lin %d)" % [_character_name(echo.source_character_id), echo.lineage_depth])
	return "Parents: %s" % "  +  ".join(names)


func _route_detail_text() -> String:
	var tuning := TrainingSimulator.route_tuning(selected_route)
	if tuning.is_empty():
		return "Route unavailable"
	return "%s · growth %d%% · magnitude every %d floors" % [
		_route_label(selected_route),
		int(tuning["growth_percent"]),
		int(tuning["magnitude_interval"])
	]


func _has_parent(echo: FrozenEcho) -> bool:
	return selected_parents.has(echo)


func _selected_character() -> CharacterDef:
	if session != null and session.has_method("get_character"):
		return session.get_character(selected_character_id)
	return null


func _character_name(character_id: String) -> String:
	if session != null and session.has_method("get_character"):
		var character: CharacterDef = session.get_character(character_id)
		if character != null:
			return character.name
	return character_id.capitalize()


func _route_label(route: String) -> String:
	return route.replace("_", " ").capitalize()


func _format_stat(stat: BigStat) -> String:
	if session != null and session.has_method("format_stat"):
		return session.format_stat(stat)
	var normalized := stat.normalized()
	return "%d·10^%d" % [normalized.mantissa, normalized.magnitude]


func _plain_label(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.add_theme_color_override("font_color", BODY_COLOR)
	return label


func _stat_label(text: String, color: Color, minimum_width: int) -> Label:
	var label := Label.new()
	label.text = text
	label.clip_text = false
	label.text_overrun_behavior = TextServer.OVERRUN_NO_TRIMMING
	label.custom_minimum_size = Vector2(minimum_width, 0)
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.add_theme_color_override("font_color", color)
	return label


func _on_character_selected(index: int) -> void:
	if index < 0 or index >= _character_ids.size():
		return
	selected_character_id = _character_ids[index]
	selected_parents.clear()
	last_message = "Base character selected."
	_refresh()


func _on_route_selected(index: int) -> void:
	if index < 0 or index >= _route_ids.size():
		return
	selected_route = _route_ids[index]
	last_message = "Route selected."
	_refresh()


func _on_start_pressed() -> void:
	navigation_requested.emit("run_progress")


func _on_hub_pressed() -> void:
	navigation_requested.emit("home_hub")
