extends GutTest

const ECHO_POOL_SCREEN := preload("res://scenes/echo_pool_screen.tscn")


func before_each() -> void:
	GameSession.reset(1)


func _make_screen() -> EchoPoolScreen:
	var screen := ECHO_POOL_SCREEN.instantiate() as EchoPoolScreen
	add_child_autofree(screen)
	return screen


func test_seeds_and_lists_banked_echoes_with_power() -> void:
	var screen := _make_screen()
	assert_eq(GameSession.echo_pool.size(), 3)
	var list := screen.get_node("%RecordList") as VBoxContainer
	assert_eq(list.get_child_count(), 3)
	var text := _row_text(list.get_child(0))
	assert_string_contains(text, "pwr")
	assert_string_contains((screen.get_node("%SummaryLabel") as Label).text, "Capacity")


func test_sort_selector_changes_sort_mode() -> void:
	var screen := _make_screen()
	var selector := screen.get_node("%SortSelector") as OptionButton
	selector.selected = 1
	selector.item_selected.emit(1)
	assert_eq(screen.sort_mode, "icon")


func test_favorite_delete_and_exchange_protect_favorites() -> void:
	var screen := _make_screen()
	var favorite := GameSession.echo_pool.sorted_records("favorite")[0]
	assert_true(favorite.favorite)
	assert_null(screen.delete_record(favorite.id))
	assert_push_error("favorite echoes must be unfavorited before deletion")
	assert_string_contains(screen.last_message, "Favorite")
	assert_null(screen.exchange_record(favorite.id))
	assert_push_error("favorite echoes must be unfavorited before deletion")
	assert_string_contains(screen.last_message, "Favorite")
	screen.favorite_record(favorite.id)
	assert_false(GameSession.echo_pool.get_record(favorite.id).favorite)
	assert_not_null(screen.delete_record(favorite.id))


func test_exchange_adds_currency_and_removes_record() -> void:
	var screen := _make_screen()
	var record := GameSession.echo_pool.sorted_records("power")[1]
	var before_size := GameSession.echo_pool.size()
	var before_essence := GameSession.essence
	var reward := screen.exchange_record(record.id)
	assert_not_null(reward)
	assert_eq(GameSession.echo_pool.size(), before_size - 1)
	assert_gt(GameSession.essence, before_essence)


func test_exchange_event_and_hub_buttons_request_navigation() -> void:
	var screen := _make_screen()
	watch_signals(screen)
	(screen.get_node("%ExchangeButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["exchange_event"])
	(screen.get_node("%HubButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["home_hub"])


func _row_text(row: Node) -> String:
	var margin := row.get_child(0)
	var hbox := margin.get_child(0)
	var label := hbox.get_child(0) as Label
	return label.text
