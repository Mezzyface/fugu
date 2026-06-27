#!/usr/bin/env bash
#
# gif.sh — capture a Godot scene to an animated GIF so animations can be reviewed.
#
# Renders WINDOWED (Godot's --headless draws nothing), captures a short frame
# sequence, and assembles a looping GIF with tools/gif.py (stdlib only — no ffmpeg
# needed). For a meaningful result the scene must actually animate (e.g. an
# AnimatedSprite2D that is .play()-ing).
#
# Usage:
#   bash tools/gif.sh <res://scene.tscn> <out-path.gif> [frames] [fps]
# Example:
#   bash tools/gif.sh res://scenes/units_demo.tscn screenshots/23/units.gif 24 20
#
# Environment:
#   GODOT   override the Godot binary (else `godot` on PATH, then the bundled
#           Windows 4.7 build used from WSL).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

SCENE="${1:?usage: gif.sh <res://scene.tscn> <out.gif> [frames] [fps]}"
OUT="${2:?usage: gif.sh <res://scene.tscn> <out.gif> [frames] [fps]}"
FRAMES="${3:-24}"
FPS="${4:-20}"
GAME_DIR="$PWD/game"
[[ -d "$GAME_DIR" ]] || { echo "gif.sh: game/ not found at $GAME_DIR" >&2; exit 2; }

# --- locate Godot (same logic as shoot.sh) ---------------------------------
WIN_GODOT="/mnt/c/Project-Fugu/Godot_v4.7-stable_win64.exe/Godot_v4.7-stable_win64.exe"
GODOT_BIN="${GODOT:-}"
if [[ -z "$GODOT_BIN" ]]; then
	if command -v godot >/dev/null 2>&1; then GODOT_BIN="$(command -v godot)"
	elif [[ -x "$WIN_GODOT" ]]; then GODOT_BIN="$WIN_GODOT"; fi
fi
if [[ -z "$GODOT_BIN" || ! -x "$GODOT_BIN" ]]; then
	echo "gif.sh: Godot binary not found. Set GODOT=/path/to/godot." >&2
	exit 2
fi

PROJECT_PATH="$GAME_DIR"
if [[ "$GODOT_BIN" == *.exe ]] && command -v wslpath >/dev/null 2>&1; then
	PROJECT_PATH="$(wslpath -w "$GAME_DIR")"
fi

CAP_DIR="$GAME_DIR/.__cap"
rm -rf "$CAP_DIR"

# NOT --headless: the GPU must render real frames.
"$GODOT_BIN" --path "$PROJECT_PATH" -s res://tools/record.gd -- \
	"$SCENE" "res://.__cap" "$FRAMES" 2 480
RC=$?
if [[ $RC -ne 0 || ! -f "$CAP_DIR/meta.txt" ]]; then
	echo "gif.sh: frame capture failed (rc=$RC) for $SCENE" >&2
	rm -rf "$CAP_DIR"
	exit 1
fi

DELAY=$(( 100 / FPS )); (( DELAY < 2 )) && DELAY=2
mkdir -p "$(dirname "$OUT")"
if ! python3 tools/gif.py "$CAP_DIR" "$OUT" "$DELAY"; then
	echo "gif.sh: GIF assembly failed" >&2
	rm -rf "$CAP_DIR"
	exit 1
fi
rm -rf "$CAP_DIR"
echo "gif.sh: wrote $OUT"
