extends SceneTree
## Record a scene to a sequence of raw RGB frames (for tools/gif.py -> animated GIF).
## Run WITHOUT --headless so the GPU renders. Prefer the tools/gif.sh wrapper.
##
## Usage:
##   godot --path game -s res://tools/record.gd -- <res://scene.tscn> <out_dir> [frames] [every] [max_w]
##     frames : number of frames to capture (default 24)
##     every  : capture once per N rendered frames (default 2)
##     max_w  : downscale frames to this width (default 480) to keep the GIF small

func _initialize() -> void:
	_record()


func _record() -> void:
	var args := OS.get_cmdline_user_args()
	var scene_path := "res://main.tscn"
	var out_dir := "res://.__cap"
	var frames := 24
	var every := 2
	var max_w := 480
	if args.size() > 0: scene_path = args[0]
	if args.size() > 1: out_dir = args[1]
	if args.size() > 2: frames = maxi(1, int(args[2]))
	if args.size() > 3: every = maxi(1, int(args[3]))
	if args.size() > 4: max_w = maxi(16, int(args[4]))

	var packed := load(scene_path) as PackedScene
	if packed == null:
		push_error("record.gd: cannot load scene: " + scene_path)
		quit(1)
		return
	root.add_child(packed.instantiate())

	DirAccess.make_dir_recursive_absolute(out_dir)
	var w := 0
	var h := 0
	var captured := 0
	# warm up a couple of frames so the first capture isn't blank
	await process_frame
	await process_frame
	while captured < frames:
		for _k in every:
			await process_frame
		var img := root.get_texture().get_image()
		if max_w > 0 and img.get_width() > max_w:
			var scale := float(max_w) / float(img.get_width())
			img.resize(max_w, int(img.get_height() * scale), Image.INTERPOLATE_NEAREST)
		img.convert(Image.FORMAT_RGB8)
		w = img.get_width()
		h = img.get_height()
		var f := FileAccess.open("%s/%03d.rgb" % [out_dir, captured], FileAccess.WRITE)
		f.store_buffer(img.get_data())
		f.close()
		captured += 1

	var meta := FileAccess.open("%s/meta.txt" % out_dir, FileAccess.WRITE)
	meta.store_string("%d %d %d" % [w, h, captured])
	meta.close()
	print("record.gd: wrote %d frames (%dx%d) to %s" % [captured, w, h, out_dir])
	quit(0)
