"""Training run screen.

Renders a live `RunResult` (12-floor run) from the shared `GameSession`
using the asset map in docs/asset_map_iteration_1.md section 2. A
"Start Run" button triggers a real `TrainingSimulator.run` call, and a
"Bank Echo" button banks the resulting `FrozenEcho` into the shared
`EchoPool`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.assets import BODY_FONT, CAPS_FONT, load_font, nine_slice, scaled  # noqa: E402

PANEL = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/panel.standard/panel_0.png"
ROW_BG = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/box.standard/box_0.png"
ENCOUNTER_ICONS = {
    "combat": "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_sword_153.png",
    "elite": "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_shortsword_154.png",
    "boss": "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_boss_key_111.png",
    "event": "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_book_132.png",
    "shrine": "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_candle_121.png",
    "rest": "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_tent_90.png",
}
CHECKMARK = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_controls/ui_pack_icons.standard/ui_pack_icon_checkmark_1.png"
CROSS = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_controls/ui_pack_icons.standard/ui_pack_icon_cross_0.png"
POWER_BAR_TRACK = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/progress_bar.standard/progress_bar_0.png"
POWER_BAR_FILL = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/progress_bar.standard/progress_bar_1.png"
VICTORY_BANNER = "tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Banners from the store page/Ribbons/Ribbon_Yellow.png"
ECHO_CARD = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/dialog_box.standard/dialog_box_0.png"
STAT_ICONS = {
    "hp": "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_heart_piece_full_120.png",
    "atk": "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_sword_153.png",
    "def": "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_iron_shield_182.png",
    "spd": "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_boot_192.png",
}
INSTABILITY_ICON = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_controls/ui_pack_icons.standard/ui_pack_icon_exclamation_mark_40.png"
GOLD_ICON = "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_gold_nugget_29.png"
RELIC_ICON = "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_chest_140.png"


class TrainingScreen:
    """Interactive training-run screen, driven by the shared `GameSession`."""

    name = "Training"

    #: Fixed default character/route for this phase -- exposing every
    #: possible input is out of scope per the task brief.
    character_id = "iron_vow"
    route = "deep_scaling"

    def __init__(self, session) -> None:
        self.session = session
        self.simulator = session.simulator
        self.run_result = None
        self.banked = False
        self.start_button_rect = pygame.Rect(0, 0, 0, 0)
        self.bank_button_rect = pygame.Rect(0, 0, 0, 0)

    def start_run(self) -> None:
        character = self.session.characters[self.character_id]
        parents = self.session.echo_pool.best_parents(self.character_id)
        self.run_result = self.simulator.run(character, route=self.route, parents=parents)
        self.banked = False

    def bank_echo(self) -> None:
        if self.run_result is None or self.banked:
            return
        pool = self.session.echo_pool
        if pool.is_full:
            return
        pool.bank_echo(self.run_result.echo)
        self.banked = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.start_button_rect.collidepoint(event.pos):
                self.start_run()
            elif self.bank_button_rect.collidepoint(event.pos):
                self.bank_echo()

    def draw(self, surface: pygame.Surface) -> None:
        if self.run_result is None:
            self._draw_empty_state(surface)
            return
        self._draw_result(surface)

    def _draw_empty_state(self, surface: pygame.Surface) -> None:
        surface.fill((18, 24, 22))
        width, height = surface.get_size()
        surface.blit(nine_slice(PANEL, (width - 60, height - 60), border=16), (30, 30))

        title_font = load_font(CAPS_FONT, 26)
        body_font = load_font(BODY_FONT, 16)

        title_surface = title_font.render("NO RUN YET", True, (255, 255, 255))
        surface.blit(title_surface, (60, 44))

        hint_surface = body_font.render(
            "Click Start Run to send a character through a 12-floor run.", True, (210, 210, 210)
        )
        surface.blit(hint_surface, (60, 100))

        self._draw_start_button(surface, width, height)

    def _draw_start_button(self, surface: pygame.Surface, width: int, height: int) -> None:
        body_font = load_font(BODY_FONT, 16)
        button_w, button_h = 160, 50
        button_x, button_y = width // 2 - button_w // 2, height - 100
        self.start_button_rect = pygame.Rect(button_x, button_y, button_w, button_h)
        pygame.draw.rect(surface, (70, 140, 90), self.start_button_rect, border_radius=8)
        pygame.draw.rect(surface, (20, 20, 20), self.start_button_rect, width=2, border_radius=8)
        label = body_font.render("Start Run", True, (255, 255, 255))
        surface.blit(
            label,
            (
                self.start_button_rect.centerx - label.get_width() // 2,
                self.start_button_rect.centery - label.get_height() // 2,
            ),
        )

    def _draw_bank_button(self, surface: pygame.Surface, card_x: int, button_y: int, card_w: int) -> None:
        body_font = load_font(BODY_FONT, 16)
        button_w, button_h = card_w - 40, 36
        button_x = card_x + 20
        self.bank_button_rect = pygame.Rect(button_x, button_y, button_w, button_h)
        color = (90, 90, 90) if self.banked else (70, 110, 170)
        pygame.draw.rect(surface, color, self.bank_button_rect, border_radius=8)
        pygame.draw.rect(surface, (20, 20, 20), self.bank_button_rect, width=2, border_radius=8)
        label_text = "Echo Banked" if self.banked else "Bank Echo"
        label = body_font.render(label_text, True, (255, 255, 255))
        surface.blit(
            label,
            (
                self.bank_button_rect.centerx - label.get_width() // 2,
                self.bank_button_rect.centery - label.get_height() // 2,
            ),
        )

    def _draw_result(self, surface: pygame.Surface) -> None:
        surface.fill((18, 24, 22))
        width, height = surface.get_size()

        surface.blit(nine_slice(PANEL, (width - 60, height - 60), border=16), (30, 30))

        title_font = load_font(CAPS_FONT, 26)
        body_font = load_font(BODY_FONT, 16)
        small_font = load_font(BODY_FONT, 13)

        header = "VICTORY" if self.run_result.victory else f"FLOOR {self.run_result.floors_cleared} OF 12"
        title_surface = title_font.render(header, True, (255, 255, 255))
        surface.blit(title_surface, (60, 44))

        if self.run_result.victory:
            surface.blit(scaled(VICTORY_BANNER, (200, 60)), (width - 260, 40))

        # Encounter list (left column).
        list_x, list_y = 60, 100
        row_h = 36
        for index, record in enumerate(self.run_result.encounters):
            row_y = list_y + index * row_h
            surface.blit(nine_slice(ROW_BG, (360, row_h - 4), border=10), (list_x, row_y))
            icon_path = ENCOUNTER_ICONS.get(record.kind, ENCOUNTER_ICONS["combat"])
            surface.blit(scaled(icon_path, (24, 24)), (list_x + 6, row_y + 4))
            status_icon = CHECKMARK if record.cleared else CROSS
            surface.blit(scaled(status_icon, (20, 20)), (list_x + 36, row_y + 6))
            label = small_font.render(
                f"Floor {record.floor:>2}  {record.kind:<7} pwr {record.power} vs {record.difficulty}",
                True,
                (230, 230, 230),
            )
            surface.blit(label, (list_x + 64, row_y + 8))

            # Power/difficulty bar.
            bar_x, bar_y, bar_w, bar_h = list_x + 360 + 10, row_y + 8, 90, 16
            surface.blit(scaled(POWER_BAR_TRACK, (bar_w, bar_h)), (bar_x, bar_y))
            ratio = min(1.0, record.power / max(1, record.difficulty))
            fill_w = max(1, int(bar_w * ratio))
            surface.blit(scaled(POWER_BAR_FILL, (fill_w, bar_h)), (bar_x, bar_y))

        # Checkpoint rewards.
        checkpoint_y = list_y + len(self.run_result.encounters) * row_h + 20
        checkpoint_label = body_font.render("CHECKPOINTS", True, (255, 255, 255))
        surface.blit(checkpoint_label, (list_x, checkpoint_y))
        for index, checkpoint in enumerate(self.run_result.rewards.checkpoints):
            row_y = checkpoint_y + 28 + index * 26
            surface.blit(scaled(GOLD_ICON, (18, 18)), (list_x, row_y))
            surface.blit(scaled(RELIC_ICON, (18, 18)), (list_x + 130, row_y))
            text = small_font.render(
                f"Floor {checkpoint.floor} tier {checkpoint.tier}: "
                f"+{checkpoint.shards} shards   +{checkpoint.relic_rolls} relic rolls   "
                f"+{checkpoint.echo_quality_bonus}% echo quality",
                True,
                (230, 230, 230),
            )
            surface.blit(text, (list_x + 20, row_y + 1))

        # Frozen echo summary card (right column).
        card_x, card_y, card_w, card_h = width - 380, 100, 320, 420
        surface.blit(nine_slice(ECHO_CARD, (card_w, card_h), border=14), (card_x, card_y))
        echo = self.run_result.echo
        echo_title = body_font.render("FROZEN ECHO", True, (255, 255, 255))
        surface.blit(echo_title, (card_x + 20, card_y + 16))
        source_label = small_font.render(f"source: {echo.source_character_id}", True, (210, 210, 210))
        surface.blit(source_label, (card_x + 20, card_y + 44))
        lineage_label = small_font.render(f"lineage depth: {echo.lineage_depth}", True, (210, 210, 210))
        surface.blit(lineage_label, (card_x + 20, card_y + 64))

        stat_y = card_y + 96
        for index, (stat_name, value) in enumerate(echo.stats.items()):
            icon_path = STAT_ICONS.get(stat_name)
            row_y = stat_y + index * 30
            if icon_path:
                surface.blit(scaled(icon_path, (22, 22)), (card_x + 20, row_y))
            stat_label = small_font.render(f"{stat_name.upper()}: {value}", True, (235, 235, 235))
            surface.blit(stat_label, (card_x + 50, row_y + 2))

        instability_y = stat_y + len(echo.stats) * 30 + 16
        if echo.instability:
            surface.blit(scaled(INSTABILITY_ICON, (22, 22)), (card_x + 20, instability_y))
        instability_label = small_font.render(f"instability: {echo.instability}", True, (255, 180, 90))
        surface.blit(instability_label, (card_x + 50, instability_y + 2))

        skills_label = small_font.render("skills: " + ", ".join(echo.skills), True, (210, 210, 210))
        surface.blit(skills_label, (card_x + 20, instability_y + 36))
        traits_label = small_font.render("traits: " + ", ".join(echo.traits), True, (210, 210, 210))
        surface.blit(traits_label, (card_x + 20, instability_y + 56))

        self._draw_bank_button(surface, card_x, instability_y + 80, card_w)
        self._draw_start_button(surface, width, height)
