class_name RunResultsScreen
extends Control

signal navigation_requested(screen_id: String)

const TITLE_COLOR := Color(0.854902, 0.321569, 0.364706, 1.0)
const BODY_COLOR := Color(0.94, 0.94, 0.90, 1.0)
const MUTED_COLOR := Color(0.776471, 0.788235, 0.823529, 1.0)
const SUCCESS_COLOR := Color(0.588235, 0.819608, 0.666667, 1.0)
const WARNING_COLOR := Color(0.772549, 0.623529, 0.419608, 1.0)

@export var screen_id: String = "run_results"
@export var screen_title: String = "Run Results"

var session: Node
var character_id: String = "iron_vow"
var route: String = "balanced"
var run_result: RunResult
var banked_record: EchoRecord
var last_message: String = ""

@onready var _outcome_label: Label = %OutcomeLabel
@onready var _summary_label: Label = %SummaryLabel
@onready var _stats_grid: GridContainer = %StatsGrid
@onready var _skills_label: Label = %SkillsLabel
@onready var _traits_label: Label = %TraitsLabel
@onready var _lineage_label: Label = %LineageLabel
@onready var _rewards_label: Label = %RewardsLabel
@onready var _message_label: Label = %MessageLabel
@onready var _bank_button: Button = %BankButton
@onready var _forge_button: Button = %ForgeButton
@onready var _hub_button: Button = %HubButton


func _ready() -> void:
	if session == null:
		session = get_node_or_null("/root/GameSession")
	_bank_button.pressed.connect(_on_bank_pressed)
	_forge_button.pressed.connect(_on_forge_pressed)
	_hub_button.pressed.connect(_on_hub_pressed)
	_build_result()
	_refresh()


func setup_screen(p_screen_id: String, p_screen_title: String, p_session: Node) -> void:
	screen_id = p_screen_id
	screen_title = p_screen_title
	session = p_session
	if is_node_ready():
		_build_result()
		_refresh()


func bank_echo() -> EchoRecord:
	if session == null or not ("echo_pool" in session) or run_result == null:
		return null
	if banked_record != null:
		return banked_record
	banked_record = session.echo_pool.bank_echo(run_result.echo, "run_result")
	if banked_record != null:
		last_message = "Banked echo #%d into EchoPool." % banked_record.id
		if session.has_signal("state_changed"):
			session.state_changed.emit()
	else:
		last_message = "EchoPool is full — delete or exchange an echo first."
	_refresh()
	return banked_record


func _build_result() -> void:
	var character := _character()
	if character == null:
		return
	var simulator := TrainingSimulator.new(7)
	simulator.random_source = func() -> float: return 1.0
	run_result = simulator.run(character, route)


func _refresh() -> void:
	if not is_node_ready() or run_result == null:
		return
	_outcome_label.text = "VICTORY" if run_result.victory else "DEFEAT"
	_outcome_label.add_theme_color_override("font_color", SUCCESS_COLOR if run_result.victory else TITLE_COLOR)
	_summary_label.text = "%s · cleared %d / 12 floors · always-echo frozen" % [
		_character_name(character_id),
		run_result.floors_cleared
	]
	_build_stats(run_result.echo.stats)
	_skills_label.text = "Skills: %s" % _join_or_dash(run_result.echo.skills)
	_traits_label.text = "Traits: %s" % _join_or_dash(run_result.echo.traits)
	_lineage_label.text = "Lineage depth %d · instability ⚠ %d" % [run_result.echo.lineage_depth, run_result.echo.instability]
	_rewards_label.text = _reward_text()
	_message_label.text = last_message
	_bank_button.disabled = banked_record != null
	_bank_button.text = "Echo Banked" if banked_record != null else "Bank Echo"


func _build_stats(stats: Dictionary) -> void:
	for child in _stats_grid.get_children():
		child.queue_free()
	var keys: Array = stats.keys()
	keys.sort()
	for stat_name: String in keys:
		_stats_grid.add_child(_label(stat_name.to_upper(), MUTED_COLOR, 90))
		_stats_grid.add_child(_label(_format_stat(stats[stat_name]), BODY_COLOR, 170))


func _reward_text() -> String:
	var rewards := run_result.rewards
	return "+%d◆ banked shards · +%d⬡ relic rolls · echo quality %d%% · +%d◆ instability dividend" % [
		rewards.banked_shards,
		rewards.relic_rolls,
		rewards.echo_quality_percent,
		rewards.instability_dividend_shards
	]


func _join_or_dash(values: PackedStringArray) -> String:
	return "—" if values.is_empty() else ", ".join(values)


func _format_stat(stat: BigStat) -> String:
	if session != null and session.has_method("format_stat"):
		return session.format_stat(stat)
	var normalized := stat.normalized()
	return "%d·10^%d" % [normalized.mantissa, normalized.magnitude]


func _label(text: String, color: Color, minimum_width: int) -> Label:
	var label := Label.new()
	label.text = text
	label.custom_minimum_size = Vector2(minimum_width, 0)
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.add_theme_color_override("font_color", color)
	return label


func _character() -> CharacterDef:
	if session != null and session.has_method("get_character"):
		var featured: Array = session.featured_banner_ids() if session.has_method("featured_banner_ids") else []
		if not featured.is_empty():
			character_id = featured[0]
		return session.get_character(character_id)
	return CharacterCatalog.sample_characters().get(character_id, null)


func _character_name(id: String) -> String:
	var character := _character()
	return character.name if character != null else id.capitalize()


func _on_bank_pressed() -> void:
	bank_echo()


func _on_forge_pressed() -> void:
	if session != null and "relic_rolls" in session and run_result != null:
		session.relic_rolls += run_result.rewards.relic_rolls
		if session.has_signal("state_changed"):
			session.state_changed.emit()
	navigation_requested.emit("relic_forge")


func _on_hub_pressed() -> void:
	navigation_requested.emit("home_hub")
