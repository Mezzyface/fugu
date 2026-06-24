"""Asset loading helpers for the pygame UI skeleton.

Centralizes path resolution (relative to ``prototype/assets/``) and caches
loaded images/fonts so screens can just ask for a logical asset path without
re-reading from disk every frame.

All paths used by the screen modules come from
``docs/asset_map_iteration_1.md`` -- see that file for the asset-to-element
mapping this UI is built against.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import pygame

ASSETS_ROOT = Path(__file__).resolve().parent.parent / "assets"

_image_cache: Dict[str, pygame.Surface] = {}
_font_cache: Dict[Tuple[str, int], pygame.font.Font] = {}

CAPS_FONT = "honeyblot_caps/honeyblot_caps.ttf"
BODY_FONT = "HoneyPigeon/HoneyPigeon.ttf"


def load_image(relative_path: str) -> pygame.Surface:
    """Load (and cache) an image given a path relative to ``assets/``.

    Returns a small magenta placeholder surface instead of raising if the
    file is missing, so a single bad path can't crash the whole skeleton.
    """
    cached = _image_cache.get(relative_path)
    if cached is not None:
        return cached
    full_path = ASSETS_ROOT / relative_path
    try:
        surface = pygame.image.load(str(full_path)).convert_alpha()
    except (pygame.error, FileNotFoundError):
        surface = pygame.Surface((32, 32))
        surface.fill((255, 0, 255))
    _image_cache[relative_path] = surface
    return surface


def load_font(relative_path: str, size: int) -> pygame.font.Font:
    """Load (and cache) a font given a path relative to ``assets/``."""
    key = (relative_path, size)
    cached = _font_cache.get(key)
    if cached is not None:
        return cached
    full_path = ASSETS_ROOT / relative_path
    try:
        font = pygame.font.Font(str(full_path), size)
    except (pygame.error, FileNotFoundError):
        font = pygame.font.Font(None, size)
    _font_cache[key] = font
    return font


def scaled(relative_path: str, size: Tuple[int, int]) -> pygame.Surface:
    """Load an image and scale it to ``size`` (width, height)."""
    image = load_image(relative_path)
    return pygame.transform.smoothscale(image, size)
