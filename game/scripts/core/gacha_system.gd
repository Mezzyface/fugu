class_name GachaSystem
extends RefCounted
## Banner pulls, pity, the 52-week featured rotation, and resonance-node spending.
##
## Ported 1:1 from the Python prototype's `GachaSystem` (`prototype/game.py`).
## Each character owns a [BannerState] tracking pity and shards. Pulls roll a
## uniform value in [0, 100]; soft pity ramps the Legendary chance and hard pity
## guarantees a Legendary once the per-banner counter reaches the target.
##
## Determinism: pulls draw from a seeded [RandomNumberGenerator], so the same
## seed reproduces the same sequence (matching the Python `Random(seed)` contract,
## though the underlying algorithm differs). Tests force specific rolls by
## replacing [member uniform_func] with their own [Callable] — the GDScript
## equivalent of the prototype's `gacha.rng.uniform = lambda ...` monkeypatch.

## (cost, node label) for each resonance level, in unlock order.
const RESONANCE_NODES: Array = [
	[20, "origin story"],
	[40, "signature skill variant"],
	[80, "alternate portrait"],
	[120, "lineage title"],
]

## Base drop rates per rarity string; sums to 100.
const BASE_RARITY_RATES: Dictionary = {
	"common": 79.5,
	"rare": 15.0,
	"epic": 4.0,
	"legendary": 1.5,
}

## Pity tuning keyed by whether the banner is featured (true) or permanent (false).
const BANNER_TUNING: Dictionary = {
	false:
	{
		"soft_pity_start": 70,
		"hard_pity_target": 90,
		"legendary_shards": 10,
		"non_legendary_shards": 1,
		"soft_pity_increment": 4.5,
	},
	true:
	{
		"soft_pity_start": 60,
		"hard_pity_target": 80,
		"legendary_shards": 15,
		"non_legendary_shards": 2,
		"soft_pity_increment": 4.5,
	},
}

var characters: Dictionary
var rng := RandomNumberGenerator.new()
## Roll source for [method pull]; defaults to the seeded RNG. Override in tests
## to force a specific roll, e.g. `gacha.uniform_func = func(_a, _b): return 100.0`.
var uniform_func: Callable
var banners: Dictionary


func _init(p_characters: Dictionary, p_seed: int = 1) -> void:
	characters = p_characters
	rng.seed = p_seed
	uniform_func = _rng_uniform
	banners = {}
	for character_id: String in characters:
		banners[character_id] = BannerState.new(character_id)


## Default [member uniform_func]: a uniform draw in [low, high] from the seeded RNG.
func _rng_uniform(low: float, high: float) -> float:
	return rng.randf_range(low, high)


## Fresh copy of the base rarity rates (mirrors the Python classmethod).
static func rarity_rates() -> Dictionary:
	return BASE_RARITY_RATES.duplicate(true)


## Fresh copy of the pity tuning for a permanent (default) or featured banner.
static func pity_tuning(featured: bool = false) -> Dictionary:
	return (BANNER_TUNING[featured] as Dictionary).duplicate(true)


## The resonance track as a list of `{level, cost, node}` dictionaries.
static func resonance_track() -> Array:
	var track: Array = []
	var level := 1
	for node: Array in RESONANCE_NODES:
		track.append({"level": level, "cost": node[0], "node": node[1]})
		level += 1
	return track


## Per-node preview for a character marking which nodes are unlocked and which the
## next affordable upgrade is.
func resonance_preview(character_id: String) -> Array:
	var banner: BannerState = banners[character_id]
	var preview: Array = []
	for entry: Dictionary in resonance_track():
		var level: int = entry["level"]
		preview.append(
			{
				"level": level,
				"cost": entry["cost"],
				"node": entry["node"],
				"unlocked": level <= banner.resonance_level,
				"affordable":
				level == banner.resonance_level + 1 and banner.shards >= int(entry["cost"]),
			}
		)
	return preview


## Cost of the next resonance node, or `null` if the track is complete.
func next_resonance_cost(character_id: String) -> Variant:
	var banner: BannerState = banners[character_id]
	if banner.resonance_level >= RESONANCE_NODES.size():
		return null
	return RESONANCE_NODES[banner.resonance_level][0]


## Spend shards to unlock the next resonance node. Pushes an error and returns
## `null` if the track is complete or the banner cannot afford the node (the
## prototype raised `ValueError`).
func upgrade_resonance(character_id: String) -> ResonanceUpgrade:
	var banner: BannerState = banners[character_id]
	if banner.resonance_level >= RESONANCE_NODES.size():
		push_error("resonance track complete")
		return null
	var entry: Array = RESONANCE_NODES[banner.resonance_level]
	var cost: int = entry[0]
	var node: String = entry[1]
	if banner.shards < cost:
		push_error("not enough shards")
		return null
	banner.shards -= cost
	banner.resonance_level += 1
	return ResonanceUpgrade.new(character_id, banner.resonance_level, node, cost, banner.shards)


## Perform a single pull on a character's banner. Advances pity, applies soft/hard
## pity, awards shards, and returns the [PullResult].
func pull(banner_character_id: String, featured: bool = false) -> PullResult:
	var banner: BannerState = banners[banner_character_id]
	var tuning := pity_tuning(featured)
	banner.pulls_since_legendary += 1
	var soft_pity_start: int = tuning["soft_pity_start"]
	var hard_pity_target: int = tuning["hard_pity_target"]
	var legendary_shards: int = tuning["legendary_shards"]
	var non_legendary_shards: int = tuning["non_legendary_shards"]
	var soft_pity_increment: float = tuning["soft_pity_increment"]
	var legendary_chance: float = BASE_RARITY_RATES["legendary"]
	if banner.pulls_since_legendary >= soft_pity_start:
		legendary_chance += (
			(banner.pulls_since_legendary - soft_pity_start + 1) * soft_pity_increment
		)
	var hard_pity := banner.pulls_since_legendary >= hard_pity_target
	var epic_threshold: float = BASE_RARITY_RATES["legendary"] + BASE_RARITY_RATES["epic"]
	var rare_threshold: float = epic_threshold + BASE_RARITY_RATES["rare"]
	var roll: float = uniform_func.call(0.0, 100.0)
	if hard_pity or roll <= legendary_chance:
		banner.pulls_since_legendary = 0
		banner.shards += legendary_shards
		return PullResult.new(Rarity.LEGENDARY, banner_character_id, legendary_shards, true)
	var rarity: int
	if roll <= epic_threshold:
		rarity = Rarity.EPIC
	elif roll <= rare_threshold:
		rarity = Rarity.RARE
	else:
		rarity = Rarity.COMMON
	banner.shards += non_legendary_shards
	return PullResult.new(rarity, banner_character_id, non_legendary_shards, false)


## Perform `count` pulls in sequence; a non-positive `count` yields an empty list.
func pull_batch(banner_character_id: String, count: int = 10, featured: bool = false) -> Array:
	var results: Array = []
	for _i in range(maxi(0, count)):
		results.append(pull(banner_character_id, featured))
	return results


## The featured banner ids active in a given week (1-based), wrapping around the
## sorted roster so the schedule repeats predictably.
func featured_banners_for_week(week: int, slots_per_week: int = 3) -> Array:
	var ids := characters.keys()
	ids.sort()
	if ids.is_empty() or slots_per_week <= 0:
		return []
	var start := ((maxi(1, week) - 1) * slots_per_week) % ids.size()
	var result: Array = []
	for index in range(mini(slots_per_week, ids.size())):
		result.append(ids[(start + index) % ids.size()])
	return result


## The week-by-week featured schedule for the first `weeks` weeks.
func featured_schedule(weeks: int = 52, slots_per_week: int = 3) -> Array:
	var schedule: Array = []
	for week in range(1, maxi(0, weeks) + 1):
		schedule.append(featured_banners_for_week(week, slots_per_week))
	return schedule


## Sorted list of every banner id that appears at least once across the schedule.
func featured_coverage(weeks: int = 52, slots_per_week: int = 3) -> Array:
	var seen: Dictionary = {}
	for banners_for_week: Array in featured_schedule(weeks, slots_per_week):
		for banner_id: String in banners_for_week:
			seen[banner_id] = true
	var coverage := seen.keys()
	coverage.sort()
	return coverage


## Count of featured appearances per banner over the schedule window.
func annual_featured_counts(weeks: int = 52, slots_per_week: int = 3) -> Dictionary:
	var counts: Dictionary = {}
	for character_id: String in characters:
		counts[character_id] = 0
	for week in range(1, maxi(0, weeks) + 1):
		for character_id: String in featured_banners_for_week(week, slots_per_week):
			counts[character_id] += 1
	return counts


## Sorted list of banners that never appear in the schedule window.
func missing_annual_featured_banners(weeks: int = 52, slots_per_week: int = 3) -> Array:
	var counts := annual_featured_counts(weeks, slots_per_week)
	var missing: Array = []
	for character_id: String in counts:
		if counts[character_id] == 0:
			missing.append(character_id)
	missing.sort()
	return missing
