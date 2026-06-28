extends GutTest
## TrainingSimulator tests.
##
## Ported 1:1 from the Python prototype's `TrainingSimulator` cases in
## `prototype/test_game.py`, keeping identical expected values. The prototype
## monkey-patched `simulator.rng.random`; here we set [member
## TrainingSimulator.random_source] to a constant [Callable] to pin the per-floor
## failure roll the same way.

## Per-floor failure rolls pinned to a constant, the GUT equivalent of the
## prototype's `simulator.rng.random = lambda: ...`. A draw of 1.0 never trips the
## `< 0.45` failure check (always clear); 0.0 always trips it (fail when under-powered).
var _always_clear := func() -> float: return 1.0
var _always_fail := func() -> float: return 0.0


func _characters() -> Dictionary:
	return CharacterCatalog.sample_characters()


# --- inheritance ------------------------------------------------------------


func test_inheritance_increases_starting_power() -> void:
	var characters := _characters()
	var simulator := TrainingSimulator.new(3)
	simulator.random_source = _always_clear
	var base := simulator.start_stats(characters["star_witch"])
	var base_stats: Dictionary = base[0]
	var first := simulator.run(characters["star_witch"], "deep_scaling")
	var inherited := simulator.start_stats(characters["star_witch"], [first.echo])
	var inherited_stats: Dictionary = inherited[0]
	var depth: int = inherited[1]
	assert_eq(depth, 1)
	assert_true(
		inherited_stats["atk"].magnitude >= base_stats["atk"].magnitude,
		"inherited atk magnitude is at least the base magnitude"
	)


func test_two_parents_increase_lineage_depth_using_the_deeper_parent() -> void:
	var characters := _characters()
	var simulator := TrainingSimulator.new(42)
	simulator.random_source = _always_clear
	var grandparent := simulator.run(characters["iron_vow"], "deep_scaling")
	var deep_parent := simulator.run(characters["star_witch"], "deep_scaling", [grandparent.echo])
	var shallow_parent := simulator.run(characters["iron_vow"], "deep_scaling")
	assert_eq(deep_parent.echo.lineage_depth, 1)
	assert_eq(shallow_parent.echo.lineage_depth, 0)

	var combined := simulator.start_stats(
		characters["rat_squire"], [deep_parent.echo, shallow_parent.echo]
	)
	assert_eq(combined[1], 2, "lineage depth is the deeper parent + 1")


func test_two_parents_contribute_more_stats_than_a_single_parent() -> void:
	var characters := _characters()
	var simulator := TrainingSimulator.new(43)
	simulator.random_source = _always_clear
	var parent_a := simulator.run(characters["iron_vow"], "deep_scaling")
	var parent_b := simulator.run(characters["star_witch"], "deep_scaling")

	var single := simulator.start_stats(characters["rat_squire"], [parent_a.echo])
	var dual := simulator.start_stats(characters["rat_squire"], [parent_a.echo, parent_b.echo])
	var single_atk: BigStat = single[0]["atk"]
	var dual_atk: BigStat = dual[0]["atk"]

	var single_score := single_atk.magnitude * 1000 + single_atk.mantissa
	var dual_score := dual_atk.magnitude * 1000 + dual_atk.mantissa
	assert_true(dual_score >= single_score, "two parents contribute at least as much atk")


func test_training_run_rejects_more_than_two_parents() -> void:
	var characters := _characters()
	var simulator := TrainingSimulator.new(43)
	simulator.random_source = _always_clear
	var parents := [
		simulator.run(characters["iron_vow"], "deep_scaling").echo,
		simulator.run(characters["star_witch"], "deep_scaling").echo,
		simulator.run(characters["rat_squire"], "deep_scaling").echo,
	]
	simulator.start_stats(characters["rat_squire"], parents)
	assert_push_error("at most 2 parents may be inherited")
	simulator.run(characters["rat_squire"], "deep_scaling", parents)
	assert_push_error("at most 2 parents may be inherited")


# --- routes -----------------------------------------------------------------


func test_available_routes_are_discoverable() -> void:
	var routes := TrainingSimulator.available_routes()
	assert_eq(routes.size(), 4)
	for route in ["balanced", "boss_rush", "skill_hunt", "deep_scaling"]:
		assert_true(routes.has(route), "routes include %s" % route)


func test_route_tuning_is_discoverable() -> void:
	var tuning := TrainingSimulator.route_tuning("deep_scaling")
	assert_eq(tuning, {"growth_percent": 125, "magnitude_interval": 8})
	assert_eq(TrainingSimulator.route_tuning("turbo_mode"), {})
	assert_push_error("unknown training route")


func test_unknown_route_is_rejected_instead_of_silent_fallback() -> void:
	var characters := _characters()
	var simulator := TrainingSimulator.new(41)
	var result := simulator.run(characters["iron_vow"], "turbo_mode")
	assert_push_error("unknown training route")
	assert_eq(result.floors_cleared, 0)
	assert_false(result.victory)


func test_route_patterns_can_emit_all_documented_encounter_types() -> void:
	var kinds := {}
	for route in ["balanced", "boss_rush", "skill_hunt", "deep_scaling"]:
		for floor in range(1, 13):
			kinds[TrainingSimulator.encounter_kind(floor, route)] = true
	var seen := kinds.keys()
	seen.sort()
	assert_eq(seen, ["boss", "combat", "elite", "event", "rest", "shrine"])


# --- echoes & encounters ----------------------------------------------------


func test_echo_is_always_created_even_on_immediate_failure() -> void:
	var weakling := CharacterDef.new(
		"weakling",
		"Test Weakling",
		Rarity.COMMON,
		"fighter",
		{
			"hp": BigStat.new(50),
			"atk": BigStat.new(10),
			"def": BigStat.new(10),
			"spd": BigStat.new(10),
		},
		PackedStringArray(["Flail"]),
		PackedStringArray(["frail"]),
	)
	var simulator := TrainingSimulator.new(5)
	simulator.random_source = _always_fail
	var result := simulator.run(weakling, "balanced")
	assert_eq(result.floors_cleared, 0)
	assert_false(result.victory)
	assert_not_null(result.echo)
	assert_eq(result.rewards.highest_checkpoint_floor, 0)
	assert_eq(result.rewards.banked_shards, 0)
	assert_eq(result.echo.source_character_id, "weakling")
	assert_eq(result.encounters.size(), 1)
	assert_eq(result.encounters[0].floor, 1)
	assert_eq(result.encounters[0].kind, "combat")
	assert_false(result.encounters[0].cleared)


func test_training_run_records_deterministic_encounters() -> void:
	var characters := _characters()
	var simulator := TrainingSimulator.new(41)
	simulator.random_source = _always_clear
	var result := simulator.run(characters["iron_vow"], "skill_hunt")
	assert_eq(result.encounters.size(), result.floors_cleared)
	var first_four: Array[String] = []
	for i in range(4):
		first_four.append(result.encounters[i].kind)
	assert_eq(first_four, ["event", "combat", "rest", "boss"] as Array[String])
	for i in range(result.encounters.size()):
		assert_eq(result.encounters[i].floor, i + 1)
		assert_true(result.encounters[i].cleared)
		assert_true(result.encounters[i].power > 0)
		assert_true(result.encounters[i].difficulty > 0)


func test_partial_clear_records_the_failed_floor_encounter() -> void:
	var characters := _characters()
	var simulator := TrainingSimulator.new(5)
	simulator.random_source = _always_fail
	var result := simulator.run(characters["rat_squire"], "balanced")
	assert_false(result.victory)
	assert_true(result.floors_cleared > 0)
	assert_true(result.floors_cleared < 12)
	assert_eq(result.encounters.size(), result.floors_cleared + 1)
	for i in range(result.encounters.size() - 1):
		assert_true(result.encounters[i].cleared, "earlier floors cleared")
	var failed: EncounterRecord = result.encounters[-1]
	assert_false(failed.cleared)
	assert_eq(failed.floor, result.floors_cleared + 1)
	assert_eq(failed.kind, TrainingSimulator.encounter_kind(failed.floor, "balanced"))


# --- checkpoints & dividend -------------------------------------------------


func test_checkpoint_rewards_escalate() -> void:
	var simulator := TrainingSimulator.new(7)
	var tier1 := simulator.checkpoint_reward(1, 4)
	var tier2 := simulator.checkpoint_reward(2, 8)
	var tier3 := simulator.checkpoint_reward(3, 12)
	assert_true(tier1.shards < tier2.shards)
	assert_true(tier2.shards < tier3.shards)
	assert_true(tier1.relic_rolls < tier2.relic_rolls)
	assert_true(tier1.echo_quality_bonus < tier2.echo_quality_bonus)


func test_banked_rewards_are_monotonic_and_full_clear_banks_all() -> void:
	var characters := _characters()
	var simulator := TrainingSimulator.new(11)
	simulator.random_source = _always_clear
	var result := simulator.run(characters["iron_vow"], "deep_scaling")
	assert_eq(result.floors_cleared, 12)
	assert_eq(result.rewards.highest_checkpoint_floor, 12)
	assert_eq(result.rewards.checkpoints.size(), 3)
	var banked: Array[int] = []
	for cp: CheckpointReward in result.rewards.checkpoints:
		banked.append(cp.shards)
	var sorted_banked := banked.duplicate()
	sorted_banked.sort()
	assert_eq(banked, sorted_banked, "checkpoint shards bank in ascending order")
	var total := 0
	for shards in banked:
		total += shards
	assert_eq(result.rewards.banked_shards, total)
	assert_true(result.rewards.echo_quality_percent > 100)


func test_pushing_further_is_worth_more() -> void:
	var characters := _characters()
	var early := TrainingSimulator.new(2)
	early.random_source = _always_fail
	var early_result := early.run(characters["iron_vow"], "deep_scaling")
	var full := TrainingSimulator.new(2)
	full.random_source = _always_clear
	var full_result := full.run(characters["iron_vow"], "deep_scaling")
	assert_true(full_result.rewards.banked_shards > early_result.rewards.banked_shards)
	assert_true(
		full_result.rewards.echo_quality_percent > early_result.rewards.echo_quality_percent
	)


func test_checkpoint_rewards_stay_banked_after_later_failure() -> void:
	var checkpoint_runner := CharacterDef.new(
		"checkpoint_runner",
		"Test Checkpoint Runner",
		Rarity.COMMON,
		"fighter",
		{
			"hp": BigStat.new(460),
			"atk": BigStat.new(110),
			"def": BigStat.new(110),
			"spd": BigStat.new(110),
		},
		PackedStringArray(["Push"]),
		PackedStringArray(["steady"]),
	)
	var simulator := TrainingSimulator.new(13)
	simulator.random_source = _always_fail
	var result := simulator.run(checkpoint_runner, "boss_rush")
	assert_eq(result.floors_cleared, 4)
	assert_false(result.victory)
	assert_not_null(result.echo)
	assert_eq(result.rewards.highest_checkpoint_floor, 4)
	assert_eq(result.rewards.banked_shards, 15)
	assert_eq(result.rewards.relic_rolls, 1)


func test_instability_pays_a_dividend_only_when_a_checkpoint_is_banked() -> void:
	var characters := _characters()
	var simulator := TrainingSimulator.new(31)
	simulator.random_source = _always_clear
	var stable := simulator.run(characters["iron_vow"], "deep_scaling")
	assert_eq(stable.rewards.instability_dividend_shards, 0)

	var seeded := simulator.run(characters["star_witch"], "deep_scaling")
	var child := simulator.start_stats(characters["star_witch"], [seeded.echo])
	assert_true(child[2] > 0, "inheriting raises instability")
	var risky := simulator.run(characters["star_witch"], "deep_scaling", [seeded.echo])
	assert_eq(risky.rewards.highest_checkpoint_floor, 12)
	assert_true(risky.rewards.instability_dividend_shards > 0)
	assert_eq(
		risky.rewards.banked_shards - risky.rewards.instability_dividend_shards,
		stable.rewards.banked_shards,
		"the only banked difference is the instability dividend"
	)


func test_instability_dividend_is_forfeited_on_pre_checkpoint_failure() -> void:
	var glass := CharacterDef.new(
		"glass",
		"Test Glass Cannon",
		Rarity.COMMON,
		"caster",
		{
			"hp": BigStat.new(40),
			"atk": BigStat.new(10),
			"def": BigStat.new(10),
			"spd": BigStat.new(10),
		},
		PackedStringArray(["Zap"]),
		PackedStringArray(["frail"]),
	)
	var simulator := TrainingSimulator.new(33)
	simulator.random_source = _always_fail
	var result := simulator.run(glass, "balanced")
	assert_eq(result.floors_cleared, 0)
	assert_eq(result.rewards.instability_dividend_shards, 0)


# --- determinism ------------------------------------------------------------


func test_runs_are_deterministic_per_seed() -> void:
	var characters := _characters()
	var first := TrainingSimulator.new(99).run(characters["iron_vow"], "balanced")
	var second := TrainingSimulator.new(99).run(characters["iron_vow"], "balanced")
	assert_eq(first.floors_cleared, second.floors_cleared)
	assert_eq(first.victory, second.victory)
	assert_eq(first.rewards.banked_shards, second.rewards.banked_shards)
	assert_eq(first.encounters.size(), second.encounters.size())
