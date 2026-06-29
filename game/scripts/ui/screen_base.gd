class_name ScreenBase
extends Control

signal navigation_requested(screen_id: String)

@export var screen_id: String = ""
@export var screen_title: String = ""

var session: Node
var _built := false
var _title_label: Label
var _summary_label: Label
var _content_label: Label
var _featured_label: Label
var _hub_button: Button

const TITLE_COLOR := Color(0.854902, 0.321569, 0.364706, 1.0)
const BODY_COLOR := Color(0.94, 0.94, 0.90, 1.0)
const MUTED_COLOR := Color(0.776471, 0.788235, 0.823529, 1.0)


func _ready() -> void:
	_build_layout()
	_refresh()


func setup_screen(p_screen_id: String, p_screen_title: String, p_session: Node) -> void:
	screen_id = p_screen_id
	screen_title = p_screen_title
	session = p_session
	if is_node_ready():
		_refresh()


func _build_layout() -> void:
	if _built:
		return
	_built = true
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 28)
	margin.add_theme_constant_override("margin_top", 24)
	margin.add_theme_constant_override("margin_right", 28)
	margin.add_theme_constant_override("margin_bottom", 24)
	add_child(margin)
	var content := VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 12)
	margin.add_child(content)
	_title_label = Label.new()
	_title_label.theme_type_variation = &"TitleLabel"
	_title_label.add_theme_color_override("font_color", TITLE_COLOR)
	content.add_child(_title_label)
	_summary_label = Label.new()
	_summary_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_summary_label.add_theme_color_override("font_color", BODY_COLOR)
	content.add_child(_summary_label)
	_featured_label = Label.new()
	_featured_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_featured_label.add_theme_color_override("font_color", BODY_COLOR)
	content.add_child(_featured_label)
	_content_label = Label.new()
	_content_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_content_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_content_label.add_theme_color_override("font_color", MUTED_COLOR)
	content.add_child(_content_label)
	_hub_button = Button.new()
	_hub_button.text = "Back to Hub"
	_hub_button.pressed.connect(_request_hub)
	content.add_child(_hub_button)


func _refresh() -> void:
	if not _built:
		return
	_title_label.text = screen_title if screen_title != "" else screen_id.capitalize()
	_summary_label.text = _session_summary()
	_featured_label.text = _featured_summary()
	_content_label.text = "Screen contract: %s reads GameSession and requests navigation through navigation_requested." % screen_id
	_hub_button.visible = screen_id != "home_hub"


func _session_summary() -> String:
	if session != null and session.has_method("currency_summary"):
		return session.currency_summary()
	return "GameSession unavailable"


func _featured_summary() -> String:
	if session == null or not session.has_method("featured_banner_ids"):
		return "Featured banners unavailable"
	var ids: Array = session.featured_banner_ids()
	return "Featured: %s" % ", ".join(ids)


func _request_hub() -> void:
	navigation_requested.emit("home_hub")
