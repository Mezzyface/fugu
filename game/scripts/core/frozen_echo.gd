class_name FrozenEcho
extends RefCounted
## Immutable snapshot of a trained character, used as an inheritance "parent".
##
## Ported 1:1 from the Python prototype's frozen `FrozenEcho` dataclass
## (`prototype/game.py`). `stats` maps a stat key (e.g. `"atk"`) to a [BigStat];
## `lineage_depth` records how many inheritance generations deep this echo is and
## `instability` the accumulated cost of that inherited power.

var source_character_id: String
var stats: Dictionary
var skills: PackedStringArray
var traits: PackedStringArray
var lineage_depth: int
var instability: int


func _init(
	p_source_character_id: String,
	p_stats: Dictionary,
	p_skills: PackedStringArray,
	p_traits: PackedStringArray,
	p_lineage_depth: int,
	p_instability: int
) -> void:
	source_character_id = p_source_character_id
	stats = p_stats
	skills = p_skills
	traits = p_traits
	lineage_depth = p_lineage_depth
	instability = p_instability
