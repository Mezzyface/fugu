"""EchoPool screen skeleton.

Renders a hardcoded `EchoPool` with a few banked `EchoRecord`s using the
asset map in docs/asset_map_iteration_1.md section 3.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game import EchoPool, TrainingSimulator, sample_characters  # noqa: E402

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
    """Static demo of the EchoPool screen, driven by real game.py data."""

    name = "EchoPool"

    def __init__(self) -> None:
        characters = sample_characters()
        simulator = TrainingSimulator(seed=5)
        self.pool = EchoPool(capacity=20, max_favorites=5)

        run_one = simulator.run(characters["iron_vow"], route="balanced")
        record_one = self.pool.bank_echo(run_one.echo, icon="shield")

        run_two = simulator.run(characters["star_witch"], route="skill_hunt", parents=self.pool.best_parents())
        record_two = self.pool.bank_echo(run_two.echo, icon="star")
        self.pool.update_record(record_two.id, favorite=True, icon="favorite_star")

        run_three = simulator.run(characters["rat_squire"], route="boss_rush")
        self.pool.bank_echo(run_three.echo, icon="boss")

        self.selected_id = record_one.id

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

            toggle_path = TOGGLE_ON if record.favorite else TOGGLE_OFF
            surface.blit(scaled(toggle_path, (44, 24)), (row_x + slot_w - 200, row_y + 28))

            surface.blit(scaled(EXCHANGE_BUTTON, (32, 32)), (row_x + slot_w - 140, row_y + 22))
            surface.blit(scaled(DELETE_BUTTON, (32, 32)), (row_x + slot_w - 90, row_y + 22))

            row_y += row_h
