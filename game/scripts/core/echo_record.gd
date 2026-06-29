class_name EchoRecord
extends RefCounted
## A banked echo plus its inventory metadata (id, power, favorite flag, icon).
##
## Ported 1:1 from the Python prototype's frozen `EchoRecord` dataclass
## (`prototype/game.py`). Treated as immutable: [EchoPool] replaces a record with
## a fresh instance rather than mutating one in place.

var id: int
var echo: FrozenEcho
var power_score: int
var favorite: bool
var icon: String


func _init(
	p_id: int,
	p_echo: FrozenEcho,
	p_power_score: int,
	p_favorite: bool = false,
	p_icon: String = "default"
) -> void:
	id = p_id
	echo = p_echo
	power_score = p_power_score
	favorite = p_favorite
	icon = p_icon
