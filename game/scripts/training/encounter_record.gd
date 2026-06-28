class_name EncounterRecord
extends RefCounted
## A single floor's encounter outcome within a training run.
##
## Ported 1:1 from the Python prototype's frozen `EncounterRecord` dataclass
## (`prototype/game.py`). `power` is the character's total power going into the
## floor and `difficulty` the gate it had to beat; `cleared` is false only for the
## one floor that ended the run.

var floor: int
var kind: String
var power: int
var difficulty: int
var cleared: bool


func _init(p_floor: int, p_kind: String, p_power: int, p_difficulty: int, p_cleared: bool) -> void:
	floor = p_floor
	kind = p_kind
	power = p_power
	difficulty = p_difficulty
	cleared = p_cleared
