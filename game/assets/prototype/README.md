# Prototype Textures — graybox fallback

A curated subset of Kenney's CC0 **Prototype Textures** pack. Per
[`docs/art_direction.md`](../../../docs/art_direction.md) (#9) these are the
**fallback for any missing sprite/texture**: if a needed sprite/texture/icon does
not exist in the real art packs, drop a graybox in here, note it, and keep
moving — never block on missing art.

## What's here

Near-neutral light-gray surfaces (1024×1024 PNG), renamed by what they show:

| File | Surface |
| --- | --- |
| `grid_fine.png` | fine 8×8 reference grid |
| `grid.png` | quartered reference grid |
| `grid_diagonal.png` | grid with diagonals |
| `checker.png` | checkerboard |
| `crosshair.png` | registration crosshairs |
| `wall.png` | labelled "WALL" (1×1 m) block |
| `door.png` | labelled "DOOR" opening |
| `window.png` | labelled "WINDOW" opening |
| `stairs.png` | labelled "STAIRS" |

Source ordering is per-color in the pack; these are pulled from the **Light** set
so they tint cleanly (see below). Import only what you need — don't copy the whole
pack, and never commit the raw source pack.

## Using these as placeholders

1. Point your `Sprite2D` / `TextureRect` at e.g. `res://assets/prototype/grid.png`.
2. The bases are near-white, so a multiply-style **`modulate`** reproduces the
   Wada Sanzo palette (combo 282) faithfully — the same trick `terrain_demo.gd`
   uses. Tint placeholders with `eugenia_red` / `maple` / `cobalt_green` / `lilac`
   so a graybox still reads in-theme; leave `modulate` white for a raw graybox.
3. Leave a `# TODO: placeholder art` (or an issue) so it can be swapped for real
   art later.

See [`game/scenes/prototype_demo.tscn`](../../scenes/prototype_demo.tscn) for an
assembled example (raw graybox top row, palette-tinted surfaces below).

## License / attribution

Kenney **Prototype Textures (1.0)** — CC0 1.0 (public domain). Free for personal,
educational and commercial use; crediting Kenney is appreciated, not required.
Full attribution in
[`game/assets/licenses/prototype-textures.md`](../licenses/prototype-textures.md).
