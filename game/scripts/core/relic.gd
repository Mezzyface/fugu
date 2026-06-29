class_name Relic
extends RefCounted
## Immutable stat-boosting relic.
##
## Ported 1:1 from the Python prototype's frozen `Relic` dataclass
## (`prototype/game.py`). Each relic targets one stat key (e.g. `"atk"`) and
## boosts it by `bonus_percent` when applied via [RelicForge.apply_relics].

var id: int
var name: String
var rarity: int
var stat: String
var bonus_percent: int


func _init(p_id: int, p_name: String, p_rarity: int, p_stat: String, p_bonus_percent: int) -> void:
	id = p_id
	name = p_name
	rarity = p_rarity
	stat = p_stat
	bonus_percent = p_bonus_percent
