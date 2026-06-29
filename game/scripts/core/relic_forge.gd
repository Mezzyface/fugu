class_name RelicForge
extends RefCounted
## Relic-roll sink: turns relic rolls into weighted-rarity stat [Relic]s.
##
## Ported 1:1 from the Python prototype's `RelicForge` (`prototype/game.py`).
## Each roll picks a rarity by cumulative weight (common is most likely,
## legendary rarest) and a random stat, then mints a [Relic] with a unique,
## monotonically increasing id. Forging is deterministic for a given seed.
##
## The Python sequence cannot be reproduced bit-for-bit because Godot's RNG
## differs from CPython's, but the same seed always yields the same sequence
## here — which is what callers and tests rely on.

## Cumulative roll thresholds (inclusive, out of 100) paired with the rarity and
## bonus percent they award. Ordered common-to-legendary; the first threshold the
## roll falls at or below wins.
const RELIC_RARITIES: Array = [
	[60, Rarity.COMMON, 8],
	[85, Rarity.RARE, 15],
	[97, Rarity.EPIC, 25],
	[100, Rarity.LEGENDARY, 40],
]
## Stat keys a relic can target, matching the prototype's tuple order.
const RELIC_STATS: PackedStringArray = ["hp", "atk", "def", "spd"]

var _rng := RandomNumberGenerator.new()
var _next_id: int = 1


func _init(seed_value: int = 4) -> void:
	_rng.seed = seed_value


## Maps a roll in [0, 100] to its `[rarity, bonus_percent]`. Returns the first
## tier whose threshold the roll falls at or below; defaults to common.
static func rarity_for_roll(roll: float) -> Array:
	for tier: Array in RELIC_RARITIES:
		if roll <= tier[0]:
			return [tier[1], tier[2]]
	return [Rarity.COMMON, 8]


## Rolls a single relic: weighted rarity, random stat, unique id.
func roll_relic() -> Relic:
	var roll := _rng.randf_range(0.0, 100.0)
	var picked := rarity_for_roll(roll)
	var rarity: int = picked[0]
	var bonus: int = picked[1]
	var stat := RELIC_STATS[_rng.randi() % RELIC_STATS.size()]
	var relic_name := "%s %s Sigil" % [Rarity.to_string_value(rarity).capitalize(), stat.to_upper()]
	var relic := Relic.new(_next_id, relic_name, rarity, stat, bonus)
	_next_id += 1
	return relic


## Rolls `relic_rolls` relics (clamped at zero, so negatives yield an empty list).
func forge(relic_rolls: int) -> Array[Relic]:
	var relics: Array[Relic] = []
	for _i in maxi(0, relic_rolls):
		relics.append(roll_relic())
	return relics


## Returns a copy of `stats` with each relic's bonus applied to its target stat.
## Does not mutate the input dictionary or its [BigStat] values — missing stats
## default to zero before scaling.
static func apply_relics(stats: Dictionary, relics: Array) -> Dictionary:
	var boosted := stats.duplicate()
	for relic: Relic in relics:
		var current: BigStat = boosted.get(relic.stat, BigStat.new(0))
		boosted[relic.stat] = current.scale(100 + relic.bonus_percent)
	return boosted
