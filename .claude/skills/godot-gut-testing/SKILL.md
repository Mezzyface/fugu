---
name: godot-gut-testing
description: Unit testing Godot 4.x with GUT (Godot Unit Test) — installing the addon, writing test scripts, and running headless from the CLI for the verification gate. Use when adding tests for GDScript logic, setting up the test harness, or running tests to verify a task.
---

# GUT (Godot Unit Test) for Godot 4.x

GUT is the standard GDScript unit-test framework. It installs as an in-repo addon and runs
headless, which makes it the verification gate for dispatcher tasks.

## Install (once, committed to the repo)
- Add via the AssetLib in-editor, or vendor `addons/gut/` from
  https://github.com/bitwes/Gut (use the Godot 4.x branch).
- Enable the plugin in Project Settings → Plugins (or it can run purely from CLI).

## Write a test
Tests live in `game/test/`, file names `test_*.gd`, extending `GutTest`:
```gdscript
extends GutTest

func test_monster_takes_damage() -> void:
    var m := Monster.new()
    m.max_hp = 100
    add_child_autofree(m)          # auto-freed after the test
    m.take_damage(30)
    assert_eq(m._current_hp, 70, "hp should drop by damage amount")

func test_dies_at_zero() -> void:
    var m := autofree(Monster.new())
    m.max_hp = 10
    m.take_damage(999)
    assert_false(m.is_alive())
```
Common asserts: `assert_eq/ne`, `assert_true/false`, `assert_null`, `assert_almost_eq`,
`assert_signal_emitted(obj, "died")`. Use `before_each()/after_each()` for setup.

## Run headless (verification gate)
```bash
GODOT="/mnt/c/Project-Fugu/Godot_v4.7-stable_win64.exe/Godot_v4.7-stable_win64.exe"
"$GODOT" --path "$(wslpath -w game)" --headless \
  -s addons/gut/gut_cmdln.gd -gdir=res://test -ginclude_subdirs -gexit
```
`-gexit` returns a non-zero exit code on failure, so it works as a CI/verification check.
A wrapper at `tools/verify.sh` (added by the verification task) bundles gdlint + GUT.

Docs: https://gut.readthedocs.io/  •  https://github.com/bitwes/Gut
