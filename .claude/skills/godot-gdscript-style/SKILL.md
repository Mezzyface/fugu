---
name: godot-gdscript-style
description: GDScript style and conventions for Godot 4.x — static typing, naming, @export/@onready, enums/constants, and formatting/linting with gdformat and gdlint. Use when writing or reviewing .gd scripts so they match the official style guide and pass the project's lint gate.
---

# GDScript style (Godot 4.x)

Follow the official GDScript style guide. Use **static typing** everywhere it's practical —
it catches errors and improves editor/agent accuracy.

## Typing
```gdscript
class_name Monster
extends Node2D

@export var max_hp: int = 100
@export var move_speed: float = 200.0
var _current_hp: int = max_hp                # leading underscore = private-by-convention

func take_damage(amount: int) -> void:
    _current_hp = maxi(_current_hp - amount, 0)

func is_alive() -> bool:
    return _current_hp > 0
```
- Prefer `:=` inferred typing when the right-hand type is obvious; otherwise annotate.
- Use typed arrays/dicts: `var picks: Array[String] = []`.

## Naming
- `snake_case` for vars/functions/signals; `PascalCase` for classes/nodes;
  `CONSTANT_CASE` for `const` and enum values.
- One `class_name` per reusable type; file name `snake_case.gd`.

## Common annotations
- `@onready` — defer initialization until the node is in the tree.
- `@export` — expose in the Inspector; `@export_range`, `@export_enum`, `@export_file`.
- `@tool` — run the script in the editor (use sparingly).

## Formatting & linting (the project verification gate)
```bash
gdformat game/          # auto-format in place (gdtoolkit)
gdlint game/            # lint; fix all warnings before finishing a task
```
Install once: `pipx install gdtoolkit` (or `pip install gdtoolkit`). If neither is
available in the environment, set it up in a venv and note it in the task.

Docs: https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_styleguide.html
