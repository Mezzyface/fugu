# Asset Map - Iteration 1 (pygame UI, 3 screens)

Scope: Banner screen, Training Run screen, EchoPool screen. Grounded in the
dataclasses in `prototype/game.py` (`PullResult`, `Rarity`, `RunResult`,
`EncounterRecord`, `CheckpointReward`, `FrozenEcho`, `EchoRecord`, `Relic`,
`RelicForge.relic_stats`) and the icon vocabulary referenced in
`prototype/test_game.py` (`icon="shield"`, `icon="star"`, `icon="favorite_star"`).

## Chosen pack subset

| Pack | Extracted to | Why |
| --- | --- | --- |
| `Tiny Swords (Free Pack).zip` | `prototype/assets/tiny-swords-free-pack/` | Buttons, panels, bars, banners/ribbons (5 colors), avatars, a gold-resource sprite, and a tileset usable as a backdrop. Validated: has real UI chrome, not just battle sprites. |
| `isle-of-lore-2-ui-pack-final.zip` | `prototype/assets/isle-of-lore-2-ui-pack-final/` | Dedicated UI kit: panel, dialog_box, inventory_slot, selection_frame, progress_bar/circle, scrollbar, tooltip, checkbox, toggle_button (green/red), star icon. This is the primary chrome source for all 3 screens. |
| `isle-of-lore-2-rpg-item-icons-final.zip` | `prototype/assets/isle-of-lore-2-rpg-item-icons-final/` | 200 RPG icons (outline + transparent variants). Has direct hits for relic stats (sword/shield/heart/boot) and echo-pool icon vocabulary (shield, skull, gold, boss_key). Validated against the actual file list, not assumed. |
| `honeyblot_caps.zip` | `prototype/assets/honeyblot_caps/` | All-caps display font; pack's own README says it's meant for "captions, labels, headings... in games" — fits rarity labels and screen titles. |
| `HoneyPigeon.zip` | `prototype/assets/HoneyPigeon/` | Companion body font; pack's own README says it's meant for "text bodies of smaller sizes" — fits run logs, descriptions, tooltips. Kept alongside honeyblot_caps rather than choosing one, since they serve different text roles (display vs. body) and both license cleanly. |

Not extracted (out of scope, per task constraints): `80_Monster_Packs.zip`,
`Kenney Game Assets All-in-1*.zip`, `Tiny Swords (Enemy Pack).zip`,
`isle-of-lore-2-hex-tiles-*.zip`, `isle-of-lore-2-strategy-figures-final.zip`,
`tinypot_graybox-2d_*.zip` — these are bestiary/dungeon-board/token assets
with no map/board screen in the current 3-screen scope.

All paths below are relative to `prototype/assets/`.

---

## 1. Banner screen

Backed by `PullResult` (rarity, character_id, shards_gained, pity_reset) and
`GachaSystem` pity/shard state.

| UI element | File path | Notes |
| --- | --- | --- |
| Screen backdrop / banner panel | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/dialog_box_with_shadow.standard/dialog_box_with_shadow_0.png` | Main frame for the pull screen. |
| Decorative top banner ribbon | `tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Banners from the store page/Banner/Banner.png` | Title bar art ("Astra, Iron Vow" banner name etc.). |
| Pull button (idle) | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/button_round_big.standard/button_round_big_0.png` | "Pull x1". |
| Pull button (pressed) | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/button_round_big_pressed.standard/button_round_big_pressed_0.png` | |
| Pull x10 button | `tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Elements/Buttons/BigBlueButton_Regular.png` | Secondary action, visually distinct from the round pull button. |
| Result card frame (common) | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/inventory_slot.standard/inventory_slot_0.png` | + ribbon tint below (no native per-rarity frame art exists — see Gaps). |
| Result card frame (rare) | `tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Banners from the store page/Ribbons/Ribbon_Blue.png` | Composited as a colored ribbon banner under/behind the slot frame. |
| Result card frame (epic) | `tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Banners from the store page/Ribbons/Ribbon_Purple.png` | |
| Result card frame (legendary) | `tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Banners from the store page/Ribbons/Ribbon_Yellow.png` | |
| Result card frame (common, alt) | `tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Banners from the store page/Ribbons/Ribbon_Black.png` | Used instead of the unused Red ribbon to keep 4 distinct colors for 4 rarities. |
| Character portrait placeholder | `tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Elements/Human Avatars/Avatars_01.png` (through `Avatars_25.png`) | 25 generic avatars; assign by character id until bespoke art exists. |
| Shard counter icon | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_gold_nugget_29.png` | Shards are a currency-like value (`shards_gained`, `BannerState.shards`). |
| Pity progress bar track | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/progress_bar.standard/progress_bar_0.png` | Fill = `pulls_since_legendary / hard_pity_target`. |
| Pity progress bar fill | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/progress_bar.standard/progress_bar_1.png` | |
| "Pity reset!" flash icon | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_controls/ui_pack_icons.standard/ui_pack_icon_star_33.png` | Shown when `PullResult.pity_reset` is true. |
| Resonance node icons (4 nodes) | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/heart_piece.standard/heart_piece_empty_0.png` / `heart_piece_full_5.png` | Use empty/full state per unlocked resonance level (0-4). |
| Rarity label font | `honeyblot_caps/honeyblot_caps.ttf` | "LEGENDARY", "EPIC" etc. |
| Body / shard count text font | `HoneyPigeon/HoneyPigeon.ttf` | Smaller numeric/log text. |

**Gap:** there is no native per-rarity card-frame artwork (no gold-bordered
"legendary frame" vs. "common frame" PNGs) in any of the 4 chosen packs.
Substitute chosen: one neutral `inventory_slot` frame plus a color-coded
Tiny Swords ribbon behind it per `Rarity` value. If true bordered rarity
frames are required later, revisit `Kenney Game Assets All-in-1` (not
extracted) which likely has gacha-style colored frame sets, or commission art.

---

## 2. Training Run screen

Backed by `RunResult` (`floors_cleared`, `victory`, `echo`, `rewards`, `log`,
`encounters: List[EncounterRecord]`), `EncounterRecord` (`floor`, `kind`,
`power`, `difficulty`, `cleared`), `CheckpointReward` (`floor`, `tier`,
`shards`, `relic_rolls`, `echo_quality_bonus`), and `FrozenEcho`.

| UI element | File path | Notes |
| --- | --- | --- |
| Screen panel | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/panel.standard/panel_0.png` | Wraps the floor-by-floor encounter list. |
| Floor-step row background | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/box.standard/box_0.png` | One per `EncounterRecord`. |
| Encounter icon — combat | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_sword_153.png` | `kind == "combat"`. |
| Encounter icon — elite | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_shortsword_154.png` | `kind == "elite"` (visually distinct from combat's full sword). |
| Encounter icon — boss | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_boss_key_111.png` | `kind == "boss"`, floors 4/8/12. |
| Encounter icon — event | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_book_132.png` | `kind == "event"`. |
| Encounter icon — shrine | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_candle_121.png` | `kind == "shrine"`. |
| Encounter icon — rest | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_tent_90.png` | `kind == "rest"`. |
| Cleared checkmark | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_controls/ui_pack_icons.standard/ui_pack_icon_checkmark_1.png` | `EncounterRecord.cleared == True`. |
| Failed marker | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_controls/ui_pack_icons.standard/ui_pack_icon_cross_0.png` | `EncounterRecord.cleared == False` (the one extra record on a non-victory run). |
| Power/difficulty bar track | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/progress_bar.standard/progress_bar_0.png` | Visualize `power` vs `difficulty` per floor. |
| Power/difficulty bar fill | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/progress_bar.standard/progress_bar_1.png` | |
| Boss-gate checkpoint banner | `tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Elements/Banners/Banner.png` | Shown at floors 4/8/12 when a `CheckpointReward` is banked. |
| Checkpoint shard reward icon | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_gold_nugget_29.png` | `CheckpointReward.shards`. |
| Checkpoint relic-roll icon | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_chest_140.png` | `CheckpointReward.relic_rolls`. |
| Echo quality bonus icon | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_controls/ui_pack_icons.standard/ui_pack_icon_star_33.png` | `CheckpointReward.echo_quality_bonus`. |
| Victory banner | `tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Banners from the store page/Ribbons/Ribbon_Yellow.png` | `RunResult.victory == True` (floor 12 cleared). |
| Frozen Echo summary card | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/dialog_box.standard/dialog_box_0.png` | End-of-run panel showing `FrozenEcho` (stats, skills, traits, lineage_depth, instability). |
| Stat row icon — hp | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_heart_piece_full_120.png` | |
| Stat row icon — atk | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_sword_153.png` | Reused from combat icon — same visual vocabulary (sword = offense) is intentional, not a collision. |
| Stat row icon — def | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_iron_shield_182.png` | |
| Stat row icon — spd | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_boot_192.png` | |
| Instability warning icon | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_controls/ui_pack_icons.standard/ui_pack_icon_exclamation_mark_40.png` | `FrozenEcho.instability`, render scaled by value. |
| Log text font | `HoneyPigeon/HoneyPigeon.ttf` | `RunResult.log` lines. |
| Floor/header font | `honeyblot_caps/honeyblot_caps.ttf` | "FLOOR 4", "VICTORY", "FROZEN ECHO". |

**Gap:** none of the chosen packs have a literal "shrine" or "rest-site"
building sprite; `candle` and `tent` are the closest icon-level substitutes
and are sufficient for a list-row icon at this screen's fidelity. If a later
iteration wants a full dungeon/board view per floor (not just a list), the
hex-tile or strategy-figures packs would need to be revisited — out of scope
here since there is no map/board screen yet.

---

## 3. EchoPool screen

Backed by `EchoRecord` (`id`, `echo`, `power_score`, `favorite`, `icon`) and
`EchoPool` operations (favorite/delete/exchange), plus the icon vocabulary
used in `prototype/test_game.py` (`icon="shield"`, `icon="star"`,
`icon="favorite_star"`) and the broader vocabulary named in the task
(`shield`, `star`, `skull`, `gold`, `boss`, `favorite`, `default`).

| Icon name (EchoRecord.icon) | File path | Notes |
| --- | --- | --- |
| `shield` | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_iron_shield_182.png` | Matches `icon="shield"` used in `test_game.py`. |
| `star` | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_controls/ui_pack_icons.standard/ui_pack_icon_star_33.png` | Matches `icon="star"` used in `test_game.py`. |
| `skull` | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_skull_69.png` | |
| `gold` | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_gold_ingot_30.png` | |
| `boss` | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_boss_key_111.png` | |
| `favorite` / `favorite_star` overlay | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_controls/ui_pack_icons.standard/ui_pack_icon_star_33.png` | Same file as `star`; the favorite *state* is the gold/filled rendering of this icon, not a separate asset — see Gap below. |
| `default` | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/inventory_slot.standard/inventory_slot_0.png` | Empty slot glyph used when `icon` is unset/unrecognized. |

| UI element | File path | Notes |
| --- | --- | --- |
| Pool list panel | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/panel.standard/panel_0.png` | Container for the scrollable echo list. |
| Echo row slot frame | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/inventory_slot.standard/inventory_slot_1.png` | One per `EchoRecord`; icon (above) renders inside it. |
| Selected-row highlight | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/selection_frame_square.standard/selection_frame_square_0.png` | On click/focus. |
| Favorite toggle (off) | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/toggle_button.standard/toggle_button_0.png` | `EchoRecord.favorite == False`. |
| Favorite toggle (on) | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/toggle_button.green/toggle_button_0.png` | `EchoRecord.favorite == True`. |
| Delete button | `tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Elements/Buttons/SmallRedRoundButton_Regular.png` | `EchoPool.delete_echo`. |
| Delete button (pressed) | `tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Elements/Buttons/SmallRedRoundButton_Pressed.png` | |
| Exchange button | `tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Elements/Buttons/SmallBlueRoundButton_Regular.png` | `EchoPool.exchange_echo` / `exchange_event` (batch). |
| Exchange button (pressed) | `tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Elements/Buttons/SmallBlueRoundButton_Pressed.png` | |
| Power score bar | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/progress_circle.standard/progress_circle_18.png` | Visualize relative `power_score` (e.g. ring fill against pool max). |
| Sort dropdown control | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/scrollbar_horizontal_button.standard/scrollbar_horizontal_button_0.png` | For `sorted_records(by=...)` (power/icon/favorite/source/lineage). |
| Lineage depth icon | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_amulet_105.png` | `EchoRecord.echo.lineage_depth`. |
| Exchange reward — essence icon | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_crystal_41.png` | `EchoExchangeReward.essence`. |
| Exchange reward — shards icon | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_gold_nugget_29.png` | `EchoExchangeReward.shards`. |
| Exchange reward — relic rolls icon | `isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_chest_140.png` | `EchoExchangeReward.relic_rolls`. |
| Pool capacity bar | `isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/progress_bar.standard/progress_bar_0.png` / `progress_bar_1.png` | `len(pool)` vs `pool.capacity`. |
| Row label / id font | `HoneyPigeon/HoneyPigeon.ttf` | Echo id, source character id, stat text. |
| Screen title font | `honeyblot_caps/honeyblot_caps.ttf` | "ECHO POOL". |

**Gap:** there is no dedicated filled-vs-outline "favorite star" pair in any
chosen pack — only a single `ui_pack_icon_star_33` asset exists. The favorite
*toggle control* (on/off) is covered by `toggle_button.standard` /
`toggle_button.green`; the in-row `favorite`/`favorite_star` icon slot reuses
the same `star` file as the `star` icon. If `test_game.py`'s
`icon="favorite_star"` value needs visually distinct art from plain `star`,
that is a known gap — recolor/overlay the star asset, or substitute the
`isle-of-lore-2-ui-pack-final` `heart_piece_full` icon for the favorite state
instead.

---

## License summary

| Pack | License file | Summary |
| --- | --- | --- |
| `isle-of-lore-2-ui-pack-final` | `License.txt` ("Steven Colling Game Asset License 1.0") | Use in unlimited commercial/non-commercial projects (games, software, websites, print). No attribution required. Modification allowed. Cannot redistribute/resell the assets standalone or repackaged outside of a finished project. |
| `isle-of-lore-2-rpg-item-icons-final` | `License.txt` (same "Steven Colling Game Asset License 1.0") | Identical terms to the UI pack — same author/license family. |
| `Tiny Swords (Free Pack)` | **None found in the zip.** | No `License.txt`/`readme.txt`/`Credits.txt` inside the archive at all (verified: zip contains only asset folders, no top-level text files). This is the itch.io "Tiny Swords" free pack by Pixel Frog, commonly distributed under permissive itch.io terms, but **the terms are not bundled in this file** — treat as an open gap. Before shipping anything built on this pack, pull the current license text from the asset's itch.io page and store a copy alongside the extracted folder. |
| `HoneyPigeon` | `License.txt` ("Steven Colling Font License 1.1") | Use in unlimited commercial/non-commercial projects if a proper license was purchased. Install on unlimited machines. Cannot redistribute/sell the font file itself, except where embedding it is a technical necessity (e.g. bundling the `.ttf` so the game can render it). No attribution required (but appreciated). README notes it's tuned for smaller body text. |
| `honeyblot_caps` | `License.txt` ("Steven Colling Font License 1.0") | Same terms as HoneyPigeon (same author, font-license family). README notes it's an all-caps display face for "captions, labels, headings, and dialogue boxes" — used here for screen titles and rarity labels. |

**Action item:** confirm/attach the Tiny Swords license text before this
project goes beyond internal prototyping — it is the one pack in the chosen
subset without bundled usage terms.
