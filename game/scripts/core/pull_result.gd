class_name PullResult
extends RefCounted
## Outcome of a single gacha pull.
##
## Ported 1:1 from the Python prototype's frozen `PullResult` dataclass
## (`prototype/game.py`). `rarity` is a [Rarity] enum value; `pity_reset` is true
## only when the pull rolled (or was forced to) Legendary and cleared the pity
## counter.

var rarity: int
var character_id: String
var shards_gained: int
var pity_reset: bool


func _init(p_rarity: int, p_character_id: String, p_shards_gained: int, p_pity_reset: bool) -> void:
	rarity = p_rarity
	character_id = p_character_id
	shards_gained = p_shards_gained
	pity_reset = p_pity_reset
