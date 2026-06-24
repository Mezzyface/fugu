import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from assets import catalog_asset_directory, classify_asset_pack
from game import BigStat, EchoPool, GachaSystem, RelicForge, TrainingSimulator, demo, sample_characters


class PrototypeTests(unittest.TestCase):
    def test_big_stat_normalizes(self):
        self.assertEqual(str(BigStat(12_000, 0).normalized()), "120e2")

    def test_big_stat_zero_has_canonical_magnitude(self):
        self.assertEqual(str(BigStat(0, 7).normalized()), "0e0")
        self.assertEqual(str(BigStat(-50, 3).normalized()), "0e0")
        self.assertEqual(str(BigStat(10, -2).normalized()), "10e0")

    def test_big_stat_add_normalizes_operands(self):
        self.assertEqual(str(BigStat(0, 9).add(BigStat(5, 0))), "5e0")
        self.assertEqual(str(BigStat(10, 0).add(BigStat(0, 9))), "10e0")

    def test_big_stat_scale_rejects_non_positive_denominator(self):
        self.assertEqual(str(BigStat(100).scale(-50)), "0e0")
        with self.assertRaises(ValueError):
            BigStat(100).scale(50, 0)
        with self.assertRaises(ValueError):
            BigStat(100).scale(50, -100)

    def test_big_stat_scale_down_preserves_value_across_magnitude(self):
        self.assertEqual(str(BigStat(200, 0).scale(125)), "250e0")
        self.assertEqual(str(BigStat(5, 2).scale(50)), "2e2")
        self.assertEqual(str(BigStat(8, 2).scale(50)), "4e2")
        self.assertEqual(str(BigStat(1, 3).scale(50)), "5e2")
        self.assertEqual(str(BigStat(1, 2).scale(50)), "5e1")

    def test_big_stat_scale_floors_to_zero_only_without_magnitude(self):
        self.assertEqual(str(BigStat(1, 0).scale(50)), "0e0")
        self.assertEqual(str(BigStat(0, 0).scale(50)), "0e0")
        self.assertEqual(str(BigStat(0, 5).scale(50)), "0e0")

    def test_hard_pity_guarantees_banner_character(self):
        gacha = GachaSystem(sample_characters(), seed=999)
        gacha.rng.uniform = lambda _, __: 100
        result = None
        for _ in range(90):
            result = gacha.pull("star_witch")
        self.assertEqual(result.character_id, "star_witch")
        self.assertEqual(result.rarity.value, "legendary")

    def test_featured_banner_has_discounted_pity_and_bonus_shards(self):
        gacha = GachaSystem(sample_characters(), seed=998)
        gacha.rng.uniform = lambda _, __: 100
        result = None
        for _ in range(80):
            result = gacha.pull("star_witch", featured=True)
        self.assertEqual(result.character_id, "star_witch")
        self.assertEqual(result.rarity.value, "legendary")
        self.assertEqual(result.shards_gained, 15)
        self.assertEqual(gacha.banners["star_witch"].shards, 173)

    def test_featured_non_legendary_pull_grants_bonus_shards(self):
        gacha = GachaSystem(sample_characters(), seed=997)
        gacha.rng.uniform = lambda _, __: 100
        result = gacha.pull("iron_vow", featured=True)
        self.assertEqual(result.rarity.value, "common")
        self.assertEqual(result.shards_gained, 2)
        self.assertEqual(gacha.banners["iron_vow"].shards, 2)

    def test_base_rarity_rates_are_discoverable_and_sum_to_100(self):
        rates = GachaSystem.rarity_rates()
        self.assertEqual(set(rates), {"common", "rare", "epic", "legendary"})
        self.assertAlmostEqual(sum(rates.values()), 100.0)

    def test_pity_tuning_is_discoverable(self):
        self.assertEqual(
            GachaSystem.pity_tuning(),
            {
                "soft_pity_start": 70,
                "hard_pity_target": 90,
                "legendary_shards": 10,
                "non_legendary_shards": 1,
                "soft_pity_increment": 4.5,
            },
        )
        self.assertEqual(
            GachaSystem.pity_tuning(featured=True),
            {
                "soft_pity_start": 60,
                "hard_pity_target": 80,
                "legendary_shards": 15,
                "non_legendary_shards": 2,
                "soft_pity_increment": 4.5,
            },
        )

    def test_soft_pity_increment_drives_legendary_ramp(self):
        gacha = GachaSystem(sample_characters(), seed=1)
        increment = GachaSystem.pity_tuning()["soft_pity_increment"]
        base_legendary = GachaSystem.rarity_rates()["legendary"]
        soft_pity_start = GachaSystem.pity_tuning()["soft_pity_start"]
        gacha.banners["star_witch"].pulls_since_legendary = soft_pity_start - 1
        gacha.rng.uniform = lambda _, __: base_legendary + increment
        result = gacha.pull("star_witch")
        self.assertEqual(result.rarity.value, "legendary")

    def test_pull_rarity_thresholds_follow_base_rates(self):
        gacha = GachaSystem(sample_characters(), seed=1)
        rates = GachaSystem.rarity_rates()
        gacha.rng.uniform = lambda _, __: rates["legendary"]
        self.assertEqual(gacha.pull("star_witch").rarity.value, "legendary")
        gacha.rng.uniform = lambda _, __: rates["legendary"] + rates["epic"]
        self.assertEqual(gacha.pull("rat_squire").rarity.value, "epic")
        gacha.rng.uniform = lambda _, __: rates["legendary"] + rates["epic"] + rates["rare"]
        self.assertEqual(gacha.pull("iron_vow").rarity.value, "rare")
        gacha.rng.uniform = lambda _, __: 100
        self.assertEqual(gacha.pull("iron_vow").rarity.value, "common")

    def test_pull_batch_advances_pity_and_handles_empty_counts(self):
        gacha = GachaSystem(sample_characters(), seed=994)
        gacha.rng.uniform = lambda _, __: 100
        self.assertEqual(gacha.pull_batch("star_witch", 0), [])
        self.assertEqual(gacha.pull_batch("star_witch", -5), [])
        results = gacha.pull_batch("star_witch", 10)
        self.assertEqual(len(results), 10)
        self.assertTrue(all(result.rarity.value == "common" for result in results))
        self.assertEqual(gacha.banners["star_witch"].pulls_since_legendary, 10)
        self.assertEqual(gacha.banners["star_witch"].shards, 10)

    def test_pull_batch_respects_featured_hard_pity(self):
        gacha = GachaSystem(sample_characters(), seed=993)
        gacha.rng.uniform = lambda _, __: 100
        results = gacha.pull_batch("star_witch", 80, featured=True)
        self.assertEqual(results[-1].rarity.value, "legendary")
        self.assertTrue(results[-1].pity_reset)
        self.assertEqual(gacha.banners["star_witch"].pulls_since_legendary, 0)
        self.assertEqual(gacha.banners["star_witch"].shards, 173)

    def test_resonance_track_is_discoverable(self):
        self.assertEqual(
            GachaSystem.resonance_track(),
            [
                {"level": 1, "cost": 20, "node": "origin story"},
                {"level": 2, "cost": 40, "node": "signature skill variant"},
                {"level": 3, "cost": 80, "node": "alternate portrait"},
                {"level": 4, "cost": 120, "node": "lineage title"},
            ],
        )

    def test_resonance_preview_marks_unlocked_and_affordable_nodes(self):
        gacha = GachaSystem(sample_characters(), seed=996)
        gacha.banners["star_witch"].shards = 65
        gacha.upgrade_resonance("star_witch")
        preview = gacha.resonance_preview("star_witch")
        self.assertTrue(preview[0]["unlocked"])
        self.assertFalse(preview[0]["affordable"])
        self.assertFalse(preview[1]["unlocked"])
        self.assertTrue(preview[1]["affordable"])
        self.assertFalse(preview[2]["affordable"])

    def test_shards_upgrade_resonance_nodes(self):
        gacha = GachaSystem(sample_characters(), seed=996)
        gacha.banners["star_witch"].shards = 65
        first = gacha.upgrade_resonance("star_witch")
        self.assertEqual(first.level, 1)
        self.assertEqual(first.node, "origin story")
        self.assertEqual(first.cost, 20)
        self.assertEqual(first.remaining_shards, 45)
        second = gacha.upgrade_resonance("star_witch")
        self.assertEqual(second.level, 2)
        self.assertEqual(second.node, "signature skill variant")
        self.assertEqual(second.remaining_shards, 5)
        self.assertEqual(gacha.next_resonance_cost("star_witch"), 80)

    def test_resonance_requires_shards_and_has_a_cap(self):
        gacha = GachaSystem(sample_characters(), seed=995)
        with self.assertRaises(ValueError):
            gacha.upgrade_resonance("iron_vow")
        gacha.banners["iron_vow"].shards = 260
        for _ in range(4):
            gacha.upgrade_resonance("iron_vow")
        self.assertIsNone(gacha.next_resonance_cost("iron_vow"))
        with self.assertRaises(ValueError):
            gacha.upgrade_resonance("iron_vow")

    def test_inheritance_increases_starting_power(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=3)
        base_stats, _, _ = simulator.start_stats(characters["star_witch"])
        first = simulator.run(characters["star_witch"], "deep_scaling")
        inherited_stats, depth, _ = simulator.start_stats(characters["star_witch"], [first.echo])
        self.assertEqual(depth, 1)
        self.assertGreaterEqual(inherited_stats["atk"].magnitude, base_stats["atk"].magnitude)

    def test_two_parents_increase_lineage_depth_using_the_deeper_parent(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=42)
        simulator.rng.random = lambda: 1.0
        grandparent = simulator.run(characters["iron_vow"], "deep_scaling")
        deep_parent = simulator.run(characters["star_witch"], "deep_scaling", [grandparent.echo])
        shallow_parent = simulator.run(characters["iron_vow"], "deep_scaling")
        self.assertEqual(deep_parent.echo.lineage_depth, 1)
        self.assertEqual(shallow_parent.echo.lineage_depth, 0)

        _, depth, _ = simulator.start_stats(characters["rat_squire"], [deep_parent.echo, shallow_parent.echo])
        self.assertEqual(depth, 2)

    def test_two_parents_contribute_more_stats_than_a_single_parent(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=43)
        simulator.rng.random = lambda: 1.0
        parent_a = simulator.run(characters["iron_vow"], "deep_scaling")
        parent_b = simulator.run(characters["star_witch"], "deep_scaling")

        single_stats, _, _ = simulator.start_stats(characters["rat_squire"], [parent_a.echo])
        dual_stats, _, _ = simulator.start_stats(characters["rat_squire"], [parent_a.echo, parent_b.echo])

        self.assertGreaterEqual(
            (dual_stats["atk"].magnitude, dual_stats["atk"].mantissa),
            (single_stats["atk"].magnitude, single_stats["atk"].mantissa),
        )

    def test_training_run_rejects_more_than_two_parents(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=43)
        simulator.rng.random = lambda: 1.0
        parents = [
            simulator.run(characters["iron_vow"], "deep_scaling").echo,
            simulator.run(characters["star_witch"], "deep_scaling").echo,
            simulator.run(characters["rat_squire"], "deep_scaling").echo,
        ]
        with self.assertRaises(ValueError):
            simulator.start_stats(characters["rat_squire"], parents)
        with self.assertRaises(ValueError):
            simulator.run(characters["rat_squire"], "deep_scaling", parents)

    def test_echo_pool_best_parents_returns_up_to_two_by_power(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=44)
        simulator.rng.random = lambda: 1.0
        pool = EchoPool(capacity=5)
        pool.bank_echo(simulator.run(characters["rat_squire"], "skill_hunt").echo)
        pool.bank_echo(simulator.run(characters["iron_vow"], "deep_scaling").echo)
        pool.bank_echo(simulator.run(characters["star_witch"], "deep_scaling").echo)

        top_two_records = pool.top(2)
        best_two = pool.best_parents(count=2)
        self.assertEqual(len(best_two), 2)
        self.assertEqual(best_two, [record.echo for record in top_two_records])
        self.assertEqual(pool.best_parents(count=1), [top_two_records[0].echo])

    def test_available_routes_are_discoverable(self):
        routes = TrainingSimulator.available_routes()
        self.assertEqual(
            set(routes), {"balanced", "boss_rush", "skill_hunt", "deep_scaling"}
        )

    def test_route_tuning_is_discoverable(self):
        self.assertEqual(
            TrainingSimulator.route_tuning("deep_scaling"),
            {"growth_percent": 125, "magnitude_interval": 8},
        )
        with self.assertRaises(ValueError):
            TrainingSimulator.route_tuning("turbo_mode")

    def test_unknown_route_is_rejected_instead_of_silent_fallback(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=41)
        with self.assertRaises(ValueError):
            simulator.run(characters["iron_vow"], "turbo_mode")

    def test_featured_rotation_is_bounded(self):
        gacha = GachaSystem(sample_characters())
        self.assertEqual(len(gacha.featured_banners_for_week(1)), 3)
        self.assertEqual(len(gacha.featured_banners_for_week(52)), 3)

    def test_annual_featured_rotation_covers_every_banner(self):
        gacha = GachaSystem(sample_characters())
        counts = gacha.annual_featured_counts()
        self.assertEqual(set(counts), set(sample_characters()))
        self.assertEqual(gacha.missing_annual_featured_banners(), [])
        self.assertTrue(all(count > 0 for count in counts.values()))

    def test_featured_schedule_covers_all_current_characters(self):
        gacha = GachaSystem(sample_characters())
        self.assertEqual(gacha.featured_coverage(), sorted(sample_characters()))
        schedule = gacha.featured_schedule(weeks=2, slots_per_week=2)
        self.assertEqual(len(schedule), 2)
        self.assertTrue(all(len(banners) == 2 for banners in schedule))

    def test_featured_rotation_handles_empty_or_disabled_slots(self):
        empty = GachaSystem({})
        self.assertEqual(empty.featured_banners_for_week(1), [])
        self.assertEqual(empty.featured_schedule(), [[] for _ in range(52)])
        gacha = GachaSystem(sample_characters())
        self.assertEqual(gacha.featured_banners_for_week(1, slots_per_week=0), [])
        self.assertEqual(gacha.featured_schedule(weeks=-1), [])
        self.assertEqual(gacha.missing_annual_featured_banners(slots_per_week=0), sorted(sample_characters()))

    def test_echo_is_always_created_even_on_immediate_failure(self):
        from game import CharacterDef, Rarity

        weakling = CharacterDef(
            "weakling",
            "Test Weakling",
            Rarity.COMMON,
            "fighter",
            {"hp": BigStat(50), "atk": BigStat(10), "def": BigStat(10), "spd": BigStat(10)},
            ("Flail",),
            ("frail",),
        )
        simulator = TrainingSimulator(seed=5)
        simulator.rng.random = lambda: 0.0
        result = simulator.run(weakling, "balanced")
        self.assertEqual(result.floors_cleared, 0)
        self.assertFalse(result.victory)
        self.assertIsNotNone(result.echo)
        self.assertEqual(result.rewards.highest_checkpoint_floor, 0)
        self.assertEqual(result.rewards.banked_shards, 0)
        self.assertEqual(result.echo.source_character_id, "weakling")
        self.assertEqual(len(result.encounters), 1)
        self.assertEqual(result.encounters[0].floor, 1)
        self.assertEqual(result.encounters[0].kind, "combat")
        self.assertFalse(result.encounters[0].cleared)

    def test_training_run_records_deterministic_encounters(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=41)
        simulator.rng.random = lambda: 1.0
        result = simulator.run(characters["iron_vow"], "skill_hunt")
        self.assertEqual(len(result.encounters), result.floors_cleared)
        self.assertTrue(all(encounter.cleared for encounter in result.encounters))
        self.assertEqual(
            [encounter.kind for encounter in result.encounters[:4]],
            ["event", "combat", "rest", "boss"],
        )
        self.assertEqual([encounter.floor for encounter in result.encounters], list(range(1, 13)))
        self.assertTrue(all(encounter.power > 0 for encounter in result.encounters))
        self.assertTrue(all(encounter.difficulty > 0 for encounter in result.encounters))

    def test_partial_clear_records_the_failed_floor_encounter(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=5)
        simulator.rng.random = lambda: 0.0
        result = simulator.run(characters["rat_squire"], "balanced")
        self.assertFalse(result.victory)
        self.assertGreater(result.floors_cleared, 0)
        self.assertLess(result.floors_cleared, 12)
        self.assertEqual(len(result.encounters), result.floors_cleared + 1)
        self.assertTrue(all(encounter.cleared for encounter in result.encounters[:-1]))
        failed = result.encounters[-1]
        self.assertFalse(failed.cleared)
        self.assertEqual(failed.floor, result.floors_cleared + 1)
        self.assertEqual(failed.kind, TrainingSimulator.encounter_kind(failed.floor, "balanced"))

    def test_route_patterns_can_emit_all_documented_encounter_types(self):
        kinds = {
            TrainingSimulator.encounter_kind(floor, route)
            for route in ("balanced", "boss_rush", "skill_hunt", "deep_scaling")
            for floor in range(1, 13)
        }
        self.assertEqual(kinds, {"combat", "event", "elite", "boss", "shrine", "rest"})

    def test_checkpoint_rewards_escalate(self):
        simulator = TrainingSimulator(seed=7)
        tier1 = simulator.checkpoint_reward(1, 4)
        tier2 = simulator.checkpoint_reward(2, 8)
        tier3 = simulator.checkpoint_reward(3, 12)
        self.assertLess(tier1.shards, tier2.shards)
        self.assertLess(tier2.shards, tier3.shards)
        self.assertLess(tier1.relic_rolls, tier2.relic_rolls)
        self.assertLess(tier1.echo_quality_bonus, tier2.echo_quality_bonus)

    def test_banked_rewards_are_monotonic_and_full_clear_banks_all(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=11)
        simulator.rng.random = lambda: 1.0
        result = simulator.run(characters["iron_vow"], "deep_scaling")
        self.assertEqual(result.floors_cleared, 12)
        self.assertEqual(result.rewards.highest_checkpoint_floor, 12)
        self.assertEqual(len(result.rewards.checkpoints), 3)
        banked = [cp.shards for cp in result.rewards.checkpoints]
        self.assertEqual(banked, sorted(banked))
        self.assertEqual(result.rewards.banked_shards, sum(banked))
        self.assertGreater(result.rewards.echo_quality_percent, 100)

    def test_pushing_further_is_worth_more(self):
        characters = sample_characters()
        early = TrainingSimulator(seed=2)
        early.rng.random = lambda: 0.0
        early_result = early.run(characters["iron_vow"], "deep_scaling")
        full = TrainingSimulator(seed=2)
        full.rng.random = lambda: 1.0
        full_result = full.run(characters["iron_vow"], "deep_scaling")
        self.assertGreater(full_result.rewards.banked_shards, early_result.rewards.banked_shards)
        self.assertGreater(
            full_result.rewards.echo_quality_percent,
            early_result.rewards.echo_quality_percent,
        )

    def test_checkpoint_rewards_stay_banked_after_later_failure(self):
        from game import CharacterDef, Rarity

        checkpoint_runner = CharacterDef(
            "checkpoint_runner",
            "Test Checkpoint Runner",
            Rarity.COMMON,
            "fighter",
            {"hp": BigStat(460), "atk": BigStat(110), "def": BigStat(110), "spd": BigStat(110)},
            ("Push",),
            ("steady",),
        )
        simulator = TrainingSimulator(seed=13)
        simulator.rng.random = lambda: 0.0
        result = simulator.run(checkpoint_runner, "boss_rush")
        self.assertEqual(result.floors_cleared, 4)
        self.assertFalse(result.victory)
        self.assertIsNotNone(result.echo)
        self.assertEqual(result.rewards.highest_checkpoint_floor, 4)
        self.assertEqual(result.rewards.banked_shards, 15)
        self.assertEqual(result.rewards.relic_rolls, 1)

    def test_instability_pays_a_dividend_only_when_a_checkpoint_is_banked(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=31)
        simulator.rng.random = lambda: 1.0
        stable = simulator.run(characters["iron_vow"], "deep_scaling")
        self.assertEqual(stable.rewards.instability_dividend_shards, 0)

        seeded = simulator.run(characters["star_witch"], "deep_scaling")
        child_stats, _, instability = simulator.start_stats(characters["star_witch"], [seeded.echo])
        self.assertGreater(instability, 0)
        risky = simulator.run(characters["star_witch"], "deep_scaling", [seeded.echo])
        self.assertEqual(risky.rewards.highest_checkpoint_floor, 12)
        self.assertGreater(risky.rewards.instability_dividend_shards, 0)
        self.assertEqual(
            risky.rewards.banked_shards
            - risky.rewards.instability_dividend_shards,
            stable.rewards.banked_shards,
        )

    def test_instability_dividend_is_forfeited_on_pre_checkpoint_failure(self):
        from game import CharacterDef, Rarity

        glass = CharacterDef(
            "glass",
            "Test Glass Cannon",
            Rarity.COMMON,
            "caster",
            {"hp": BigStat(40), "atk": BigStat(10), "def": BigStat(10), "spd": BigStat(10)},
            ("Zap",),
            ("frail",),
        )
        simulator = TrainingSimulator(seed=33)
        simulator.rng.random = lambda: 0.0
        result = simulator.run(glass, "balanced")
        self.assertEqual(result.floors_cleared, 0)
        self.assertEqual(result.rewards.instability_dividend_shards, 0)

    def test_echo_pool_ranks_without_pruning_and_enforces_capacity(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=21)
        simulator.rng.random = lambda: 1.0
        pool = EchoPool(capacity=2)
        weak = simulator.run(characters["rat_squire"], "skill_hunt")
        strong = simulator.run(characters["star_witch"], "deep_scaling", [weak.echo])
        strongest = simulator.run(characters["iron_vow"], "deep_scaling", [strong.echo])
        pool.bank_echo(weak.echo)
        pool.bank_echo(strong.echo)
        with self.assertRaises(ValueError):
            pool.bank_echo(strongest.echo)
        self.assertEqual(len(pool), 2)
        scores = [record.power_score for record in pool.top(2)]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(pool.best_parents(count=1), [pool.top(1)[0].echo])

    def test_echo_pool_supports_favorites_icons_delete_and_exchange(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=23)
        simulator.rng.random = lambda: 1.0
        pool = EchoPool(capacity=3)
        iron = simulator.run(characters["iron_vow"], "deep_scaling")
        witch = simulator.run(characters["star_witch"], "deep_scaling")
        iron_record = pool.bank_echo(iron.echo, icon="shield")
        witch_record = pool.bank_echo(witch.echo, icon="star")
        updated = pool.update_record(witch_record.id, favorite=True, icon="favorite_star")
        self.assertTrue(updated.favorite)
        self.assertEqual(pool.sorted_records("icon", descending=False)[0].icon, "favorite_star")
        with self.assertRaises(ValueError):
            pool.delete_echo(witch_record.id)
        with self.assertRaises(ValueError):
            pool.exchange_echo(witch_record.id)
        removed = pool.delete_echo(iron_record.id)
        self.assertEqual(removed.id, iron_record.id)
        pool.update_record(witch_record.id, favorite=False)
        reward = pool.exchange_echo(witch_record.id, event_multiplier=2)
        self.assertGreater(reward.essence, 0)
        self.assertGreater(reward.shards, 0)
        self.assertEqual(len(pool), 0)

    def test_echo_pool_favorite_cap_prevents_soft_lock(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=24)
        simulator.rng.random = lambda: 1.0
        pool = EchoPool(capacity=3)
        self.assertEqual(pool.max_favorites, 2)
        records = [
            pool.bank_echo(simulator.run(characters["iron_vow"], "deep_scaling").echo)
            for _ in range(3)
        ]
        pool.update_record(records[0].id, favorite=True)
        pool.update_record(records[1].id, favorite=True)
        with self.assertRaises(ValueError):
            pool.update_record(records[2].id, favorite=True)
        self.assertLess(pool.favorite_count, pool.capacity)
        self.assertEqual(pool.delete_echo(records[2].id).id, records[2].id)

    def test_echo_pool_custom_favorite_cap_cannot_lock_pool(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=27)
        simulator.rng.random = lambda: 1.0
        pool = EchoPool(capacity=2, max_favorites=99)
        self.assertEqual(pool.max_favorites, 1)
        first = pool.bank_echo(simulator.run(characters["iron_vow"], "deep_scaling").echo, favorite=True)
        second = pool.bank_echo(simulator.run(characters["star_witch"], "deep_scaling").echo)
        with self.assertRaises(ValueError):
            pool.update_record(second.id, favorite=True)
        self.assertEqual(pool.delete_echo(second.id).id, second.id)
        self.assertIsNotNone(pool.get_record(first.id))

    def test_echo_pool_batch_exchange_event_aggregates_rewards(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=25)
        simulator.rng.random = lambda: 1.0
        pool = EchoPool(capacity=5)
        ids = [
            pool.bank_echo(simulator.run(characters["star_witch"], "deep_scaling").echo).id
            for _ in range(3)
        ]
        keep = pool.bank_echo(simulator.run(characters["iron_vow"], "deep_scaling").echo, favorite=True)
        single = pool.exchange_echo(ids[0])
        with self.assertRaises(ValueError):
            pool.exchange_event([ids[1], keep.id])
        self.assertIsNotNone(pool.get_record(ids[1]))
        batch = pool.exchange_event(ids[1:], event_multiplier=2)
        self.assertGreaterEqual(batch.essence, single.essence)
        self.assertEqual(len(pool), 1)
        self.assertEqual(pool.records[0].id, keep.id)
        with self.assertRaises(ValueError):
            pool.exchange_event([keep.id])

    def test_echo_pool_batch_exchange_is_atomic_on_failure(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=27)
        simulator.rng.random = lambda: 1.0
        pool = EchoPool(capacity=5)
        first = pool.bank_echo(simulator.run(characters["star_witch"], "deep_scaling").echo).id
        favorite = pool.bank_echo(
            simulator.run(characters["iron_vow"], "deep_scaling").echo, favorite=True
        ).id
        second = pool.bank_echo(simulator.run(characters["star_witch"], "deep_scaling").echo).id

        with self.assertRaises(ValueError):
            pool.exchange_event([first, favorite, second])
        self.assertEqual([record.id for record in pool.records], [first, favorite, second])

        with self.assertRaises(KeyError):
            pool.exchange_event([first, 9999])
        self.assertEqual([record.id for record in pool.records], [first, favorite, second])

        with self.assertRaises(ValueError):
            pool.exchange_event([first, first])
        self.assertEqual([record.id for record in pool.records], [first, favorite, second])

        reward = pool.exchange_event([first, second])
        self.assertGreater(reward.essence, 0)
        self.assertEqual([record.id for record in pool.records], [favorite])

    def test_echo_pool_can_filter_by_source_character(self):
        characters = sample_characters()
        simulator = TrainingSimulator(seed=22)
        simulator.rng.random = lambda: 1.0
        pool = EchoPool(capacity=5)
        iron = simulator.run(characters["iron_vow"], "deep_scaling")
        witch = simulator.run(characters["star_witch"], "deep_scaling")
        pool.bank_echo(iron.echo)
        pool.bank_echo(witch.echo)
        self.assertEqual(pool.best_parents("iron_vow")[0].source_character_id, "iron_vow")
        self.assertEqual(pool.best_parents("missing"), [])

    def test_relic_forge_spends_relic_rolls(self):
        forge = RelicForge(seed=4)
        relics = forge.forge(5)
        self.assertEqual(len(relics), 5)
        self.assertEqual(forge.forge(0), [])
        self.assertEqual(forge.forge(-3), [])
        for relic in relics:
            self.assertIn(relic.stat, ("hp", "atk", "def", "spd"))
            self.assertGreater(relic.bonus_percent, 0)
        ids = [relic.id for relic in relics]
        self.assertEqual(ids, sorted(set(ids)))

    def test_relics_boost_only_their_stat(self):
        from game import Rarity, Relic

        base = {"hp": BigStat(100), "atk": BigStat(200)}
        relics = [Relic(1, "Epic ATK Sigil", Rarity.EPIC, "atk", 25)]
        boosted = RelicForge.apply_relics(base, relics)
        self.assertEqual(str(boosted["atk"]), str(BigStat(250)))
        self.assertEqual(str(boosted["hp"]), str(BigStat(100)))
        self.assertEqual(str(base["atk"]), str(BigStat(200)))

    def test_relic_forge_is_deterministic_per_seed(self):
        first = [r.name for r in RelicForge(seed=9).forge(6)]
        second = [r.name for r in RelicForge(seed=9).forge(6)]
        self.assertEqual(first, second)

    def test_relic_forge_rarity_thresholds_are_ordered_common_to_legendary(self):
        forge = RelicForge(seed=10)
        forge.rng.uniform = lambda _, __: 50
        self.assertEqual(forge.roll_relic().rarity.value, "common")
        forge.rng.uniform = lambda _, __: 75
        self.assertEqual(forge.roll_relic().rarity.value, "rare")
        forge.rng.uniform = lambda _, __: 90
        self.assertEqual(forge.roll_relic().rarity.value, "epic")
        forge.rng.uniform = lambda _, __: 99
        self.assertEqual(forge.roll_relic().rarity.value, "legendary")

    def test_demo_pipeline_runs_end_to_end(self):
        with redirect_stdout(io.StringIO()):
            result = demo()
        self.assertEqual(len(result["pulls"]), 10)
        self.assertEqual(len(result["banked_records"]), 3)
        self.assertEqual(len(result["echo_pool"]), 3)
        second = result["second"]
        self.assertEqual(second.echo.lineage_depth, 1)
        third = result["third"]
        self.assertEqual(third.echo.lineage_depth, 2)
        self.assertEqual(len(result["relics"]), third.rewards.relic_rolls)
        for stat, value in result["forged_stats"].items():
            self.assertGreaterEqual(
                (value.magnitude, value.mantissa),
                (third.echo.stats[stat].magnitude, third.echo.stats[stat].mantissa),
            )

    def test_asset_pack_classifier(self):
        category, use = classify_asset_pack("isle-of-lore-2-ui-pack-final.zip")
        self.assertEqual(category, "interface")
        self.assertIn("menus", use)

    def test_asset_catalog_reads_project_packs(self):
        packs = catalog_asset_directory(Path(__file__).parents[1] / "Game-Assets")
        self.assertGreaterEqual(len(packs), 10)
        self.assertTrue(any(pack.category == "interface" for pack in packs))


if __name__ == "__main__":
    unittest.main()
