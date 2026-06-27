# Unit sprites — Blue team

Curated subset of the **Tiny Swords (Free Pack)** by Pixel Frog (CC0).
See `../licenses/tiny-swords-License.txt` for attribution/license.

Five player unit types (Blue/default team), `Idle` and `Run` spritesheets each:

| Unit    | Folder     | Frame size | Idle frames | Run frames |
|---------|------------|-----------:|------------:|-----------:|
| Pawn    | `pawn/`    | 192×192    | 8           | 6          |
| Warrior | `warrior/` | 192×192    | 8           | 6          |
| Lancer  | `lancer/`  | 320×320    | 12          | 6          |
| Archer  | `archer/`  | 192×192    | 6           | 4          |
| Monk    | `monk/`    | 192×192    | 6           | 4          |

Each PNG is a single-row horizontal spritesheet. Slice with `hframes` (frame
size = width / frame-count) on a `Sprite2D`, or feed into `SpriteFrames` /
`AnimatedSprite2D`.

Pixel art: keep texture filtering on **Nearest** so sprites stay crisp. The
project default is set to Nearest (`rendering/textures/canvas_textures/default_texture_filter=0`),
and the demo scene also sets `texture_filter = 1` per sprite.

Demo: `res://scenes/units_demo.tscn` shows a row of idle frames.
