extends GutTest
## Screen 03 — Banner / Pull behavior.

const BANNER_PULL := preload("res://scenes/banner_pull.tscn")


func before_each() -> void:
	GameSession.reset(1)


func _make_screen() -> BannerPullScreen:
	var screen := BANNER_PULL.instantiate() as BannerPullScreen
	add_child_autofree(screen)
	return screen


func _force_roll(value: float) -> void:
	# Replace the seeded RNG draw so pull outcomes are deterministic in tests.
	GameSession.gacha_system.uniform_func = func(_a: float, _b: float) -> float: return value


func test_defaults_to_week_lead_featured_banner() -> void:
	var screen := _make_screen()
	var lead: String = GameSession.featured_banner_ids(BannerPullScreen.SLOTS_PER_WEEK)[0]
	assert_eq(screen.banner_character_id, lead, "shows the week's lead featured banner")
	var name_label := screen.get_node("%PortraitName") as Label
	assert_string_contains(name_label.text, GameSession.get_character(lead).name.to_upper())


func test_pity_bar_uses_featured_hard_target() -> void:
	var screen := _make_screen()
	# Week 1 features the whole 3-character roster, so the lead banner is featured.
	var bar := screen.get_node("%PityBar") as ProgressBar
	assert_eq(int(bar.max_value), 80, "featured hard pity target is 80")
	assert_eq(int(bar.value), 0, "starts with no pity")


func test_resonance_track_renders_four_nodes() -> void:
	var screen := _make_screen()
	var track := screen.get_node("%ResonanceTrack") as HBoxContainer
	assert_eq(track.get_child_count(), GachaSystem.RESONANCE_NODES.size())


func test_pull_one_advances_pity_and_awards_shards() -> void:
	var screen := _make_screen()
	_force_roll(100.0)  # guaranteed non-legendary
	var banner := GameSession.get_banner_state(screen.banner_character_id)
	var shards_before := banner.shards
	(screen.get_node("%Pull1Button") as Button).pressed.emit()
	assert_eq(banner.pulls_since_legendary, 1, "pity advanced by one")
	assert_gt(banner.shards, shards_before, "pull awarded resonance shards")
	var bar := screen.get_node("%PityBar") as ProgressBar
	assert_eq(int(bar.value), 1, "pity bar reflects the new counter")
	var detail := screen.get_node("%ResultDetail") as Label
	assert_string_contains(detail.text, "shards")


func test_pull_one_legendary_resets_pity_and_flags_it() -> void:
	var screen := _make_screen()
	_force_roll(0.0)  # guaranteed legendary
	var banner := GameSession.get_banner_state(screen.banner_character_id)
	(screen.get_node("%Pull1Button") as Button).pressed.emit()
	assert_eq(banner.pulls_since_legendary, 0, "legendary resets pity")
	var badge := screen.get_node("%ResultBadge") as Label
	assert_string_contains(badge.text, "LEGENDARY")
	var detail := screen.get_node("%ResultDetail") as Label
	assert_string_contains(detail.text, "PITY RESET")


func test_pull_ten_performs_ten_pulls() -> void:
	var screen := _make_screen()
	_force_roll(100.0)  # all non-legendary, no resets
	var banner := GameSession.get_banner_state(screen.banner_character_id)
	(screen.get_node("%Pull10Button") as Button).pressed.emit()
	assert_eq(banner.pulls_since_legendary, 10, "ten pulls advanced pity by ten")
	var badge := screen.get_node("%ResultBadge") as Label
	assert_string_contains(badge.text, "×10")


func test_upgrade_resonance_spends_shards_never_base_stats() -> void:
	var screen := _make_screen()
	var character := GameSession.get_character(screen.banner_character_id)
	var base_stats_before := character.base_stats.duplicate()
	var banner := GameSession.get_banner_state(screen.banner_character_id)
	banner.shards = 50  # enough for the first node (20)
	var level_before := banner.resonance_level
	screen._refresh()  # re-enable the button now that shards are affordable
	var button := screen.get_node("%ResonanceButton") as Button
	assert_false(button.disabled, "upgrade is affordable")
	button.pressed.emit()
	assert_eq(banner.resonance_level, level_before + 1, "resonance level advanced")
	assert_eq(banner.shards, 30, "spent 20 shards on the first node")
	assert_eq(character.base_stats, base_stats_before, "base stats are untouched")


func test_selector_switches_banner() -> void:
	var screen := _make_screen()
	var selector := screen.get_node("%BannerSelector") as OptionButton
	var target_index := (selector.selected + 1) % selector.item_count
	selector.selected = target_index
	selector.item_selected.emit(target_index)
	var sorted_ids: Array = GameSession.characters.keys()
	sorted_ids.sort()
	assert_eq(screen.banner_character_id, sorted_ids[target_index], "banner follows the selector")


func test_hub_button_requests_home_hub() -> void:
	var screen := _make_screen()
	watch_signals(screen)
	(screen.get_node("%HubButton") as Button).pressed.emit()
	assert_signal_emitted_with_parameters(screen, "navigation_requested", ["home_hub"])
