class_name ResonanceUpgrade
extends RefCounted
## Result of spending shards to unlock a resonance node.
##
## Ported 1:1 from the Python prototype's frozen `ResonanceUpgrade` dataclass
## (`prototype/game.py`). Reports the newly unlocked `level`, its `node` label,
## the `cost` paid, and the shards left over afterwards.

var character_id: String
var level: int
var node: String
var cost: int
var remaining_shards: int


func _init(
	p_character_id: String, p_level: int, p_node: String, p_cost: int, p_remaining_shards: int
) -> void:
	character_id = p_character_id
	level = p_level
	node = p_node
	cost = p_cost
	remaining_shards = p_remaining_shards
