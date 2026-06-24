"""Banner / gacha pull screen skeleton.

Renders a hardcoded `PullResult` (and the `BannerState` pity/shard info it
came from) using the asset map in docs/asset_map_iteration_1.md section 1.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game import GachaSystem, Rarity, sample_characters  # noqa: E402

from ui.assets import BODY_FONT, CAPS_FONT, load_font, scaled  # noqa: E402

RARITY_RIBBONS = {
    Rarity.COMMON: "tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Banners from the store page/Ribbons/Ribbon_Black.png",
    Rarity.RARE: "tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Banners from the store page/Ribbons/Ribbon_Blue.png",
    Rarity.EPIC: "tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Banners from the store page/Ribbons/Ribbon_Purple.png",
    Rarity.LEGENDARY: "tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Banners from the store page/Ribbons/Ribbon_Yellow.png",
}

DIALOG_BOX = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/dialog_box_with_shadow.standard/dialog_box_with_shadow_0.png"
TOP_BANNER = "tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Banners from the store page/Banner/Banner.png"
PULL_BUTTON = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/button_round_big.standard/button_round_big_0.png"
PULL_BUTTON_PRESSED = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/button_round_big_pressed.standard/button_round_big_pressed_0.png"
PULL_X10_BUTTON = "tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Elements/Buttons/BigBlueButton_Regular.png"
RESULT_FRAME = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/inventory_slot.standard/inventory_slot_0.png"
AVATAR = "tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Elements/Human Avatars/Avatars_01.png"
SHARD_ICON = "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_gold_nugget_29.png"
PITY_BAR_TRACK = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/progress_bar.standard/progress_bar_0.png"
PITY_BAR_FILL = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/progress_bar.standard/progress_bar_1.png"
PITY_FLASH_ICON = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_controls/ui_pack_icons.standard/ui_pack_icon_star_33.png"
RESONANCE_EMPTY = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/heart_piece.standard/heart_piece_empty_0.png"
RESONANCE_FULL = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/heart_piece.standard/heart_piece_full_5.png"

RARITY_COLORS = {
    Rarity.COMMON: (200, 200, 200),
    Rarity.RARE: (90, 150, 255),
    Rarity.EPIC: (190, 110, 255),
    Rarity.LEGENDARY: (255, 210, 70),
}


class BannerScreen:
    """Static demo of the gacha pull screen, driven by real game.py data."""

    name = "Banner"

    def __init__(self) -> None:
        self.characters = sample_characters()
        self.gacha = GachaSystem(self.characters, seed=7)
        # Pull a handful of times so pity/shards have realistic state, then
        # keep the final pull as the "just pulled" result shown on screen.
        character_id = "star_witch"
        pulls = self.gacha.pull_batch(character_id, count=12, featured=True)
        self.latest_pull = pulls[-1]
        self.character = self.characters[character_id]
        self.banner_state = self.gacha.banners[character_id]
        self.resonance = self.gacha.resonance_preview(character_id)
        self.hard_pity_target = self.gacha.pity_tuning(featured=True)["hard_pity_target"]

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((24, 20, 32))
        width, height = surface.get_size()

        surface.blit(scaled(DIALOG_BOX, (width - 80, height - 80)), (40, 40))
        surface.blit(scaled(TOP_BANNER, (420, 90)), (width // 2 - 210, 56))

        title_font = load_font(CAPS_FONT, 30)
        body_font = load_font(BODY_FONT, 20)
        small_font = load_font(BODY_FONT, 16)

        title_surface = title_font.render(self.character.name.upper(), True, (255, 255, 255))
        surface.blit(title_surface, (width // 2 - title_surface.get_width() // 2, 80))

        # Result card.
        card_x, card_y = width // 2 - 110, 170
        ribbon_path = RARITY_RIBBONS[self.latest_pull.rarity]
        surface.blit(scaled(ribbon_path, (220, 70)), (card_x, card_y - 10))
        surface.blit(scaled(RESULT_FRAME, (220, 220)), (card_x, card_y + 40))
        surface.blit(scaled(AVATAR, (160, 160)), (card_x + 30, card_y + 70))

        rarity_color = RARITY_COLORS[self.latest_pull.rarity]
        rarity_surface = title_font.render(self.latest_pull.rarity.value.upper(), True, rarity_color)
        surface.blit(rarity_surface, (card_x + 110 - rarity_surface.get_width() // 2, card_y + 250))

        if self.latest_pull.pity_reset:
            surface.blit(scaled(PITY_FLASH_ICON, (36, 36)), (card_x + 180, card_y))
            flash_surface = small_font.render("PITY RESET!", True, (255, 220, 90))
            surface.blit(flash_surface, (card_x + 20, card_y + 290))

        # Shard counter.
        shard_y = card_y + 320
        surface.blit(scaled(SHARD_ICON, (28, 28)), (card_x + 10, shard_y))
        shard_surface = body_font.render(
            f"+{self.latest_pull.shards_gained} shards  (total {self.banner_state.shards})",
            True,
            (235, 235, 235),
        )
        surface.blit(shard_surface, (card_x + 46, shard_y + 4))

        # Pity progress bar.
        bar_x, bar_y, bar_w, bar_h = width // 2 + 160, 220, 260, 28
        surface.blit(scaled(PITY_BAR_TRACK, (bar_w, bar_h)), (bar_x, bar_y))
        progress = min(1.0, self.banner_state.pulls_since_legendary / self.hard_pity_target)
        fill_w = max(1, int(bar_w * progress))
        surface.blit(scaled(PITY_BAR_FILL, (fill_w, bar_h)), (bar_x, bar_y))
        pity_label = small_font.render(
            f"Pity {self.banner_state.pulls_since_legendary}/{self.hard_pity_target}",
            True,
            (235, 235, 235),
        )
        surface.blit(pity_label, (bar_x, bar_y - 22))

        # Resonance nodes.
        node_y = bar_y + 60
        node_label = small_font.render("Resonance", True, (235, 235, 235))
        surface.blit(node_label, (bar_x, node_y - 22))
        for index, node in enumerate(self.resonance):
            icon_path = RESONANCE_FULL if node["unlocked"] else RESONANCE_EMPTY
            surface.blit(scaled(icon_path, (36, 36)), (bar_x + index * 44, node_y))

        # Buttons.
        button_y = height - 140
        surface.blit(scaled(PULL_BUTTON, (140, 70)), (width // 2 - 260, button_y))
        pull_label = body_font.render("Pull x1", True, (20, 20, 20))
        surface.blit(pull_label, (width // 2 - 260 + 70 - pull_label.get_width() // 2, button_y + 25))

        surface.blit(scaled(PULL_X10_BUTTON, (160, 70)), (width // 2 + 100, button_y))
        pull10_label = body_font.render("Pull x10", True, (20, 20, 20))
        surface.blit(pull10_label, (width // 2 + 100 + 80 - pull10_label.get_width() // 2, button_y + 25))

        # Reference the pressed-state asset too, as a faded "last pressed" hint.
        pressed_preview = scaled(PULL_BUTTON_PRESSED, (60, 30))
        pressed_preview.set_alpha(120)
        surface.blit(pressed_preview, (width // 2 - 260, button_y + 80))
