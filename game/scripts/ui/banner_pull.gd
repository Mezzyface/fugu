class_name BannerPullScreen
extends Control
## Screen 03 — Banner / Pull (wireframes §03).
##
## The gacha pull screen for a single character's banner. A portrait panel names
## the character and its rarity; a pity bar visualises
## [member BannerState.pulls_since_legendary] against the banner's
## `hard_pity_target` (90 permanent · 80 featured, soft pity from 70/60); a
## resonance track shows the ◇◇◇◇ nodes (20/40/80/120 shards) with the next
## affordable upgrade. Pull ×1 calls [method GachaSystem.pull] and Pull ×10 calls
## [method GachaSystem.pull_batch]; the latest outcome renders a rarity badge, a
## pity-reset highlight, and the shards gained. Upgrade Resonance spends banner
## shards through [method GachaSystem.upgrade_resonance] — it never touches base
## stats.
##
## Which banner is shown defaults to the week's lead featured character but can be
## switched with the selector, so both featured (hard 80) and permanent (hard 90)
## tunings are reachable. Like every screen it never navigates directly: it emits
## [signal navigation_requested] and the navigation root (`scripts/main.gd`)
## performs the switch.

## Emitted when the hub button is pressed; the navigation root listens and
## switches screens.
signal navigation_requested(screen_id: String)

const TITLE_COLOR := Color(0.854902, 0.321569, 0.364706, 1.0)  # eugenia_red
const BODY_COLOR := Color(0.94, 0.94, 0.90, 1.0)
const MUTED_COLOR := Color(0.776471, 0.788235, 0.823529, 1.0)

## Rarity → accent colour ladder (common→legendary): muted, cobalt green, lilac,
## maple gold. Mirrors the art-direction palette.
const RARITY_COLORS: Array[Color] = [
	Color(0.776471, 0.788235, 0.823529, 1.0),  # common — muted
	Color(0.588235, 0.819608, 0.666667, 1.0),  # rare — cobalt green
	Color(0.725490, 0.517647, 0.686275, 1.0),  # epic — lilac
	Color(0.772549, 0.623529, 0.419608, 1.0),  # legendary — maple gold
]

## Featured-banner slots per week, matching screens 01/02 and the design.
const SLOTS_PER_WEEK: int = 3

@export var screen_id: String = "banner_pull"
@export var screen_title: String = "Banner / Pull"

## The state source. Set by the navigation root via [method setup_screen]; falls
## back to the [GameSession] autoload when the scene is opened standalone.
var session: Node

## Currently shown banner id; defaults to the week's lead featured character.
var banner_character_id: String = ""

@onready var _banner_selector: OptionButton = %BannerSelector
@onready var _portrait_panel: PanelContainer = %PortraitPanel
@onready var _portrait_name: Label = %PortraitName
@onready var _portrait_rarity: Label = %PortraitRarity
@onready var _portrait_role: Label = %PortraitRole
@onready var _pity_bar: ProgressBar = %PityBar
@onready var _pity_label: Label = %PityLabel
@onready var _resonance_track: HBoxContainer = %ResonanceTrack
@onready var _resonance_shards: Label = %ResonanceShards
@onready var _resonance_button: Button = %ResonanceButton
@onready var _result_badge: Label = %ResultBadge
@onready var _result_detail: Label = %ResultDetail
@onready var _pull1_button: Button = %Pull1Button
@onready var _pull10_button: Button = %Pull10Button
@onready var _hub_button: Button = %HubButton

# Roster ids in selector order, parallel to the OptionButton items.
var _selector_ids: Array[String] = []


func _ready() -> void:
	if session == null:
		session = get_node_or_null("/root/GameSession")
	_pull1_button.pressed.connect(_on_pull1_pressed)
	_pull10_button.pressed.connect(_on_pull10_pressed)
	_resonance_button.pressed.connect(_on_resonance_pressed)
	_hub_button.pressed.connect(_on_hub_pressed)
	_banner_selector.item_selected.connect(_on_banner_selected)
	_connect_session()
	_populate_selector()
	_clear_result()
	_refresh()


## Navigation-root contract (see `scripts/main.gd`): inject the screen id, title,
## and shared [GameSession] when this screen is mounted.
func setup_screen(p_screen_id: String, p_screen_title: String, p_session: Node) -> void:
	screen_id = p_screen_id
	screen_title = p_screen_title
	session = p_session
	if is_node_ready():
		_connect_session()
		_populate_selector()
		_refresh()


func _connect_session() -> void:
	if session != null and session.has_signal("state_changed"):
		if not session.state_changed.is_connected(_refresh):
			session.state_changed.connect(_refresh)


## Fill the selector with the roster in stable id order and select the week's lead
## featured banner (or the first roster id if nothing is featured).
func _populate_selector() -> void:
	_banner_selector.clear()
	_selector_ids.clear()
	for character_id: String in _sorted_character_ids():
		_selector_ids.append(character_id)
		_banner_selector.add_item(_character_name(character_id))
	if _selector_ids.is_empty():
		banner_character_id = ""
		return
	if not _selector_ids.has(banner_character_id):
		banner_character_id = _default_banner_id()
	_banner_selector.selected = maxi(0, _selector_ids.find(banner_character_id))


func _default_banner_id() -> String:
	var featured: Array = _featured_ids()
	if not featured.is_empty():
		return featured[0]
	return _selector_ids[0]


func _refresh() -> void:
	if not is_node_ready() or banner_character_id == "":
		return
	_refresh_portrait()
	_refresh_pity()
	_refresh_resonance()
	_refresh_buttons()


func _refresh_portrait() -> void:
	var character: CharacterDef = _character()
	var featured := _is_featured(banner_character_id)
	_portrait_name.text = _character_name(banner_character_id).to_upper()
	var rarity_text := _rarity_label(banner_character_id).to_upper()
	_portrait_rarity.text = "★ FEATURED · %s" % rarity_text if featured else rarity_text
	var accent := _rarity_color(banner_character_id)
	_portrait_name.add_theme_color_override("font_color", accent)
	_portrait_rarity.add_theme_color_override("font_color", accent)
	_portrait_role.text = character.role.capitalize() if character != null else ""
	_tint_panel(_portrait_panel, accent)


func _refresh_pity() -> void:
	var banner: BannerState = _banner_state()
	var featured := _is_featured(banner_character_id)
	var tuning := GachaSystem.pity_tuning(featured)
	var hard: int = tuning["hard_pity_target"]
	var soft: int = tuning["soft_pity_start"]
	var pity: int = banner.pulls_since_legendary if banner != null else 0
	_pity_bar.max_value = hard
	_pity_bar.value = pity
	_pity_label.text = "pity %d / %d   (soft %d · hard %d)" % [pity, hard, soft, hard]


## Rebuild the ◇◇◇◇ resonance nodes from [method GachaSystem.resonance_preview]:
## ◆ for unlocked nodes, ◇ for locked, with each node's cost and label.
func _refresh_resonance() -> void:
	for child in _resonance_track.get_children():
		child.queue_free()
	var banner: BannerState = _banner_state()
	for entry: Dictionary in _resonance_preview():
		var unlocked: bool = entry["unlocked"]
		var node := Label.new()
		node.text = "%s\n%d ◆\n%s" % ["◆" if unlocked else "◇", int(entry["cost"]), entry["node"]]
		node.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		node.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		node.add_theme_color_override(
			"font_color", _rarity_color(banner_character_id) if unlocked else MUTED_COLOR
		)
		_resonance_track.add_child(node)
	var shards: int = banner.shards if banner != null else 0
	_resonance_shards.text = "◆ %d resonance shards" % shards


func _refresh_buttons() -> void:
	var next_cost: Variant = _next_resonance_cost()
	var banner: BannerState = _banner_state()
	var shards: int = banner.shards if banner != null else 0
	if next_cost == null:
		_resonance_button.text = "Resonance complete"
		_resonance_button.disabled = true
	else:
		var cost: int = int(next_cost)
		_resonance_button.text = "Upgrade Resonance  (%d ◆)" % cost
		_resonance_button.disabled = shards < cost


func _on_banner_selected(index: int) -> void:
	if index < 0 or index >= _selector_ids.size():
		return
	banner_character_id = _selector_ids[index]
	_clear_result()
	_refresh()


func _on_pull1_pressed() -> void:
	if session == null or session.gacha_system == null:
		return
	var result: PullResult = session.gacha_system.pull(
		banner_character_id, _is_featured(banner_character_id)
	)
	_show_pull_result(result)
	_refresh()


func _on_pull10_pressed() -> void:
	if session == null or session.gacha_system == null:
		return
	var results: Array = session.gacha_system.pull_batch(
		banner_character_id, 10, _is_featured(banner_character_id)
	)
	_show_batch_result(results)
	_refresh()


func _on_resonance_pressed() -> void:
	if session == null or session.gacha_system == null:
		return
	var upgrade: ResonanceUpgrade = session.gacha_system.upgrade_resonance(banner_character_id)
	if upgrade == null:
		return
	_result_badge.text = "RESONANCE  ◆ Lv %d" % upgrade.level
	_result_badge.add_theme_color_override("font_color", _rarity_color(banner_character_id))
	_result_detail.text = (
		"Unlocked “%s” for %d ◆ · %d ◆ left" % [upgrade.node, upgrade.cost, upgrade.remaining_shards]
	)
	_result_detail.add_theme_color_override("font_color", BODY_COLOR)
	_refresh()


func _on_hub_pressed() -> void:
	navigation_requested.emit("home_hub")


func _show_pull_result(result: PullResult) -> void:
	var accent := RARITY_COLORS[result.rarity]
	_result_badge.text = Rarity.to_string_value(result.rarity).to_upper()
	_result_badge.add_theme_color_override("font_color", accent)
	var detail := "+%d ◆ resonance shards" % result.shards_gained
	if result.pity_reset:
		detail = "✦ PITY RESET → LEGENDARY ✦   %s" % detail
		_result_detail.add_theme_color_override("font_color", TITLE_COLOR)
	else:
		_result_detail.add_theme_color_override("font_color", BODY_COLOR)
	_result_detail.text = detail


func _show_batch_result(results: Array) -> void:
	if results.is_empty():
		_clear_result()
		return
	var best := Rarity.COMMON
	var total_shards := 0
	var legendaries := 0
	for result: PullResult in results:
		best = maxi(best, result.rarity)
		total_shards += result.shards_gained
		if result.pity_reset:
			legendaries += 1
	_result_badge.text = "×%d · BEST %s" % [results.size(), Rarity.to_string_value(best).to_upper()]
	_result_badge.add_theme_color_override("font_color", RARITY_COLORS[best])
	var detail := "+%d ◆ shards" % total_shards
	if legendaries > 0:
		detail = "✦ %d PITY RESET ✦   %s" % [legendaries, detail]
		_result_detail.add_theme_color_override("font_color", TITLE_COLOR)
	else:
		_result_detail.add_theme_color_override("font_color", BODY_COLOR)
	_result_detail.text = detail


func _clear_result() -> void:
	_result_badge.text = "—"
	_result_badge.add_theme_color_override("font_color", MUTED_COLOR)
	_result_detail.text = "Pull to roll · base rates 79.5 / 15 / 4 / 1.5 %"
	_result_detail.add_theme_color_override("font_color", MUTED_COLOR)


func _tint_panel(panel: PanelContainer, accent: Color) -> void:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.13, 0.145, 0.19, 1.0)
	style.border_color = accent
	style.set_border_width_all(2)
	style.set_corner_radius_all(8)
	style.set_content_margin_all(20)
	panel.add_theme_stylebox_override("panel", style)


func _sorted_character_ids() -> Array:
	if session == null or not ("characters" in session):
		return []
	var ids: Array = (session.characters as Dictionary).keys()
	ids.sort()
	return ids


func _featured_ids() -> Array:
	if session != null and session.has_method("featured_banner_ids"):
		return session.featured_banner_ids(SLOTS_PER_WEEK)
	return []


func _is_featured(character_id: String) -> bool:
	return _featured_ids().has(character_id)


func _character() -> CharacterDef:
	if session != null and session.has_method("get_character"):
		return session.get_character(banner_character_id)
	return null


func _banner_state() -> BannerState:
	if session != null and session.has_method("get_banner_state"):
		return session.get_banner_state(banner_character_id)
	return null


func _resonance_preview() -> Array:
	if session != null and session.gacha_system != null:
		return session.gacha_system.resonance_preview(banner_character_id)
	return []


func _next_resonance_cost() -> Variant:
	if session != null and session.gacha_system != null:
		return session.gacha_system.next_resonance_cost(banner_character_id)
	return null


func _character_name(character_id: String) -> String:
	if session != null and session.has_method("get_character"):
		var character: CharacterDef = session.get_character(character_id)
		if character != null:
			return character.name
	return character_id.capitalize()


func _rarity_label(character_id: String) -> String:
	var character: CharacterDef = null
	if session != null and session.has_method("get_character"):
		character = session.get_character(character_id)
	if character != null:
		return Rarity.to_string_value(character.rarity)
	return "—"


func _rarity_color(character_id: String) -> Color:
	var character: CharacterDef = null
	if session != null and session.has_method("get_character"):
		character = session.get_character(character_id)
	if character != null:
		return RARITY_COLORS[character.rarity]
	return MUTED_COLOR
