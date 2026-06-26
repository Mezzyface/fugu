# Art direction (decision record — closes #9)

The art direction for Fugu, decided by the human. This is the authoritative mapping from
game element → source asset pack. Agents must follow it when building visuals.

## Direction at a glance

| Element | Source | Notes |
| --- | --- | --- |
| Title & header text | **honeyblot_caps** ("Honeyplay caps") | display font, all-caps feel |
| Body / everything-else text | **HoneyPigeon** | readable UI/body font |
| Player characters / units | **Tiny Swords (Free Pack)** → `Units/` | color-team variants (Blue is the default) |
| Enemies | **Tiny Swords (Enemy Pack)** → `Enemy Pack/Enemies/` + `Enemy Avatars/` | |
| Terrain | **Isometric Miniature Prototype** | isometric prototype tiles |
| UI panels / frames / icons | **Isle of Lore 2 UI pack** + RPG item icons | already partly imported (#8) |
| Fallback (any missing sprite/texture) | **Prototype Textures** | graybox stand-in until real art exists |
| Splat / particles / patterns / light masks / extra | Kenney FX packs (see catalog) | cataloged, used as needed |

**Fallback rule:** if a needed sprite/texture/icon does not exist in the packs above, use a
**Prototype Textures** graybox placeholder and note it (so it can be replaced later). Never
block on missing art.

## Color palette

Base palette: **Wada Sanzo, "A Dictionary of Color Combinations", combination 282 (classic)**.
Use it wherever we control color — UI theme, text, panel tints, particle/light tints, prototype
graybox tints, backgrounds/patterns. Sprite art (Tiny Swords, terrain) keeps its own colors; the
palette governs everything around it so the mixed packs read as one game.

| Role | Name | HEX | Use |
| --- | --- | --- | --- |
| Primary accent | Eugenia Red | `#da525d` | CTAs, danger/enemy, highlights, important numbers |
| Warm neutral | Maple | `#c59f6b` | panel frames, wood/earth, secondary UI, borders |
| Secondary | Cobalt Green | `#96d1aa` | success/positive, nature/terrain accents, calm UI |
| Tertiary accent | Lilac | `#b984af` | magic/rarity, selection/focus, subtle highlights |

Guidance: pick **one** accent per screen as the lead; use Maple as the connective neutral; keep
text high-contrast over panels (a real bug we already hit). For Tiny Swords' color-team unit
variants, default to the **Blue** team and let the palette drive UI/effects around them. Define
these as named colors in the project `Theme` so they're reused, not hard-coded per node.

Source: [Wada Sanzo Colors — combination 282](https://www.wada-sanzo-colors.com/combination/classic/282),
hex via [W.S. Colors](https://wscolors.com/colors) / [colors.elwyn.co](https://colors.elwyn.co/).

## Source asset inventory

All sources live under `C:\Project-Fugu` (= `/mnt/c/Project-Fugu`, the parent of this repo),
**outside** the repo. They are NOT committed — import only the curated subset you need into
`game/assets/` (see "In-repo layout"). The chosen zips have been extracted to plain folders.

| Source (under `/mnt/c/Project-Fugu/`) | Files | Format | Use |
| --- | --- | --- | --- |
| `honeyblot_caps/honeyblot_caps.ttf` (+ `.otf`) | 1 font | ttf/otf | title + header font |
| `HoneyPigeon/HoneyPigeon.ttf` | 1 font | ttf | body font |
| `Tiny Swords (Free Pack)/Units/` | ~ | png (+aseprite) | player units (Lancer, Archer, …) in Black/Blue/Purple/Red/Yellow teams |
| `Tiny Swords (Free Pack)/Buildings/`, `Terrain/`, `UI Elements/`, `Particle FX/` | ~ | png | extra Tiny Swords art (secondary) |
| `Tiny Swords (Enemy Pack)/Enemy Pack/Enemies/` | ~ | png | enemies: Caveborn, Gnoll, Gnome, Goblin Raiders, Minotaur, sharks, fish… |
| `Tiny Swords (Enemy Pack)/Enemy Pack/Enemy Avatars/` | ~ | png | enemy portrait avatars |
| `Isometric Miniature Prototype/extracted/Isometric/` | 651 png total | png | terrain tiles (blocks, angles, ramps) |
| `Prototype Textures/PNG/` | 80 png | png/svg | graybox fallback textures |
| `Splat Pack/PNG/` | 73 png | png/svg | splats (impact/ground decals) |
| `Particle Pack/PNG (Transparent)/` | 193 png | png | particles (fire, smoke, circles, flames…) |
| `Smoke Particles/PNG/` | 79 png | png | smoke particles |
| `Explosion Pack/PNG/` (+ `Spritesheets/`) | 69 png | png | explosions |
| `Pattern Pack/PNG/`, `Pattern Pack Lines/PNG/` | 171 + 125 png | png | background patterns |
| `Light Masks/{Default,Inverted,Transparent}/` | 457 png | png | light masks / glow / vignettes |
| `Isle of Lore 2` UI pack + item icons (zips) | — | png | UI frames + RPG icons (#8) |

Counts are source totals; import a small, relevant subset, not the whole pack.

## In-repo layout (`game/assets/`)

Import curated subsets here (mirrors the existing `game/assets/ui/` from #8):

```
game/assets/
  fonts/        honeyblot_caps.ttf, HoneyPigeon.ttf
  ui/           (existing — Isle of Lore 2 panels/buttons/bars)
  units/        Tiny Swords player units (default: Blue team)
  enemies/      Tiny Swords enemies + avatars
  terrain/      Isometric Miniature Prototype tiles
  prototype/    Prototype Textures graybox fallbacks
  fx/           curated splats / particles / explosions / light masks (as needed)
  licenses/     a license/attribution file per pack used
```

## Import conventions (for agents)

- Source packs are reachable from a task worktree via **Bash** (`cp`, `find`, `python3`) at
  their absolute `/mnt/c/Project-Fugu/...` paths. Copy with Bash; do not rely on the Read
  tool for binary assets.
- Skip macOS junk: never copy `._*` or `.DS_Store` files.
- Import a **curated subset** — only what the current task needs. Never copy a whole pack,
  and never commit the raw source packs/zips (they're outside the repo and stay there).
- Record license/attribution for every pack you pull from under `game/assets/licenses/`.
- Visual changes need a screenshot in the PR — use `tools/shoot.sh` (see CLAUDE.md). Asset
  import tasks are labelled `ui`.
- Update `deliverables/manifest.md` (these tasks are labelled `deliverable`).

## Theme wiring (fonts)

The project `Theme` must default body/label text to **HoneyPigeon** and use **honeyblot_caps**
for titles and section headers (larger sizes). Apply via the theme on the UI root so children
inherit it; override per-control only for headers.
