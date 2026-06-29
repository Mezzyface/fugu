extends GutTest

const COLLECTION := preload("res://scenes/character_collection.tscn")


func before_each() -> void:
	GameSession.reset(1)


func _make_screen() -> CharacterCollectionScreen:
	var screen := COLLECTION.instantiate() as CharacterCollectionScreen
	add_child_autofree(screen)
	return screen


func test_shows_owned_count_and_roster_rows() -> void:
	var screen := _make_screen()
	assert_eq(screen.owned_count(), 2)
	assert_string_contains((screen.get_node("%OwnedLabel") as Label).text, "owned 2 / 3")
	var list := screen.get_node("%RosterList") as VBoxContainer
	assert_eq(list.get_child_count(), GameSession.characters.size())


func test_roster_rows_show_rarity_and_resonance() -> void:
	var screen := _make_screen()
	var list := screen.get_node("%RosterList") as VBoxContainer
	var first := list.get_child(0) as Button
	assert_string_contains(first.text, "Legendary")
	assert_true(first.text.contains("◆") or first.text.contains("◇"))


func test_role_filter_limits_visible_characters() -> void:
	var screen := _make_screen()
	var role_index := screen._roles.find("caster")
	screen._on_role_filter_selected(role_index)
	assert_eq(screen.role_filter, "caster")
	assert_eq(screen.visible_character_ids(), ["star_witch"])


func test_sort_modes_change_visible_order() -> void:
	var screen := _make_screen()
	screen.sort_mode = "name"
	var ids := screen.visible_character_ids()
	assert_eq(ids[0], "iron_vow")
	screen.sort_mode = "role"
	ids = screen.visible_character_ids()
	assert_eq(GameSession.get_character(ids[0]).role, "caster")


func test_select_detail_and_navigation_buttons() -> void:
	var screen := _make_screen()
	screen.select_character("rat_squire")
	assert_string_contains((screen.get_node("%DetailLabel") as Label).text, "Pip")
	watch_signals(screen)
	(screen.get_node("%BannerButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["banner_pull"])
	(screen.get_node("%RunButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["run_setup"])
	(screen.get_node("%HubButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["home_hub"])
