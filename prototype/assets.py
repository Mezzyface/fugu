from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile


@dataclass(frozen=True)
class AssetPack:
    filename: str
    total_files: int
    image_files: int
    audio_files: int
    category: str
    recommended_use: str


def classify_asset_pack(filename: str) -> tuple[str, str]:
    name = filename.lower()
    if "monster" in name or "enemy" in name:
        return "creatures", "enemy rosters, boss families, summon silhouettes"
    if "tiny swords" in name:
        return "characters", "prototype overworld units, buildings, encounter maps"
    if "hex" in name or "tiles" in name:
        return "environment", "dungeon biomes, route maps, tactical boards"
    if "item" in name or "icons" in name:
        return "items", "relics, skills, currencies, inheritance materials"
    if "ui" in name:
        return "interface", "menus, gacha panels, training result screens"
    if "figure" in name:
        return "tokens", "party markers, enemies, map encounter icons"
    if "kenney" in name:
        return "general", "audio, placeholders, UI, particles, cross-genre prototypes"
    if "graybox" in name:
        return "graybox", "fast layout tests and combat readability prototypes"
    if "honey" in name:
        return "fonts", "logo, rarity labels, banner typography"
    return "misc", "review manually"


def inspect_asset_pack(path: Path) -> AssetPack:
    with ZipFile(path) as archive:
        names = archive.namelist()
    image_files = sum(name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) for name in names)
    audio_files = sum(name.lower().endswith((".wav", ".ogg", ".mp3")) for name in names)
    category, recommended_use = classify_asset_pack(path.name)
    return AssetPack(path.name, len(names), image_files, audio_files, category, recommended_use)


def catalog_asset_directory(directory: Path) -> list[AssetPack]:
    return [inspect_asset_pack(path) for path in sorted(directory.glob("*.zip"))]
