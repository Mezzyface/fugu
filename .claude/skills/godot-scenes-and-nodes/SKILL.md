---
name: godot-scenes-and-nodes
description: Godot 4.x scene tree, nodes, instancing, and the node lifecycle (_ready, _process, _physics_process, @onready). Use when creating or wiring scenes (.tscn), instancing subscenes, getting node references, or deciding where game logic should live.
---

# Godot 4.x scenes and nodes

Everything is a **Node** arranged in a tree; a **scene** (`.tscn`) is a reusable subtree
with one root. Scenes are composed by instancing other scenes.

## Node references
```gdscript
@onready var health_bar: ProgressBar = $UI/HealthBar      # $ is get_node()
@onready var label := get_node("UI/Label") as Label
# % is the unique-name accessor: mark a node "Access as Unique Name" then $%Player
```
Prefer `@onready` typed vars over repeated `get_node` calls. `$Path` resolves relative to
the current node.

## Lifecycle (override these)
- `_ready()` — once, after the node and its children enter the tree. Do setup here.
- `_process(delta)` — every rendered frame (variable rate). Visuals, input polling.
- `_physics_process(delta)` — fixed timestep. Movement/physics.
- `_enter_tree()` / `_exit_tree()` — when (de)parented.
Call `queue_free()` to delete a node safely at frame end.

## Instancing a scene at runtime
```gdscript
const Enemy := preload("res://scenes/enemy.tscn")
func spawn() -> void:
    var e := Enemy.instantiate()
    add_child(e)
    e.global_position = $SpawnPoint.global_position
```

## Composition guidance
- One responsibility per scene; build screens by instancing component scenes.
- Communicate **up** via signals (see `godot-signals`), **down** via method calls or
  exported properties (`@export var speed: float = 200.0`).
- Avoid reaching across the tree with long `get_node("../../..")` paths; use unique names,
  exported NodePaths, or signals/autoloads instead.

Docs: https://docs.godotengine.org/en/stable/getting_started/step_by_step/scene_tree.html
