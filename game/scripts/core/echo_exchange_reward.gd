class_name EchoExchangeReward
extends RefCounted
## Currency payout from exchanging one or more echoes back to the pool.
##
## Ported 1:1 from the Python prototype's frozen `EchoExchangeReward` dataclass
## (`prototype/game.py`). Batch exchanges sum these field-by-field.

var essence: int
var shards: int
var relic_rolls: int


func _init(p_essence: int, p_shards: int, p_relic_rolls: int) -> void:
	essence = p_essence
	shards = p_shards
	relic_rolls = p_relic_rolls
