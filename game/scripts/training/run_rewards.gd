class_name RunRewards
extends RefCounted
## Mutable accumulator for everything a training run banks.
##
## Ported 1:1 from the Python prototype's `RunRewards` dataclass
## (`prototype/game.py`). Banked rewards stay banked even if the run later fails,
## so these fields only ever grow over the course of a run. `echo_quality_percent`
## starts at 100 (a 1x echo) and climbs as checkpoints are cleared.

var banked_shards: int = 0
var relic_rolls: int = 0
var highest_checkpoint_floor: int = 0
var echo_quality_percent: int = 100
var instability_dividend_shards: int = 0
var checkpoints: Array[CheckpointReward] = []
