class_name RelicForgeScreen
extends Control

signal navigation_requested(screen_id: String)

const TITLE_COLOR := Color(0.854902, 0.321569, 0.364706, 1.0)
const BODY_COLOR := Color(0.94, 0.94, 0.90, 1.0)
const MUTED_COLOR := Color(0.776471, 0.788235, 0.823529, 1.0)
const SUCCESS_COLOR := Color(0.588235, 0.819608, 0.666667, 1.0)
const EPIC_COLOR := Color(0.72549, 0.517647, 0.686275, 1.0)
const LEGENDARY_COLOR := Color(0.772549, 0.623529, 0.419608, 1.0)

@export var screen_id: String = "relic_forge"
@export var screen_title: String = "Relic Forge"

var session: Node
var forge := RelicForge.new(11)
var target_echo: FrozenEcho
var forged_relics: Array[Relic] = []
var boosted_stats: Dictionary = {}
var last_message: String = ""

@onready var _rolls_label: Label = %RollsLabel
@onready var _odds_label: Label = %OddsLabel
@onready var _relic_list: VBoxContainer = %RelicList
@onready var _stats_grid: GridContainer = %StatsGrid
@onready var _message_label: Label = %MessageLabel
@onready var _forge_button: Button = %ForgeButton
@onready var _apply_button: Button = %ApplyButton
@onready var _results_button: Button = %ResultsButton
@onready var _hub_button: Button = %HubButton


func _ready() -> void:
	if session == null:
		session = get_node_or_null("/root/GameSession")
	_forge_button.pressed.connect(_on_forge_pressed)
	_apply_button.pressed.connect(_on_apply_pressed)
	_results_button.pressed.connect(_on_results_pressed)
	_hub_button.pressed.connect(_on_hub_pressed)
	_seed_defaults()
	_refresh()


func setup_screen(p_screen_id: String, p_screen_title: String, p_session: Node) -> void:
	screen_id = p_screen_id
	screen_title = p_screen_title
	session = p_session
	if is_node_ready():
		_seed_defaults()
		_refresh()


func forge_relics(count: int = 0) -> Array[Relic]:
	var spend := count if count > 0 else mini(3, _available_rolls())
	if spend <= 0:
		last_message = "No ⬡ relic rolls available."
		_refresh()
		return []
	forged_relics = forge.forge(spend)
	if session != null and "relic_rolls" in session:
		session.relic_rolls = maxi(0, session.relic_rolls - spend)
	last_message = "Forged %d relic(s)." % forged_relics.size()
	_refresh()
	return forged_relics


func apply_relics_to_echo() -> Dictionary:
	if target_echo == null or forged_relics.is_empty():
		return {}
	var original := target_echo.stats.duplicate(true)
	boosted_stats = RelicForge.apply_relics(target_echo.stats, forged_relics)
	last_message = "Applied relic preview; source echo stats are unchanged."
	_refresh()
	assert(original == target_echo.stats)
	return boosted_stats


func _seed_defaults() -> void:
	if session != null and "relic_rolls" in session and session.relic_rolls <= 0:
		session.relic_rolls = 6
	if session != null and "echo_pool" in session and session.echo_pool.size() == 0:
		session.echo_pool.bank_echo(_echo("iron_vow", 900), "shield")
	target_echo = session.echo_pool.records[0].echo if session != null and "echo_pool" in session and session.echo_pool.size() > 0 else _echo("iron_vow", 900)
	if forged_relics.is_empty():
		forged_relics = forge.forge(3)


func _refresh() -> void:
	if not is_node_ready():
		return
	_rolls_label.text = "⬡ relic rolls available — %d" % _available_rolls()
	_odds_label.text = "Odds: Common 60%/+8 · Rare 25%/+15 · Epic 12%/+25 · Legendary 3%/+40"
	_build_relic_list()
	_build_stats()
	_message_label.text = last_message
	_forge_button.disabled = _available_rolls() <= 0
	_apply_button.disabled = forged_relics.is_empty()


func _build_relic_list() -> void:
	for child in _relic_list.get_children():
		child.queue_free()
	for relic: Relic in forged_relics:
		_relic_list.add_child(_label("#%d %s · %s · +%d%% %s" % [relic.id, relic.name, Rarity.to_string_value(relic.rarity).capitalize(), relic.bonus_percent, relic.stat.to_upper()], _rarity_color(relic.rarity)))


func _build_stats() -> void:
	for child in _stats_grid.get_children():
		child.queue_free()
	var stats := boosted_stats if not boosted_stats.is_empty() else target_echo.stats
	var keys: Array = stats.keys()
	keys.sort()
	for stat_name: String in keys:
		_stats_grid.add_child(_stat_label(stat_name.to_upper(), MUTED_COLOR, 96))
		_stats_grid.add_child(_stat_label(_format_stat(stats[stat_name]), BODY_COLOR, 180))


func _available_rolls() -> int:
	return session.relic_rolls if session != null and "relic_rolls" in session else 0


func _format_stat(stat: BigStat) -> String:
	if session != null and session.has_method("format_stat"):
		return session.format_stat(stat)
	var normalized := stat.normalized()
	return "%d·10^%d" % [normalized.mantissa, normalized.magnitude]


func _rarity_color(rarity: int) -> Color:
	match rarity:
		Rarity.RARE:
			return SUCCESS_COLOR
		Rarity.EPIC:
			return EPIC_COLOR
		Rarity.LEGENDARY:
			return LEGENDARY_COLOR
		_:
			return BODY_COLOR


func _label(text: String, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.add_theme_color_override("font_color", color)
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


func _echo(source: String, hp: int) -> FrozenEcho:
	return FrozenEcho.new(
		source,
		{"hp": BigStat.new(hp), "atk": BigStat.new(hp / 5), "def": BigStat.new(hp / 7), "spd": BigStat.new(80)},
		PackedStringArray(["Echo Skill"]),
		PackedStringArray(["lineage"]),
		1,
		0
	)


func _on_forge_pressed() -> void:
	forge_relics()


func _on_apply_pressed() -> void:
	apply_relics_to_echo()


func _on_results_pressed() -> void:
	navigation_requested.emit("run_results")


func _on_hub_pressed() -> void:
	navigation_requested.emit("home_hub")
