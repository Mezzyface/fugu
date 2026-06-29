extends GutTest

const RELIC_FORGE_SCREEN := preload("res://scenes/relic_forge_screen.tscn")


func before_each() -> void:
	GameSession.reset(1)


func _make_screen() -> RelicForgeScreen:
	var screen := RELIC_FORGE_SCREEN.instantiate() as RelicForgeScreen
	add_child_autofree(screen)
	return screen


func test_defaults_to_available_rolls_and_forged_relics() -> void:
	var screen := _make_screen()
	assert_eq(GameSession.relic_rolls, 6)
	assert_eq(screen.forged_relics.size(), 3)
	assert_string_contains((screen.get_node("%RollsLabel") as Label).text, "6")
	assert_string_contains((screen.get_node("%OddsLabel") as Label).text, "Common 60%")


func test_forge_spends_relic_rolls() -> void:
	var screen := _make_screen()
	var before := GameSession.relic_rolls
	var relics := screen.forge_relics(2)
	assert_eq(relics.size(), 2)
	assert_eq(GameSession.relic_rolls, before - 2)


func test_apply_relics_boosts_preview_without_mutating_source() -> void:
	var screen := _make_screen()
	var original := screen.target_echo.stats.duplicate(true)
	var boosted := screen.apply_relics_to_echo()
	assert_false(boosted.is_empty())
	assert_eq(screen.target_echo.stats, original)
	var changed := false
	for key: String in boosted:
		if str(boosted[key]) != str(original[key]):
			changed = true
	assert_true(changed, "at least one stat preview is boosted")


func test_stats_grid_uses_big_number_format() -> void:
	var screen := _make_screen()
	var grid := screen.get_node("%StatsGrid") as GridContainer
	var found := false
	for child in grid.get_children():
		if child is Label and (child as Label).text.contains("·10^"):
			found = true
	assert_true(found)


func test_navigation_buttons() -> void:
	var screen := _make_screen()
	watch_signals(screen)
	(screen.get_node("%ResultsButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["run_results"])
	(screen.get_node("%HubButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["home_hub"])
