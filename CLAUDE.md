# Project Fugu — agent guide

Fugu is a gacha-RPG being built in **Godot 4.7**. Earlier Python (`prototype/`) and
Phaser (`prototype-phaser/`) prototypes are legacy reference only — new gameplay work
targets the Godot project under `game/`.

Work is driven by the **GitHub Project board** (`Mezzyface/projects/1`). A polling
dispatcher (`tools/dispatch.py`) hands you one issue at a time inside an isolated git
worktree and expects a reviewable PR back. If you are reading this inside a dispatcher
run, your task is in `.dispatch/TASK.md`.

## How a task runs

1. You are on a branch `task/<issue#>-<slug>` in a worktree off `origin/master`.
2. Read `.dispatch/TASK.md` — it has Context, Resources, Acceptance Criteria, Outputs,
   and the exact Verification commands for this task.
3. Do the work. Stay within the task's scope; don't refactor unrelated code.
4. Run the Verification commands yourself before finishing.
5. The dispatcher commits, pushes, and opens the PR (`Closes #<issue>`). Don't open PRs
   yourself unless the task says to.

## Repo layout

- `game/` — the Godot 4.7 project (`project.godot`, scenes, scripts, `addons/`).
- `tools/` — automation: `dispatch.py` (board dispatcher), `autoloop.py` (deprecated).
- `docs/` — design docs (GDD, asset map).
- `deliverables/manifest.md` — tracker for every deliverable, code or not.
- `Game-Assets/` — raw asset packs (gitignored, ~1.5 GB). Import subsets into
  `game/assets/`, never commit the raw zips.
- `.claude/skills/godot-*` — Godot how-to skills; consult them for engine-specific work.

## Godot conventions

- Target **Godot 4.7 / GDScript**. Use current 4.x APIs (typed GDScript, `@onready`,
  `signal`, `Callable`). When unsure, check the skills or https://docs.godotengine.org.
- Format and lint GDScript before finishing:
  - `gdformat game/` (auto-format)
  - `gdlint game/` (lint; fix warnings)
- Tests use **GUT** (Godot Unit Test) under `game/addons/gut/`, run headless. You MUST
  run an import pass first, or GUT's `class_name`s won't resolve **and it still exits 0**
  (a false pass):
  - `godot --headless --import`
  - `godot --headless -s addons/gut/gut_cmdln.gd -gdir=res://test -gexit`
  Always confirm the output says "All tests passed!" — don't trust the exit code alone.
- **Standard verification command:** `bash tools/verify.sh`. It runs the GDScript lint
  gate (`gdformat --check` + `gdlint` over `game/`) and the GUT suite headless (import
  pass first, then asserts the "All tests passed!" banner), and **exits non-zero if
  either fails** — so the dispatcher and reviewers run one script. If `gdtoolkit`
  (`gdformat`/`gdlint`) isn't installed it prints an install hint and skips the lint
  step rather than hard-failing; pass `--strict-lint` to make a missing gdtoolkit a
  failure. Override the Godot binary with the `GODOT` env var if it's not on `PATH`.

### Godot binary / paths (WSL note)

The editor is a Windows build at
`/mnt/c/Project-Fugu/Godot_v4.7-stable_win64.exe/Godot_v4.7-stable_win64.exe`, invoked
from WSL via interop. A Windows Godot build expects Windows-style project paths
(`C:\Project-Fugu\fugu\game`), not `/mnt/c/...`. Use `wslpath -w <path>` to convert when
passing project paths to the binary directly. The `godot` MCP server abstracts most of
this — prefer it for launching/running.

## MCP tools

The `godot` MCP server (`@coding-solo/godot-mcp`, configured in `.mcp.json`) can launch
the editor, run the project headless, capture debug output/errors, and do scene/node
operations. Use it to actually run a scene and read the resulting errors rather than
guessing — it's the fastest way to verify Godot behavior.

## Separation of duties

- Implementers do **not** sign off on their own work — run the verification commands and
  report results honestly, but final acceptance is the human PR review (and, later, a
  separate verifier agent).
- If verification is red and you can't fix it within scope, stop and report it; the
  dispatcher will route the task to `Needs Human`.

## Deliverables

If your task's outputs include anything tracked as a deliverable (a design doc, an asset
import, an external artifact, a decision), update `deliverables/manifest.md` in the same
PR: check the item off and link the in-repo path or external URL plus the issue number.

## Commits & PRs

- Keep changes scoped to the task; small, reviewable diffs.
- End commit messages with:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
