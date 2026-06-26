# Godot skills

Concise, agent-facing how-to skills for developing this project in Godot 4.x, mirroring
the `.opencode/skills/phaser-*` pattern but for Claude Code (`.claude/skills/`). Each skill
is a folder with a `SKILL.md` carrying `name` + `description` frontmatter so Claude Code
can surface it when relevant.

## Current skills
- `godot-project-setup` — project.godot, layout, running the editor/headless from CLI.
- `godot-scenes-and-nodes` — scene tree, instancing, node lifecycle, references.
- `godot-gdscript-style` — typed GDScript, naming, gdformat/gdlint.
- `godot-signals` — declaring/emitting/connecting signals (Callable syntax).
- `godot-ui-control` — Control nodes, containers, themes, NinePatchRect (nine-slice).
- `godot-gut-testing` — GUT unit tests + headless run for the verification gate.

## Sources / updating
Distilled from the official Godot 4.x documentation (https://docs.godotengine.org/en/stable)
and GUT (https://github.com/bitwes/Gut). They target Godot **4.7**. When the engine or APIs
move, update the affected `SKILL.md` and the doc links. Validate engine-specific claims
against the real editor via the `godot` MCP during the first Godot tasks.

> Claude Code loads skills at session start — restart the session (or the dispatcher run)
> after adding or editing skills.
