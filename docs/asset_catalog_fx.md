# FX asset catalog (#26)

Catalog of the Kenney FX packs available under `/mnt/c/Project-Fugu/` (raw packs are
**gitignored / never committed**) and the small curated starter subset imported into
`game/assets/fx/` for early prototyping.

All packs below are **Kenney (www.kenney.nl), Creative Commons Zero (CC0 1.0)** — free
for personal, educational and commercial use; crediting Kenney is appreciated but not
required. Attribution is recorded in `game/assets/licenses/fx-kenney.md`.

Art direction: `docs/art_direction.md` (#9). Screens these feed: `docs/wireframes.md`.
Palette (Wada Sanzo combo 282) used for tinting in the demo: Eugenia Red `#da525d`,
Maple `#c59f6b`, Cobalt Green `#96d1aa`, Lilac `#b984af`.

## Packs

| Pack | Source path (under `/mnt/c/Project-Fugu/`) | PNGs | Intended use |
| --- | --- | --- | --- |
| Splat Pack | `Splat Pack/PNG/` | 72 (36 @256px + 36 @512px) | Blood/ink/impact decals on the ground; hit markers; one-shot impact stamps. Tint with palette per damage type. |
| Particle Pack | `Particle Pack/PNG (Transparent)/` | 96 (80 + 16 pre-rotated) | Atlas frames for `GPUParticles2D` / `CPUParticles2D` — circles, dirt, fire, flame, flare, light, magic, muzzle, scorch, scratch, slash, smoke, spark, star, symbol, trace, twirl, window. Additive glow for ability/hit FX. |
| Smoke Particles | `Smoke Particles/PNG/` | 77 (Black smoke 25, White puff 25, Explosion 9, Flash 9, Gas 9) | Frame sequences for smoke/puff/flash AnimatedSprite2D or particle textures. |
| Explosion Pack | `Explosion Pack/PNG/` | 62 (Ground/Pixel/Regular/Simple/Sonic = 9 frames each, Particles 17) | 9-frame explosion sequences for `AnimatedSprite2D` / `SpriteFrames` — ability impacts, deaths, criticals. |
| Pattern Pack | `Pattern Pack/PNG/` | 168 (84 @Default + 84 @Double) | Seamless background/overlay patterns for panels, banners, card backs, UI fills. |
| Pattern Pack Lines | `Pattern Pack Lines/PNG/` | 120 (Thick/Thin × Default/Double, 30 each) | Line-art patterns — dividers, frames, decorative strokes, subtle UI texture. |
| Light Masks | `Light Masks/` | 457 (Default 152, Inverted 152, Transparent 152 + preview) | `PointLight2D` / `Light2D` texture masks (cones, circles, rings, fans, foliage, shapes) and additive glow overlays for lighting and aura/ability glows. |

## Curated starter subset → `game/assets/fx/`

A deliberately tiny subset for prototyping; expand later as real screens need it.

| Folder | Files | From |
| --- | --- | --- |
| `splat/` | `splat00`–`splat03` (4) | Splat Pack / Default (256px) |
| `particles/` | `circle_05`, `flame_06`, `spark_05`, `magic_05`, `star_07`, `smoke_07` (6) | Particle Pack (Transparent) |
| `explosion/` | `regularExplosion00`–`08` (9-frame sequence) | Explosion Pack / Regular explosion |
| `light_masks/` | `circle_a`, `cone_a`, `ring_a`, `fan_a` (4) | Light Masks / Default |

**23 PNGs total.** Demonstrated in `game/scenes/fx_demo.tscn`: palette-tinted splats, an
additive-glow particle row, the explosion as both an autoplaying `AnimatedSprite2D` and a
filmstrip of frames, and two light masks as additive glow overlays.
