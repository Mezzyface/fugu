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
    """Ready agent tasks, capped by remaining concurrency.

    QA review tasks are picked before implementation tasks (then oldest-first within
    each group), so each PR gets reviewed before the dispatcher starts new work — reviews
    keep pace instead of piling up behind a backlog of implementations.
    """
    slots = max(0, max_concurrency - in_progress)
    if slots <= 0:
        return []
    qa_label = labels_cfg.get("qa", "qa")
    ready = [
        t
        for t in tasks
        if t.state == "OPEN"
        and t.status == status_values["ready"]
        and is_agent_task(t, labels_cfg)
    ]
    ready.sort(key=lambda t: (qa_label not in t.labels, t.number))
    return ready[:slots]


def count_in_progress(tasks: List["Task"], status_values: Dict[str, str]) -> int:
    return sum(1 for t in tasks if t.status == status_values["in_progress"])


def closed_to_reconcile(tasks: List["Task"], done_status: str) -> List["Task"]:
    """Closed issues whose Status isn't Done yet (GitHub closes the issue on PR merge
    but doesn't move the Project's Status field). Excludes items with no status set."""
    return [t for t in tasks if t.state == "CLOSED" and t.status and t.status != done_status]


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
    is_ui = labels_cfg.get("ui", "ui") in task.labels

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
    manifest_note = (
        f"> **Record your deliverable as its own file.** If this task produces a tracked"
        f" deliverable (code, doc, or external artifact), add"
        f" `deliverables/items/{task.number}-<slug>.md` with frontmatter"
        f" (`section:` — one of `Foundation / tooling` / `Game (Godot)` / `Design`;"
        f" `issue: {task.number}`; `checked: true`) then a one-line description with the"
        f" in-repo paths/links and `(#{task.number})`. **Only add that one item file.**"
        f" Do NOT run `tools/build_manifest.py` and do NOT add/commit"
        f" `deliverables/manifest.md` — it is gitignored and generated locally; committing it"
        f" reintroduces the merge conflicts this design removed."
    )
    if is_deliverable:
        manifest_note += " This task is labelled `deliverable`, so the item file is **required**."
    lines += ["", manifest_note]
    if is_ui:
        lines += [
            "",
            "> **Visual task — screenshots required.** After implementing, capture each new or",
            "> changed screen so the PR can be reviewed visually:",
            f">   `bash tools/shoot.sh res://<scene>.tscn screenshots/{task.number}/<name>.png`",
            "> (renders windowed; do NOT use `--headless`). Commit the PNG(s) under"
            f" `screenshots/{task.number}/` — the dispatcher embeds them in the PR. Open each one"
            " and confirm it actually shows the intended result before you finish.",
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


# ---- QA (verifier) tasks -----------------------------------------------------
# A QA task is the "implementer != verifier" gate: when an implementation task
# opens a PR, the dispatcher files a `qa`-labelled follow-up. The poller later
# runs a FRESH agent that checks out the PR branch, runs the verification gate
# and acceptance criteria, comments PASS/FAIL on the PR, and (on failure) files a
# bug. QA tasks never spawn QA tasks (no recursion).
QA_META_RE = re.compile(r"<!--\s*qa-meta\s+(.*?)\s*-->", re.S)


def is_qa_task(task: "Task", labels_cfg: Dict[str, str]) -> bool:
    return labels_cfg.get("qa", "qa") in task.labels


def pr_number_from_url(url: str) -> Optional[int]:
    m = re.search(r"/pull/(\d+)", url or "")
    return int(m.group(1)) if m else None


def parse_qa_meta(body: str) -> Dict[str, str]:
    """Extract the `<!-- qa-meta k=v ... -->` block the dispatcher embeds."""
    m = QA_META_RE.search(body or "")
    meta: Dict[str, str] = {}
    if m:
        for kv in m.group(1).split():
            if "=" in kv:
                k, v = kv.split("=", 1)
                meta[k] = v
    return meta


def strip_title_prefix(title: str) -> str:
    return re.sub(r"^\[[^\]]+\]\s*", "", title).strip()


def qa_issue_body(impl_task: "Task", parsed_impl: Dict[str, str],
                  pr_url: str, pr_number: int, is_ui: bool = False) -> str:
    acceptance = _section(parsed_impl, "acceptance") or "_(none specified)_"
    verification = (_section(parsed_impl, "verification")
                    or "_(none specified — run tools/verify.sh)_")
    return "\n".join([
        f"<!-- qa-meta pr={pr_number} branch={impl_task.branch} impl={impl_task.number}"
        f" ui={'1' if is_ui else '0'} -->",
        "",
        f"Automated QA for #{impl_task.number} (PR {pr_url}). A verifier agent checks out the",
        "PR branch, runs the verification gate, and checks the acceptance criteria below, then",
        "comments **QA PASSED** / **QA FAILED** on the PR. On failure it files a linked bug.",
        "",
        "### Acceptance Criteria",
        acceptance,
        "",
        "### Verification commands",
        verification,
    ]) + "\n"


def build_qa_md(task: "Task", meta: Dict[str, str], acceptance: str,
                verification: str, repo: str) -> str:
    pr = meta.get("pr", "?")
    impl = meta.get("impl", "?")
    branch = meta.get("branch", "?")
    return "\n".join([
        f"# QA review of PR #{pr} (implements #{impl})",
        "",
        "You are a **verifier**, not the implementer. The proposed work is already checked",
        f"out on branch `{branch}` (this worktree). Do NOT modify the implementation — only",
        "inspect, run checks, and report.",
        "",
        "## Steps",
        "1. Run the verification gate. Prefer `bash tools/verify.sh`; if that file isn't on",
        "   this branch yet, run the import + GUT steps from CLAUDE.md directly.",
        "2. Check every Acceptance Criteria item below against the actual code/behaviour."
        + (" Re-render the affected screen(s) with `bash tools/shoot.sh res://<scene>.tscn"
           f" screenshots/{impl}/qa-<name>.png` and compare against the screenshots committed"
           " in the PR — they must match the intended result." if meta.get("ui") == "1" else ""),
        "3. Post your verdict as a PR **comment** (the bot and PR author are the same GitHub",
        "   account, so `--approve`/`--request-changes` are rejected — use `gh pr comment`):",
        f"   - PASS: `gh pr comment {pr} --repo {repo} --body \"✅ QA PASSED — <summary>\"`",
        f"   - FAIL: `gh pr comment {pr} --repo {repo} --body \"❌ QA FAILED — <what failed>\"`",
        "4. On FAIL, also file a linked bug:",
        f"   `gh issue create --repo {repo} --label bug \\",
        f"      --title \"[Bug] <short> (PR #{pr})\" \\",
        f"      --body \"Found during QA of #{impl} / PR #{pr}. <details + repro steps>\"`",
        "",
        "## Acceptance Criteria",
        acceptance or "_(none specified — infer from the PR diff + verify.sh)_",
        "",
        "## Task-specific verification commands",
        verification or "_(none — rely on tools/verify.sh)_",
        "",
        "---",
        "End your final message with exactly one sentinel on its own line:",
        f"  {TASK_DONE}                       (QA passed; you posted ✅ on the PR)",
        f"  {NEEDS_HUMAN} <one-line summary>  (QA failed; you posted ❌ and filed a bug)",
    ]) + "\n"


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


def _set_status_by_item(config: Config, state: dict, item_id: str, status_key: str) -> None:
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
        "-f", f"item={item_id}",
        "-f", f"field={state['status_field_id']}",
        "-f", f"option={option_id}",
    ])
    if code != 0:
        raise RuntimeError(f"set_status failed:\n{out}")


def set_status(config: Config, state: dict, task: Task, status_key: str) -> None:
    _set_status_by_item(config, state, task.item_id, status_key)


def comment_issue(config: Config, number: int, body: str) -> None:
    _run(["gh", "issue", "comment", str(number), "--repo", config.repo, "--body", body])


def pr_review_state(config: Config, pr: str) -> str:
    """OPEN / MERGED / CLOSED for a PR (empty string if it can't be read)."""
    code, out = _run(["gh", "pr", "view", str(pr), "--repo", config.repo, "--json", "state"])
    if code != 0:
        return ""
    try:
        return json.loads(out).get("state", "")
    except json.JSONDecodeError:
        return ""


def reconcile_closed(config: Config, state: dict, tasks: List["Task"],
                     log: Callable[[str], None]) -> int:
    """Move closed issues that aren't Done yet -> Done (a PR merge closes the issue
    but leaves the board's Status field untouched). Safety net for the GitHub
    'item closed -> Done' workflow."""
    done_name = config.status_values.get("done")
    if not done_name:
        return 0
    stale = closed_to_reconcile(tasks, done_name)
    for t in stale:
        try:
            set_status(config, state, t, "done")
            log(f"  [reconcile] #{t.number} closed -> Done (was {t.status or 'no status'})")
        except Exception as exc:
            log(f"  [reconcile] #{t.number} failed: {exc}")
    return len(stale)


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


def screenshot_markdown(config: Config, task: Task, wt: Path) -> str:
    """Embed any PNGs the agent left under screenshots/<issue>/ into the PR body.

    Uses raw.githubusercontent URLs on the task branch so GitHub renders them inline.
    """
    shot_dir = wt / "screenshots" / str(task.number)
    if not shot_dir.is_dir():
        return ""
    shots = sorted(shot_dir.glob("*.png"))
    if not shots:
        return ""
    out = ["", "## Screenshots", ""]
    for p in shots:
        rel = f"screenshots/{task.number}/{p.name}"
        url = f"https://raw.githubusercontent.com/{config.repo}/{task.branch}/{rel}"
        out.append(f"**{p.stem}**")
        out.append("")
        out.append(f"![{p.stem}]({url})")
        out.append("")
    return "\n".join(out)


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
            f"(run `{run_id}`). Please review.\n"
            f"{screenshot_markdown(config, task, wt)}\n"
            f"\n🤖 Generated with [Claude Code](https://claude.com/claude-code)")
    # Run from the main repo, not the linked worktree: gh 2.93 fails with
    # "not a git repository: (NULL)" inside linked worktrees. The branch is
    # already pushed, so an explicit --head + --repo is sufficient here.
    code, out = _run([
        "gh", "pr", "create", "--repo", config.repo,
        "--base", config.base_branch, "--head", task.branch,
        "--title", task.title, "--body", body,
    ], cwd=ROOT)
    if code != 0:
        raise RuntimeError(f"gh pr create failed:\n{out}")
    return out.strip().splitlines()[-1] if out.strip() else None


def create_qa_worktree(config: Config, branch: str, run_id: str, number: int) -> Path:
    """Detached worktree at the PR head branch so QA inspects the proposed work."""
    wt_root = ROOT / config.worktree_dir
    wt_root.mkdir(parents=True, exist_ok=True)
    wt = wt_root / f"qa-{number}-{run_id}"
    _run(["git", "fetch", "origin", branch], cwd=ROOT, check=True)
    _run(["git", "worktree", "add", "--detach", str(wt), "FETCH_HEAD"], cwd=ROOT, check=True)
    return wt


def create_qa_task(config: Config, state: dict, impl_task: Task,
                   parsed_impl: Dict[str, str], pr_url: str,
                   log: Callable[[str], None]) -> None:
    """File a verifier QA task for a just-opened PR. Best-effort; never recurses."""
    if is_qa_task(impl_task, config.labels):
        return
    pr_number = pr_number_from_url(pr_url)
    if not pr_number:
        log("  [qa] could not parse PR number; skipping QA task")
        return
    title = f"[QA] Review #{impl_task.number}: {strip_title_prefix(impl_task.title)}"
    is_ui = config.labels.get("ui", "ui") in impl_task.labels
    body = qa_issue_body(impl_task, parsed_impl, pr_url, pr_number, is_ui)
    code, out = _run([
        "gh", "issue", "create", "--repo", config.repo,
        "--title", title, "--body", body,
        "--label", config.labels["agent"], "--label", config.labels.get("qa", "qa"),
    ])
    if code != 0:
        log(f"  [qa] gh issue create failed:\n{out}")
        return
    qa_url = out.strip().splitlines()[-1]
    code, out = _run(["gh", "project", "item-add", str(config.project_number),
                      "--owner", config.owner, "--url", qa_url, "--format", "json"])
    if code != 0:
        log(f"  [qa] item-add failed:\n{out}")
        return
    try:
        item_id = json.loads(out)["id"]
    except (json.JSONDecodeError, KeyError):
        log("  [qa] QA issue created but could not be added to the board")
        return
    _set_status_by_item(config, state, item_id, "ready")
    log(f"  [qa] filed QA task: {qa_url}")


def run_qa(config: Config, state: dict, task: Task, agent: Agent,
           run_id: str, log: Callable[[str], None]) -> str:
    """Execute a QA task: verify the PR branch, comment PASS/FAIL, close or escalate."""
    meta = parse_qa_meta(task.body)
    branch, pr = meta.get("branch"), meta.get("pr")
    if not branch or not pr:
        set_status(config, state, task, "needs_human")
        comment_issue(config, task.number,
                      "🚧 QA task is missing its `qa-meta` (branch/PR); needs a human.")
        return "needs_human"
    # If the human already merged/closed the PR, QA is moot (and the branch may be
    # gone). Close the QA task cleanly instead of failing to fetch a dead branch.
    if pr_review_state(config, pr) in ("MERGED", "CLOSED"):
        set_status(config, state, task, "done")
        comment_issue(config, task.number,
                      f"ℹ️ PR #{pr} is already resolved; QA is moot. Closing.")
        _run(["gh", "issue", "close", str(task.number), "--repo", config.repo])
        return "qa_moot"
    set_status(config, state, task, "in_progress")
    comment_issue(config, task.number,
                  f"🤖 QA started (run `{run_id}`): verifying PR #{pr} on `{branch}`.")
    wt = create_qa_worktree(config, branch, run_id, task.number)
    try:
        parsed = parse_issue_body(task.body)
        qa_md = build_qa_md(task, meta, _section(parsed, "acceptance"),
                            _section(parsed, "verification"), config.repo)
        (wt / ".dispatch").mkdir(exist_ok=True)
        (wt / ".dispatch" / "TASK.md").write_text(qa_md)
        prompt = ("You are performing QA. Follow .dispatch/TASK.md exactly "
                  "(reproduced below). Follow CLAUDE.md.\n\n" + qa_md)
        log_path = ROOT / config.runs_dir / f"qa-{task.number}-{run_id}.log"
        rc, out = agent.run(wt, prompt, log_path)
        verdict, message = classify_result(rc, out)
        log(f"  qa verdict: {verdict} {('- ' + message) if message else ''}")
        if verdict == "ok":
            # Tag the PR itself so the human sees "this one's cleared, merge it" — the
            # signal belongs on the PR being reviewed, not just on the QA task.
            label = config.labels.get("ready_to_merge", "ready-to-merge")
            _run(["gh", "pr", "edit", str(pr), "--repo", config.repo, "--add-label", label])
            set_status(config, state, task, "done")
            comment_issue(config, task.number,
                          f"✅ QA passed; labelled PR #{pr} `{label}` — ready for you to merge. Closing QA.")
            _run(["gh", "issue", "close", str(task.number), "--repo", config.repo])
            return "qa_passed"
        set_status(config, state, task, "needs_human")
        _run(["gh", "pr", "edit", str(pr), "--repo", config.repo,
              "--remove-label", config.labels.get("ready_to_merge", "ready-to-merge")])
        comment_issue(config, task.number,
                      f"❌ QA flagged PR #{pr} ({verdict}): {message}\n\n"
                      f"The verifier commented on the PR and (on failure) filed a bug. "
                      f"Log: `{log_path.name}`")
        return "qa_failed"
    finally:
        remove_worktree(wt)


# ---- rework (send a PR back for changes) -------------------------------------
# A rework task revises an EXISTING PR in place: a fresh agent checks out the PR
# branch, makes the requested changes, and the dispatcher pushes them back to the
# same branch (updating the PR) and re-renders screenshots. Reuses the qa-meta
# block (pr/branch/impl) to know which PR to revise.
def is_rework_task(task: "Task", labels_cfg: Dict[str, str]) -> bool:
    return labels_cfg.get("rework", "rework") in task.labels


def comment_pr(config: Config, pr: str, body: str) -> None:
    _run(["gh", "pr", "comment", str(pr), "--repo", config.repo, "--body", body])


def build_rework_md(task: "Task", meta: Dict[str, str], changes: str, repo: str) -> str:
    pr = meta.get("pr", "?"); branch = meta.get("branch", "?"); impl = meta.get("impl", "?")
    return "\n".join([
        f"# Rework of PR #{pr} (branch `{branch}`, implements #{impl})",
        "",
        "A reviewer asked for changes. The current work is already checked out on this branch.",
        "Make ONLY the requested changes; keep everything else. Do NOT open a PR — the dispatcher",
        "pushes your commit to the existing branch, which updates the PR.",
        "",
        "## Requested changes",
        changes or "_(see the PR review)_",
        "",
        "## Steps",
        "1. Make the requested changes.",
        "2. Run `bash tools/verify.sh` and confirm it passes.",
        f"3. If the change is visual, re-capture the affected screen(s) into `screenshots/{impl}/`",
        "   with `tools/shoot.sh`, OVERWRITING the existing PNGs so the PR's screenshots update.",
        "",
        "---",
        "End your final message with exactly one sentinel on its own line:",
        f"  {TASK_DONE}                       (changes made and verified)",
        f"  {NEEDS_HUMAN} <one-line reason>   (blocked)",
    ]) + "\n"


def create_rework_worktree(config: Config, branch: str, run_id: str, number: int) -> Path:
    """Worktree on a temp local branch at the PR head, so commits can be pushed back."""
    wt_root = ROOT / config.worktree_dir
    wt_root.mkdir(parents=True, exist_ok=True)
    wt = wt_root / f"rework-{number}-{run_id}"
    _run(["git", "fetch", "origin", branch], cwd=ROOT, check=True)
    _run(["git", "worktree", "add", str(wt), "-B", f"__rework_{number}", "FETCH_HEAD"],
         cwd=ROOT, check=True)
    return wt


def run_rework(config: Config, state: dict, task: Task, agent: Agent,
               run_id: str, log: Callable[[str], None]) -> str:
    meta = parse_qa_meta(task.body)
    branch, pr = meta.get("branch"), meta.get("pr")
    if not branch or not pr:
        set_status(config, state, task, "needs_human")
        comment_issue(config, task.number, "🚧 Rework task missing its branch/PR meta; needs a human.")
        return "needs_human"
    set_status(config, state, task, "in_progress")
    comment_issue(config, task.number, f"🤖 Rework started (run `{run_id}`): revising PR #{pr} on `{branch}`.")
    wt = create_rework_worktree(config, branch, run_id, task.number)
    try:
        parsed = parse_issue_body(task.body)
        changes = _section(parsed, "requested", "change", "context", "goal") or task.body
        rmd = build_rework_md(task, meta, changes, config.repo)
        (wt / ".dispatch").mkdir(exist_ok=True)
        (wt / ".dispatch" / "TASK.md").write_text(rmd)
        prompt = ("You are revising an existing PR. Follow .dispatch/TASK.md exactly "
                  "(reproduced below). Follow CLAUDE.md.\n\n" + rmd)
        log_path = ROOT / config.runs_dir / f"rework-{task.number}-{run_id}.log"
        rc, out = agent.run(wt, prompt, log_path)
        verdict, message = classify_result(rc, out)
        log(f"  rework verdict: {verdict} {('- ' + message) if message else ''}")
        if verdict == "ok":
            _run(["git", "add", "-A"], cwd=wt, check=True)
            code, _ = _run(["git", "diff", "--cached", "--quiet"], cwd=wt)
            if code == 0:
                set_status(config, state, task, "needs_human")
                comment_issue(config, task.number,
                              f"⚠️ Rework agent produced no changes. Needs human. Log: `{log_path.name}`")
                return "no_changes"
            _run(["git", "commit", "-m",
                  f"Rework: address review on PR #{pr}\n\n"
                  f"Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"], cwd=wt, check=True)
            code, out = _run(["git", "push", "origin", f"HEAD:{branch}"], cwd=wt)
            if code != 0:
                raise RuntimeError(f"rework push failed:\n{out}")
            set_status(config, state, task, "done")
            # The PR changed, so it's no longer "ready to merge" until QA re-passes.
            _run(["gh", "pr", "edit", str(pr), "--repo", config.repo,
                  "--remove-label", config.labels.get("ready_to_merge", "ready-to-merge")])
            comment_pr(config, pr, f"🔧 Revised per the rework request (run `{run_id}`); please re-review.")
            comment_issue(config, task.number, f"✅ Pushed revisions to PR #{pr}; closing rework.")
            _run(["gh", "issue", "close", str(task.number), "--repo", config.repo])
            return "reworked"
        set_status(config, state, task, "needs_human")
        comment_issue(config, task.number,
                      f"🚧 Rework → Needs Human ({verdict}): {message}. Log: `{log_path.name}`")
        return verdict
    finally:
        remove_worktree(wt)
        _run(["git", "branch", "-D", f"__rework_{task.number}"], cwd=ROOT)


def create_rework_task(config: Config, state: dict, pr_number: int, message: str,
                       log: Callable[[str], None]) -> Optional[str]:
    """File a rework task for an open PR. Looks up the PR's head branch + origin issue."""
    code, out = _run(["gh", "pr", "view", str(pr_number), "--repo", config.repo,
                      "--json", "headRefName,title"])
    if code != 0:
        log(f"[rework] gh pr view #{pr_number} failed:\n{out}"); return None
    info = json.loads(out)
    branch = info["headRefName"]; title = info.get("title", "")
    m = re.search(r"task/(\d+)-", branch)
    impl = m.group(1) if m else str(pr_number)
    body = (f"<!-- qa-meta pr={pr_number} branch={branch} impl={impl} -->\n\n"
            f"Reviewer requested changes on PR #{pr_number} ({title}).\n\n"
            f"### Requested changes\n\n{message}\n")
    code, out = _run(["gh", "issue", "create", "--repo", config.repo,
                      "--title", f"[Rework] PR #{pr_number}: {message[:48]}",
                      "--body", body, "--label", config.labels["agent"],
                      "--label", config.labels.get("rework", "rework")])
    if code != 0:
        log(f"[rework] issue create failed:\n{out}"); return None
    url = out.strip().splitlines()[-1]
    code, out = _run(["gh", "project", "item-add", str(config.project_number),
                      "--owner", config.owner, "--url", url, "--format", "json"])
    if code == 0:
        try:
            _set_status_by_item(config, state, json.loads(out)["id"], "ready")
        except (json.JSONDecodeError, KeyError) as exc:
            log(f"[rework] board add issue: {exc}")
    log(f"[rework] filed: {url}")
    return url


# ---- dispatch one task -------------------------------------------------------
def dispatch_one(config: Config, state: dict, task: Task, agent: Agent, act: bool,
                 log: Callable[[str], None]) -> str:
    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    if is_qa_task(task, config.labels):
        log(f"[qa] #{task.number} '{task.title}' (run {run_id})")
        if not act:
            log("  [no-act] would: QA the PR branch, comment PASS/FAIL, close or Needs Human")
            return "skipped"
        return run_qa(config, state, task, agent, run_id, log)
    if is_rework_task(task, config.labels):
        log(f"[rework] #{task.number} '{task.title}' (run {run_id})")
        if not act:
            log("  [no-act] would: revise the PR branch in place, push, re-screenshot, close")
            return "skipped"
        return run_rework(config, state, task, agent, run_id, log)
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
            try:
                create_qa_task(config, state, task, parsed, pr, log)
            except Exception as exc:
                log(f"  [qa] could not create QA task: {exc}")
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
    if act:
        reconciled = reconcile_closed(config, state, tasks, log)
    else:
        reconciled = len(closed_to_reconcile(tasks, config.status_values.get("done", "Done")))
    in_progress = count_in_progress(tasks, config.status_values)
    selected = select_ready(tasks, in_progress, config.max_concurrency,
                            config.status_values, config.labels)
    human = [t for t in tasks if config.labels["human"] in t.labels
             and t.status == config.status_values["ready"]]
    log(f"[poll] {len(tasks)} items | {in_progress} in-progress | "
        f"{len(selected)} selected | {len(human)} human-ready | {reconciled} closed→Done")
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

    labels = {"agent": "agent:claude", "human": "human", "deliverable": "deliverable",
              "qa": "qa", "ui": "ui", "rework": "rework"}
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
    # QA tasks are picked before implementation tasks, even with higher numbers
    qa_pri = [mk(1, "Ready", ["agent:claude"]), mk(99, "Ready", ["agent:claude", "qa"])]
    check("qa prioritized over impl",
          [t.number for t in select_ready(qa_pri, 0, 1, sv, labels)], [99])
    check("qa-first ordering full",
          [t.number for t in select_ready(qa_pri, 0, 5, sv, labels)], [99, 1])

    # reconcile: closed issues not yet Done
    rec_tasks = [
        Task("a", 10, "t", "", "", "CLOSED", "In review", [], []),   # stuck -> reconcile
        Task("b", 11, "t", "", "", "CLOSED", "Done", [], []),        # already Done -> skip
        Task("c", 12, "t", "", "", "OPEN", "In review", [], []),     # open -> skip
        Task("d", 13, "t", "", "", "CLOSED", "", [], []),            # no status -> skip
    ]
    check("closed_to_reconcile", [t.number for t in closed_to_reconcile(rec_tasks, "Done")], [10])
    md_deliv = build_task_md(tasks[4], parse_issue_body(""), labels)   # deliverable-labelled
    md_plain = build_task_md(tasks[0], parse_issue_body(""), labels)   # not labelled
    check("manifest note present (deliverable)", "deliverables/manifest.md" in md_deliv, True)
    check("manifest note present (plain)", "deliverables/manifest.md" in md_plain, True)
    check("required wording for deliverable", "required" in md_deliv, True)
    check("no required wording for plain", "required" in md_plain, False)

    # UI / screenshot logic
    md_ui = build_task_md(mk(7, "Ready", ["agent:claude", "ui"]), parse_issue_body(""), labels)
    check("ui task asks for screenshots", "tools/shoot.sh" in md_ui and "screenshots/7/" in md_ui, True)
    check("plain task no screenshot ask", "tools/shoot.sh" in md_plain, False)
    ub = qa_issue_body(mk(7, "Ready", ["agent:claude", "ui"]), parse_issue_body(""),
                       "https://github.com/o/r/pull/20", 20, is_ui=True)
    check("qa meta carries ui flag", "ui=1" in ub, True)
    qmd_ui = build_qa_md(mk(7, "Ready", ["agent:claude", "qa"]),
                         {"pr": "20", "impl": "7", "branch": "task/7-x", "ui": "1"},
                         "- [ ] x", "", "o/r")
    check("qa md adds visual compare for ui", "tools/shoot.sh" in qmd_ui, True)

    # QA (verifier) logic
    check("is_qa_task true", is_qa_task(mk(9, "Ready", ["agent:claude", "qa"]), labels), True)
    check("is_qa_task false", is_qa_task(mk(9, "Ready", ["agent:claude"]), labels), False)
    check("pr_number_from_url", pr_number_from_url("https://github.com/o/r/pull/13"), 13)
    check("pr_number_from_url none", pr_number_from_url("nope"), None)
    qmeta = parse_qa_meta("text <!-- qa-meta pr=13 branch=task/8-x impl=8 --> more")
    check("parse_qa_meta", (qmeta.get("pr"), qmeta.get("branch"), qmeta.get("impl")),
          ("13", "task/8-x", "8"))
    check("strip_title_prefix", strip_title_prefix("[Task] Do a thing"), "Do a thing")
    qbody = qa_issue_body(mk(8, "Ready", ["agent:claude"]),
                          parse_issue_body("### Acceptance Criteria\n\n- [ ] x\n"),
                          "https://github.com/o/r/pull/13", 13)
    check("qa body has meta", "qa-meta pr=13" in qbody and "impl=8" in qbody, True)
    qmd = build_qa_md(mk(99, "Ready", ["agent:claude", "qa"]),
                      {"pr": "13", "impl": "8", "branch": "task/8-x"},
                      "- [ ] x", "bash tools/verify.sh", "o/r")
    check("qa md uses gh pr comment", "gh pr comment 13" in qmd, True)
    check("qa md frames verifier role", "verifier" in qmd, True)

    # Rework (send-back) logic
    check("is_rework_task true", is_rework_task(mk(9, "Ready", ["agent:claude", "rework"]), labels), True)
    check("is_rework_task false", is_rework_task(mk(9, "Ready", ["agent:claude"]), labels), False)
    rmd = build_rework_md(mk(9, "Ready", ["rework"]),
                          {"pr": "27", "branch": "task/21-x", "impl": "21"},
                          "fix the nine-patch margins", "o/r")
    check("rework md targets the branch", "task/21-x" in rmd, True)
    check("rework md re-screenshots impl", "screenshots/21/" in rmd, True)
    check("rework md says no new PR", "Do NOT open a PR" in rmd, True)

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
    p.add_argument("--rework", type=int, metavar="PR", default=None,
                   help="File a rework task to revise the given open PR (use with --message)")
    p.add_argument("--message", default=None, help="The requested-changes note for --rework")
    p.add_argument("--task", type=int, metavar="ISSUE", default=None,
                   help="Dispatch one specific board issue now (bypasses selection order)")
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

    if args.rework is not None:
        fetch_board(config, state); save_state(DEFAULT_STATE, state)  # resolve ids
        url = create_rework_task(config, state, args.rework,
                                 args.message or "See the PR review for requested changes.", log)
        return 0 if url else 1

    if args.task is not None:
        tasks = fetch_board(config, state); save_state(DEFAULT_STATE, state)
        target = next((t for t in tasks if t.number == args.task), None)
        if target is None:
            log(f"[dispatch] issue #{args.task} not found on the board"); return 1
        dispatch_one(config, state, target, agent, act=not args.no_act, log=log)
        return 0

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
