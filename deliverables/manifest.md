# Deliverables manifest

Every deliverable — code, doc, or non-code artifact — is tracked here. Tasks labeled
`deliverable` must update this file in their PR: check the item off and link the in-repo
path or external URL, plus the issue number.

Format: `- [ ] <name> — <type> — <link or path> (#issue)`

## Foundation / tooling

- [x] Board dispatcher (`tools/dispatch.py`) — code — `tools/dispatch.py`
- [x] Godot agent guide — doc — `CLAUDE.md`
- [x] Godot MCP wiring — code — `.mcp.json`
- [x] Agent task issue template — doc — `.github/ISSUE_TEMPLATE/agent-task.yml`

## Game (Godot)

- [x] Godot 4.7 project scaffold — code — `game/` (#6)
- [x] GUT test framework vendored — code — `game/addons/gut/` (#6)
- [x] Verification wrapper (gdlint + GUT) — code — `tools/verify.sh` (#7)
- [x] Asset import (first subset) — non-code artifact — `game/assets/ui/` (panels, buttons, bars + honeyblot caps / HoneyPigeon fonts from the Isle of Lore 2 UI pack and Steven Colling font packs; nine-patch demo in `game/scenes/ui_showcase.tscn`; licenses under `game/assets/ui/licenses/`, details in `game/assets/ui/README.md`) (#8)
- [x] Project Theme (fonts + Wada Sanzo palette) — code — `game/assets/theme/fugu_theme.tres` (honeyblot caps titles/headers + HoneyPigeon body; four named `Palette` colors from Wada Sanzo combo 282; set as project default via `gui/theme/custom` and applied to `main.tscn` / `ui_showcase.tscn`; attribution in `game/assets/licenses/README.md`) (#21)
- [x] Terrain tiles import + demo — non-code artifact — `game/assets/terrain/` (curated 84-tile isometric ground/height/ramp subset from Kenney's CC0 Isometric Miniature Prototype; assembled patch in `game/scenes/terrain_demo.tscn`; attribution in `game/assets/licenses/terrain-isometric-miniature.md`; screenshot under `screenshots/22/`) (#22)

## Design

- [x] Art direction decided (fonts, sprites, terrain, palette) — doc — `docs/art_direction.md` (#9)
- [ ] GDD ported/updated for Godot — doc — `docs/` (TBD)
