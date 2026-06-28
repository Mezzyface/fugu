extends GutTest
## EchoPool tests — banking, ranking, sorting, favorites, delete, single/batch
## exchange, and best_parents.
##
## Ported from the Python prototype's `EchoPool` cases in
## `prototype/test_game.py`. The prototype drove these through `TrainingSimulator`
## runs; that system isn't ported yet, so here echoes are built directly with
## controlled stats to get the same deterministic power ordering. The prototype
## raised exceptions; the GDScript port pushes an error and returns null, so the
## failure paths use `assert_push_error` plus a null/unchanged-state check.


## Builds an echo whose power is dominated by its single `hp` stat, so callers can
## order echoes simply by choosing distinct `hp` values.
func _echo(
	source: String,
	hp: int,
	skills := PackedStringArray(),
	traits := PackedStringArray(),
	lineage := 0,
	instability := 0
) -> FrozenEcho:
	return FrozenEcho.new(source, {"hp": BigStat.new(hp)}, skills, traits, lineage, instability)


func test_power_score_matches_prototype_formula() -> void:
	var echo := _echo(
		"iron_vow", 900, PackedStringArray(["a", "b"]), PackedStringArray(["x"]), 3, 2
	)
	# 900 stat + 2*250 skills + 1*500 traits + 3*100 lineage - 2*50 instability.
	assert_eq(EchoPool.power_score(echo), 900 + 500 + 500 + 300 - 100)


func test_power_score_never_negative() -> void:
	var echo := _echo("weak", 1, PackedStringArray(), PackedStringArray(), 0, 99)
	assert_eq(EchoPool.power_score(echo), 0)


func test_best_parents_returns_up_to_two_by_power() -> void:
	var pool := EchoPool.new(5)
	pool.bank_echo(_echo("rat_squire", 100))
	pool.bank_echo(_echo("iron_vow", 900))
	pool.bank_echo(_echo("star_witch", 500))

	var top_two := pool.top(2)
	var best_two := pool.best_parents("", 2)
	assert_eq(best_two.size(), 2)
	assert_eq(best_two[0], top_two[0].echo)
	assert_eq(best_two[1], top_two[1].echo)

	var best_one := pool.best_parents("", 1)
	assert_eq(best_one.size(), 1)
	assert_eq(best_one[0], top_two[0].echo)


func test_ranks_without_pruning_and_enforces_capacity() -> void:
	var pool := EchoPool.new(2)
	pool.bank_echo(_echo("rat_squire", 100))
	pool.bank_echo(_echo("star_witch", 500))
	# Capacity is hard: a stronger echo does not evict a weaker one.
	var overflow := pool.bank_echo(_echo("iron_vow", 900))
	assert_null(overflow, "banking past capacity fails")
	assert_push_error("echo pool is full")
	assert_eq(pool.size(), 2)

	var scores: Array[int] = []
	for record in pool.top(2):
		scores.append(record.power_score)
	assert_eq(scores, [500, 100], "top is power-descending")
	assert_eq(pool.best_parents("", 1)[0], pool.top(1)[0].echo)


func test_supports_favorites_icons_delete_and_exchange() -> void:
	var pool := EchoPool.new(3)
	var iron_record := pool.bank_echo(_echo("iron_vow", 900), "shield")
	var witch_record := pool.bank_echo(_echo("star_witch", 500), "star")
	var updated := pool.update_record(witch_record.id, true, "favorite_star")
	assert_true(updated.favorite)
	assert_eq(pool.sorted_records("icon", false)[0].icon, "favorite_star")

	assert_null(pool.delete_echo(witch_record.id), "favorite is delete-protected")
	assert_push_error("favorite echoes must be unfavorited before deletion")
	assert_null(pool.exchange_echo(witch_record.id), "favorite is exchange-protected")
	assert_push_error("favorite echoes must be unfavorited before deletion")

	var removed := pool.delete_echo(iron_record.id)
	assert_eq(removed.id, iron_record.id)
	pool.update_record(witch_record.id, false)
	var reward := pool.exchange_echo(witch_record.id, 2)
	assert_gt(reward.essence, 0)
	assert_gt(reward.shards, 0)
	assert_eq(pool.size(), 0)


func test_favorite_cap_prevents_soft_lock() -> void:
	var pool := EchoPool.new(3)
	assert_eq(pool.max_favorites, 2, "auto cap is capacity - 1")
	var records: Array[EchoRecord] = []
	for i in 3:
		records.append(pool.bank_echo(_echo("iron_vow", 900)))
	pool.update_record(records[0].id, true)
	pool.update_record(records[1].id, true)
	assert_null(pool.update_record(records[2].id, true), "third favorite is capped")
	assert_push_error("favorite limit reached")
	assert_lt(pool.favorite_count(), pool.capacity, "at least one slot stays removable")
	assert_eq(pool.delete_echo(records[2].id).id, records[2].id)


func test_custom_favorite_cap_cannot_lock_pool() -> void:
	var pool := EchoPool.new(2, 99)
	assert_eq(pool.max_favorites, 1, "cap clamped to capacity - 1")
	var first := pool.bank_echo(_echo("iron_vow", 900), "default", true)
	var second := pool.bank_echo(_echo("star_witch", 500))
	assert_null(pool.update_record(second.id, true), "second favorite is capped")
	assert_push_error("favorite limit reached")
	assert_eq(pool.delete_echo(second.id).id, second.id)
	assert_not_null(pool.get_record(first.id))


func test_batch_exchange_event_aggregates_rewards() -> void:
	var pool := EchoPool.new(5)
	var ids: Array[int] = []
	for i in 3:
		ids.append(pool.bank_echo(_echo("star_witch", 500)).id)
	var keep := pool.bank_echo(_echo("iron_vow", 900), "default", true)

	var single := pool.exchange_echo(ids[0])
	assert_null(pool.exchange_event([ids[1], keep.id]), "batch with favorite fails")
	assert_push_error("favorite echoes must be unfavorited before exchange")
	assert_not_null(pool.get_record(ids[1]), "failed batch removes nothing")

	var batch := pool.exchange_event([ids[1], ids[2]], 2)
	assert_gte(batch.essence, single.essence)
	assert_eq(pool.size(), 1)
	assert_eq(pool.records[0].id, keep.id)

	assert_null(pool.exchange_event([keep.id]), "exchanging a favorite fails")
	assert_push_error("favorite echoes must be unfavorited before exchange")


func test_batch_exchange_is_atomic_on_failure() -> void:
	var pool := EchoPool.new(5)
	var first := pool.bank_echo(_echo("star_witch", 500)).id
	var favorite := pool.bank_echo(_echo("iron_vow", 900), "default", true).id
	var second := pool.bank_echo(_echo("star_witch", 500)).id

	assert_null(pool.exchange_event([first, favorite, second]), "favorite aborts batch")
	assert_push_error("favorite echoes must be unfavorited before exchange")
	assert_eq(_ids(pool), [first, favorite, second])

	assert_null(pool.exchange_event([first, 9999]), "unknown id aborts batch")
	assert_push_error("unknown echo id")
	assert_eq(_ids(pool), [first, favorite, second])

	assert_null(pool.exchange_event([first, first]), "duplicate id aborts batch")
	assert_push_error("duplicate echo in exchange selection")
	assert_eq(_ids(pool), [first, favorite, second])

	var reward := pool.exchange_event([first, second])
	assert_gt(reward.essence, 0)
	assert_eq(_ids(pool), [favorite])


func test_can_filter_by_source_character() -> void:
	var pool := EchoPool.new(5)
	pool.bank_echo(_echo("iron_vow", 900))
	pool.bank_echo(_echo("star_witch", 500))
	assert_eq(pool.best_parents("iron_vow")[0].source_character_id, "iron_vow")
	assert_eq(pool.best_parents("missing").size(), 0)


func _ids(pool: EchoPool) -> Array[int]:
	var ids: Array[int] = []
	for record in pool.records:
		ids.append(record.id)
	return ids
