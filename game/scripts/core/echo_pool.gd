class_name EchoPool
extends RefCounted
## The inheritance inventory: banking, power ranking, sorting, favorites, delete,
## and (single or batch) exchange of [FrozenEcho]s back to currency.
##
## Ported 1:1 from the Python prototype's `EchoPool` (`prototype/game.py`). The
## Python original raised exceptions on invalid operations; GDScript has none, so
## those paths `push_error` and return `null` (or an empty result). Callers — and
## the GUT suite via `assert_push_error` — detect failure by the `null`/error.
##
## Soft-lock safety: `max_favorites` is clamped to `capacity - 1` so at least one
## record is always non-favorite and therefore removable even when full.

var capacity: int
var max_favorites: int
var records: Array[EchoRecord] = []

var _next_id: int = 1


## `p_max_favorites < 0` (the default) means "auto" — every slot but one may be a
## favorite. Any requested cap is still clamped to `capacity - 1`.
func _init(p_capacity: int = 100, p_max_favorites: int = -1) -> void:
	capacity = maxi(1, p_capacity)
	var requested := capacity - 1 if p_max_favorites < 0 else maxi(0, p_max_favorites)
	max_favorites = mini(capacity - 1, requested)


## Number of banked records (mirrors Python's `len(pool)`).
func size() -> int:
	return records.size()


func is_full() -> bool:
	return records.size() >= capacity


func favorite_count() -> int:
	var count := 0
	for record in records:
		if record.favorite:
			count += 1
	return count


## Deterministic power ranking for an echo: stat magnitude/mantissa weighted, plus
## flat bonuses for skills, traits, and lineage depth, minus an instability cost.
## Never negative.
static func power_score(echo: FrozenEcho) -> int:
	var stat_score := 0
	for value: BigStat in echo.stats.values():
		stat_score += value.magnitude * 10000 + value.mantissa
	var skill_score := echo.skills.size() * 250
	var trait_score := echo.traits.size() * 500
	var lineage_score := echo.lineage_depth * 100
	var instability_cost := echo.instability * 50
	return maxi(0, stat_score + skill_score + trait_score + lineage_score - instability_cost)


## Banks an echo. Fails (push_error + null) when the pool is full or the favorite
## cap would be exceeded.
func bank_echo(echo: FrozenEcho, icon: String = "default", favorite: bool = false) -> EchoRecord:
	if is_full():
		push_error("echo pool is full")
		return null
	if favorite and favorite_count() >= max_favorites:
		push_error("favorite limit reached")
		return null
	var record := EchoRecord.new(_next_id, echo, power_score(echo), favorite, icon)
	_next_id += 1
	records.append(record)
	return record


func get_record(record_id: int) -> EchoRecord:
	var index := _find_index(record_id)
	return records[index] if index != -1 else null


## Replaces a record's `favorite`/`icon`. Pass `null` for a field to leave it
## unchanged. Fails (push_error + null) on an unknown id, or when turning on a
## favorite would exceed the cap.
func update_record(record_id: int, favorite: Variant = null, icon: Variant = null) -> EchoRecord:
	var index := _find_index(record_id)
	if index == -1:
		push_error("unknown echo id %d" % record_id)
		return null
	var record: EchoRecord = records[index]
	if favorite == true and not record.favorite and favorite_count() >= max_favorites:
		push_error("favorite limit reached")
		return null
	var new_favorite := record.favorite if favorite == null else bool(favorite)
	var new_icon := record.icon if icon == null else String(icon)
	var updated := EchoRecord.new(record.id, record.echo, record.power_score, new_favorite, new_icon)
	records[index] = updated
	return updated


## Removes and returns a record. Favorites are protected unless `allow_favorite`.
## Fails (push_error + null) on an unknown id or a protected favorite.
func delete_echo(record_id: int, allow_favorite: bool = false) -> EchoRecord:
	var index := _find_index(record_id)
	if index == -1:
		push_error("unknown echo id %d" % record_id)
		return null
	var record: EchoRecord = records[index]
	if record.favorite and not allow_favorite:
		push_error("favorite echoes must be unfavorited before deletion")
		return null
	records.remove_at(index)
	return record


## Exchanges a single record for currency. Returns null if the underlying delete
## fails (the delete already pushed the error).
func exchange_echo(
	record_id: int, event_multiplier: int = 1, allow_favorite: bool = false
) -> EchoExchangeReward:
	var record := delete_echo(record_id, allow_favorite)
	if record == null:
		return null
	var multiplier := maxi(1, event_multiplier)
	return EchoExchangeReward.new(
		maxi(1, record.power_score / 100) * multiplier,
		(10 + record.echo.lineage_depth * 5) * multiplier,
		(1 + record.echo.skills.size() / 2) * multiplier
	)


## Batch-exchanges several records, summing the rewards. Atomic: the whole
## selection is validated (no duplicates, every id present, no protected
## favorites) before anything is removed, so a failure leaves the pool untouched.
## Fails (push_error + null) on any validation problem.
func exchange_event(
	record_ids: Array, event_multiplier: int = 1, allow_favorite: bool = false
) -> EchoExchangeReward:
	var seen := {}
	for record_id: int in record_ids:
		if seen.has(record_id):
			push_error("duplicate echo in exchange selection")
			return null
		seen[record_id] = true
	for record_id: int in record_ids:
		var record := get_record(record_id)
		if record == null:
			push_error("unknown echo id %d" % record_id)
			return null
		if record.favorite and not allow_favorite:
			push_error("favorite echoes must be unfavorited before exchange")
			return null
	var total := EchoExchangeReward.new(0, 0, 0)
	for record_id: int in record_ids:
		var reward := exchange_echo(record_id, event_multiplier, allow_favorite)
		total = EchoExchangeReward.new(
			total.essence + reward.essence,
			total.shards + reward.shards,
			total.relic_rolls + reward.relic_rolls
		)
	return total


## Records sorted by one of: "power" (default), "icon", "favorite", "source",
## "lineage". Each key breaks ties by power then id, so the order is total and the
## sort deterministic. `descending` reverses the whole ordering.
func sorted_records(by: String = "power", descending: bool = true) -> Array[EchoRecord]:
	var arr: Array[EchoRecord] = records.duplicate()
	arr.sort_custom(
		func(a: EchoRecord, b: EchoRecord) -> bool:
			var cmp := _compare_keys(_sort_key(a, by), _sort_key(b, by))
			return cmp > 0 if descending else cmp < 0
	)
	return arr


## The `limit` highest-power records (descending).
func top(limit: int = 5) -> Array[EchoRecord]:
	return sorted_records("power").slice(0, maxi(0, limit))


## The strongest echoes usable as inheritance parents, optionally filtered to a
## single source character (empty string = any). Highest power first.
func best_parents(source_character_id: String = "", count: int = 2) -> Array[FrozenEcho]:
	var result: Array[FrozenEcho] = []
	for record in sorted_records("power"):
		if source_character_id == "" or record.echo.source_character_id == source_character_id:
			result.append(record.echo)
	return result.slice(0, maxi(0, count))


func _find_index(record_id: int) -> int:
	for index in records.size():
		if records[index].id == record_id:
			return index
	return -1


## Sort key for a record under the named mode. Every key ends in (power, id) so
## ties resolve to a total order and the sort is deterministic.
func _sort_key(record: EchoRecord, by: String) -> Array:
	match by:
		"icon":
			return [record.icon, record.power_score, record.id]
		"favorite":
			return [int(record.favorite), record.power_score, record.id]
		"source":
			return [record.echo.source_character_id, record.power_score, record.id]
		"lineage":
			return [record.echo.lineage_depth, record.power_score, record.id]
		_:
			return [record.power_score, record.id]


## Element-wise tuple comparison returning -1/0/1. Each position holds a single
## comparable type (int or String), so `<`/`>` order them as Python's tuples did.
func _compare_keys(a: Array, b: Array) -> int:
	for i in a.size():
		if a[i] < b[i]:
			return -1
		if a[i] > b[i]:
			return 1
	return 0
