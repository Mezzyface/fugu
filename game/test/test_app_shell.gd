extends GutTest


func before_each() -> void:
	GameSession.reset(1)


func test_game_session_tracks_player_state() -> void:
	assert_eq(GameSession.currency_totals(), {"shards": 0, "essence": 0, "relic_rolls": 0})
	assert_eq(GameSession.current_week, 1)
	assert_true(GameSession.echo_pool is EchoPool)
	assert_eq(GameSession.echo_pool.size(), 0)
	assert_eq(GameSession.owned_banners.size(), CharacterCatalog.sample_characters().size())
	GameSession.add_currency(25, 40, 3)
	assert_eq(GameSession.currency_totals(), {"shards": 25, "essence": 40, "relic_rolls": 3})
	assert_eq(GameSession.currency_summary(), "◆ 25 · ✦ 40 · ⬡ 3 · Week 1/52")


func test_game_session_wraps_week_and_exposes_featured_banners() -> void:
	GameSession.set_current_week(53)
	assert_eq(GameSession.current_week, 1)
	GameSession.advance_week(1)
	assert_eq(GameSession.current_week, 2)
	var featured_ids := GameSession.featured_banner_ids()
	assert_eq(featured_ids.size(), 3)
	assert_eq(GameSession.featured_banners().size(), 3)
	assert_true(GameSession.get_banner_state(featured_ids[0]) is BannerState)


func test_game_session_formats_big_stats_for_ui() -> void:
	assert_eq(GameSession.format_stat(BigStat.new(4200)), "420·10^1")
	var formatted := GameSession.format_stats({"hp": BigStat.new(900), "atk": BigStat.new(1800)})
	assert_eq(formatted["hp"], "900·10^0")
	assert_eq(formatted["atk"], "180·10^1")


func test_navigation_root_switches_all_screens_and_returns_home() -> void:
	var packed := load("res://main.tscn") as PackedScene
	var main := packed.instantiate()
	add_child_autofree(main)
	assert_eq(main.current_screen_id, "home_hub")
	assert_eq(main.screen_ids().size(), 10)
	for screen_id: String in main.screen_ids():
		assert_true(main.go_to_screen(screen_id), "can switch to %s" % screen_id)
		assert_eq(main.current_screen_id, screen_id)
		assert_not_null(main.current_screen)
	assert_true(main.go_home())
	assert_eq(main.current_screen_id, "home_hub")


func test_navigation_rejects_unknown_screen() -> void:
	var packed := load("res://main.tscn") as PackedScene
	var main := packed.instantiate()
	add_child_autofree(main)
	assert_false(main.go_to_screen("missing_screen"))
	assert_push_error("unknown screen missing_screen")
