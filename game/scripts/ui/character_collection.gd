class_name CharacterCollectionScreen
extends Control

signal navigation_requested(screen_id: String)

const TITLE_COLOR := Color(0.854902, 0.321569, 0.364706, 1.0)
const BODY_COLOR := Color(0.94, 0.94, 0.90, 1.0)
const MUTED_COLOR := Color(0.776471, 0.788235, 0.823529, 1.0)
const OWNED_COLOR := Color(0.588235, 0.819608, 0.666667, 1.0)
const LEGENDARY_COLOR := Color(0.772549, 0.623529, 0.419608, 1.0)

@export var screen_id: String = "character_collection"
@export var screen_title: String = "Character Collection"

var session: Node
var role_filter: String = "all"
var sort_mode: String = "rarity"
var selected_character_id: String = ""

@onready var _owned_label: Label = %OwnedLabel
@onready var _role_filter: OptionButton = %RoleFilter
@onready var _sort_selector: OptionButton = %SortSelector
@onready var _roster_list: VBoxContainer = %RosterList
@onready var _detail_label: Label = %DetailLabel
@onready var _banner_button: Button = %BannerButton
@onready var _run_button: Button = %RunButton
@onready var _hub_button: Button = %HubButton

var _roles: Array[String] = ["all"]
var _sort_modes: Array[String] = ["rarity", "name", "role"]


func _ready() -> void:
	if session == null:
		session = get_node_or_null("/root/GameSession")
	_role_filter.item_selected.connect(_on_role_filter_selected)
	_sort_selector.item_selected.connect(_on_sort_selected)
	_banner_button.pressed.connect(_on_banner_pressed)
	_run_button.pressed.connect(_on_run_pressed)
	_hub_button.pressed.connect(_on_hub_pressed)
	_seed_demo_progress()
	_populate_controls()
	_refresh()


func setup_screen(p_screen_id: String, p_screen_title: String, p_session: Node) -> void:
	screen_id = p_screen_id
	screen_title = p_screen_title
	session = p_session
	if is_node_ready():
		_seed_demo_progress()
		_populate_controls()
		_refresh()


func visible_character_ids() -> Array[String]:
	var ids: Array[String] = []
	for character_id: String in _characters().keys():
		var character: CharacterDef = _characters()[character_id]
		if role_filter == "all" or character.role == role_filter:
			ids.append(character_id)
	ids.sort_custom(_compare_ids)
	return ids


func owned_count() -> int:
	var count := 0
	for id: String in _characters().keys():
		if _is_owned(id):
			count += 1
	return count


func select_character(character_id: String) -> void:
	selected_character_id = character_id
	_refresh_detail()


func _populate_controls() -> void:
	_roles = ["all"]
	for id: String in _characters().keys():
		var role: String = (_characters()[id] as CharacterDef).role
		if not _roles.has(role):
			_roles.append(role)
	_roles.sort()
	_role_filter.clear()
	for role: String in _roles:
		_role_filter.add_item(role.capitalize())
	_role_filter.selected = maxi(0, _roles.find(role_filter))
	_sort_selector.clear()
	for mode: String in _sort_modes:
		_sort_selector.add_item(mode.capitalize())
	_sort_selector.selected = maxi(0, _sort_modes.find(sort_mode))


func _refresh() -> void:
	if not is_node_ready():
		return
	_owned_label.text = "owned %d / %d" % [owned_count(), _characters().size()]
	_build_roster()
	if selected_character_id == "" and not visible_character_ids().is_empty():
		selected_character_id = visible_character_ids()[0]
	_refresh_detail()


func _build_roster() -> void:
	for child in _roster_list.get_children():
		child.queue_free()
	for id: String in visible_character_ids():
		_roster_list.add_child(_row_button(id))


func _row_button(id: String) -> Button:
	var character: CharacterDef = _characters()[id]
	var button := Button.new()
	button.alignment = HORIZONTAL_ALIGNMENT_LEFT
	button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	button.custom_minimum_size = Vector2(0, 86)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.text = "%s %s · %s · %s · %s" % [
		"✓" if _is_owned(id) else "🔒",
		character.name,
		Rarity.to_string_value(character.rarity).capitalize(),
		character.role.capitalize(),
		_resonance_text(id)
	]
	button.add_theme_color_override("font_color", OWNED_COLOR if _is_owned(id) else MUTED_COLOR)
	button.pressed.connect(select_character.bind(id))
	return button


func _refresh_detail() -> void:
	var character := _selected_character()
	if character == null:
		_detail_label.text = "Select a character."
		return
	_detail_label.text = "%s\n%s · %s\n%s\nBase: HP %s · ATK %s · DEF %s · SPD %s" % [
		character.name,
		Rarity.to_string_value(character.rarity).capitalize(),
		character.role.capitalize(),
		"Owned" if _is_owned(character.id) else "Locked — pull from banner",
		_format_stat(character.base_stats["hp"]),
		_format_stat(character.base_stats["atk"]),
		_format_stat(character.base_stats["def"]),
		_format_stat(character.base_stats["spd"])
	]


func _compare_ids(a: String, b: String) -> bool:
	var left: CharacterDef = _characters()[a]
	var right: CharacterDef = _characters()[b]
	match sort_mode:
		"name":
			return left.name < right.name
		"role":
			return left.role < right.role if left.role != right.role else left.name < right.name
		_:
			return left.rarity > right.rarity if left.rarity != right.rarity else left.name < right.name


func _resonance_text(id: String) -> String:
	var banner := _banner(id)
	var level := banner.resonance_level if banner != null else 0
	var marks := ""
	for i in 4:
		marks += "◆" if i < level else "◇"
	return marks


func _is_owned(id: String) -> bool:
	var banner := _banner(id)
	return banner != null and (banner.shards > 0 or banner.resonance_level > 0 or id == "iron_vow")


func _banner(id: String) -> BannerState:
	if session != null and session.has_method("get_banner_state"):
		return session.get_banner_state(id)
	return null


func _characters() -> Dictionary:
	return session.characters if session != null and "characters" in session else CharacterCatalog.sample_characters()


func _selected_character() -> CharacterDef:
	return _characters().get(selected_character_id, null)


func _format_stat(stat: BigStat) -> String:
	if session != null and session.has_method("format_stat"):
		return session.format_stat(stat)
	var normalized := stat.normalized()
	return "%d·10^%d" % [normalized.mantissa, normalized.magnitude]


func _seed_demo_progress() -> void:
	if session == null:
		return
	var iron := _banner("iron_vow")
	if iron != null:
		iron.shards = maxi(iron.shards, 20)
		iron.resonance_level = maxi(iron.resonance_level, 2)
	var witch := _banner("star_witch")
	if witch != null:
		witch.shards = maxi(witch.shards, 5)
		witch.resonance_level = maxi(witch.resonance_level, 1)


func _on_role_filter_selected(index: int) -> void:
	if index >= 0 and index < _roles.size():
		role_filter = _roles[index]
		_refresh()


func _on_sort_selected(index: int) -> void:
	if index >= 0 and index < _sort_modes.size():
		sort_mode = _sort_modes[index]
		_refresh()


func _on_banner_pressed() -> void:
	navigation_requested.emit("banner_pull")


func _on_run_pressed() -> void:
	navigation_requested.emit("run_setup")


func _on_hub_pressed() -> void:
	navigation_requested.emit("home_hub")
