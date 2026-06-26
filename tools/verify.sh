#!/usr/bin/env bash
#
# verify.sh — the single verification gate for Godot tasks in this repo.
#
# Runs, in order:
#   1. gdformat --check + gdlint over game/   (GDScript style/lint gate)
#   2. a headless Godot import pass            (so class_name's resolve)
#   3. the GUT test suite headless            (unit tests)
#
# Exits non-zero if the lint step or the test step fails. The GUT runner
# exits 0 even when tests fail (a false pass), so we additionally require the
# "All tests passed!" banner in its output.
#
# Degrades gracefully: if gdtoolkit (gdformat/gdlint) is not installed it
# prints a clear message and SKIPS the lint step rather than hard-failing, so
# the test gate can still run. Pass --strict-lint to treat a missing
# gdtoolkit as a failure instead.
#
# Usage:
#   bash tools/verify.sh [--strict-lint]
#
# Environment:
#   GODOT   override the Godot binary (otherwise: `godot` on PATH, then the
#           bundled Windows 4.7 build used from WSL).

set -uo pipefail

# --- locate repo + game dir -------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
GAME_DIR="${REPO_ROOT}/game"

STRICT_LINT=0
for arg in "$@"; do
	case "$arg" in
		--strict-lint) STRICT_LINT=1 ;;
		*) echo "verify.sh: unknown argument: $arg" >&2; exit 2 ;;
	esac
done

if [[ ! -d "$GAME_DIR" ]]; then
	echo "verify.sh: game/ directory not found at $GAME_DIR" >&2
	exit 2
fi

bold() { printf '\033[1m%s\033[0m\n' "$1"; }

LINT_STATUS="skipped"
TEST_STATUS="failed"

# --- 1. lint (gdformat --check + gdlint) ------------------------------------
bold "==> Lint (gdformat --check + gdlint)"
if command -v gdformat >/dev/null 2>&1 && command -v gdlint >/dev/null 2>&1; then
	lint_ok=1
	if ! gdformat --check "$GAME_DIR"; then
		echo "verify.sh: gdformat found unformatted files (run: gdformat $GAME_DIR)" >&2
		lint_ok=0
	fi
	if ! gdlint "$GAME_DIR"; then
		echo "verify.sh: gdlint reported problems" >&2
		lint_ok=0
	fi
	if [[ $lint_ok -eq 1 ]]; then
		LINT_STATUS="passed"
	else
		LINT_STATUS="failed"
	fi
else
	echo "verify.sh: gdtoolkit not found (gdformat/gdlint missing)." >&2
	echo "           Install with: pipx install \"gdtoolkit==4.*\"  (or pip install)" >&2
	if [[ $STRICT_LINT -eq 1 ]]; then
		echo "           --strict-lint set: treating missing gdtoolkit as a failure." >&2
		LINT_STATUS="failed"
	else
		echo "           Skipping lint step; run again after installing gdtoolkit." >&2
		LINT_STATUS="skipped"
	fi
fi
echo

# --- locate the Godot binary ------------------------------------------------
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
	echo "verify.sh: Godot binary not found." >&2
	echo "           Set GODOT=/path/to/godot, or put 'godot' on PATH." >&2
	exit 2
fi

# A Windows Godot build run from WSL expects a Windows-style project path.
PROJECT_PATH="$GAME_DIR"
if [[ "$GODOT_BIN" == *.exe ]] && command -v wslpath >/dev/null 2>&1; then
	PROJECT_PATH="$(wslpath -w "$GAME_DIR")"
fi

# --- 2. import pass (so class_name's resolve before GUT) --------------------
bold "==> Godot import pass"
if ! "$GODOT_BIN" --headless --path "$PROJECT_PATH" --import; then
	echo "verify.sh: Godot import pass failed" >&2
	exit 1
fi
echo

# --- 3. GUT test suite ------------------------------------------------------
bold "==> GUT test suite"
GUT_OUT="$("$GODOT_BIN" --headless --path "$PROJECT_PATH" \
	-s addons/gut/gut_cmdln.gd -gdir=res://test -gexit 2>&1)"
echo "$GUT_OUT"
echo
# GUT exits 0 even on failure, so require the success banner explicitly.
if grep -q "All tests passed!" <<<"$GUT_OUT"; then
	TEST_STATUS="passed"
else
	TEST_STATUS="failed"
fi

# --- summary ----------------------------------------------------------------
bold "==> Summary"
echo "  lint:  $LINT_STATUS"
echo "  tests: $TEST_STATUS"

if [[ "$LINT_STATUS" == "failed" || "$TEST_STATUS" != "passed" ]]; then
	echo "verify.sh: FAILED"
	exit 1
fi
echo "verify.sh: OK"
exit 0
