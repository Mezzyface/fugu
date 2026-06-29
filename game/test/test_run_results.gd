extends GutTest

const RUN_RESULTS := preload("res://scenes/run_results.tscn")


func before_each() -> void:
	GameSession.reset(1)


func _make_screen() -> RunResultsScreen:
	var screen := RUN_RESULTS.instantiate() as RunResultsScreen
	add_child_autofree(screen)
	return screen


func test_renders_victory_echo_and_rewards() -> void:
	var screen := _make_screen()
	assert_true(screen.run_result.victory)
	var outcome := screen.get_node("%OutcomeLabel") as Label
	assert_eq(outcome.text, "VICTORY")
	var rewards := screen.get_node("%RewardsLabel") as Label
	assert_string_contains(rewards.text, "banked shards")
	assert_string_contains(rewards.text, "relic rolls")
	assert_string_contains(rewards.text, "echo quality")


func test_stats_render_big_number_format() -> void:
	var screen := _make_screen()
	var grid := screen.get_node("%StatsGrid") as GridContainer
	var found := false
	for child in grid.get_children():
		if child is Label and (child as Label).text.contains("·10^"):
			found = true
	assert_true(found)


func test_skills_traits_lineage_and_instability_render() -> void:
	var screen := _make_screen()
	assert_string_contains((screen.get_node("%SkillsLabel") as Label).text, "Skills:")
	assert_string_contains((screen.get_node("%TraitsLabel") as Label).text, "Traits:")
	var lineage := screen.get_node("%LineageLabel") as Label
	assert_string_contains(lineage.text, "Lineage depth")
	assert_string_contains(lineage.text, "instability")


func test_bank_echo_adds_to_echo_pool_once() -> void:
	var screen := _make_screen()
	assert_eq(GameSession.echo_pool.size(), 0)
	var record := screen.bank_echo()
	assert_not_null(record)
	assert_eq(GameSession.echo_pool.size(), 1)
	assert_eq(GameSession.echo_pool.records[0].echo, screen.run_result.echo)
	screen.bank_echo()
	assert_eq(GameSession.echo_pool.size(), 1, "bank button is idempotent")


func test_buttons_request_forge_and_hub_navigation() -> void:
	var screen := _make_screen()
	watch_signals(screen)
	(screen.get_node("%ForgeButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["relic_forge"])
	assert_gt(GameSession.relic_rolls, 0)
	(screen.get_node("%HubButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["home_hub"])
