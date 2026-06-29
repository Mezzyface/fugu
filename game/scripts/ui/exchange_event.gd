class_name ExchangeEventScreen
extends Control

signal navigation_requested(screen_id: String)

const TITLE_COLOR := Color(0.854902, 0.321569, 0.364706, 1.0)
const BODY_COLOR := Color(0.94, 0.94, 0.90, 1.0)
const MUTED_COLOR := Color(0.776471, 0.788235, 0.823529, 1.0)
const FAVORITE_COLOR := Color(0.772549, 0.623529, 0.419608, 1.0)
const SUCCESS_COLOR := Color(0.588235, 0.819608, 0.666667, 1.0)

@export var screen_id: String = "exchange_event"
@export var screen_title: String = "Exchange Event"

var session: Node
var event_multiplier: int = 3
var selected_ids: Array[int] = []
var last_message: String = ""

@onready var _event_label: Label = %EventLabel
@onready var _record_list: VBoxContainer = %RecordList
@onready var _preview_label: Label = %PreviewLabel
@onready var _message_label: Label = %MessageLabel
@onready var _confirm_button: Button = %ConfirmButton
@onready var _pool_button: Button = %PoolButton
@onready var _hub_button: Button = %HubButton


func _ready() -> void:
	if session == null:
		session = get_node_or_null("/root/GameSession")
	_confirm_button.pressed.connect(_on_confirm_pressed)
	_pool_button.pressed.connect(_on_pool_pressed)
	_hub_button.pressed.connect(_on_hub_pressed)
	_seed_demo_echoes_if_empty()
	_select_default_echoes()
	_refresh()


func setup_screen(p_screen_id: String, p_screen_title: String, p_session: Node) -> void:
	screen_id = p_screen_id
	screen_title = p_screen_title
	session = p_session
	if is_node_ready():
		_seed_demo_echoes_if_empty()
		_select_default_echoes()
		_refresh()


func toggle_record(record_id: int) -> void:
	var record := _pool().get_record(record_id)
	if record == null:
		return
	if record.favorite:
		last_message = "Favorites are locked for this event."
		_refresh()
		return
	if selected_ids.has(record_id):
		selected_ids.erase(record_id)
	else:
		selected_ids.append(record_id)
	last_message = "Selection updated."
	_refresh()


func preview_reward() -> EchoExchangeReward:
	var total := EchoExchangeReward.new(0, 0, 0)
	for record_id: int in selected_ids:
		var record := _pool().get_record(record_id)
		if record == null or record.favorite:
			continue
		var essence := maxi(1, record.power_score / 100) * event_multiplier
		var shards := (10 + record.echo.lineage_depth * 5) * event_multiplier
		var relic_rolls := (1 + record.echo.skills.size() / 2) * event_multiplier
		total = EchoExchangeReward.new(total.essence + essence, total.shards + shards, total.relic_rolls + relic_rolls)
	return total


func confirm_exchange() -> EchoExchangeReward:
	var reward := _pool().exchange_event(selected_ids, event_multiplier)
	if reward == null:
		last_message = "Exchange failed — favorites locked or selection invalid."
		_refresh()
		return null
	if session != null and session.has_method("add_currency"):
		session.add_currency(reward.shards, reward.essence, reward.relic_rolls)
	last_message = "Exchange confirmed: +%d✦ +%d◆ +%d⬡." % [reward.essence, reward.shards, reward.relic_rolls]
	selected_ids.clear()
	_refresh()
	return reward


func _refresh() -> void:
	if not is_node_ready() or _pool() == null:
		return
	_event_label.text = "Resonant Tide — ×%d multiplier · 2d left · favorites locked" % event_multiplier
	_build_records()
	var reward := preview_reward()
	_preview_label.text = "%d selected → +%d✦ +%d◆ +%d⬡" % [selected_ids.size(), reward.essence, reward.shards, reward.relic_rolls]
	_confirm_button.disabled = selected_ids.is_empty()
	_message_label.text = last_message


func _build_records() -> void:
	for child in _record_list.get_children():
		child.queue_free()
	for record: EchoRecord in _pool().sorted_records("power"):
		_record_list.add_child(_record_row(record))


func _record_row(record: EchoRecord) -> Control:
	var button := Button.new()
	button.alignment = HORIZONTAL_ALIGNMENT_LEFT
	button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	button.custom_minimum_size = Vector2(0, 72)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.disabled = record.favorite
	button.text = _record_text(record)
	button.add_theme_color_override("font_color", FAVORITE_COLOR if record.favorite else (SUCCESS_COLOR if selected_ids.has(record.id) else BODY_COLOR))
	button.pressed.connect(toggle_record.bind(record.id))
	return button


func _record_text(record: EchoRecord) -> String:
	var state := "LOCKED ♥" if record.favorite else ("SELECTED" if selected_ids.has(record.id) else "select")
	return "%s  #%d · pwr %d · %s · lineage %d" % [state, record.id, record.power_score, _character_name(record.echo.source_character_id), record.echo.lineage_depth]


func _select_default_echoes() -> void:
	selected_ids.clear()
	for record: EchoRecord in _pool().sorted_records("power"):
		if not record.favorite and selected_ids.size() < 2:
			selected_ids.append(record.id)


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


func _pool() -> EchoPool:
	if session != null and "echo_pool" in session:
		return session.echo_pool
	return null


func _character_name(id: String) -> String:
	if session != null and session.has_method("get_character"):
		var character: CharacterDef = session.get_character(id)
		if character != null:
			return character.name
	return id.capitalize()


func _on_confirm_pressed() -> void:
	confirm_exchange()


func _on_pool_pressed() -> void:
	navigation_requested.emit("echo_pool")


func _on_hub_pressed() -> void:
	navigation_requested.emit("home_hub")
