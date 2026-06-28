extends GutTest
## RelicForge tests.
##
## Ported 1:1 from the Python prototype's `RelicForge` cases in
## `prototype/test_game.py` (rarity weights, stat application, determinism).


func test_relic_forge_spends_relic_rolls() -> void:
	var forge := RelicForge.new(4)
	var relics := forge.forge(5)
	assert_eq(relics.size(), 5, "forge(5) yields five relics")
	assert_eq(forge.forge(0).size(), 0, "forge(0) yields none")
	assert_eq(forge.forge(-3).size(), 0, "forge(-3) yields none")

	var ids: Array[int] = []
	for relic in relics:
		assert_true(RelicForge.RELIC_STATS.has(relic.stat), "stat is a known relic stat")
		assert_gt(relic.bonus_percent, 0, "bonus percent is positive")
		ids.append(relic.id)

	var sorted_unique := ids.duplicate()
	sorted_unique.sort()
	assert_eq(ids, sorted_unique, "ids are issued in ascending order")
	assert_eq(ids.size(), _unique_count(ids), "ids are unique")


func test_relics_boost_only_their_stat() -> void:
	var base := {"hp": BigStat.new(100), "atk": BigStat.new(200)}
	var relics: Array = [Relic.new(1, "Epic ATK Sigil", Rarity.EPIC, "atk", 25)]
	var boosted := RelicForge.apply_relics(base, relics)
	assert_eq(str(boosted["atk"]), str(BigStat.new(250)), "boosted stat scaled by 25%")
	assert_eq(str(boosted["hp"]), str(BigStat.new(100)), "untargeted stat unchanged")
	# apply_relics must not mutate the input stats.
	assert_eq(str(base["atk"]), str(BigStat.new(200)), "input dictionary left untouched")


func test_relic_forge_is_deterministic_per_seed() -> void:
	var first := _relic_names(RelicForge.new(9).forge(6))
	var second := _relic_names(RelicForge.new(9).forge(6))
	assert_eq(first, second, "same seed forges the same relic sequence")


func test_relic_forge_rarity_thresholds_are_ordered_common_to_legendary() -> void:
	assert_eq(Rarity.to_string_value(RelicForge.rarity_for_roll(50.0)[0]), "common")
	assert_eq(Rarity.to_string_value(RelicForge.rarity_for_roll(75.0)[0]), "rare")
	assert_eq(Rarity.to_string_value(RelicForge.rarity_for_roll(90.0)[0]), "epic")
	assert_eq(Rarity.to_string_value(RelicForge.rarity_for_roll(99.0)[0]), "legendary")


func _relic_names(relics: Array) -> PackedStringArray:
	var names := PackedStringArray()
	for relic in relics:
		names.append(relic.name)
	return names


func _unique_count(values: Array[int]) -> int:
	var seen := {}
	for value in values:
		seen[value] = true
	return seen.size()
