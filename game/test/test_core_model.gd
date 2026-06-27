extends GutTest
## Core data-model + BigStat math tests.
##
## Ported 1:1 from the Python prototype's `BigStat` cases in
## `prototype/test_game.py`, keeping identical expected values, plus a check that
## `CharacterCatalog.sample_characters()` returns the three expected characters.


func test_big_stat_normalizes() -> void:
	assert_eq(str(BigStat.new(12000, 0).normalized()), "120e2")


func test_big_stat_zero_has_canonical_magnitude() -> void:
	assert_eq(str(BigStat.new(0, 7).normalized()), "0e0")
	assert_eq(str(BigStat.new(-50, 3).normalized()), "0e0")
	assert_eq(str(BigStat.new(10, -2).normalized()), "10e0")


func test_big_stat_add_normalizes_operands() -> void:
	assert_eq(str(BigStat.new(0, 9).add(BigStat.new(5, 0))), "5e0")
	assert_eq(str(BigStat.new(10, 0).add(BigStat.new(0, 9))), "10e0")


func test_big_stat_scale_rejects_non_positive_denominator() -> void:
	# A negative numerator with a valid denominator simply floors to zero.
	assert_eq(str(BigStat.new(100).scale(-50)), "0e0")
	# A non-positive denominator is invalid (Python raised ValueError; here it
	# pushes an error and returns the canonical zero).
	assert_eq(str(BigStat.new(100).scale(50, 0)), "0e0")
	assert_push_error("scale denominator must be positive")
	assert_eq(str(BigStat.new(100).scale(50, -100)), "0e0")
	assert_push_error("scale denominator must be positive")


func test_big_stat_scale_down_preserves_value_across_magnitude() -> void:
	assert_eq(str(BigStat.new(200, 0).scale(125)), "250e0")
	assert_eq(str(BigStat.new(5, 2).scale(50)), "2e2")
	assert_eq(str(BigStat.new(8, 2).scale(50)), "4e2")
	assert_eq(str(BigStat.new(1, 3).scale(50)), "5e2")
	assert_eq(str(BigStat.new(1, 2).scale(50)), "5e1")


func test_big_stat_scale_floors_to_zero_only_without_magnitude() -> void:
	assert_eq(str(BigStat.new(1, 0).scale(50)), "0e0")
	assert_eq(str(BigStat.new(0, 0).scale(50)), "0e0")
	assert_eq(str(BigStat.new(0, 5).scale(50)), "0e0")


func test_sample_characters_returns_three_expected() -> void:
	var characters := CharacterCatalog.sample_characters()
	assert_eq(characters.size(), 3, "three sample characters")
	assert_true(characters.has("iron_vow"), "has iron_vow")
	assert_true(characters.has("star_witch"), "has star_witch")
	assert_true(characters.has("rat_squire"), "has rat_squire")

	var iron_vow: CharacterDef = characters["iron_vow"]
	assert_eq(iron_vow.name, "Astra, Iron Vow")
	assert_eq(iron_vow.rarity, Rarity.LEGENDARY)
	assert_eq(Rarity.to_string_value(iron_vow.rarity), "legendary")
	assert_eq(iron_vow.role, "guardian")
	assert_eq(str(iron_vow.base_stats["hp"]), "900e0")
	assert_eq(iron_vow.skills, PackedStringArray(["Aegis Break", "Oath Wall", "Counterflare"]))
	assert_eq(iron_vow.traits, PackedStringArray(["armor", "counter"]))

	var rat_squire: CharacterDef = characters["rat_squire"]
	assert_eq(rat_squire.rarity, Rarity.RARE)
	assert_eq(Rarity.to_string_value(rat_squire.rarity), "rare")
	assert_eq(str(rat_squire.base_stats["spd"]), "100e0")
