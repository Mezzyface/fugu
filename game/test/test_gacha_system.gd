extends GutTest
## GachaSystem tests — banners, pity, featured rotation, and resonance spending.
##
## Ported 1:1 from the Python prototype's gacha cases in `prototype/test_game.py`,
## keeping identical seeds and expected values. Forced rolls (the prototype's
## `gacha.rng.uniform = lambda ...` monkeypatch) are reproduced by replacing
## `gacha.uniform_func` with a [Callable] returning a fixed value.


## Returns a [Callable] matching `uniform_func`'s `(low, high) -> float` shape that
## always yields `value`, the equivalent of the prototype's forced-roll lambda.
func _forced_roll(value: float) -> Callable:
	return func(_low: float, _high: float) -> float: return value


func _new_gacha(seed_value: int = 1) -> GachaSystem:
	return GachaSystem.new(CharacterCatalog.sample_characters(), seed_value)


func test_hard_pity_guarantees_banner_character() -> void:
	# Forced non-Legendary rolls every pull (roll == 100) so the only Legendary
	# can come from hard pity at pull 90 — the GDD QA note's scenario.
	var gacha := _new_gacha(999)
	gacha.uniform_func = _forced_roll(100.0)
	var result: PullResult = null
	for _i in range(90):
		result = gacha.pull("star_witch")
	assert_eq(result.character_id, "star_witch")
	assert_eq(Rarity.to_string_value(result.rarity), "legendary")


func test_featured_banner_has_discounted_pity_and_bonus_shards() -> void:
	var gacha := _new_gacha(998)
	gacha.uniform_func = _forced_roll(100.0)
	var result: PullResult = null
	for _i in range(80):
		result = gacha.pull("star_witch", true)
	assert_eq(result.character_id, "star_witch")
	assert_eq(Rarity.to_string_value(result.rarity), "legendary")
	assert_eq(result.shards_gained, 15)
	assert_eq((gacha.banners["star_witch"] as BannerState).shards, 173)


func test_featured_non_legendary_pull_grants_bonus_shards() -> void:
	var gacha := _new_gacha(997)
	gacha.uniform_func = _forced_roll(100.0)
	var result := gacha.pull("iron_vow", true)
	assert_eq(Rarity.to_string_value(result.rarity), "common")
	assert_eq(result.shards_gained, 2)
	assert_eq((gacha.banners["iron_vow"] as BannerState).shards, 2)


func test_base_rarity_rates_are_discoverable_and_sum_to_100() -> void:
	var rates := GachaSystem.rarity_rates()
	var keys := rates.keys()
	keys.sort()
	assert_eq(keys, ["common", "epic", "legendary", "rare"])
	var total := 0.0
	for value: float in rates.values():
		total += value
	assert_almost_eq(total, 100.0, 0.0001)


func test_pity_tuning_is_discoverable() -> void:
	assert_eq(
		GachaSystem.pity_tuning(),
		{
			"soft_pity_start": 70,
			"hard_pity_target": 90,
			"legendary_shards": 10,
			"non_legendary_shards": 1,
			"soft_pity_increment": 4.5,
		}
	)
	assert_eq(
		GachaSystem.pity_tuning(true),
		{
			"soft_pity_start": 60,
			"hard_pity_target": 80,
			"legendary_shards": 15,
			"non_legendary_shards": 2,
			"soft_pity_increment": 4.5,
		}
	)


func test_soft_pity_increment_drives_legendary_ramp() -> void:
	var gacha := _new_gacha(1)
	var increment: float = GachaSystem.pity_tuning()["soft_pity_increment"]
	var base_legendary: float = GachaSystem.rarity_rates()["legendary"]
	var soft_pity_start: int = GachaSystem.pity_tuning()["soft_pity_start"]
	(gacha.banners["star_witch"] as BannerState).pulls_since_legendary = soft_pity_start - 1
	gacha.uniform_func = _forced_roll(base_legendary + increment)
	var result := gacha.pull("star_witch")
	assert_eq(Rarity.to_string_value(result.rarity), "legendary")


func test_pull_rarity_thresholds_follow_base_rates() -> void:
	var gacha := _new_gacha(1)
	var rates := GachaSystem.rarity_rates()
	gacha.uniform_func = _forced_roll(rates["legendary"])
	assert_eq(Rarity.to_string_value(gacha.pull("star_witch").rarity), "legendary")
	gacha.uniform_func = _forced_roll(rates["legendary"] + rates["epic"])
	assert_eq(Rarity.to_string_value(gacha.pull("rat_squire").rarity), "epic")
	gacha.uniform_func = _forced_roll(rates["legendary"] + rates["epic"] + rates["rare"])
	assert_eq(Rarity.to_string_value(gacha.pull("iron_vow").rarity), "rare")
	gacha.uniform_func = _forced_roll(100.0)
	assert_eq(Rarity.to_string_value(gacha.pull("iron_vow").rarity), "common")


func test_pull_batch_advances_pity_and_handles_empty_counts() -> void:
	var gacha := _new_gacha(994)
	gacha.uniform_func = _forced_roll(100.0)
	assert_eq(gacha.pull_batch("star_witch", 0), [])
	assert_eq(gacha.pull_batch("star_witch", -5), [])
	var results := gacha.pull_batch("star_witch", 10)
	assert_eq(results.size(), 10)
	for result: PullResult in results:
		assert_eq(Rarity.to_string_value(result.rarity), "common")
	assert_eq((gacha.banners["star_witch"] as BannerState).pulls_since_legendary, 10)
	assert_eq((gacha.banners["star_witch"] as BannerState).shards, 10)


func test_pull_batch_respects_featured_hard_pity() -> void:
	var gacha := _new_gacha(993)
	gacha.uniform_func = _forced_roll(100.0)
	var results := gacha.pull_batch("star_witch", 80, true)
	var last: PullResult = results[-1]
	assert_eq(Rarity.to_string_value(last.rarity), "legendary")
	assert_true(last.pity_reset)
	assert_eq((gacha.banners["star_witch"] as BannerState).pulls_since_legendary, 0)
	assert_eq((gacha.banners["star_witch"] as BannerState).shards, 173)


func test_resonance_track_is_discoverable() -> void:
	assert_eq(
		GachaSystem.resonance_track(),
		[
			{"level": 1, "cost": 20, "node": "origin story"},
			{"level": 2, "cost": 40, "node": "signature skill variant"},
			{"level": 3, "cost": 80, "node": "alternate portrait"},
			{"level": 4, "cost": 120, "node": "lineage title"},
		]
	)


func test_resonance_preview_marks_unlocked_and_affordable_nodes() -> void:
	var gacha := _new_gacha(996)
	(gacha.banners["star_witch"] as BannerState).shards = 65
	gacha.upgrade_resonance("star_witch")
	var preview := gacha.resonance_preview("star_witch")
	assert_true(preview[0]["unlocked"])
	assert_false(preview[0]["affordable"])
	assert_false(preview[1]["unlocked"])
	assert_true(preview[1]["affordable"])
	assert_false(preview[2]["affordable"])


func test_shards_upgrade_resonance_nodes() -> void:
	var gacha := _new_gacha(996)
	(gacha.banners["star_witch"] as BannerState).shards = 65
	var first := gacha.upgrade_resonance("star_witch")
	assert_eq(first.level, 1)
	assert_eq(first.node, "origin story")
	assert_eq(first.cost, 20)
	assert_eq(first.remaining_shards, 45)
	var second := gacha.upgrade_resonance("star_witch")
	assert_eq(second.level, 2)
	assert_eq(second.node, "signature skill variant")
	assert_eq(second.remaining_shards, 5)
	assert_eq(gacha.next_resonance_cost("star_witch"), 80)


func test_resonance_requires_shards_and_has_a_cap() -> void:
	var gacha := _new_gacha(995)
	# Not enough shards to upgrade (prototype raised ValueError).
	assert_null(gacha.upgrade_resonance("iron_vow"))
	assert_push_error("not enough shards")
	(gacha.banners["iron_vow"] as BannerState).shards = 260
	for _i in range(4):
		gacha.upgrade_resonance("iron_vow")
	assert_null(gacha.next_resonance_cost("iron_vow"))
	# Track complete (prototype raised ValueError).
	assert_null(gacha.upgrade_resonance("iron_vow"))
	assert_push_error("resonance track complete")


func test_featured_rotation_is_bounded() -> void:
	var gacha := _new_gacha()
	assert_eq(gacha.featured_banners_for_week(1).size(), 3)
	assert_eq(gacha.featured_banners_for_week(52).size(), 3)


func test_annual_featured_rotation_covers_every_banner() -> void:
	var gacha := _new_gacha()
	var counts := gacha.annual_featured_counts()
	var count_keys := counts.keys()
	count_keys.sort()
	var expected := CharacterCatalog.sample_characters().keys()
	expected.sort()
	assert_eq(count_keys, expected)
	assert_eq(gacha.missing_annual_featured_banners(), [])
	for count: int in counts.values():
		assert_gt(count, 0)


func test_featured_schedule_covers_all_current_characters() -> void:
	var gacha := _new_gacha()
	var expected := CharacterCatalog.sample_characters().keys()
	expected.sort()
	assert_eq(gacha.featured_coverage(), expected)
	var schedule := gacha.featured_schedule(2, 2)
	assert_eq(schedule.size(), 2)
	for week_banners: Array in schedule:
		assert_eq(week_banners.size(), 2)


func test_featured_rotation_handles_empty_or_disabled_slots() -> void:
	var empty := GachaSystem.new({})
	assert_eq(empty.featured_banners_for_week(1), [])
	var empty_schedule := empty.featured_schedule()
	assert_eq(empty_schedule.size(), 52)
	for week_banners: Array in empty_schedule:
		assert_eq(week_banners, [])
	var gacha := _new_gacha()
	assert_eq(gacha.featured_banners_for_week(1, 0), [])
	assert_eq(gacha.featured_schedule(-1), [])
	var all_ids := CharacterCatalog.sample_characters().keys()
	all_ids.sort()
	assert_eq(gacha.missing_annual_featured_banners(52, 0), all_ids)


func test_seeded_rng_is_deterministic() -> void:
	# Same seed reproduces the same pull sequence (the Python Random(seed) contract).
	var a := _new_gacha(42)
	var b := _new_gacha(42)
	for _i in range(50):
		var ra := a.pull("star_witch")
		var rb := b.pull("star_witch")
		assert_eq(ra.rarity, rb.rarity)
		assert_eq(ra.shards_gained, rb.shards_gained)
	assert_eq(
		(a.banners["star_witch"] as BannerState).shards,
		(b.banners["star_witch"] as BannerState).shards
	)
