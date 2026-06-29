class_name EchoPoolScreen
extends Control

signal navigation_requested(screen_id: String)

const TITLE_COLOR := Color(0.854902, 0.321569, 0.364706, 1.0)
const BODY_COLOR := Color(0.94, 0.94, 0.90, 1.0)
const MUTED_COLOR := Color(0.776471, 0.788235, 0.823529, 1.0)
const FAVORITE_COLOR := Color(0.772549, 0.623529, 0.419608, 1.0)
const SUCCESS_COLOR := Color(0.588235, 0.819608, 0.666667, 1.0)

@export var screen_id: String = "echo_pool"
@export var screen_title: String = "Echo Pool"

var session: Node
var sort_mode: String = "power"
var last_message: String = ""

@onready var _summary_label: Label = %SummaryLabel
@onready var _sort_selector: OptionButton = %SortSelector
@onready var _record_list: VBoxContainer = %RecordList
@onready var _message_label: Label = %MessageLabel
@onready var _exchange_button: Button = %ExchangeButton
@onready var _hub_button: Button = %HubButton

var _sort_modes: Array[String] = ["power", "icon", "favorite", "source", "lineage"]


func _ready() -> void:
	if session == null:
		session = get_node_or_null("/root/GameSession")
	_sort_selector.item_selected.connect(_on_sort_selected)
	_exchange_button.pressed.connect(_on_exchange_pressed)
	_hub_button.pressed.connect(_on_hub_pressed)
	_seed_demo_echoes_if_empty()
	_populate_sort_selector()
	_refresh()


func setup_screen(p_screen_id: String, p_screen_title: String, p_session: Node) -> void:
	screen_id = p_screen_id
	screen_title = p_screen_title
	session = p_session
	if is_node_ready():
		_seed_demo_echoes_if_empty()
		_populate_sort_selector()
		_refresh()


func favorite_record(record_id: int) -> EchoRecord:
	var record := _pool().get_record(record_id)
	if record == null:
		return null
	var updated := _pool().update_record(record_id, not record.favorite)
	last_message = "Favorite toggled for #%d." % record_id if updated != null else "Favorite cap reached."
	_refresh()
	return updated


func delete_record(record_id: int) -> EchoRecord:
	var removed := _pool().delete_echo(record_id)
	last_message = "Deleted echo #%d." % record_id if removed != null else "Favorite echoes must be unfavorited before deletion."
	_refresh()
	return removed


func exchange_record(record_id: int) -> EchoExchangeReward:
	var reward := _pool().exchange_echo(record_id)
	if reward != null:
		if session != null and session.has_method("add_currency"):
			session.add_currency(reward.shards, reward.essence, reward.relic_rolls)
		last_message = "Exchanged echo #%d: +%d✦ +%d◆ +%d⬡." % [record_id, reward.essence, reward.shards, reward.relic_rolls]
	else:
		last_message = "Favorite echoes must be unfavorited before exchange."
	_refresh()
	return reward


func _populate_sort_selector() -> void:
	_sort_selector.clear()
	for mode: String in _sort_modes:
		_sort_selector.add_item(mode.capitalize())
	_sort_selector.selected = maxi(0, _sort_modes.find(sort_mode))


func _refresh() -> void:
	if not is_node_ready() or _pool() == null:
		return
	_summary_label.text = "Capacity %d / %d · favorites %d / %d · sorted by %s" % [
		_pool().size(),
		_pool().capacity,
		_pool().favorite_count(),
		_pool().max_favorites,
		sort_mode
	]
	_build_records()
	_message_label.text = last_message


func _build_records() -> void:
	for child in _record_list.get_children():
		child.queue_free()
	var records := _pool().sorted_records(sort_mode)
	if records.is_empty():
		_record_list.add_child(_label("No echoes banked yet.", MUTED_COLOR))
		return
	for record: EchoRecord in records:
		_record_list.add_child(_record_row(record))


func _record_row(record: EchoRecord) -> Control:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(0, 82)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_top", 8)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_bottom", 8)
	panel.add_child(margin)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	margin.add_child(row)
	var detail := _label(_record_text(record), FAVORITE_COLOR if record.favorite else BODY_COLOR)
	detail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(detail)
	row.add_child(_button("♥" if record.favorite else "♡", _on_favorite_pressed.bind(record.id)))
	row.add_child(_button("⇄", _on_exchange_one_pressed.bind(record.id)))
	row.add_child(_button("Delete", _on_delete_pressed.bind(record.id)))
	return panel


func _record_text(record: EchoRecord) -> String:
	return "#%d %s · pwr %d · icon %s · source %s · lineage %d" % [
		record.id,
		"♥" if record.favorite else "echo",
		record.power_score,
		record.icon,
		_character_name(record.echo.source_character_id),
		record.echo.lineage_depth
	]


func _button(text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(72, 42)
	button.pressed.connect(callback)
	return button


func _label(text: String, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.add_theme_color_override("font_color", color)
	return label


func _pool() -> EchoPool:
	if session != null and "echo_pool" in session:
		return session.echo_pool
	return null


func _seed_demo_echoes_if_empty() -> void:
	if _pool() == null or _pool().size() > 0:
		return
	_pool().bank_echo(_echo("iron_vow", 900, 2, 1), "shield", true)
	_pool().bank_echo(_echo("star_witch", 620, 1, 0), "star")
	_pool().bank_echo(_echo("rat_squire", 480, 0, 0), "rat")


func _echo(source: String, hp: int, lineage: int, instability: int) -> FrozenEcho:
	return FrozenEcho.new(
		source,
		{"hp": BigStat.new(hp), "atk": BigStat.new(hp / 5), "def": BigStat.new(hp / 7), "spd": BigStat.new(80)},
		PackedStringArray(["Echo Skill"]),
		PackedStringArray(["lineage"]),
		lineage,
		instability
	)


func _character_name(id: String) -> String:
	if session != null and session.has_method("get_character"):
		var character: CharacterDef = session.get_character(id)
		if character != null:
			return character.name
	return id.capitalize()


func _on_sort_selected(index: int) -> void:
	if index >= 0 and index < _sort_modes.size():
		sort_mode = _sort_modes[index]
		_refresh()


func _on_favorite_pressed(record_id: int) -> void:
	favorite_record(record_id)


func _on_delete_pressed(record_id: int) -> void:
	delete_record(record_id)


func _on_exchange_one_pressed(record_id: int) -> void:
	exchange_record(record_id)


func _on_exchange_pressed() -> void:
	navigation_requested.emit("exchange_event")


func _on_hub_pressed() -> void:
	navigation_requested.emit("home_hub")
