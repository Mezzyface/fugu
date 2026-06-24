#!/usr/bin/env python3
"""Entry point for the pygame UI skeleton.

Usage:
    python3 run_ui.py                 # launch the interactive app
    python3 run_ui.py --smoke-test     # run ~30 frames headless, then exit 0

The --smoke-test flag is intended for use with SDL_VIDEODRIVER=dummy so this
can be checked in CI / headless environments without a real display.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ui.app import App  # noqa: E402


def main() -> int:
    smoke_test = "--smoke-test" in sys.argv
    app = App()
    app.run(max_frames=30 if smoke_test else None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
