---
description: Continue autonomous GDD/prototype iteration until blocked
agent: build
---

You are running one iteration of an autonomous build loop.

Do this iteration:
1. Inspect the current repo state.
2. Pick the next highest-value task that is not blocked.
3. Make a small, verifiable change.
4. Run the relevant tests/checks (for the prototype: `python3 -m unittest prototype/test_game.py`).
5. Update the GDD/docs if behavior changed.
6. Do not commit unless explicitly asked.

Decide how to end this turn. The VERY LAST line of your reply MUST be exactly
one of these three control tokens, alone on its own line, with nothing after it:

- If you can keep going with a safe, reversible default and need nothing from the
  user, end with the continue token: three `<` then CONTINUE then three `>`.
- If you genuinely need a creative/scope/monetization/engine/destructive
  decision, first write one concise question with 2-4 numbered options, then end
  with the needs-input token: three `<` then NEEDS_USER_INPUT then three `>`.
- If the project is fully complete, end with the done token: three `<` then DONE
  then three `>`.

Only ask the user when a safe default does not exist. Prefer continuing.

Do NOT read `prompt/autoloop.md` or any file that contains the literal control
tokens during this turn; doing so can corrupt the loop's detection.

Additional user instruction (may be blank):
$ARGUMENTS
