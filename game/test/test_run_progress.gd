extends GutTest

const RUN_PROGRESS := preload("res://scenes/run_progress.tscn")


func before_each() -> void:
	GameSession.reset(1)


func _make_screen() -> RunProgressScreen:
	var screen := RUN_PROGRESS.instantiate() as RunProgressScreen
	add_child_autofree(screen)
	return screen


func test_builds_deterministic_twelve_floor_run() -> void:
	var screen := _make_screen()
	assert_eq(screen.encounter_count(), 12)
	assert_eq(screen.run_result.floors_cleared, 12)
	assert_true(screen.run_result.victory)
	assert_eq(screen.current_encounter().kind, TrainingSimulator.encounter_kind(4, screen.route))


func test_floor_map_renders_all_floors_and_boss_gates() -> void:
	var screen := _make_screen()
	var grid := screen.get_node("%FloorGrid") as GridContainer
	assert_eq(grid.get_child_count(), 12)
	var fourth_floor := grid.get_child(3) as PanelContainer
	var label := fourth_floor.get_child(0).get_child(0) as Label
	assert_string_contains(label.text, "boss")


func test_next_and_previous_step_through_encounters() -> void:
	var screen := _make_screen()
	assert_eq(screen.current_index, 3)
	(screen.get_node("%NextButton") as Button).pressed.emit()
	assert_eq(screen.current_index, 4)
	(screen.get_node("%PrevButton") as Button).pressed.emit()
	assert_eq(screen.current_index, 3)


func test_checkpoint_text_updates_after_boss_gate() -> void:
	var screen := _make_screen()
	screen.current_index = 3
	screen._refresh()
	var checkpoint := screen.get_node("%CheckpointLabel") as Label
	assert_string_contains(checkpoint.text, "F4")
	assert_string_contains(checkpoint.text, "+15◆")
	assert_string_contains(checkpoint.text, "+1⬡")


func test_uses_tiny_swords_and_isometric_textures() -> void:
	var screen := _make_screen()
	var unit := screen.get_node("Margin/Root/Body/MapPanel/MapMargin/MapStack/ArtStrip/UnitSprite") as TextureRect
	var enemy := screen.get_node("Margin/Root/Body/MapPanel/MapMargin/MapStack/ArtStrip/EnemySprite") as TextureRect
	var terrain := screen.get_node("Margin/Root/Body/MapPanel/MapMargin/MapStack/ArtStrip/TerrainSprite") as TextureRect
	assert_not_null(unit.texture)
	assert_not_null(enemy.texture)
	assert_not_null(terrain.texture)


func test_results_and_hub_buttons_request_navigation() -> void:
	var screen := _make_screen()
	watch_signals(screen)
	(screen.get_node("%ResultsButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["run_results"])
	(screen.get_node("%HubButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["home_hub"])
