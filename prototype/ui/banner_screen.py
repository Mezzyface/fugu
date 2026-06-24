"""Banner / gacha pull screen.

Renders live `PullResult`/`BannerState` data from the shared `GameSession`
and exposes a clickable "Pull x1" button (asset per
docs/asset_map_iteration_1.md section 1) that performs a real
`GachaSystem.pull` against the session and updates the screen.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game import Rarity  # noqa: E402

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
    """Interactive gacha pull screen, driven by the shared `GameSession`."""

    name = "Banner"

    #: Fixed default banner character for this phase -- a banner-selection
    #: UI is out of scope here per the task brief.
    character_id = "star_witch"
    featured = True

    def __init__(self, session) -> None:
        self.session = session
        self.gacha = session.gacha
        self.character = session.characters[self.character_id]
        self.banner_state = self.gacha.banners[self.character_id]
        self.hard_pity_target = self.gacha.pity_tuning(featured=self.featured)["hard_pity_target"]
        # No pull has happened yet this session -- show a neutral
        # "not pulled yet" placeholder until the player clicks Pull x1.
        self.latest_pull = None
        self.pull_button_rect = pygame.Rect(0, 0, 0, 0)

    @property
    def resonance(self):
        return self.gacha.resonance_preview(self.character_id)

    def do_pull(self) -> None:
        self.latest_pull = self.gacha.pull(self.character_id, featured=self.featured)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.pull_button_rect.collidepoint(event.pos):
                self.do_pull()

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
        if self.latest_pull is None:
            surface.blit(scaled(RESULT_FRAME, (220, 220)), (card_x, card_y + 40))
            surface.blit(scaled(AVATAR, (160, 160)), (card_x + 30, card_y + 70))
            hint_surface = body_font.render("Pull to reveal a result", True, (200, 200, 200))
            surface.blit(hint_surface, (card_x + 110 - hint_surface.get_width() // 2, card_y + 260))
        else:
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
        shards_gained = self.latest_pull.shards_gained if self.latest_pull else 0
        shard_surface = body_font.render(
            f"+{shards_gained} shards  (total {self.banner_state.shards})",
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
        self.pull_button_rect = pygame.Rect(width // 2 - 260, button_y, 140, 70)
        surface.blit(scaled(PULL_BUTTON, (140, 70)), self.pull_button_rect.topleft)
        pull_label = body_font.render("Pull x1", True, (20, 20, 20))
        surface.blit(pull_label, (width // 2 - 260 + 70 - pull_label.get_width() // 2, button_y + 25))

        surface.blit(scaled(PULL_X10_BUTTON, (160, 70)), (width // 2 + 100, button_y))
        pull10_label = body_font.render("Pull x10", True, (20, 20, 20))
        surface.blit(pull10_label, (width // 2 + 100 + 80 - pull10_label.get_width() // 2, button_y + 25))

        # Reference the pressed-state asset too, as a faded "last pressed" hint.
        pressed_preview = scaled(PULL_BUTTON_PRESSED, (60, 30))
        pressed_preview.set_alpha(120)
        surface.blit(pressed_preview, (width // 2 - 260, button_y + 80))
