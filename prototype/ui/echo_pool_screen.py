"""EchoPool screen.

Renders the shared `GameSession`'s live `EchoPool` using the asset map in
docs/asset_map_iteration_1.md section 3, and wires the existing favorite
toggle / exchange / delete row controls to real `EchoPool` calls.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.assets import BODY_FONT, CAPS_FONT, load_font, nine_slice, scaled  # noqa: E402

PANEL = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/panel.standard/panel_0.png"
SLOT_FRAME = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/inventory_slot.standard/inventory_slot_1.png"
# selection_frame_square_0.png is a small (38x38) open corner-bracket shape,
# not a closed rectangular frame, so it can't be 9-sliced. Rows are wide
# (~880px) and stretching the 38px source that far smears it into a solid
# black blob (the bug QA reported). Draw a rounded-rect outline instead,
# using the border color sampled from that source art, and reserve the PNG
# itself for any future use at native-ish size.
SELECTION_FRAME_COLOR = (63, 63, 63)
TOGGLE_OFF = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/toggle_button.standard/toggle_button_0.png"
TOGGLE_ON = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/toggle_button.green/toggle_button_0.png"
DELETE_BUTTON = "tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Elements/Buttons/SmallRedRoundButton_Regular.png"
EXCHANGE_BUTTON = "tiny-swords-free-pack/Tiny Swords (Free Pack)/UI Elements/UI Elements/Buttons/SmallBlueRoundButton_Regular.png"
POWER_RING = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/progress_circle.standard/progress_circle_18.png"
LINEAGE_ICON = "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_amulet_105.png"
CAPACITY_TRACK = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/progress_bar.standard/progress_bar_0.png"
CAPACITY_FILL = "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/progress_bar.standard/progress_bar_1.png"

ICON_PATHS = {
    "shield": "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_iron_shield_182.png",
    "star": "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_controls/ui_pack_icons.standard/ui_pack_icon_star_33.png",
    "favorite_star": "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_controls/ui_pack_icons.standard/ui_pack_icon_star_33.png",
    "skull": "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_skull_69.png",
    "gold": "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_gold_ingot_30.png",
    "boss": "isle-of-lore-2-rpg-item-icons-final/Sources/output/rpg_item_icons.standard_outline/rpg_item_icon_boss_key_111.png",
    "default": "isle-of-lore-2-ui-pack-final/Sources/output/ui_pack_elements/inventory_slot.standard/inventory_slot_0.png",
}


class EchoPoolScreen:
    """Interactive EchoPool screen, driven by the shared `GameSession`.

    Each row's existing favorite toggle / exchange / delete button art is
    made clickable: toggle calls `EchoPool.update_record(favorite=...)`,
    exchange calls `EchoPool.exchange_echo`, delete calls
    `EchoPool.delete_echo`. Hit rects are recomputed every `draw()` call
    (rows can reorder/resize as records change) and consulted in
    `handle_event`.
    """

    name = "EchoPool"

    def __init__(self, session) -> None:
        self.session = session
        self.pool = session.echo_pool
        self.selected_id = None
        # record_id -> {"toggle": Rect, "exchange": Rect, "delete": Rect}
        self._row_controls: dict[int, dict[str, pygame.Rect]] = {}
        self.message = ""

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        pos = event.pos
        for record_id, controls in self._row_controls.items():
            if controls["toggle"].collidepoint(pos):
                self._toggle_favorite(record_id)
                return
            if controls["exchange"].collidepoint(pos):
                self._exchange(record_id)
                return
            if controls["delete"].collidepoint(pos):
                self._delete(record_id)
                return
            if controls["row"].collidepoint(pos):
                self.selected_id = record_id
                return

    def _toggle_favorite(self, record_id: int) -> None:
        record = self.pool.get_record(record_id)
        if record is None:
            return
        try:
            self.pool.update_record(record_id, favorite=not record.favorite)
            self.message = ""
        except ValueError as exc:
            self.message = str(exc)

    def _exchange(self, record_id: int) -> None:
        try:
            reward = self.pool.exchange_echo(record_id)
            self.message = (
                f"Exchanged #{record_id}: +{reward.essence} essence, "
                f"+{reward.shards} shards, +{reward.relic_rolls} relic rolls"
            )
            if self.selected_id == record_id:
                self.selected_id = None
        except (KeyError, ValueError) as exc:
            self.message = str(exc)

    def _delete(self, record_id: int) -> None:
        try:
            self.pool.delete_echo(record_id)
            self.message = f"Deleted echo #{record_id}"
            if self.selected_id == record_id:
                self.selected_id = None
        except (KeyError, ValueError) as exc:
            self.message = str(exc)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 18, 26))
        width, height = surface.get_size()

        surface.blit(nine_slice(PANEL, (width - 60, height - 60), border=16), (30, 30))

        title_font = load_font(CAPS_FONT, 26)
        body_font = load_font(BODY_FONT, 16)
        small_font = load_font(BODY_FONT, 13)

        title_surface = title_font.render("ECHO POOL", True, (255, 255, 255))
        surface.blit(title_surface, (60, 44))

        capacity_x, capacity_y, capacity_w, capacity_h = width - 280, 50, 200, 22
        surface.blit(scaled(CAPACITY_TRACK, (capacity_w, capacity_h)), (capacity_x, capacity_y))
        ratio = len(self.pool) / self.pool.capacity
        fill_w = max(1, int(capacity_w * ratio))
        surface.blit(scaled(CAPACITY_FILL, (fill_w, capacity_h)), (capacity_x, capacity_y))
        capacity_label = small_font.render(
            f"{len(self.pool)}/{self.pool.capacity}", True, (235, 235, 235)
        )
        surface.blit(capacity_label, (capacity_x, capacity_y - 18))

        records = self.pool.sorted_records(by="power")
        max_power = max((record.power_score for record in records), default=1)

        self._row_controls = {}

        row_x, row_y = 60, 100
        row_h = 86
        for record in records:
            slot_w = width - 120
            is_selected = record.id == self.selected_id
            if is_selected:
                selection_rect = pygame.Rect(row_x, row_y, slot_w, row_h - 6)
                pygame.draw.rect(
                    surface, SELECTION_FRAME_COLOR, selection_rect, width=3, border_radius=10
                )
            surface.blit(scaled(SLOT_FRAME, (70, row_h - 10)), (row_x, row_y + 2))

            icon_path = ICON_PATHS.get(record.icon, ICON_PATHS["default"])
            surface.blit(scaled(icon_path, (48, 48)), (row_x + 11, row_y + 13))

            text_x = row_x + 90
            id_label = body_font.render(
                f"Echo #{record.id}  ({record.echo.source_character_id})", True, (255, 255, 255)
            )
            surface.blit(id_label, (text_x, row_y + 6))

            power_label = small_font.render(f"power score: {record.power_score}", True, (220, 220, 220))
            surface.blit(power_label, (text_x, row_y + 30))

            surface.blit(scaled(LINEAGE_ICON, (18, 18)), (text_x + 220, row_y + 28))
            lineage_label = small_font.render(str(record.echo.lineage_depth), True, (220, 220, 220))
            surface.blit(lineage_label, (text_x + 242, row_y + 30))

            ring_diameter = 40
            ring_ratio = record.power_score / max_power if max_power else 0
            ring_size = max(8, int(ring_diameter * (0.4 + 0.6 * ring_ratio)))
            surface.blit(
                scaled(POWER_RING, (ring_size, ring_size)),
                (row_x + slot_w - 260, row_y + 20),
            )

            toggle_rect = pygame.Rect(row_x + slot_w - 200, row_y + 28, 44, 24)
            toggle_path = TOGGLE_ON if record.favorite else TOGGLE_OFF
            surface.blit(scaled(toggle_path, (44, 24)), toggle_rect.topleft)

            exchange_rect = pygame.Rect(row_x + slot_w - 140, row_y + 22, 32, 32)
            surface.blit(scaled(EXCHANGE_BUTTON, (32, 32)), exchange_rect.topleft)

            delete_rect = pygame.Rect(row_x + slot_w - 90, row_y + 22, 32, 32)
            surface.blit(scaled(DELETE_BUTTON, (32, 32)), delete_rect.topleft)

            self._row_controls[record.id] = {
                "row": pygame.Rect(row_x, row_y, slot_w, row_h - 6),
                "toggle": toggle_rect,
                "exchange": exchange_rect,
                "delete": delete_rect,
            }

            row_y += row_h

        if self.message:
            message_surface = small_font.render(self.message, True, (255, 220, 150))
            surface.blit(message_surface, (60, height - 36))
