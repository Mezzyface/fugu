class_name RunProgressScreen
extends Control

signal navigation_requested(screen_id: String)

const TITLE_COLOR := Color(0.854902, 0.321569, 0.364706, 1.0)
const BODY_COLOR := Color(0.94, 0.94, 0.90, 1.0)
const MUTED_COLOR := Color(0.776471, 0.788235, 0.823529, 1.0)
const CLEAR_COLOR := Color(0.588235, 0.819608, 0.666667, 1.0)
const FAIL_COLOR := Color(0.854902, 0.321569, 0.364706, 1.0)
const BOSS_COLOR := Color(0.772549, 0.623529, 0.419608, 1.0)

const TERRAIN_TEXTURE := preload("res://assets/terrain/floor_N.png")
const UNIT_TEXTURE := preload("res://assets/units/warrior/Warrior_Idle.png")
const ENEMY_TEXTURE := preload("res://assets/enemies/torch_goblin/TorchGoblin_Idle.png")

@export var screen_id: String = "run_progress"
@export var screen_title: String = "Run In Progress"

var session: Node
var route: String = "balanced"
var character_id: String = "iron_vow"
var current_index: int = 3
var run_result: RunResult

@onready var _summary_label: Label = %SummaryLabel
@onready var _floor_grid: GridContainer = %FloorGrid
@onready var _encounter_title: Label = %EncounterTitle
@onready var _encounter_detail: Label = %EncounterDetail
@onready var _checkpoint_label: Label = %CheckpointLabel
@onready var _log_label: Label = %LogLabel
@onready var _prev_button: Button = %PrevButton
@onready var _next_button: Button = %NextButton
@onready var _results_button: Button = %ResultsButton
@onready var _hub_button: Button = %HubButton


func _ready() -> void:
	if session == null:
		session = get_node_or_null("/root/GameSession")
	_prev_button.pressed.connect(_on_prev_pressed)
	_next_button.pressed.connect(_on_next_pressed)
	_results_button.pressed.connect(_on_results_pressed)
	_hub_button.pressed.connect(_on_hub_pressed)
	_build_run()
	_refresh()


func setup_screen(p_screen_id: String, p_screen_title: String, p_session: Node) -> void:
	screen_id = p_screen_id
	screen_title = p_screen_title
	session = p_session
	if is_node_ready():
		_build_run()
		_refresh()


func encounter_count() -> int:
	return run_result.encounters.size() if run_result != null else 0


func current_encounter() -> EncounterRecord:
	if run_result == null or run_result.encounters.is_empty():
		return null
	return run_result.encounters[clampi(current_index, 0, run_result.encounters.size() - 1)]


func _build_run() -> void:
	var character := _character()
	if character == null:
		return
	var simulator := TrainingSimulator.new(7)
	simulator.random_source = func() -> float: return 1.0
	run_result = simulator.run(character, route)
	current_index = mini(current_index, maxi(0, encounter_count() - 1))


func _refresh() -> void:
	if not is_node_ready() or run_result == null:
		return
	_summary_label.text = _summary_text()
	_build_floor_map()
	_refresh_encounter()
	_refresh_buttons()


func _summary_text() -> String:
	return "%s · %s route · floor %d / 12 · %s" % [
		_character_name(character_id),
		route.replace("_", " ").capitalize(),
		run_result.floors_cleared,
		"VICTORY" if run_result.victory else "IN PROGRESS"
	]


func _build_floor_map() -> void:
	for child in _floor_grid.get_children():
		child.queue_free()
	for floor in range(1, 13):
		var cell := PanelContainer.new()
		cell.custom_minimum_size = Vector2(96, 58)
		cell.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var stack := VBoxContainer.new()
		stack.alignment = BoxContainer.ALIGNMENT_CENTER
		stack.add_theme_constant_override("separation", 1)
		cell.add_child(stack)
		var encounter := _encounter_for_floor(floor)
		var label := Label.new()
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		label.text = _floor_label(floor, encounter)
		label.add_theme_color_override("font_color", _floor_color(floor, encounter))
		stack.add_child(label)
		_floor_grid.add_child(cell)


func _refresh_encounter() -> void:
	var encounter := current_encounter()
	if encounter == null:
		return
	_encounter_title.text = "Floor %d · %s" % [encounter.floor, encounter.kind.to_upper()]
	_encounter_title.add_theme_color_override("font_color", _encounter_color(encounter))
	_encounter_detail.text = "power %d vs difficulty %d · %s" % [
		encounter.power,
		encounter.difficulty,
		"cleared" if encounter.cleared else "failed"
	]
	_checkpoint_label.text = _checkpoint_text(encounter.floor)
	_log_label.text = "\n".join(run_result.log.slice(0, 3))


func _refresh_buttons() -> void:
	_prev_button.disabled = current_index <= 0
	_next_button.disabled = current_index >= encounter_count() - 1


func _encounter_for_floor(floor: int) -> EncounterRecord:
	if run_result == null:
		return null
	for encounter: EncounterRecord in run_result.encounters:
		if encounter.floor == floor:
			return encounter
	return null


func _floor_label(floor: int, encounter: EncounterRecord) -> String:
	var kind := TrainingSimulator.encounter_kind(floor, route)
	var marker := "▶" if encounter != null and encounter.floor == current_encounter().floor else ""
	if encounter == null:
		return "%sF%d\n%s" % [marker, floor, kind]
	return "%sF%d\n%s %s" % [marker, floor, kind, "✓" if encounter.cleared else "×"]


func _floor_color(floor: int, encounter: EncounterRecord) -> Color:
	if floor % 4 == 0:
		return BOSS_COLOR
	if encounter == null:
		return MUTED_COLOR
	return CLEAR_COLOR if encounter.cleared else FAIL_COLOR


func _encounter_color(encounter: EncounterRecord) -> Color:
	if encounter.kind == "boss":
		return BOSS_COLOR
	return CLEAR_COLOR if encounter.cleared else FAIL_COLOR


func _checkpoint_text(floor: int) -> String:
	var parts: Array[String] = []
	for reward: CheckpointReward in run_result.rewards.checkpoints:
		if reward.floor <= floor:
			parts.append("F%d +%d◆ +%d⬡ +%d%%" % [reward.floor, reward.shards, reward.relic_rolls, reward.echo_quality_bonus])
	if parts.is_empty():
		return "Boss checkpoints: F4 / F8 / F12."
	return "Banked: %s · ⚠ dividend %d◆" % [" | ".join(parts), run_result.rewards.instability_dividend_shards]


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


func _on_prev_pressed() -> void:
	current_index = maxi(0, current_index - 1)
	_refresh()


func _on_next_pressed() -> void:
	current_index = mini(encounter_count() - 1, current_index + 1)
	_refresh()


func _on_results_pressed() -> void:
	navigation_requested.emit("run_results")


func _on_hub_pressed() -> void:
	navigation_requested.emit("home_hub")
