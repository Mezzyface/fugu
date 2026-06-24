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


_nine_slice_cache: Dict[Tuple[str, Tuple[int, int], int], pygame.Surface] = {}


def nine_slice(relative_path: str, size: Tuple[int, int], border: int) -> pygame.Surface:
    """Scale a bordered-frame asset to ``size`` using 9-slice scaling.

    Splits the source image into a 3x3 grid using a fixed ``border`` margin
    on every side: the four corner tiles are blitted unscaled, the four edge
    tiles are stretched along a single axis, and the center tile is
    stretched in both axes to fill the remainder. This keeps small panel /
    box / dialog "frame" art crisp at any target size instead of smearing
    the whole border into a blurry blob the way a uniform
    ``smoothscale()`` does on a large up-scale.

    ``border`` is clamped so it never exceeds half of the source image's
    smaller dimension, and the target ``size`` is clamped to be at least
    ``2 * border`` in each dimension so corners never overlap or invert.
    """
    width, height = size
    width = max(1, int(width))
    height = max(1, int(height))

    cache_key = (relative_path, (width, height), border)
    cached = _nine_slice_cache.get(cache_key)
    if cached is not None:
        return cached

    image = load_image(relative_path)
    src_w, src_h = image.get_size()
    b = max(0, min(border, src_w // 2, src_h // 2))

    target_w = max(width, 2 * b)
    target_h = max(height, 2 * b)

    result = pygame.Surface((target_w, target_h), pygame.SRCALPHA)

    if b == 0:
        # No border to preserve; fall back to a plain stretch.
        result.blit(pygame.transform.smoothscale(image, (target_w, target_h)), (0, 0))
        _nine_slice_cache[cache_key] = result
        return result

    mid_src_w = src_w - 2 * b
    mid_src_h = src_h - 2 * b
    mid_dst_w = target_w - 2 * b
    mid_dst_h = target_h - 2 * b

    def region(x: int, y: int, w: int, h: int) -> pygame.Surface:
        sub = pygame.Surface((w, h), pygame.SRCALPHA)
        sub.blit(image, (0, 0), pygame.Rect(x, y, w, h))
        return sub

    # Corners (unscaled).
    top_left = region(0, 0, b, b)
    top_right = region(src_w - b, 0, b, b)
    bottom_left = region(0, src_h - b, b, b)
    bottom_right = region(src_w - b, src_h - b, b, b)

    result.blit(top_left, (0, 0))
    result.blit(top_right, (target_w - b, 0))
    result.blit(bottom_left, (0, target_h - b))
    result.blit(bottom_right, (target_w - b, target_h - b))

    # Edges (stretched along one axis only).
    if mid_dst_w > 0 and mid_src_w > 0:
        top_edge = region(b, 0, mid_src_w, b)
        top_edge = pygame.transform.smoothscale(top_edge, (mid_dst_w, b))
        result.blit(top_edge, (b, 0))

        bottom_edge = region(b, src_h - b, mid_src_w, b)
        bottom_edge = pygame.transform.smoothscale(bottom_edge, (mid_dst_w, b))
        result.blit(bottom_edge, (b, target_h - b))

    if mid_dst_h > 0 and mid_src_h > 0:
        left_edge = region(0, b, b, mid_src_h)
        left_edge = pygame.transform.smoothscale(left_edge, (b, mid_dst_h))
        result.blit(left_edge, (0, b))

        right_edge = region(src_w - b, b, b, mid_src_h)
        right_edge = pygame.transform.smoothscale(right_edge, (b, mid_dst_h))
        result.blit(right_edge, (target_w - b, b))

    # Center (stretched in both axes).
    if mid_dst_w > 0 and mid_dst_h > 0 and mid_src_w > 0 and mid_src_h > 0:
        center = region(b, b, mid_src_w, mid_src_h)
        center = pygame.transform.smoothscale(center, (mid_dst_w, mid_dst_h))
        result.blit(center, (b, b))

    _nine_slice_cache[cache_key] = result
    return result
