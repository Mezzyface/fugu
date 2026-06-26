# Theme & palette attribution (#21)

The project `Theme` (`game/assets/theme/fugu_theme.tres`) combines two sources.

## Fonts

Wired into the theme from the already-imported faces under `game/assets/ui/fonts/`:

- **honeyblot caps** — titles and section headers (`TitleLabel` / `HeaderLabel`).
- **HoneyPigeon** — default body / label text.

Both are *Steven Colling Font License* fonts; the full license texts live under
`game/assets/ui/licenses/` and the embedding terms are summarised in
`game/assets/ui/README.md`. They permit embedding the `.ttf` as a technical
necessity to render the game; attribution is appreciated but not required.

## Palette

The four named theme colors (under the `Palette` theme type) are
**Wada Sanzo, "A Dictionary of Color Combinations", combination 282 (classic)**:

| Theme color name | Name | Hex |
| --- | --- | --- |
| `eugenia_red` | Eugenia Red | `#da525d` |
| `maple` | Maple | `#c59f6b` |
| `cobalt_green` | Cobalt Green | `#96d1aa` |
| `lilac` | Lilac | `#b984af` |

Source: <https://www.wada-sanzo-colors.com/combination/classic/282>. The
combinations in *A Dictionary of Color Combinations* (Sanzo Wada, 1933) are in the
public domain; the colors are reproduced here as plain RGB values, not as any
copyrighted layout from the book. See `docs/art_direction.md` (#9) for usage
guidance.
