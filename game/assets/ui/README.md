# UI assets — first subset (#8)

A focused, license-clean UI subset imported from the raw asset packs in
`Game-Assets/` (gitignored). Only the files actually used are committed here; the
source zips are not. Selection follows `docs/asset_map_iteration_1.md`.

## Contents

| File | Source pack | Use |
| --- | --- | --- |
| `panels/panel.png` | Isle of Lore 2 — UI Pack | Main nine-slice panel chrome |
| `panels/dialog_box.png` | Isle of Lore 2 — UI Pack | Nested dialog / message box |
| `panels/inventory_slot.png` | Isle of Lore 2 — UI Pack | Item / echo slot frame |
| `buttons/button_round_big.png` | Isle of Lore 2 — UI Pack | Primary round button (idle) |
| `buttons/button_round_big_pressed.png` | Isle of Lore 2 — UI Pack | Primary round button (pressed) |
| `bars/progress_bar_track.png` | Isle of Lore 2 — UI Pack | Progress bar track |
| `bars/progress_bar_fill.png` | Isle of Lore 2 — UI Pack | Progress bar fill |
| `fonts/honeyblot_caps.ttf` | honeyblot caps | All-caps display face — titles / rarity labels |
| `fonts/HoneyPigeon.ttf` | HoneyPigeon | Body face — logs, descriptions, numeric text |

`scenes/ui_showcase.tscn` (in the Godot project root) demonstrates these rendering
together, including the nine-patch panels at stretched sizes.

## NinePatchRect patch margins

Derived from the actual border thickness of each source PNG (pixel-measured, not
guessed) so corners stay crisp and never stretch into blobs:

| Texture | Size | `patch_margin` L / T / R / B |
| --- | --- | --- |
| `panels/panel.png` | 60×48 | 12 / 10 / 12 / 10 |
| `panels/dialog_box.png` | 48×48 | 13 / 13 / 13 / 13 |
| `bars/progress_bar_*.png` | 66×66 | 14 / 14 / 14 / 14 |

## Licenses

License texts are committed under `licenses/`.

- **Isle of Lore 2 — UI Pack** — *Steven Colling Game Asset License 1.0*
  (`licenses/isle-of-lore-2-ui-pack-License.txt`). Unlimited commercial /
  non-commercial use, modification allowed, no attribution required. Cannot
  redistribute/resell the assets standalone outside a finished project.
- **honeyblot caps** — *Steven Colling Font License 1.0*
  (`licenses/honeyblot_caps-License.txt`). Unlimited project use; the `.ttf` may be
  embedded as a technical necessity to render the game. Cannot resell the font file.
- **HoneyPigeon** — *Steven Colling Font License 1.1*
  (`licenses/HoneyPigeon-License.txt`). Same family of terms as honeyblot caps.

All three packs in this subset bundle their license text and permit embedding in a
shipped project, so this subset is license-clean. (The Tiny Swords pack named in the
asset map ships no bundled license and was deliberately excluded from this first
subset; revisit it only after its itch.io terms are attached.)
