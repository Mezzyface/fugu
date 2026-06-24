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

    #: How long a checkpoint banner stays on screen after a step that
    #: crosses a checkpoint floor, in milliseconds.
    checkpoint_banner_duration_ms = 2600

    def __init__(self, session) -> None:
        self.session = session
        self.simulator = session.simulator
        self.run_result = None
        self.banked = False
        self.start_button_rect = pygame.Rect(0, 0, 0, 0)
        self.bank_button_rect = pygame.Rect(0, 0, 0, 0)
        self.next_button_rect = pygame.Rect(0, 0, 0, 0)
        #: Number of `EncounterRecord`s revealed so far for the current run
        #: (step-through playback state -- see task brief item 1).
        self.revealed_count = 0
        #: (CheckpointReward, instability_dividend_at_step) for the banner
        #: currently being shown, or None when no banner is active.
        self._active_checkpoint_banner = None
        self._checkpoint_banner_until = 0

    def start_run(self) -> None:
        character = self.session.characters[self.character_id]
        parents = self.session.echo_pool.best_parents(self.character_id)
        self.run_result = self.simulator.run(character, route=self.route, parents=parents)
        self.banked = False
        self.revealed_count = 1 if self.run_result.encounters else 0
        self._active_checkpoint_banner = None
        self._checkpoint_banner_until = 0
        self._maybe_trigger_checkpoint_banner()

    def advance_floor(self) -> None:
        if self.run_result is None or self._playback_finished:
            return
        last_revealed = self.run_result.encounters[self.revealed_count - 1]
        if not last_revealed.cleared:
            return
        self.revealed_count += 1
        self._maybe_trigger_checkpoint_banner()

    def _maybe_trigger_checkpoint_banner(self) -> None:
        """Pop a banner if the floor just revealed is a banked checkpoint."""
        if self.run_result is None or self.revealed_count == 0:
            return
        current_floor = self.run_result.encounters[self.revealed_count - 1].floor
        for checkpoint in self.run_result.rewards.checkpoints:
            if checkpoint.floor == current_floor:
                # Mirrors TrainingSimulator.run's own dividend formula
                # (instability * 5 * tier) -- recomputed here rather than
                # re-deriving it from cumulative totals so it stays exactly
                # in sync with the per-checkpoint log line game.py emits.
                instability_dividend = self.run_result.echo.instability * 5 * checkpoint.tier
                self._active_checkpoint_banner = (checkpoint, instability_dividend)
                self._checkpoint_banner_until = pygame.time.get_ticks() + self.checkpoint_banner_duration_ms
                return

    @property
    def _playback_finished(self) -> bool:
        if self.run_result is None:
            return False
        if self.revealed_count >= len(self.run_result.encounters):
            return True
        return not self.run_result.encounters[self.revealed_count - 1].cleared

    def bank_echo(self) -> None:
        if self.run_result is None or self.banked or not self._playback_finished:
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
            elif self.next_button_rect.collidepoint(event.pos):
                self.advance_floor()
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

    def _draw_next_button(self, surface: pygame.Surface, width: int, height: int) -> None:
        """"Next Floor" action -- advances step-through playback by one
        `EncounterRecord` (task brief item 1). Hidden once playback has
        finished (run failed or every encounter has been revealed)."""
        body_font = load_font(BODY_FONT, 16)
        button_w, button_h = 160, 50
        button_x, button_y = width // 2 - button_w // 2, height - 100
        self.next_button_rect = pygame.Rect(button_x, button_y, button_w, button_h)
        pygame.draw.rect(surface, (160, 130, 60), self.next_button_rect, border_radius=8)
        pygame.draw.rect(surface, (20, 20, 20), self.next_button_rect, width=2, border_radius=8)
        label = body_font.render("Next Floor", True, (255, 255, 255))
        surface.blit(
            label,
            (
                self.next_button_rect.centerx - label.get_width() // 2,
                self.next_button_rect.centery - label.get_height() // 2,
            ),
        )

    def _draw_checkpoint_banner(self, surface: pygame.Surface, width: int) -> None:
        """Brief on-screen callout shown right when playback advances onto
        a floor that just banked a `CheckpointReward` (task brief item 2).
        Replaces the old "show every checkpoint at once" list."""
        if self._active_checkpoint_banner is None:
            return
        if pygame.time.get_ticks() >= self._checkpoint_banner_until:
            self._active_checkpoint_banner = None
            return
        checkpoint, instability_dividend = self._active_checkpoint_banner

        body_font = load_font(BODY_FONT, 18)
        small_font = load_font(BODY_FONT, 14)

        banner_w, banner_h = 420, 92
        banner_x, banner_y = width // 2 - banner_w // 2, 90
        panel = nine_slice(ECHO_CARD, (banner_w, banner_h), border=14)
        panel.set_alpha(235)
        surface.blit(panel, (banner_x, banner_y))

        title = body_font.render(
            f"CHECKPOINT BANKED -- FLOOR {checkpoint.floor} (TIER {checkpoint.tier})",
            True,
            (255, 220, 120),
        )
        surface.blit(title, (banner_x + banner_w // 2 - title.get_width() // 2, banner_y + 10))

        surface.blit(scaled(GOLD_ICON, (18, 18)), (banner_x + 24, banner_y + 44))
        surface.blit(scaled(RELIC_ICON, (18, 18)), (banner_x + 24, banner_y + 68))

        shard_line = small_font.render(
            f"+{checkpoint.shards} shards   +{checkpoint.echo_quality_bonus}% echo quality",
            True,
            (230, 230, 230),
        )
        surface.blit(shard_line, (banner_x + 50, banner_y + 44))

        relic_line = small_font.render(
            f"+{checkpoint.relic_rolls} relic rolls"
            + (f"   +{instability_dividend} instability dividend" if instability_dividend else ""),
            True,
            (230, 230, 230),
        )
        surface.blit(relic_line, (banner_x + 50, banner_y + 68))

    def _draw_result(self, surface: pygame.Surface) -> None:
        surface.fill((18, 24, 22))
        width, height = surface.get_size()

        surface.blit(nine_slice(PANEL, (width - 60, height - 60), border=16), (30, 30))

        title_font = load_font(CAPS_FONT, 26)
        body_font = load_font(BODY_FONT, 16)
        small_font = load_font(BODY_FONT, 13)

        playback_finished = self._playback_finished
        if playback_finished:
            header = "VICTORY" if self.run_result.victory else f"FLOOR {self.run_result.floors_cleared} OF 12"
        else:
            current_floor = self.run_result.encounters[self.revealed_count - 1].floor
            header = f"FLOOR {current_floor} OF 12"
        title_surface = title_font.render(header, True, (255, 255, 255))
        surface.blit(title_surface, (60, 44))

        if playback_finished and self.run_result.victory:
            surface.blit(scaled(VICTORY_BANNER, (200, 60)), (width - 260, 40))

        # Encounter list (left column) -- only the encounters revealed so
        # far via step-through playback are drawn (task brief item 1).
        list_x, list_y = 60, 100
        row_h = 36
        revealed = self.run_result.encounters[: self.revealed_count]
        for index, record in enumerate(revealed):
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

        # Frozen echo summary card (right column) -- only once playback has
        # reached the end of the encounter list (task brief item 1: don't
        # show the ending before the player has stepped through it).
        if playback_finished:
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
            self.next_button_rect = pygame.Rect(0, 0, 0, 0)
            self._draw_start_button(surface, width, height)
        else:
            self.bank_button_rect = pygame.Rect(0, 0, 0, 0)
            # Both buttons share the same on-screen slot (Start Run before
            # a run exists, Next Floor while stepping through one), so the
            # inactive one's stale rect must be cleared -- otherwise
            # handle_event's `if start_button_rect.collidepoint(...)` check
            # (which runs first) would match Next Floor clicks too, since
            # the rects are identical, and re-start the run on every click
            # instead of advancing.
            self.start_button_rect = pygame.Rect(0, 0, 0, 0)
            self._draw_next_button(surface, width, height)

        # Checkpoint/instability-dividend banner pop-up (task brief item 2)
        # is drawn last so it sits on top of everything else briefly.
        self._draw_checkpoint_banner(surface, width)
