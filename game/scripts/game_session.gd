extends Node

signal state_changed

const MAX_WEEK: int = 52
const DEFAULT_ECHO_CAPACITY: int = 100

var shards: int = 0
var essence: int = 0
var relic_rolls: int = 0
var current_week: int = 1
var characters: Dictionary = {}
var owned_banners: Dictionary = {}
var gacha_system: GachaSystem
var echo_pool: EchoPool


func _init() -> void:
	reset()


func reset(seed: int = 1) -> void:
	shards = 0
	essence = 0
	relic_rolls = 0
	current_week = 1
	characters = CharacterCatalog.sample_characters()
	gacha_system = GachaSystem.new(characters, seed)
	owned_banners = gacha_system.banners
	echo_pool = EchoPool.new(DEFAULT_ECHO_CAPACITY)
	state_changed.emit()


func currency_totals() -> Dictionary:
	return {"shards": shards, "essence": essence, "relic_rolls": relic_rolls}


func add_currency(shard_delta: int = 0, essence_delta: int = 0, relic_roll_delta: int = 0) -> void:
	shards = maxi(0, shards + shard_delta)
	essence = maxi(0, essence + essence_delta)
	relic_rolls = maxi(0, relic_rolls + relic_roll_delta)
	state_changed.emit()


func set_current_week(week: int) -> void:
	current_week = wrapi(maxi(1, week) - 1, 0, MAX_WEEK) + 1
	state_changed.emit()


func advance_week(delta: int = 1) -> void:
	set_current_week(current_week + delta)


func featured_banner_ids(slots_per_week: int = 3) -> Array:
	return gacha_system.featured_banners_for_week(current_week, slots_per_week)


func featured_banners(slots_per_week: int = 3) -> Array[BannerState]:
	var result: Array[BannerState] = []
	for character_id: String in featured_banner_ids(slots_per_week):
		result.append(owned_banners[character_id])
	return result


func get_banner_state(character_id: String) -> BannerState:
	return owned_banners.get(character_id, null)


func get_character(character_id: String) -> CharacterDef:
	return characters.get(character_id, null)


func format_stat(stat: BigStat) -> String:
	var normalized := stat.normalized()
	return "%d·10^%d" % [normalized.mantissa, normalized.magnitude]


func format_stats(stats: Dictionary) -> Dictionary:
	var formatted: Dictionary = {}
	for key: String in stats:
		formatted[key] = format_stat(stats[key])
	return formatted


func currency_summary() -> String:
	return "◆ %d · ✦ %d · ⬡ %d · Week %d/%d" % [shards, essence, relic_rolls, current_week, MAX_WEEK]
