#!/usr/bin/env python3
"""Board-driven task dispatcher for Project Fugu.

Polls a GitHub Project board, pulls "Ready" issues labelled for the agent, runs
Claude Code headless on each one inside an isolated git worktree, and opens a PR
back to the repo for human review. Tasks routed to a human are surfaced, never
executed.

Lifecycle per task:
    Ready --(pick up)--> In Progress --(PR opened)--> In Review
                                  \\--(blocked/red)--> Needs Human

Design notes (carried over from tools/autoloop.py, which this supersedes):
    * The external driver owns the lifecycle; the agent never decides to loop.
    * One fresh agent run per task, so context never accumulates across tasks.
    * Each run is isolated in its own worktree/branch -> one reviewable PR.
    * The decision logic is pure and unit-tested (`--self-test`) so we never burn
      a real agent run to test the plumbing.

Usage:
    python3 tools/dispatch.py --self-test          # pure-logic checks, no network
    python3 tools/dispatch.py --dry-run            # scripted end-to-end, no side effects
    python3 tools/dispatch.py --once --no-act      # real board read, print what it WOULD do
    python3 tools/dispatch.py --once               # one real poll+dispatch cycle
    python3 tools/dispatch.py                      # poll forever

Requires: `gh` (authed, with `project` write scope), `git`, and `claude` on PATH.
Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

# ---- sentinels the agent ends its run with -----------------------------------
TASK_DONE = "<<<TASK_DONE>>>"
NEEDS_HUMAN = "<<<NEEDS_HUMAN>>>"

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "tools" / "dispatch_config.json"
DEFAULT_STATE = ROOT / "tools" / "dispatch_state.json"


# ---- config / state ----------------------------------------------------------
@dataclass
class Config:
    owner: str
    owner_type: str
    project_number: int
    repo: str
    base_branch: str
    poll_interval_seconds: int
    max_concurrency: int
    agent: str
    model: str
    allowed_tools: str
    status_field: str
    status_values: Dict[str, str]
    labels: Dict[str, str]
    worktree_dir: str
    runs_dir: str

    @staticmethod
    def load(path: Path) -> "Config":
        data = json.loads(path.read_text())
        return Config(**data)


def load_state(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2) + "\n")


# ---- pure helpers (unit-tested) ----------------------------------------------
def slugify(title: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    # drop a leading "[task] " style prefix once normalised
    slug = re.sub(r"^(task|bug)-", "", slug)
    return (slug[:max_len].strip("-")) or "task"


def parse_issue_body(body: str) -> Dict[str, str]:
    """Split a GitHub issue-form body into {heading: content}.

    Issue forms render each field as a `### Heading` followed by its value, so we
    bucket lines by the most recent `### ` header. Robust to plain-text bodies
    (everything lands under "_preamble").
    """
    sections: Dict[str, List[str]] = {"_preamble": []}
    current = "_preamble"
    for line in body.splitlines():
        m = re.match(r"^#{2,3}\s+(.*\S)\s*$", line)
        if m:
            current = m.group(1).strip()
            sections.setdefault(current, [])
        else:
            sections[current].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def _section(parsed: Dict[str, str], *names: str) -> str:
    """Return the first section whose heading contains any of `names` (ci)."""
    lowered = {k.lower(): k for k in parsed}
    for name in names:
        for low, original in lowered.items():
            if name.lower() in low:
                return parsed[original]
    return ""


def is_agent_task(task: "Task", labels_cfg: Dict[str, str]) -> bool:
    """Agent-eligible: has the agent label, no human label, no human assignee."""
    if labels_cfg["human"] in task.labels:
        return False
    if task.assignees:
        return False
    return labels_cfg["agent"] in task.labels


def select_ready(
    tasks: List["Task"],
    in_progress: int,
    max_concurrency: int,
    status_values: Dict[str, str],
    labels_cfg: Dict[str, str],
) -> List["Task"]:
    """Oldest-first agent tasks in `Ready`, capped by remaining concurrency."""
    slots = max(0, max_concurrency - in_progress)
    if slots <= 0:
        return []
    ready = [
        t
        for t in tasks
        if t.state == "OPEN"
        and t.status == status_values["ready"]
        and is_agent_task(t, labels_cfg)
    ]
    ready.sort(key=lambda t: t.number)
    return ready[:slots]


def count_in_progress(tasks: List["Task"], status_values: Dict[str, str]) -> int:
    return sum(1 for t in tasks if t.status == status_values["in_progress"])


def classify_result(returncode: int, output: str, tail_lines: int = 25) -> Tuple[str, str]:
    """Map an agent run to ('ok'|'needs_human'|'error', message).

    Scans only the last lines for a sentinel so sentinels quoted earlier in the
    transcript don't trigger a false decision (same idea as autoloop.classify).
    """
    tail = [ln.strip() for ln in output.splitlines() if ln.strip()][-tail_lines:]
    for line in reversed(tail):
        if line.startswith(NEEDS_HUMAN):
            reason = line[len(NEEDS_HUMAN):].strip() or "agent requested human help"
            return "needs_human", reason
        if line == TASK_DONE or line.endswith(TASK_DONE):
            return ("ok", "") if returncode == 0 else ("error", f"agent exit {returncode}")
    if returncode != 0:
        return "error", f"agent exited {returncode} with no completion sentinel"
    return "needs_human", "agent finished without a completion sentinel"


def build_task_md(task: "Task", parsed: Dict[str, str], labels_cfg: Dict[str, str]) -> str:
    context = _section(parsed, "context", "goal") or task.body
    resources = _section(parsed, "resource")
    acceptance = _section(parsed, "acceptance")
    outputs = _section(parsed, "output", "deliverable")
    verification = _section(parsed, "verification")
    is_deliverable = labels_cfg["deliverable"] in task.labels

    lines = [
        f"# Task #{task.number}: {task.title}",
        "",
        f"Issue: {task.url}",
        f"Branch: {task.branch}",
        "",
        "## Context / Goal",
        context or "_(none provided)_",
        "",
        "## Resources",
        resources or "_(none provided)_",
        "",
        "## Acceptance Criteria",
        acceptance or "_(none provided — infer from context, keep scope tight)_",
        "",
        "## Outputs / Deliverables",
        outputs or "_(none provided)_",
    ]
    if is_deliverable:
        lines += [
            "",
            "> This task is labelled `deliverable`: update `deliverables/manifest.md`"
            " in your changes (check the item off + link the path or external URL).",
        ]
    lines += [
        "",
        "## Verification commands",
        verification or "_(none specified — run any relevant lint/tests you can)_",
        "",
        "---",
        "Complete the work, then run the verification commands and confirm they pass.",
        "Do NOT push or open a PR — the dispatcher does that.",
        "End your final message with exactly one sentinel on its own line:",
        f"  {TASK_DONE}                     (done and verified)",
        f"  {NEEDS_HUMAN} <one-line reason> (blocked, or verification failed)",
    ]
    return "\n".join(lines) + "\n"


# ---- task model --------------------------------------------------------------
@dataclass
class Task:
    item_id: str          # ProjectV2Item node id
    number: int           # issue number
    title: str
    body: str
    url: str
    state: str            # OPEN / CLOSED
    status: str           # Status field value name ("Ready", ...)
    labels: List[str]
    assignees: List[str]
    branch: str = ""

    def __post_init__(self):
        if not self.branch:
            self.branch = f"task/{self.number}-{slugify(self.title)}"


# ---- gh / graphql ------------------------------------------------------------
def _run(cmd: List[str], cwd: Optional[Path] = None, check: bool = False) -> Tuple[int, str]:
    proc = subprocess.run(
        cmd, cwd=str(cwd) if cwd else None, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stdout}")
    return proc.returncode, proc.stdout


ITEMS_QUERY = """
query($login:String!, $number:Int!){
  %s(login:$login){
    projectV2(number:$number){
      id
      field(name:"Status"){
        ... on ProjectV2SingleSelectField { id name options { id name } }
      }
      items(first:100){
        nodes{
          id
          fieldValueByName(name:"Status"){
            ... on ProjectV2ItemFieldSingleSelectValue { name }
          }
          content{
            ... on Issue {
              number title body url state
              assignees(first:10){ nodes { login } }
              labels(first:30){ nodes { name } }
            }
          }
        }
      }
    }
  }
}
"""


def fetch_board(config: Config, state: dict) -> List[Task]:
    """Query the board, cache field/option ids in `state`, return Task list."""
    query = ITEMS_QUERY % config.owner_type  # "user" or "organization"
    code, out = _run([
        "gh", "api", "graphql",
        "-f", f"query={query}",
        "-f", f"login={config.owner}",
        "-F", f"number={config.project_number}",
    ])
    if code != 0:
        raise RuntimeError(f"board query failed:\n{out}")
    data = json.loads(out)
    project = data["data"][config.owner_type]["projectV2"]
    state["project_id"] = project["id"]
    fld = project.get("field") or {}
    if fld:
        state["status_field_id"] = fld["id"]
        state["status_options"] = {o["name"]: o["id"] for o in fld.get("options", [])}

    tasks: List[Task] = []
    for node in project["items"]["nodes"]:
        content = node.get("content") or {}
        if "number" not in content:  # draft item, not an issue — skip
            continue
        status_value = (node.get("fieldValueByName") or {}).get("name", "")
        tasks.append(Task(
            item_id=node["id"],
            number=content["number"],
            title=content.get("title", ""),
            body=content.get("body", "") or "",
            url=content.get("url", ""),
            state=content.get("state", "OPEN"),
            status=status_value,
            labels=[l["name"] for l in content.get("labels", {}).get("nodes", [])],
            assignees=[a["login"] for a in content.get("assignees", {}).get("nodes", [])],
        ))
    return tasks


SET_STATUS_MUTATION = """
mutation($project:ID!, $item:ID!, $field:ID!, $option:String!){
  updateProjectV2ItemFieldValue(input:{
    projectId:$project, itemId:$item, fieldId:$field,
    value:{ singleSelectOptionId:$option }
  }){ projectV2Item { id } }
}
"""


def set_status(config: Config, state: dict, task: Task, status_key: str) -> None:
    option_name = config.status_values[status_key]
    option_id = state.get("status_options", {}).get(option_name)
    if not option_id or "status_field_id" not in state:
        raise RuntimeError(
            f"cannot set status '{option_name}': missing field/option id "
            f"(is the '{option_name}' option configured on the board?)"
        )
    code, out = _run([
        "gh", "api", "graphql",
        "-f", f"query={SET_STATUS_MUTATION}",
        "-f", f"project={state['project_id']}",
        "-f", f"item={task.item_id}",
        "-f", f"field={state['status_field_id']}",
        "-f", f"option={option_id}",
    ])
    if code != 0:
        raise RuntimeError(f"set_status failed:\n{out}")


def comment_issue(config: Config, number: int, body: str) -> None:
    _run(["gh", "issue", "comment", str(number), "--repo", config.repo, "--body", body])


# ---- agent abstraction -------------------------------------------------------
class Agent:
    def run(self, workdir: Path, prompt: str, log_path: Path) -> Tuple[int, str]:
        raise NotImplementedError


@dataclass
class ClaudeCodeAgent(Agent):
    model: str
    allowed_tools: str

    def run(self, workdir: Path, prompt: str, log_path: Path) -> Tuple[int, str]:
        cmd = [
            "claude", "-p", prompt,
            "--model", self.model,
            "--permission-mode", "acceptEdits",
            "--allowedTools", self.allowed_tools,
            "--output-format", "json",
        ]
        mcp = workdir / ".mcp.json"
        if mcp.exists():
            cmd += ["--mcp-config", str(mcp)]
        proc = subprocess.run(cmd, cwd=str(workdir), text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(proc.stdout)
        return proc.returncode, _agent_text(proc.stdout)


def _agent_text(stdout: str) -> str:
    """Extract the final assistant text from `claude --output-format json`,
    falling back to raw stdout when it isn't the JSON envelope we expect."""
    try:
        obj = json.loads(stdout)
        if isinstance(obj, dict) and "result" in obj:
            sentinel = ""
            if obj.get("is_error"):
                sentinel = ""  # let returncode/heuristics decide
            return f"{obj.get('result', '')}\n{sentinel}".strip()
    except json.JSONDecodeError:
        pass
    return stdout


# ---- git worktree ------------------------------------------------------------
def create_worktree(config: Config, task: Task, run_id: str) -> Path:
    wt_root = ROOT / config.worktree_dir
    wt_root.mkdir(parents=True, exist_ok=True)
    wt = wt_root / f"{task.number}-{run_id}"
    _run(["git", "fetch", "origin", config.base_branch], cwd=ROOT, check=True)
    _run(["git", "worktree", "add", "-b", task.branch, str(wt),
          f"origin/{config.base_branch}"], cwd=ROOT, check=True)
    return wt


def remove_worktree(wt: Path) -> None:
    _run(["git", "worktree", "remove", "--force", str(wt)], cwd=ROOT)


def commit_push_pr(config: Config, task: Task, wt: Path, run_id: str) -> Optional[str]:
    """Commit, push, open PR. Returns the PR url, or None if nothing changed."""
    _run(["git", "add", "-A"], cwd=wt, check=True)
    code, out = _run(["git", "diff", "--cached", "--quiet"], cwd=wt)
    if code == 0:  # no staged changes
        return None
    msg = (f"{task.title}\n\nCloses #{task.number}\n\n"
           f"Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>")
    _run(["git", "commit", "-m", msg], cwd=wt, check=True)
    _run(["git", "push", "-u", "origin", task.branch], cwd=wt, check=True)
    body = (f"Closes #{task.number}\n\nAutomated by the board dispatcher "
            f"(run `{run_id}`). Please review.\n\n"
            f"🤖 Generated with [Claude Code](https://claude.com/claude-code)")
    code, out = _run([
        "gh", "pr", "create", "--repo", config.repo,
        "--base", config.base_branch, "--head", task.branch,
        "--title", task.title, "--body", body,
    ], cwd=wt)
    if code != 0:
        raise RuntimeError(f"gh pr create failed:\n{out}")
    return out.strip().splitlines()[-1] if out.strip() else None


# ---- dispatch one task -------------------------------------------------------
def dispatch_one(config: Config, state: dict, task: Task, agent: Agent, act: bool,
                 log: Callable[[str], None]) -> str:
    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    log(f"[dispatch] #{task.number} '{task.title}' -> branch {task.branch} (run {run_id})")
    if not act:
        log(f"  [no-act] would: set In Progress, worktree, run agent, PR, set In Review")
        return "skipped"

    set_status(config, state, task, "in_progress")
    comment_issue(config, task.number,
                  f"🤖 Picked up by the dispatcher (run `{run_id}`). Working on branch "
                  f"`{task.branch}`.")
    wt = create_worktree(config, task, run_id)
    try:
        parsed = parse_issue_body(task.body)
        task_md = build_task_md(task, parsed, config.labels)
        (wt / ".dispatch").mkdir(exist_ok=True)
        (wt / ".dispatch" / "TASK.md").write_text(task_md)

        prompt = ("Complete the single task described in .dispatch/TASK.md "
                  "(also reproduced below). Follow CLAUDE.md.\n\n" + task_md)
        log_path = ROOT / config.runs_dir / f"{task.number}-{run_id}.log"
        rc, out = agent.run(wt, prompt, log_path)
        verdict, message = classify_result(rc, out)
        log(f"  agent verdict: {verdict} {('- ' + message) if message else ''}")

        if verdict == "ok":
            pr = commit_push_pr(config, task, wt, run_id)
            if pr is None:
                set_status(config, state, task, "needs_human")
                comment_issue(config, task.number,
                              "⚠️ Agent reported done but produced no changes. Routing to "
                              "**Needs Human**. Log: `" + str(log_path.name) + "`")
                return "no_changes"
            set_status(config, state, task, "in_review")
            comment_issue(config, task.number, f"✅ PR opened for review: {pr}")
            return "in_review"

        set_status(config, state, task, "needs_human")
        comment_issue(config, task.number,
                      f"🚧 Routed to **Needs Human** ({verdict}): {message}\n\n"
                      f"Branch `{task.branch}` kept for inspection. Log: "
                      f"`{log_path.name}`")
        return verdict
    finally:
        # Keep the branch (pushed or local) but drop the worktree dir to stay tidy.
        remove_worktree(wt)


# ---- poll loop ---------------------------------------------------------------
def poll_once(config: Config, state: dict, agent: Agent, act: bool,
              log: Callable[[str], None]) -> List[str]:
    tasks = fetch_board(config, state)
    save_state(DEFAULT_STATE, state)
    in_progress = count_in_progress(tasks, config.status_values)
    selected = select_ready(tasks, in_progress, config.max_concurrency,
                            config.status_values, config.labels)
    human = [t for t in tasks if config.labels["human"] in t.labels
             and t.status == config.status_values["ready"]]
    log(f"[poll] {len(tasks)} items | {in_progress} in-progress | "
        f"{len(selected)} selected | {len(human)} human-ready")
    for t in human:
        log(f"  [human] #{t.number} '{t.title}' awaits you (not executed)")
    results = []
    for task in selected:
        try:
            results.append(dispatch_one(config, state, task, agent, act, log))
        except Exception as exc:  # one bad task shouldn't kill the loop
            log(f"  [error] #{task.number}: {exc}")
            results.append("error")
    return results


# ---- self-test (pure logic) --------------------------------------------------
def _self_test() -> int:
    ok = True

    def check(name, got, expected):
        nonlocal ok
        flag = "ok" if got == expected else "FAIL"
        if got != expected:
            ok = False
        print(f"[{flag}] {name}: got={got!r} expected={expected!r}")

    check("slugify", slugify("[Task] Scaffold Godot 4.7 Project!"), "scaffold-godot-4-7-project")
    check("classify done", classify_result(0, f"did stuff\n{TASK_DONE}"), ("ok", ""))
    check("classify needs", classify_result(0, f"blocked\n{NEEDS_HUMAN} missing asset")[0], "needs_human")
    check("classify err", classify_result(1, "boom")[0], "error")
    check("classify no-sentinel", classify_result(0, "just chatter")[0], "needs_human")
    check("classify quoted-sentinel-ignored",
          classify_result(0, f"the doc mentions {TASK_DONE} here\nactually blocked\n{NEEDS_HUMAN} x")[0],
          "needs_human")

    body = (
        "### Assignee\n\nagent (claude)\n\n"
        "### Deliverable type\n\ncode\n\n"
        "### Context / Goal\n\nBuild the thing.\n\n"
        "### Resources\n\n- game/assets\n\n"
        "### Acceptance Criteria\n\n- [ ] it works\n\n"
        "### Outputs / Deliverables\n\nA scene.\n\n"
        "### Verification commands\n\ngdlint game/\n"
    )
    parsed = parse_issue_body(body)
    check("parse context", _section(parsed, "context", "goal"), "Build the thing.")
    check("parse verification", _section(parsed, "verification"), "gdlint game/")

    labels = {"agent": "agent:claude", "human": "human", "deliverable": "deliverable"}
    sv = {"ready": "Ready", "in_progress": "In Progress", "in_review": "In Review",
          "needs_human": "Needs Human"}
    mk = lambda n, status, lbls, asg=[]: Task(
        item_id=f"i{n}", number=n, title=f"t{n}", body="", url="", state="OPEN",
        status=status, labels=lbls, assignees=asg)
    tasks = [
        mk(1, "Ready", ["agent:claude"]),
        mk(2, "Ready", ["human"]),
        mk(3, "Backlog", ["agent:claude"]),
        mk(4, "Ready", ["agent:claude"], asg=["someone"]),
        mk(5, "Ready", ["agent:claude", "deliverable"]),
    ]
    sel = select_ready(tasks, in_progress=0, max_concurrency=2, status_values=sv, labels_cfg=labels)
    check("select picks agent-ready", [t.number for t in sel], [1, 5])
    sel0 = select_ready(tasks, in_progress=2, max_concurrency=2, status_values=sv, labels_cfg=labels)
    check("select respects concurrency", sel0, [])
    md = build_task_md(tasks[4], parse_issue_body(""), labels)
    check("deliverable note present", "deliverables/manifest.md" in md, True)

    print("\nSELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def _dry_run() -> int:
    """Exercise poll_once end-to-end with a fake board + fake agent, no side effects."""
    print("[dry-run] scripted board, no gh/git/claude calls\n")
    cfg = Config.load(DEFAULT_CONFIG)
    sv, labels = cfg.status_values, cfg.labels
    fake_tasks = [
        Task("i1", 1, "Add a line to README", "### Context / Goal\n\ndemo", "url", "OPEN",
             sv["ready"], [labels["agent"]], []),
        Task("i2", 2, "Human design call", "", "url", "OPEN", sv["ready"], [labels["human"]], []),
    ]

    def log(s): print(s)
    # monkeypatch board fetch + dispatch internals by running select/path directly
    in_prog = count_in_progress(fake_tasks, sv)
    selected = select_ready(fake_tasks, in_prog, cfg.max_concurrency, sv, labels)
    human = [t for t in fake_tasks if labels["human"] in t.labels]
    log(f"[poll] {len(fake_tasks)} items | {in_prog} in-progress | {len(selected)} selected | {len(human)} human-ready")
    for t in human:
        log(f"  [human] #{t.number} '{t.title}' awaits you (not executed)")
    for t in selected:
        log(f"[dispatch] #{t.number} '{t.title}' -> branch {t.branch}")
        md = build_task_md(t, parse_issue_body(t.body), labels)
        log("  built TASK.md (%d chars); fake agent -> %s" % (len(md), TASK_DONE))
        log("  would: In Progress -> commit/push -> PR -> In Review")
    print("\n[dry-run] OK")
    return 0


# ---- main --------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", default=str(DEFAULT_CONFIG))
    p.add_argument("--once", action="store_true", help="One poll cycle then exit")
    p.add_argument("--no-act", action="store_true", help="Read the board but take no actions")
    p.add_argument("--dry-run", action="store_true", help="Scripted board+agent, no network")
    p.add_argument("--self-test", action="store_true", help="Pure-logic checks, then exit")
    p.add_argument("--interval", type=int, default=None, help="Override poll interval (seconds)")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.dry_run:
        return _dry_run()

    config = Config.load(Path(args.config))
    state = load_state(DEFAULT_STATE)
    agent = ClaudeCodeAgent(model=config.model, allowed_tools=config.allowed_tools)
    interval = args.interval if args.interval is not None else config.poll_interval_seconds

    def log(s): print(s, flush=True)

    if args.once:
        poll_once(config, state, agent, act=not args.no_act, log=log)
        return 0

    log(f"[dispatch] polling {config.owner}/projects/{config.project_number} every {interval}s")
    while True:
        try:
            poll_once(config, state, agent, act=not args.no_act, log=log)
        except Exception as exc:
            log(f"[poll error] {exc}")
        time.sleep(max(5, interval))


if __name__ == "__main__":
    raise SystemExit(main())
