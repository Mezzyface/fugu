class_name CharacterCatalog
extends RefCounted
## Built-in sample roster.
##
## Ported 1:1 from the Python prototype's `sample_characters()` (`prototype/game.py`).


## The three starter characters keyed by id, matching the Python prototype.
static func sample_characters() -> Dictionary:
	return {
		"iron_vow":
		CharacterDef.new(
			"iron_vow",
			"Astra, Iron Vow",
			Rarity.LEGENDARY,
			"guardian",
			{
				"hp": BigStat.new(900),
				"atk": BigStat.new(90),
				"def": BigStat.new(140),
				"spd": BigStat.new(45),
			},
			PackedStringArray(["Aegis Break", "Oath Wall", "Counterflare"]),
			PackedStringArray(["armor", "counter"]),
		),
		"star_witch":
		CharacterDef.new(
			"star_witch",
			"Mira, Star Witch",
			Rarity.LEGENDARY,
			"caster",
			{
				"hp": BigStat.new(430),
				"atk": BigStat.new(180),
				"def": BigStat.new(55),
				"spd": BigStat.new(80),
			},
			PackedStringArray(["Nova Hex", "Meteor Seed", "Astral Refund"]),
			PackedStringArray(["magic", "scaling"]),
		),
		"rat_squire":
		CharacterDef.new(
			"rat_squire",
			"Pip, Rat Squire",
			Rarity.RARE,
			"fighter",
			{
				"hp": BigStat.new(520),
				"atk": BigStat.new(95),
				"def": BigStat.new(80),
				"spd": BigStat.new(100),
			},
			PackedStringArray(["Skitter Strike", "Tiny Guard"]),
			PackedStringArray(["beast", "underdog"]),
		),
	}
