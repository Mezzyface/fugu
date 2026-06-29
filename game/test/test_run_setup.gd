extends GutTest

const RUN_SETUP := preload("res://scenes/run_setup.tscn")


func before_each() -> void:
	GameSession.reset(1)
	_seed_echo_pool()


func _make_screen() -> RunSetupScreen:
	var screen := RUN_SETUP.instantiate() as RunSetupScreen
	add_child_autofree(screen)
	return screen


func _seed_echo_pool() -> void:
	GameSession.echo_pool.bank_echo(
		FrozenEcho.new(
			"star_witch",
			{"hp": BigStat.new(500), "atk": BigStat.new(240), "def": BigStat.new(70), "spd": BigStat.new(90)},
			PackedStringArray(["Nova Hex"]),
			PackedStringArray(["magic"]),
			1,
			0
		),
		"star"
	)
	GameSession.echo_pool.bank_echo(
		FrozenEcho.new(
			"iron_vow",
			{"hp": BigStat.new(1200), "atk": BigStat.new(120), "def": BigStat.new(240), "spd": BigStat.new(50)},
			PackedStringArray(["Oath Wall"]),
			PackedStringArray(["armor"]),
			2,
			1
		),
		"shield"
	)
	GameSession.echo_pool.bank_echo(
		FrozenEcho.new(
			"rat_squire",
			{"hp": BigStat.new(650), "atk": BigStat.new(130), "def": BigStat.new(90), "spd": BigStat.new(140)},
			PackedStringArray(["Skitter Strike"]),
			PackedStringArray(["beast"]),
			0,
			0
		),
		"rat"
	)


func test_defaults_to_featured_character_and_balanced_route() -> void:
	var screen := _make_screen()
	assert_eq(screen.selected_character_id, GameSession.featured_banner_ids()[0])
	assert_eq(screen.selected_route, "balanced")
	var detail := screen.get_node("%RouteDetailLabel") as Label
	assert_string_contains(detail.text, "Balanced")
	assert_string_contains(detail.text, "growth 112%")


func test_selecting_parent_updates_projection_from_training_simulator() -> void:
	var screen := _make_screen()
	var first_button := (screen.get_node("%ParentList") as VBoxContainer).get_child(0) as Button
	var base_projection := screen.projected_start()
	first_button.pressed.emit()
	assert_eq(screen.selected_parent_count(), 1)
	var parent_projection := screen.projected_start()
	assert_gt(parent_projection[1], base_projection[1], "lineage depth increases with a parent")
	var selected_label := screen.get_node("%SelectedParentsLabel") as Label
	assert_string_contains(selected_label.text, "Parents:")
	var instability_label := screen.get_node("%InstabilityLabel") as Label
	assert_string_contains(instability_label.text, "instability")


func test_prevents_more_than_two_parents() -> void:
	var screen := _make_screen()
	var list := screen.get_node("%ParentList") as VBoxContainer
	for index in 3:
		(list.get_child(index) as Button).pressed.emit()
	assert_eq(screen.selected_parent_count(), TrainingSimulator.MAX_PARENTS)
	assert_string_contains(screen.last_message, "Parent cap reached")


func test_route_selector_changes_projected_route() -> void:
	var screen := _make_screen()
	var selector := screen.get_node("%RouteSelector") as OptionButton
	var route_index := 1
	selector.selected = route_index
	selector.item_selected.emit(route_index)
	assert_eq(screen.selected_route, TrainingSimulator.available_routes()[route_index])
	var detail := screen.get_node("%RouteDetailLabel") as Label
	assert_string_contains(detail.text, "Boss Rush")


func test_stats_grid_uses_big_number_format() -> void:
	var screen := _make_screen()
	var grid := screen.get_node("%StatsGrid") as GridContainer
	var found_big_number := false
	for child in grid.get_children():
		if child is Label and (child as Label).text.contains("·10^"):
			found_big_number = true
	assert_true(found_big_number, "projected stats render mantissa·10^magnitude")


func test_start_and_hub_buttons_request_navigation() -> void:
	var screen := _make_screen()
	watch_signals(screen)
	(screen.get_node("%StartButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["run_progress"])
	(screen.get_node("%HubButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["home_hub"])
