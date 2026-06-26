---
name: godot-signals
description: Godot 4.x signals — declaring, emitting, and connecting them with the Callable syntax, plus when to use signals vs direct calls. Use when wiring decoupled communication between nodes/scenes, reacting to events, or refactoring tight coupling.
---

# Godot 4.x signals

Signals are the decoupled event mechanism. A node emits; listeners connect. Prefer signals
for **child → parent** / sibling communication so scenes stay reusable.

## Declare and emit
```gdscript
signal died
signal health_changed(current: int, max: int)

func take_damage(amount: int) -> void:
    _hp = maxi(_hp - amount, 0)
    health_changed.emit(_hp, max_hp)        # 4.x: emit as a method on the signal
    if _hp == 0:
        died.emit()
```

## Connect (Callable syntax — 4.x)
```gdscript
func _ready() -> void:
    $Enemy.died.connect(_on_enemy_died)
    $Enemy.health_changed.connect(_on_health_changed)
    # one-shot / deferred flags:
    $Boss.died.connect(_on_boss_died, CONNECT_ONE_SHOT)

func _on_enemy_died() -> void:
    score += 10

func _on_health_changed(current: int, _max: int) -> void:
    $UI/HealthBar.value = current
```
- Connect in code for clarity/testability, or in the editor's Node dock for designer wiring.
- Bind extra args: `button.pressed.connect(_buy.bind(item_id))`.
- Disconnect with `sig.disconnect(callable)`; check with `sig.is_connected(callable)`.

## Signals vs direct calls
- Up/sideways, or "something happened" → **signal**.
- Down the tree, or "do this now" → **direct method call** / exported reference.
- Global cross-cutting events → an autoload "event bus" singleton with signals.

Docs: https://docs.godotengine.org/en/stable/getting_started/step_by_step/signals.html
