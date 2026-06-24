# Autoloop: continuous opencode iteration

This sets up a loop where opencode keeps working on its own and only stops to
ask you when a real decision is required.

> Note: the actual control tokens are intentionally written in a "defused" form
> in THIS file (with a `Z` inserted) so that reading this doc can never trip the
> loop detector. The runner and the `/autoloop` command use the real tokens.
> Real tokens: `<<<CONTINUEZ>>>`, `<<<NEEDS_USER_INPUTZ>>>`, `<<<DONEZ>>>`
> (remove the `Z` to see the real form).

## Pieces

- `.opencode/command/autoloop.md` — the `/autoloop` command. It tells the agent
  what one iteration is and to end every turn with a control token on the last
  line. The protocol is inlined here (not read from a file) on purpose.
- `tools/autoloop.py` — an external driver that calls `opencode run` in a loop,
  inspects only the LAST few lines for a control token, and decides whether to
  continue, pause for your input, or stop.

## Why an external driver

A single agent turn cannot keep itself alive after it returns; opencode has no
built-in "run until blocked" loop. The driver supplies that outer loop by
re-invoking `opencode run` and feeding your answers back in when needed.

## Run it

Restart opencode once so the new command loads, then:

```bash
# verify the decision logic (no opencode needed)
python3 tools/autoloop.py --self-test

# prove the loop mechanics end-to-end against a scripted fake
python3 tools/autoloop.py --dry-run

# real run (safe to run multiple copies; each gets its own session/log)
python3 tools/autoloop.py --max 20 --model sakana-ai/fugu-ultra

# stronger isolation: copy the repo first, then run in that copy
python3 tools/autoloop.py --copy-workspace --max 20 --model sakana-ai/fugu-ultra
```

## How stopping works

Each iteration the agent ends with exactly one control token on the final line:

- continue token → driver runs the next iteration automatically
- needs-input token → driver prints the question and reads one answer from you,
  then feeds it into the next iteration (the loop resumes, no restart needed)
- done token → driver stops

If no token is found in the last few lines, the driver stops rather than risk a
runaway loop.

## Flags worth knowing

- `--no-interactive` exits on pause (for CI/cron) instead of prompting.
- By default each runner creates and pins its own session, so multiple runners do
  not steal each other's `--continue` target.
- `--shared-session` restores old `--continue` behavior.
- `--copy-workspace` runs in `.autoloop-runs/<run-id>/` so file edits are isolated.
- `--run-id ID` sets the session title, workspace name, and default log name.
- `--session ID` pins an existing session.
- `--log-file path` appends full transcripts; otherwise logs go to `.autoloop-runs/<run-id>.log`.
- `--tail-window N` how many trailing lines are scanned for a token.
- `--max N` hard cap on iterations (cost/safety).

## Known limitations

- The driver trusts the agent to emit a token; the inlined command + tail-only
  scan make false positives unlikely but not impossible.
- If you use `--copy-workspace`, merge useful changes back manually after review.
