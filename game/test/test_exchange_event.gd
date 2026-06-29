extends GutTest

const EXCHANGE_EVENT := preload("res://scenes/exchange_event.tscn")


func before_each() -> void:
	GameSession.reset(1)


func _make_screen() -> ExchangeEventScreen:
	var screen := EXCHANGE_EVENT.instantiate() as ExchangeEventScreen
	add_child_autofree(screen)
	return screen


func test_seeds_records_and_excludes_favorites_from_default_selection() -> void:
	var screen := _make_screen()
	assert_eq(GameSession.echo_pool.size(), 3)
	for id: int in screen.selected_ids:
		assert_false(GameSession.echo_pool.get_record(id).favorite)
	var event_label := screen.get_node("%EventLabel") as Label
	assert_string_contains(event_label.text, "×3")


func test_preview_matches_exchange_event_formula() -> void:
	var screen := _make_screen()
	var preview := screen.preview_reward()
	var clone := EchoPool.new(10)
	for record: EchoRecord in GameSession.echo_pool.records:
		clone.bank_echo(record.echo, record.icon, record.favorite)
	var expected := clone.exchange_event(screen.selected_ids, screen.event_multiplier)
	assert_eq(preview.essence, expected.essence)
	assert_eq(preview.shards, expected.shards)
	assert_eq(preview.relic_rolls, expected.relic_rolls)


func test_favorite_toggle_is_locked() -> void:
	var screen := _make_screen()
	var favorite := GameSession.echo_pool.sorted_records("favorite")[0]
	screen.toggle_record(favorite.id)
	assert_false(screen.selected_ids.has(favorite.id))
	assert_string_contains(screen.last_message, "Favorites are locked")


func test_confirm_exchange_removes_selected_and_adds_currency() -> void:
	var screen := _make_screen()
	var before_size := GameSession.echo_pool.size()
	var before_essence := GameSession.essence
	var selected_count := screen.selected_ids.size()
	var reward := screen.confirm_exchange()
	assert_not_null(reward)
	assert_eq(GameSession.echo_pool.size(), before_size - selected_count)
	assert_gt(GameSession.essence, before_essence)
	assert_eq(screen.selected_ids, [])


func test_navigation_buttons() -> void:
	var screen := _make_screen()
	watch_signals(screen)
	(screen.get_node("%PoolButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["echo_pool"])
	(screen.get_node("%HubButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["home_hub"])
