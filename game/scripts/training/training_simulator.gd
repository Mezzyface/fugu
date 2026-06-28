class_name TrainingSimulator
extends RefCounted
## The 12-floor training run engine — the game's training pillar.
##
## Ported 1:1 from the Python prototype's `TrainingSimulator` (`prototype/game.py`).
## A run walks floors 1..12: each floor is an encounter the character either clears
## (growing its stats) or fails (ending the run). Clearing checkpoint floors banks
## escalating rewards plus an "instability dividend", and clearing boss-gate floors
## (every 4th) is logged. Runs are deterministic per seed; the single random draw —
## whether an under-powered floor fails — is taken from [member random_source] so
## tests can pin it to a constant.

## Per-route tuning: `route -> [growth_percent, magnitude_interval]`. `growth_percent`
## is the per-floor stat multiplier; every `magnitude_interval`-th cleared floor also
## bumps each stat's magnitude. Insertion order defines [method available_routes].
const ROUTE_GROWTH := {
	"balanced": [112, 4],
	"boss_rush": [118, 5],
	"skill_hunt": [108, 3],
	"deep_scaling": [125, 8],
}
const MAX_PARENTS := 2

var checkpoint_interval: int
## Source of the per-floor failure roll, a [Callable] returning a float in [0, 1).
## Defaults to a seeded [RandomNumberGenerator]; override to force outcomes in tests
## (e.g. `func() -> float: return 1.0` to never fail an under-powered floor).
var random_source: Callable

var _rng := RandomNumberGenerator.new()


func _init(p_seed: int = 2, p_checkpoint_interval: int = 4) -> void:
	_rng.seed = p_seed
	checkpoint_interval = maxi(1, p_checkpoint_interval)
	random_source = func() -> float: return _rng.randf()


## The routes a player may choose, in declaration order.
static func available_routes() -> PackedStringArray:
	return PackedStringArray(ROUTE_GROWTH.keys())


## Tuning for `route` as `{"growth_percent": int, "magnitude_interval": int}`.
## An unknown route is rejected (the prototype raised `ValueError`); here it pushes
## an error and returns an empty dictionary.
static func route_tuning(route: String) -> Dictionary:
	if not ROUTE_GROWTH.has(route):
		push_error(
			(
				"unknown training route %s; choose from %s"
				% [route, ", ".join(available_routes())]
			)
		)
		return {}
	var pair: Array = ROUTE_GROWTH[route]
	return {"growth_percent": pair[0], "magnitude_interval": pair[1]}


## The encounter kind for a floor on a route. Every 4th floor is a boss; otherwise
## the route's repeating 4-floor pattern decides.
static func encounter_kind(floor: int, route: String = "balanced") -> String:
	if floor % 4 == 0:
		return "boss"
	var route_encounters := {
		"balanced": ["combat", "event", "rest", "elite"],
		"boss_rush": ["combat", "elite", "rest", "elite"],
		"skill_hunt": ["event", "combat", "rest", "shrine"],
		"deep_scaling": ["combat", "shrine", "rest", "elite"],
	}
	var pattern: Array = route_encounters.get(route, ["combat", "event", "rest", "elite"])
	return pattern[(floor - 1) % pattern.size()]


## The reward banked when checkpoint `tier` (1-based) is cleared at `floor`.
## Shards double per tier; relic rolls and echo-quality bonus grow linearly.
func checkpoint_reward(tier: int, floor: int) -> CheckpointReward:
	return CheckpointReward.new(floor, tier, 15 * (1 << (tier - 1)), tier, 20 * tier)


## Computes a character's starting stats for a run, folding in up to [constant
## MAX_PARENTS] inherited echoes. Returns `[stats: Dictionary, lineage_depth: int,
## instability: int]`. Lineage depth is one deeper than the deepest parent (or 0
## with no parents); inheriting beyond the parent cap is rejected (the prototype
## raised `ValueError`) — here it pushes an error and returns the base stats.
func start_stats(character: CharacterDef, parents: Array = []) -> Array:
	if parents.size() > MAX_PARENTS:
		push_error(
			"at most %d parents may be inherited, got %d" % [MAX_PARENTS, parents.size()]
		)
		return [character.base_stats.duplicate(), 0, 0]
	var stats: Dictionary = character.base_stats.duplicate()
	var lineage_depth := -1
	for parent: FrozenEcho in parents:
		lineage_depth = maxi(lineage_depth, parent.lineage_depth)
	lineage_depth += 1
	var instability := 0
	for parent: FrozenEcho in parents:
		var depth_factor := maxi(35, 100 - parent.lineage_depth * 8)
		for stat_name: String in parent.stats:
			var parent_value: BigStat = parent.stats[stat_name]
			var inherited := parent_value.scale(25 * depth_factor, 10000)
			var base: BigStat = stats.get(stat_name, BigStat.new(0))
			stats[stat_name] = base.add(inherited)
			var base_magnitude: int = character.base_stats.get(stat_name, BigStat.new(1)).magnitude
			instability += maxi(0, inherited.magnitude - base_magnitude)
	return [stats, lineage_depth, instability]


## Executes a full 12-floor run and returns its [RunResult]. Always yields an echo,
## even on immediate failure. An unknown route or too many parents is rejected via
## `push_error` and returns an unsuccessful result.
func run(character: CharacterDef, route: String = "balanced", parents: Array = []) -> RunResult:
	if not ROUTE_GROWTH.has(route):
		var _tuning_check := route_tuning(route)  # surfaces the push_error
		return _rejected_result(character)
	if parents.size() > MAX_PARENTS:
		var _start_check := start_stats(character, parents)  # surfaces the push_error
		return _rejected_result(character)

	var start := start_stats(character, parents)
	var stats: Dictionary = start[0]
	var lineage_depth: int = start[1]
	var instability: int = start[2]

	var tuning := route_tuning(route)
	var growth_percent: int = tuning["growth_percent"]
	var magnitude_interval: int = tuning["magnitude_interval"]

	var run_log: Array[String] = []
	var floors_cleared := 0
	var rewards := RunRewards.new()
	var encounters: Array[EncounterRecord] = []

	for floor in range(1, 13):
		var power := 0
		for value: BigStat in stats.values():
			power += value.mantissa + value.magnitude * 1000
		var difficulty := 120 + floor * floor * 65 + instability * 40
		var kind := encounter_kind(floor, route)
		if power < difficulty and random_source.call() < 0.45:
			encounters.append(EncounterRecord.new(floor, kind, power, difficulty, false))
			run_log.append(
				"failed %s floor %d at power %d vs difficulty %d" % [kind, floor, power, difficulty]
			)
			break
		encounters.append(EncounterRecord.new(floor, kind, power, difficulty, true))
		floors_cleared = floor
		for stat_name: String in stats.keys():
			var value: BigStat = stats[stat_name].scale(growth_percent)
			if floor % magnitude_interval == 0:
				value = BigStat.new(value.mantissa, value.magnitude + 1).normalized()
			stats[stat_name] = value
		if floor % 4 == 0:
			run_log.append("boss gate %d cleared" % floor)
		if floor % checkpoint_interval == 0:
			var tier := floor / checkpoint_interval
			var reward := checkpoint_reward(tier, floor)
			rewards.checkpoints.append(reward)
			rewards.banked_shards += reward.shards
			rewards.relic_rolls += reward.relic_rolls
			rewards.highest_checkpoint_floor = floor
			rewards.echo_quality_percent += reward.echo_quality_bonus
			var dividend := instability * 5 * tier
			rewards.instability_dividend_shards += dividend
			rewards.banked_shards += dividend
			run_log.append(
				(
					"checkpoint tier %d banked at floor %d: +%d shards, +%d relic rolls, "
					+ "+%d instability dividend, echo quality %d%%"
				)
				% [
					tier,
					floor,
					reward.shards,
					reward.relic_rolls,
					dividend,
					rewards.echo_quality_percent
				]
			)

	var victory := floors_cleared == 12
	var echo_stats := {}
	for stat_name: String in stats:
		echo_stats[stat_name] = stats[stat_name].scale(rewards.echo_quality_percent)
	var echo := FrozenEcho.new(
		character.id,
		echo_stats,
		character.skills.slice(0, 3),
		character.traits.slice(0, 2),
		lineage_depth,
		instability
	)
	return RunResult.new(floors_cleared, victory, echo, rewards, run_log, encounters)


## A baseline unsuccessful result returned when a run is rejected during validation.
## Still carries an echo so callers can rely on the always-echo invariant.
func _rejected_result(character: CharacterDef) -> RunResult:
	var echo := FrozenEcho.new(
		character.id,
		character.base_stats.duplicate(),
		character.skills.slice(0, 3),
		character.traits.slice(0, 2),
		0,
		0
	)
	var empty_encounters: Array[EncounterRecord] = []
	var empty_log: Array[String] = []
	return RunResult.new(0, false, echo, RunRewards.new(), empty_log, empty_encounters)
