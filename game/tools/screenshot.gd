extends SceneTree
## Render a scene to a PNG. Run WITHOUT --headless (the dummy renderer can't draw).
##
## Usage:
##   godot --path game -s res://tools/screenshot.gd -- <res://scene.tscn> <out.png> [frames]
##
## Prefer the `tools/shoot.sh` wrapper, which locates Godot, converts paths for the
## WSL/Windows build, and moves the result into the repo.

func _initialize() -> void:
	_capture()


func _capture() -> void:
	var args := OS.get_cmdline_user_args()
	var scene_path := "res://main.tscn"
	var out_path := "res://screenshot.png"
	var frames := 4
	if args.size() > 0:
		scene_path = args[0]
	if args.size() > 1:
		out_path = args[1]
	if args.size() > 2:
		frames = maxi(1, int(args[2]))

	var packed := load(scene_path) as PackedScene
	if packed == null:
		push_error("screenshot.gd: cannot load scene: " + scene_path)
		quit(1)
		return
	root.add_child(packed.instantiate())

	# Let the renderer actually produce frames before we read the framebuffer.
	for _i in frames:
		await process_frame

	var img := root.get_texture().get_image()
	var err := img.save_png(out_path)
	if err != OK:
		push_error("screenshot.gd: save_png failed (%d) -> %s" % [err, out_path])
		quit(1)
		return
	print("screenshot.gd: wrote %s %s" % [out_path, img.get_size()])
	quit(0)
