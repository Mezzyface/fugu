"""Shared game session for the UI.

Holds one `GachaSystem`, one `TrainingSimulator`, and one `EchoPool`
instance so all three screens act against the same live state instead of
each screen building its own isolated demo data (the old skeleton
behavior). Screens read/write through this object so player actions (a
pull, a training run, banking/favoriting/deleting an echo) are visible
across screens.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game import EchoPool, GachaSystem, TrainingSimulator, sample_characters  # noqa: E402


class GameSession:
    """Owns the shared simulation state for the whole app."""

    def __init__(self, seed: int = 1) -> None:
        self.characters = sample_characters()
        self.gacha = GachaSystem(self.characters, seed=seed)
        self.simulator = TrainingSimulator(seed=seed + 1)
        self.echo_pool = EchoPool(capacity=20, max_favorites=5)
