#!/usr/bin/env bash
# Seed the project board with the bootstrap tasks. Idempotency is NOT guaranteed —
# run once. Requires `gh` with project WRITE scope (gh auth refresh -s project,read:org).
set -euo pipefail
cd "$(dirname "$0")/.."

REPO="Mezzyface/fugu"
OWNER="Mezzyface"
PROJECT=1

# Ensure the id cache exists (read-only board poll populates tools/dispatch_state.json).
[ -f tools/dispatch_state.json ] || python3 tools/dispatch.py --once --no-act >/dev/null

read_state() { python3 -c "import json;print(json.load(open('tools/dispatch_state.json'))$1)"; }
PROJECT_ID=$(read_state "['project_id']")
FIELD_ID=$(read_state "['status_field_id']")
READY_OPT=$(read_state "['status_options']['Ready']")

create_task() {            # title  body  label...
  local title="$1"; local body="$2"; shift 2
  local label_args=(); for l in "$@"; do label_args+=(--label "$l"); done
  echo "Creating: $title"
  local url; url=$(gh issue create --repo "$REPO" --title "$title" --body "$body" "${label_args[@]}")
  echo "  $url"
  local item_id
  item_id=$(gh project item-add "$PROJECT" --owner "$OWNER" --url "$url" --format json \
            | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
  gh api graphql -f query='mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,value:{singleSelectOptionId:$o}}){projectV2Item{id}}}' \
    -f p="$PROJECT_ID" -f i="$item_id" -f f="$FIELD_ID" -f o="$READY_OPT" >/dev/null
  echo "  -> added to board, Status=Ready"
}

create_task "[Task] Scaffold Godot 4.7 project under game/" "$(cat <<'EOF'
### Assignee

agent (claude)

### Deliverable type

code

### Context / Goal

Create the Godot 4.7 project that all gameplay work will build on. Pivoting from the
Python/Phaser prototypes; this is the new home.

### Resources

- CLAUDE.md (Godot conventions, binary path, verification)
- .claude/skills/godot-project-setup, godot-scenes-and-nodes, godot-gut-testing
- docs/gdd_iteration_1.md (design intent)

### Acceptance Criteria

- [ ] game/project.godot exists, config version targets 4.7
- [ ] A main scene (game/main.tscn) is set as run/main_scene and opens a placeholder screen
- [ ] addons/gut/ vendored (Godot 4.x branch) and a sample test in game/test/test_smoke.gd passes
- [ ] Project boots headless with no errors
- [ ] .godot/ and import caches are gitignored

### Outputs / Deliverables

The game/ Godot project (project.godot, main.tscn, addons/gut, test/test_smoke.gd).

### Verification commands

GODOT="/mnt/c/Project-Fugu/Godot_v4.7-stable_win64.exe/Godot_v4.7-stable_win64.exe"
"$GODOT" --path "$(wslpath -w game)" --headless --quit
"$GODOT" --path "$(wslpath -w game)" --headless -s addons/gut/gut_cmdln.gd -gdir=res://test -gexit
EOF
)" "agent:claude"

create_task "[Task] Add verification wrapper tools/verify.sh (gdlint + GUT)" "$(cat <<'EOF'
### Assignee

agent (claude)

### Deliverable type

code

### Context / Goal

Give every Godot task a single verification command. Wrap gdformat-check/gdlint and the
GUT headless run so the dispatcher and reviewers run one script.

### Resources

- .claude/skills/godot-gdscript-style, godot-gut-testing
- CLAUDE.md

### Acceptance Criteria

- [ ] tools/verify.sh runs gdlint over game/ and the GUT suite headless
- [ ] Exits non-zero if lint or tests fail
- [ ] Documented in CLAUDE.md as the standard verification command
- [ ] Degrades gracefully with a clear message if gdtoolkit isn't installed

### Outputs / Deliverables

tools/verify.sh and a CLAUDE.md note.

### Verification commands

bash tools/verify.sh
EOF
)" "agent:claude"

create_task "[Task] Import first UI/asset subset into game/assets" "$(cat <<'EOF'
### Assignee

agent (claude)

### Deliverable type

non-code artifact

### Context / Goal

Bring a small, license-clean asset subset into the Godot project so screens have real art.
Do not commit the raw zips (gitignored); import only the needed files.

### Resources

- Game-Assets/ (Kenney All-in-1, Tiny Swords, Isle of Lore) — gitignored source zips
- .claude/skills/godot-ui-control (NinePatchRect usage)
- docs/asset_map_iteration_1.md

### Acceptance Criteria

- [ ] A focused UI subset (panels, buttons, a font) imported under game/assets/ui/
- [ ] At least one NinePatchRect panel renders correctly (no stretched blobs)
- [ ] deliverables/manifest.md updated with what was imported + source pack + license note

### Outputs / Deliverables

game/assets/ui/* and an updated deliverables/manifest.md (this task is labelled deliverable).

### Verification commands

GODOT="/mnt/c/Project-Fugu/Godot_v4.7-stable_win64.exe/Godot_v4.7-stable_win64.exe"
"$GODOT" --path "$(wslpath -w game)" --headless --quit
EOF
)" "agent:claude" "deliverable"

create_task "[Human] Decide primary art direction / asset pack" "$(cat <<'EOF'
### Assignee

human

### Deliverable type

non-code artifact

### Context / Goal

Pick the primary visual direction and lead asset pack(s) so agents stop guessing. This is a
taste/brand call better made by a human.

### Acceptance Criteria

- [ ] Primary pack(s) chosen and noted in docs/ or this issue
- [ ] deliverables/manifest.md updated with the decision + link

### Outputs / Deliverables

A short decision note + manifest entry.
EOF
)" "human" "deliverable"

echo
echo "Seed complete. Review the board: https://github.com/users/$OWNER/projects/$PROJECT"
