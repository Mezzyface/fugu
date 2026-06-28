class_name FrozenEcho
extends RefCounted
## A frozen inheritance echo distilled from a training run.
##
## Ported 1:1 from the Python prototype's frozen `FrozenEcho` dataclass
## (`prototype/game.py`). `stats` maps a stat key (e.g. `"hp"`) to a [BigStat].
## Instances are treated as immutable — fields are set once at construction.

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
	p_lineage_depth: int = 0,
	p_instability: int = 0
) -> void:
	source_character_id = p_source_character_id
	stats = p_stats
	skills = p_skills
	traits = p_traits
	lineage_depth = p_lineage_depth
	instability = p_instability
