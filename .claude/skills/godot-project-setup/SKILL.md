---
name: godot-project-setup
description: How a Godot 4.x project is laid out and run — project.godot, the main scene, res:// vs user://, autoloads/singletons, and running the editor or headless from the CLI. Use when scaffolding a Godot project, configuring project settings, adding an autoload, or running/exporting the game.
---

# Godot 4.x project setup

A Godot project is any folder containing a `project.godot` file. Paths inside the
project use the `res://` scheme; writable runtime data uses `user://`.

## Minimal layout
```
game/
  project.godot        # project config (INI-like); [application], [autoload], [input], ...
  main.tscn            # the main scene (set as run/main_scene)
  scenes/  scripts/  assets/  addons/  test/
```

## project.godot essentials
- `[application] run/main_scene="res://main.tscn"` — what launches on run.
- `[application] config/features=PackedStringArray("4.7", ...)` — engine feature tags.
- `[autoload]` — singletons available globally, e.g. `GameState="*res://scripts/game_state.gd"`
  (the `*` enables the node/script as a singleton).
- `[input]` — input actions (see the `godot-input-actions` skill).

## Running from the CLI (this repo uses a Windows build under WSL)
```bash
GODOT="/mnt/c/Project-Fugu/Godot_v4.7-stable_win64.exe/Godot_v4.7-stable_win64.exe"
"$GODOT" --version
"$GODOT" --path "$(wslpath -w game)" --headless --quit        # import + headless boot
"$GODOT" --path "$(wslpath -w game)" --headless --check-only main.tscn
```
A Windows Godot build needs Windows-style `--path` (use `wslpath -w`). Prefer the
`godot` MCP server for launching/running and reading errors — it abstracts this.

## Tips
- After adding assets/scripts, let Godot import once (a headless boot creates `.godot/`,
  which is gitignored).
- Keep generated `.godot/` and `*.import` caches out of meaningful diffs.

Docs: https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html
