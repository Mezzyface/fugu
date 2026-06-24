#!/usr/bin/env python3
"""Autoloop runner for opencode.

Repeatedly invokes a single opencode session, letting the agent iterate on its
own. The agent ends every turn with a sentinel on the final line:

    <<<CONTINUE>>>          keep looping, no input needed
    <<<NEEDS_USER_INPUT>>>  pause; a question + options precede this line
    <<<DONE>>>              project complete, stop

The loop only asks the human when it sees NEEDS_USER_INPUT. In interactive mode
it reads one answer from the terminal and feeds it straight back into the next
iteration, so the loop resumes without restarting.

Usage:
    python3 tools/autoloop.py --max 20 --model sakana-ai/fugu-ultra
    python3 tools/autoloop.py --self-test        # verify decision logic
    python3 tools/autoloop.py --dry-run          # exercise loop w/o opencode

Caveats:
    * Restart opencode once so the .opencode/command/autoloop.md command loads.
    * Sessions: by default every process creates and pins its own session.
      Use --shared-session to restore --continue behavior.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Set, Tuple

CONTINUE = "<<<CONTINUE>>>"
NEEDS_USER_INPUT = "<<<NEEDS_USER_INPUT>>>"
DONE = "<<<DONE>>>"
SENTINELS = (CONTINUE, NEEDS_USER_INPUT, DONE)

RESULT_DONE = "done"
RESULT_PAUSED = "paused"
RESULT_ABORTED = "aborted"
RESULT_ERROR = "error"
RESULT_NO_SENTINEL = "no_sentinel"
RESULT_MAX = "max_iterations"

QUIT_WORDS = {"", "q", "quit", "exit", "stop", "abort"}
DEFAULT_COPY_EXCLUDES = {
    ".git",
    ".mypy_cache",
    ".opencode/node_modules",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
}


def classify(output: str, tail_window: int = 8) -> Optional[str]:
    """Return the controlling sentinel, or None.

    Only the last `tail_window` non-empty lines are inspected, and the first
    exact-match sentinel found scanning upward from the bottom wins. This makes
    the decision immune to sentinels that appear earlier in the output (for
    example when the agent reads a file that documents the sentinels), while
    still tolerating a few trailing footer lines (cost/usage summaries).
    """
    seen = 0
    for line in reversed(output.splitlines()):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in SENTINELS:
            return stripped
        seen += 1
        if seen >= tail_window:
            break
    return None


def extract_question(output: str, tail_window: int = 40) -> str:
    """Return the lines just above the NEEDS_USER_INPUT sentinel for display."""
    lines = output.splitlines()
    for index in range(len(lines) - 1, -1, -1):
        if lines[index].strip() == NEEDS_USER_INPUT:
            start = max(0, index - tail_window)
            question = [line for line in lines[start:index] if line.strip()]
            return "\n".join(question).strip()
    return ""


@dataclass
class LoopConfig:
    max_iterations: int = 20
    interactive: bool = True
    tail_window: int = 8


def run_loop(
    runner: Callable[[str], Tuple[int, str]],
    build_message: Callable[[int, Optional[str]], str],
    ask_user: Callable[[str], Optional[str]],
    log: Callable[[str], None],
    config: LoopConfig,
) -> str:
    """Drive the loop with injected dependencies (kept pure for testing)."""
    pending_answer: Optional[str] = None
    for iteration in range(1, config.max_iterations + 1):
        message = build_message(iteration, pending_answer)
        pending_answer = None
        code, output = runner(message)
        log(output)
        if code != 0:
            log(f"opencode exited with code {code}; stopping")
            return RESULT_ERROR
        decision = classify(output, config.tail_window)
        if decision == DONE:
            return RESULT_DONE
        if decision == NEEDS_USER_INPUT:
            if not config.interactive:
                return RESULT_PAUSED
            answer = ask_user(extract_question(output))
            if answer is None or answer.strip().lower() in QUIT_WORDS:
                return RESULT_ABORTED
            pending_answer = answer.strip()
            continue
        if decision == CONTINUE:
            continue
        log("No sentinel on final lines; stopping to avoid a runaway loop.")
        return RESULT_NO_SENTINEL
    return RESULT_MAX


def recent_sessions(project_dir: Path) -> Set[str]:
    command = ["opencode", "session", "list", "--max-count", "200", "--format", "json"]
    process = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if process.returncode != 0:
        return set()
    try:
        sessions = json.loads(process.stdout)
    except json.JSONDecodeError:
        return set()
    directory = str(project_dir)
    return {item["id"] for item in sessions if item.get("directory") == directory and item.get("id")}


def newest_session(project_dir: Path, before: Set[str], title: str) -> Optional[str]:
    command = ["opencode", "session", "list", "--max-count", "200", "--format", "json"]
    process = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if process.returncode != 0:
        return None
    try:
        sessions = json.loads(process.stdout)
    except json.JSONDecodeError:
        return None
    directory = str(project_dir)
    candidates = [
        item
        for item in sessions
        if item.get("directory") == directory
        and item.get("title") == title
        and item.get("id") not in before
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda item: item.get("created", 0), reverse=True)
    return candidates[0].get("id")


def copy_workspace(source: Path, target: Path, excludes: Set[str]) -> None:
    def ignore(directory: str, names: List[str]) -> Set[str]:
        base = Path(directory)
        ignored = set()
        for name in names:
            path = base / name
            relative = path.relative_to(source).as_posix()
            if name in excludes or relative in excludes:
                ignored.add(name)
        return ignored

    shutil.copytree(source, target, ignore=ignore)


def make_runner(
    project_dir: Path,
    model: Optional[str],
    agent: Optional[str],
    session: Optional[str],
    log_path: Optional[Path],
    isolate_session: bool,
    run_title: str,
) -> Callable[[str], Tuple[int, str]]:
    state = {"session": session, "before": recent_sessions(project_dir) if isolate_session and not session else set()}

    def runner(message: str) -> Tuple[int, str]:
        command = ["opencode", "run", "--dir", str(project_dir)]
        if state["session"]:
            command.extend(["--session", state["session"]])
        elif not isolate_session:
            command.append("--continue")
        else:
            command.extend(["--title", run_title])
        if model:
            command.extend(["--model", model])
        if agent:
            command.extend(["--agent", agent])
        command.append(message)
        process = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if isolate_session and not state["session"] and process.returncode == 0:
            state["session"] = newest_session(project_dir, state["before"], run_title)
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"\n$ {' '.join(command)}\n{process.stdout}\n")
        return process.returncode, process.stdout

    return runner


def make_dry_run_runner(log: Callable[[str], None]) -> Callable[[str], Tuple[int, str]]:
    """A scripted fake that proves loop mechanics without invoking opencode."""
    script: List[str] = [
        f"iteration A: did work\n{CONTINUE}",
        "iteration B: read prompt/autoloop.md which mentions "
        f"{NEEDS_USER_INPUT} and {DONE} mid-text\n{CONTINUE}",
        "Question: pick an engine?\n1. Godot\n2. Web\n"
        f"{NEEDS_USER_INPUT}",
        f"iteration D: applied your answer\n{CONTINUE}",
        f"iteration E: finished\n{DONE}",
    ]
    state = {"i": 0}

    def runner(message: str) -> Tuple[int, str]:
        log(f"[dry-run message] {message}")
        index = min(state["i"], len(script) - 1)
        state["i"] += 1
        return 0, script[index]

    return runner


def build_message_factory(extra: str) -> Callable[[int, Optional[str]], str]:
    def build_message(iteration: int, pending_answer: Optional[str]) -> str:
        message = "/autoloop"
        if pending_answer:
            return f"{message} {pending_answer}"
        if iteration == 1 and extra:
            return f"{message} {extra}"
        return message

    return build_message


def _self_test() -> int:
    cases = {
        f"work done\n{CONTINUE}": CONTINUE,
        f"mentions {DONE} early\nthen\n{CONTINUE}": CONTINUE,
        f"q?\n{NEEDS_USER_INPUT}": NEEDS_USER_INPUT,
        f"{DONE}\ntokens: 123 cost: $0.01": DONE,
        "no sentinel here": None,
        f"{NEEDS_USER_INPUT}\nbut continue wins\n{CONTINUE}": CONTINUE,
    }
    ok = True
    for text, expected in cases.items():
        got = classify(text)
        flag = "ok" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print(f"[{flag}] expected={expected} got={got} :: {text!r}")
    return 0 if ok else 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Loop opencode until it needs input or finishes.")
    parser.add_argument("--dir", default=".", help="Project directory")
    parser.add_argument("--max", type=int, default=20, help="Maximum iterations")
    parser.add_argument("--run-id", default=None, help="Unique run ID for session titles, workspaces, and logs")
    parser.add_argument("--shared-session", action="store_true", help="Use --continue when --session is not set")
    parser.add_argument("--copy-workspace", action="store_true", help="Run in an isolated copy under --workspace-root")
    parser.add_argument("--workspace-root", default=".autoloop-runs", help="Root for isolated workspace copies")
    parser.add_argument("--exclude", action="append", default=[], help="Extra path/name to skip when copying workspaces")
    parser.add_argument("--sleep", type=float, default=1.0, help="Seconds between iterations")
    parser.add_argument("--model", default=None, help="provider/model")
    parser.add_argument("--agent", default=None, help="opencode agent")
    parser.add_argument("--session", default=None, help="Pin a session ID instead of --continue")
    parser.add_argument("--extra", default="", help="Extra instruction appended on the first iteration")
    parser.add_argument("--tail-window", type=int, default=8, help="Lines from the end scanned for a sentinel")
    parser.add_argument("--no-interactive", action="store_true", help="Exit on pause instead of asking")
    parser.add_argument("--log-file", default=None, help="Append full transcripts to this file")
    parser.add_argument("--self-test", action="store_true", help="Check decision logic and exit")
    parser.add_argument("--dry-run", action="store_true", help="Run loop against a scripted fake")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    source_dir = Path(args.dir).resolve()
    if not source_dir.exists():
        print(f"Project directory does not exist: {source_dir}", file=sys.stderr)
        return 2

    run_id = args.run_id or f"autoloop-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    project_dir = source_dir
    if args.copy_workspace:
        workspace_root = Path(args.workspace_root)
        if not workspace_root.is_absolute():
            workspace_root = source_dir / workspace_root
        project_dir = workspace_root / run_id
        if project_dir.exists():
            print(f"Workspace already exists: {project_dir}", file=sys.stderr)
            return 2
        copy_workspace(source_dir, project_dir, DEFAULT_COPY_EXCLUDES | set(args.exclude) | {workspace_root.name})
        print(f"[autoloop workspace] {project_dir}")

    config = LoopConfig(
        max_iterations=args.max,
        interactive=not args.no_interactive,
        tail_window=args.tail_window,
    )

    def log(text: str) -> None:
        print(text, end="" if text.endswith("\n") else "\n", flush=True)

    def ask_user(question: str) -> Optional[str]:
        if question:
            print("\n--- input needed ---")
            print(question)
        try:
            return input("answer (blank/q to stop) > ")
        except EOFError:
            return None

    log_path = Path(args.log_file).resolve() if args.log_file else source_dir / ".autoloop-runs" / f"{run_id}.log"
    if args.dry_run:
        runner = make_dry_run_runner(log)
    else:
        runner = make_runner(
            project_dir,
            args.model,
            args.agent,
            args.session,
            log_path,
            not args.shared_session,
            run_id,
        )

    build_message = build_message_factory(args.extra)

    iteration_counter = {"n": 0}

    def counting_runner(message: str) -> Tuple[int, str]:
        iteration_counter["n"] += 1
        print(f"\n=== autoloop iteration {iteration_counter['n']} (max {args.max}) ===", flush=True)
        result = runner(message)
        if args.sleep and not args.dry_run:
            time.sleep(max(0.0, args.sleep))
        return result

    result = run_loop(counting_runner, build_message, ask_user, log, config)
    print(f"\n[autoloop result] {result}")
    return 0 if result in {RESULT_DONE, RESULT_PAUSED, RESULT_ABORTED, RESULT_MAX} else 1


if __name__ == "__main__":
    raise SystemExit(main())
