class_name CheckpointReward
extends RefCounted
## A reward banked when a training run clears a checkpoint floor.
##
## Ported 1:1 from the Python prototype's frozen `CheckpointReward` dataclass
## (`prototype/game.py`). Rewards escalate with `tier` (every checkpoint interval
## cleared): shards double, relic rolls and echo-quality bonus grow linearly.

var floor: int
var tier: int
var shards: int
var relic_rolls: int
var echo_quality_bonus: int


func _init(
	p_floor: int, p_tier: int, p_shards: int, p_relic_rolls: int, p_echo_quality_bonus: int
) -> void:
	floor = p_floor
	tier = p_tier
	shards = p_shards
	relic_rolls = p_relic_rolls
	echo_quality_bonus = p_echo_quality_bonus
