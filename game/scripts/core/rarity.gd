class_name Rarity
## Character rarity tiers.
##
## Ported 1:1 from the Python prototype's `Rarity` str-enum (`prototype/game.py`).
## The integer enum values are ordered low-to-high; `to_string_value()` maps each
## back to the canonical lowercase string the prototype used (e.g. `"legendary"`).

enum { COMMON, RARE, EPIC, LEGENDARY }

const _STRINGS: Array[String] = ["common", "rare", "epic", "legendary"]


## Canonical lowercase name for a rarity, matching the Python enum's `.value`.
static func to_string_value(rarity: int) -> String:
	return _STRINGS[rarity]
