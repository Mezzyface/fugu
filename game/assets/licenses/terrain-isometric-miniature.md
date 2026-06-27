# Terrain tiles — Isometric Miniature Prototype (Kenney)

- **Source pack:** Isometric Miniature Prototype (v2.3)
- **Author:** Kenney — https://www.kenney.nl
- **License:** Creative Commons Zero (CC0 1.0 Universal) — public domain
  https://creativecommons.org/publicdomain/zero/1.0/
- **Free** for personal, educational and commercial projects. Crediting
  Kenney is appreciated but not required.

## What's imported here

A curated terrain subset lives under `game/assets/terrain/` — ground, height
and ramp tiles only (props such as doors, windows, crates, columns, fences and
switches from the source pack were intentionally left out). Each tile ships in
all four facings (`_N`, `_E`, `_S`, `_W`). Bases imported:

`floor`, `floorHalf`, `floorQuarter`, `slab`, `slabAngle`, `slabHalf`,
`slabQuarter`, `block`, `blockAngle`, `blockHalf`, `blockQuarter`, `slope`,
`slopeHalf`, `slopeQuarter`, `slopeSmall`, `sloperCornerInner`,
`sloperCornerOuter`, `stairs`, `stairsCornerInner`, `stairsCornerOuter`,
`steps` (84 PNGs total).

## Tile geometry (for placement)

All tiles are 256×512 px. The isometric diamond footprint is **256 wide ×
128 tall**, bottom-anchored at the bottom edge of the image. Adjacent cells
therefore offset by half a diamond: `±128 px` horizontal, `+64 px` vertical
per grid step. See `game/scenes/terrain_demo.tscn` for an assembled example.

Imported for issue #22.
