class_name CharacterDef
extends RefCounted
## Immutable definition of a roster character.
##
## Ported 1:1 from the Python prototype's frozen `CharacterDef` dataclass
## (`prototype/game.py`). `base_stats` maps a stat key (e.g. `"hp"`) to a
## [BigStat]; `rarity` is a [Rarity] enum value.

var id: String
var name: String
var rarity: int
var role: String
var base_stats: Dictionary
var skills: PackedStringArray
var traits: PackedStringArray


func _init(
	p_id: String,
	p_name: String,
	p_rarity: int,
	p_role: String,
	p_base_stats: Dictionary,
	p_skills: PackedStringArray,
	p_traits: PackedStringArray
) -> void:
	id = p_id
	name = p_name
	rarity = p_rarity
	role = p_role
	base_stats = p_base_stats
	skills = p_skills
	traits = p_traits
