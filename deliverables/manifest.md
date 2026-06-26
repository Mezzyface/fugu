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
- [ ] Verification wrapper (gdlint + GUT) — code — `tools/verify.sh` (#7)
- [ ] Asset import (first subset) — non-code artifact — `game/assets/` (#8)

## Design

- [ ] GDD ported/updated for Godot — doc — `docs/` (TBD)
