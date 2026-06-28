class_name BannerState
extends RefCounted
## Mutable per-character banner progress.
##
## Ported 1:1 from the Python prototype's `BannerState` dataclass
## (`prototype/game.py`). Tracks pity counter, accumulated resonance shards, and
## the unlocked resonance level for a single character's banner.

var character_id: String
var pulls_since_legendary: int
var shards: int
var resonance_level: int


func _init(
	p_character_id: String,
	p_pulls_since_legendary: int = 0,
	p_shards: int = 0,
	p_resonance_level: int = 0
) -> void:
	character_id = p_character_id
	pulls_since_legendary = p_pulls_since_legendary
	shards = p_shards
	resonance_level = p_resonance_level
