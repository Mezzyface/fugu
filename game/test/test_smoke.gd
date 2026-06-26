extends GutTest
## Smoke test confirming the test harness runs and the main scene loads.


func test_gut_runs() -> void:
	assert_true(true, "GUT executes a passing assertion")


func test_main_scene_loads() -> void:
	var packed := load("res://main.tscn") as PackedScene
	assert_not_null(packed, "main.tscn should load as a PackedScene")
	var instance := packed.instantiate()
	add_child_autofree(instance)
	assert_true(instance is Control, "main scene root should be a Control")
