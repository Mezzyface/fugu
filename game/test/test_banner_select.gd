extends GutTest
## Screen 02 — Banner Select behavior.

const BANNER_SELECT := preload("res://scenes/banner_select.tscn")


func before_each() -> void:
	GameSession.reset(1)


func _make_screen() -> BannerSelectScreen:
	var screen := BANNER_SELECT.instantiate() as BannerSelectScreen
	add_child_autofree(screen)
	return screen


func test_week_header_reflects_current_week_and_featured_count() -> void:
	var screen := _make_screen()
	var title := screen.get_node("%WeekTitle") as Label
	var featured_ids := GameSession.featured_banner_ids(BannerSelectScreen.SLOTS_PER_WEEK)
	assert_string_contains(title.text, "Week 1 / 52")
	assert_string_contains(title.text, "%d banners" % featured_ids.size())


func test_week_header_tracks_week_changes() -> void:
	var screen := _make_screen()
	var title := screen.get_node("%WeekTitle") as Label
	GameSession.set_current_week(9)
	assert_string_contains(title.text, "Week 9 / 52")


func test_builds_one_card_per_roster_character() -> void:
	var screen := _make_screen()
	var grid := screen.get_node("%BannerGrid") as GridContainer
	assert_eq(grid.get_child_count(), GameSession.characters.size())
	var first_card := grid.get_child(0) as Button
	assert_not_null(first_card, "each card is a tappable Button")


func test_featured_card_shows_featured_state() -> void:
	var screen := _make_screen()
	var grid := screen.get_node("%BannerGrid") as GridContainer
	var featured_ids := GameSession.featured_banner_ids(BannerSelectScreen.SLOTS_PER_WEEK)
	var lead_name: String = GameSession.get_character(featured_ids[0]).name
	var found_featured := false
	for card: Button in grid.get_children():
		if card.text.contains(lead_name):
			assert_string_contains(card.text, "★ Featured this week")
			found_featured = true
	assert_true(found_featured, "the week's lead banner is rendered as featured")


func test_tapping_a_banner_requests_banner_pull() -> void:
	var screen := _make_screen()
	watch_signals(screen)
	var grid := screen.get_node("%BannerGrid") as GridContainer
	var card := grid.get_child(0) as Button
	card.pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["banner_pull"])


func test_hub_button_requests_home_hub() -> void:
	var screen := _make_screen()
	watch_signals(screen)
	var hub_button := screen.get_node("%HubButton") as Button
	hub_button.pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["home_hub"])


func test_every_character_featured_at_least_once_per_year() -> void:
	# The screen states the rotation invariant; assert the data backs it up.
	var missing := GameSession.gacha_system.missing_annual_featured_banners(
		52, BannerSelectScreen.SLOTS_PER_WEEK
	)
	assert_eq(missing.size(), 0, "no character is left out of the 52-week schedule")
	var screen := _make_screen()
	var invariant := screen.get_node("%InvariantLabel") as Label
	assert_string_contains(invariant.text, "featured at least once each year")


func test_no_fomo_or_urgency_language() -> void:
	var screen := _make_screen()
	var banned := ["hurry", "last chance", "limited time", "don't miss", "expire", "ending soon"]
	var texts: Array[String] = []
	texts.append((screen.get_node("%WeekTitle") as Label).text)
	texts.append((screen.get_node("%InvariantLabel") as Label).text)
	for card: Button in (screen.get_node("%BannerGrid") as GridContainer).get_children():
		texts.append(card.text)
	for text: String in texts:
		var lowered := text.to_lower()
		for phrase: String in banned:
			assert_false(lowered.contains(phrase), "no FOMO phrase '%s' in: %s" % [phrase, text])
