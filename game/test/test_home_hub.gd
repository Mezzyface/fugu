extends GutTest
## Screen 01 — Home / Hub behavior.

const HOME_HUB := preload("res://scenes/home_hub.tscn")


func before_each() -> void:
	GameSession.reset(1)


func _make_screen() -> HomeHubScreen:
	var screen := HOME_HUB.instantiate() as HomeHubScreen
	add_child_autofree(screen)
	return screen


func test_builds_one_nav_button_per_entry_with_settings_disabled() -> void:
	var screen := _make_screen()
	var grid := screen.get_node("%NavGrid")
	assert_eq(grid.get_child_count(), HomeHubScreen.NAV_ENTRIES.size())
	var settings_button := grid.get_child(grid.get_child_count() - 1) as Button
	assert_eq(settings_button.text, "Settings")
	assert_true(settings_button.disabled, "Settings has no screen yet, so it is disabled")


func test_nav_button_emits_navigation_requested_with_screen_id() -> void:
	var screen := _make_screen()
	watch_signals(screen)
	var grid := screen.get_node("%NavGrid")
	var banner_button := grid.get_child(0) as Button
	banner_button.pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["banner_select"])


func test_shows_live_currency_totals_from_session() -> void:
	var screen := _make_screen()
	var currency_label := screen.get_node("%CurrencyLabel") as Label
	assert_string_contains(currency_label.text, "◆ 0")
	GameSession.add_currency(25, 40, 3)
	assert_string_contains(currency_label.text, "◆ 25")
	assert_string_contains(currency_label.text, "✦ 40")
	assert_string_contains(currency_label.text, "⬡ 3")


func test_shows_current_week_featured_banners() -> void:
	var screen := _make_screen()
	var title := screen.get_node("%FeaturedTitle") as Label
	var listing := screen.get_node("%FeaturedList") as Label
	var featured_ids := GameSession.featured_banner_ids()
	assert_string_contains(title.text, "Week 1 / 52")
	assert_string_contains(title.text, "%d banners" % featured_ids.size())
	var lead_name: String = GameSession.get_character(featured_ids[0]).name
	assert_string_contains(listing.text, lead_name)


func test_featured_listing_tracks_week_changes() -> void:
	var screen := _make_screen()
	var title := screen.get_node("%FeaturedTitle") as Label
	GameSession.set_current_week(7)
	assert_string_contains(title.text, "Week 7 / 52")
