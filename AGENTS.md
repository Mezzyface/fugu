# Fugu

This repo configures an OpenCode provider for [Sakana AI](https://sakana.ai).

## What's here

- `opencode.json` — registers `sakana-ai` as a provider with two models:
  - `fugu` — base model (1M context, reasoning + tool calls + attachments)
  - `fugu-ultra` — premium tier with per-token cost pricing

## Important

- Both models use `@ai-sdk/openai-compatible` pointing at `https://api.sakana.ai/v1`
- Set `SAKANA_AI_API_KEY` (or the key name OpenCode expects for `sakana-ai`) as an env var
- High reasoning effort is the default (low/medium variants are disabled)
- Timeout is 2 hours (7200000ms) — agents should expect long-running generations

## Prototype

`prototype/` holds a Python gacha-RPG prototype (`game.py`, `assets.py`) driven by
`docs/gdd_iteration_1.md`, plus its test suite (`prototype/test_game.py`, stdlib
`unittest`, no pytest required):

```bash
python3 -m unittest prototype/test_game.py
python3 prototype/game.py   # runs the demo() pipeline
```

There is no build system or CI — run the tests manually after changing `prototype/`.

## Autoloop

`tools/autoloop.py` plus `.opencode/command/autoloop.md` implement a self-driving
iteration loop (see `prompt/autoloop.md` for the full protocol). Runs started with
`--copy-workspace` write into `.autoloop-runs/<run-id>/` and do **not** touch the
real working tree — check that directory for unmerged work before assuming the
canonical `prototype/` files are up to date.
