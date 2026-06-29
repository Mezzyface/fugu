class_name BannerSelectScreen
extends Control
## Screen 02 — Banner Select (wireframes §02).
##
## The annual-rotation gallery. A header names the current week's featured group
## ("Week N / 52"), then a gallery of banner cards shows every roster character
## with its state for this week — ★ featured or permanent — plus how many weeks
## of the year it is featured (resolved through
## [method GachaSystem.annual_featured_counts]). The schedule guarantees every
## character is featured at least once per year
## ([method GachaSystem.missing_annual_featured_banners] is empty), which the
## footer states plainly. There is deliberately no countdown or urgency copy.
##
## Like every screen it never navigates directly: tapping a banner emits
## [signal navigation_requested] with `"banner_pull"` and the navigation root
## (`scripts/main.gd`) performs the switch.

## Emitted when a banner card or the hub button is pressed; the navigation root
## listens and switches screens.
signal navigation_requested(screen_id: String)

const BODY_COLOR := Color(0.94, 0.94, 0.90, 1.0)
const MUTED_COLOR := Color(0.776471, 0.788235, 0.823529, 1.0)
const FEATURED_COLOR := Color(0.72549, 0.517647, 0.686275, 1.0)  # lilac

## Slots featured each week, matching the design's `featured_schedule(52, 3)`.
const SLOTS_PER_WEEK: int = 3

@export var screen_id: String = "banner_select"
@export var screen_title: String = "Banner Select"

## The state source. Set by the navigation root via [method setup_screen]; falls
## back to the [GameSession] autoload when the scene is opened standalone.
var session: Node

@onready var _week_title: Label = %WeekTitle
@onready var _week_list: Label = %WeekList
@onready var _banner_grid: GridContainer = %BannerGrid
@onready var _invariant_label: Label = %InvariantLabel
@onready var _hub_button: Button = %HubButton


func _ready() -> void:
	if session == null:
		session = get_node_or_null("/root/GameSession")
	_hub_button.pressed.connect(_on_hub_pressed)
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


func _refresh() -> void:
	if not is_node_ready():
		return
	_week_title.text = _week_title_text()
	_week_list.text = _week_list_text()
	_build_banner_cards()
	_invariant_label.text = _invariant_text()


func _week_title_text() -> String:
	return (
		"★ Featured group — Week %d / %d · %d banners"
		% [_current_week(), _max_week(), _featured_ids().size()]
	)


func _week_list_text() -> String:
	var ids: Array = _featured_ids()
	if ids.is_empty():
		return "No featured banners this week."
	var names: Array[String] = []
	for banner_id: String in ids:
		names.append(_character_name(banner_id))
	return "   ·   ".join(names)


## Build one tappable card per roster character, in stable id order, marking the
## ones featured this week. Rebuilt on every refresh so week changes restyle the
## ★ markers.
func _build_banner_cards() -> void:
	for child in _banner_grid.get_children():
		child.queue_free()
	var featured := _featured_ids()
	var counts := _annual_counts()
	for character_id: String in _sorted_character_ids():
		var is_featured := featured.has(character_id)
		var annual: int = int(counts.get(character_id, 0))
		var card := Button.new()
		card.text = _card_text(character_id, is_featured, annual)
		card.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		card.alignment = HORIZONTAL_ALIGNMENT_LEFT
		card.clip_text = false
		card.custom_minimum_size = Vector2(0, 96)
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		card.add_theme_color_override("font_color", FEATURED_COLOR if is_featured else BODY_COLOR)
		card.tooltip_text = "Open %s's banner" % _character_name(character_id)
		card.pressed.connect(_on_banner_pressed.bind(character_id))
		_banner_grid.add_child(card)


func _card_text(character_id: String, is_featured: bool, annual_count: int) -> String:
	var state := "★ Featured this week" if is_featured else "Permanent banner"
	return (
		"%s\n%s\n%s · featured %d weeks this year"
		% [_character_name(character_id), state, _rarity_label(character_id), annual_count]
	)


## Plain statement of the rotation invariant — no countdowns, no urgency. Falls
## back to a neutral note if the schedule ever leaves a character out.
func _invariant_text() -> String:
	var missing := _missing_annual_featured()
	if missing.is_empty():
		return "Every character is featured at least once each year — take your time."
	return "Rotation gap: %d character(s) not yet scheduled this year." % missing.size()


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


func _annual_counts() -> Dictionary:
	if session != null and session.gacha_system != null:
		return session.gacha_system.annual_featured_counts(_max_week(), SLOTS_PER_WEEK)
	return {}


func _missing_annual_featured() -> Array:
	if session != null and session.gacha_system != null:
		return session.gacha_system.missing_annual_featured_banners(_max_week(), SLOTS_PER_WEEK)
	return []


func _character_name(banner_id: String) -> String:
	if session != null and session.has_method("get_character"):
		var character: CharacterDef = session.get_character(banner_id)
		if character != null:
			return character.name
	return banner_id.capitalize()


func _rarity_label(banner_id: String) -> String:
	if session != null and session.has_method("get_character"):
		var character: CharacterDef = session.get_character(banner_id)
		if character != null:
			return Rarity.to_string_value(character.rarity).capitalize()
	return "—"


func _current_week() -> int:
	if session != null and "current_week" in session:
		return session.current_week
	return 1


func _max_week() -> int:
	return 52


func _on_banner_pressed(_banner_id: String) -> void:
	navigation_requested.emit("banner_pull")


func _on_hub_pressed() -> void:
	navigation_requested.emit("home_hub")
