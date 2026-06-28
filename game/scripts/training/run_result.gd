class_name RunResult
extends RefCounted
## The full outcome of a single training run.
##
## Ported 1:1 from the Python prototype's `RunResult` dataclass
## (`prototype/game.py`). An `echo` is *always* produced — even on an immediate
## failure — so every run yields an inheritable parent (the always-echo rule).

var floors_cleared: int
var victory: bool
var echo: FrozenEcho
var rewards: RunRewards
var log: Array[String]
var encounters: Array[EncounterRecord]


func _init(
	p_floors_cleared: int,
	p_victory: bool,
	p_echo: FrozenEcho,
	p_rewards: RunRewards,
	p_log: Array[String],
	p_encounters: Array[EncounterRecord]
) -> void:
	floors_cleared = p_floors_cleared
	victory = p_victory
	echo = p_echo
	rewards = p_rewards
	log = p_log
	encounters = p_encounters
