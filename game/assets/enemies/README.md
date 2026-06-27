# Enemy sprites

Curated subset of the **Tiny Swords — Enemy Pack** by Pixel Frog.
See `../licenses/tiny-swords-enemy-pack-License.txt` for attribution/license.

Five enemy types, each with an `Idle` spritesheet and a matching avatar portrait:

| Enemy         | Folder           | Source group   | Idle frame size | Idle frames | Avatar  |
|---------------|------------------|----------------|----------------:|------------:|--------:|
| Spear Goblin  | `spear_goblin/`  | Goblin Raiders | 256×256         | 8           | 256×256 |
| Torch Goblin  | `torch_goblin/`  | Goblin Raiders | 192×192         | 8           | 256×256 |
| Hex Shaman    | `hex_shaman/`    | Goblin Raiders | 192×192         | 8           | 256×256 |
| Harpoon Shark | `harpoon_shark/` | Pirate Fish    | 192×192         | 8           | 256×256 |
| Bomb Fish     | `bomb_fish/`     | Pirate Fish    | 192×192         | 8           | 256×256 |

Each `*_Idle.png` is a single-row horizontal spritesheet. Slice with `hframes`
(frame size = width / frame-count) on a `Sprite2D`, or feed into `SpriteFrames` /
`AnimatedSprite2D`. Each `*_Avatar.png` is a single 256×256 portrait.

Pixel art: keep texture filtering on **Nearest** so sprites stay crisp. The
project default is Nearest (`rendering/textures/canvas_textures/default_texture_filter=0`),
and the demo scene also sets `texture_filter = 1` per sprite.

Demo: `res://scenes/enemies_demo.tscn` shows each enemy's idle frame above its
avatar portrait.
