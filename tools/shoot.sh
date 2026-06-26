#!/usr/bin/env bash
#
# shoot.sh — capture a Godot scene to a PNG so visual changes can be reviewed.
#
# Renders WINDOWED (Godot's --headless mode uses a dummy renderer that draws
# nothing). Saves into the repo so the PR can embed it.
#
# Usage:
#   bash tools/shoot.sh <res://scene.tscn> <out-path.png> [frames]
# Example:
#   bash tools/shoot.sh res://main.tscn screenshots/6/main.png
#
# Environment:
#   GODOT   override the Godot binary (else `godot` on PATH, then the bundled
#           Windows 4.7 build used from WSL).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

SCENE="${1:?usage: shoot.sh <res://scene.tscn> <out.png> [frames]}"
OUT="${2:?usage: shoot.sh <res://scene.tscn> <out.png> [frames]}"
FRAMES="${3:-4}"
GAME_DIR="$PWD/game"

[[ -d "$GAME_DIR" ]] || { echo "shoot.sh: game/ not found at $GAME_DIR" >&2; exit 2; }

# --- locate Godot (same logic as verify.sh) --------------------------------
WIN_GODOT="/mnt/c/Project-Fugu/Godot_v4.7-stable_win64.exe/Godot_v4.7-stable_win64.exe"
GODOT_BIN="${GODOT:-}"
if [[ -z "$GODOT_BIN" ]]; then
	if command -v godot >/dev/null 2>&1; then
		GODOT_BIN="$(command -v godot)"
	elif [[ -x "$WIN_GODOT" ]]; then
		GODOT_BIN="$WIN_GODOT"
	fi
fi
if [[ -z "$GODOT_BIN" || ! -x "$GODOT_BIN" ]]; then
	echo "shoot.sh: Godot binary not found. Set GODOT=/path/to/godot." >&2
	exit 2
fi

# A Windows Godot build run from WSL needs a Windows-style project path.
PROJECT_PATH="$GAME_DIR"
if [[ "$GODOT_BIN" == *.exe ]] && command -v wslpath >/dev/null 2>&1; then
	PROJECT_PATH="$(wslpath -w "$GAME_DIR")"
fi

TMP_RES="res://.__shot.png"
TMP_FILE="$GAME_DIR/.__shot.png"

# NOTE: intentionally NOT --headless, so the GPU renders a real frame.
"$GODOT_BIN" --path "$PROJECT_PATH" -s res://tools/screenshot.gd -- "$SCENE" "$TMP_RES" "$FRAMES"
RC=$?

if [[ $RC -ne 0 || ! -f "$TMP_FILE" ]]; then
	echo "shoot.sh: capture failed (rc=$RC) for $SCENE" >&2
	rm -f "$TMP_FILE" "$TMP_FILE.import"
	exit 1
fi

mkdir -p "$(dirname "$OUT")"
mv -f "$TMP_FILE" "$OUT"
rm -f "$TMP_FILE.import"
echo "shoot.sh: wrote $OUT"
