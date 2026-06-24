"""Pygame app shell: window setup, event loop, and screen switching.

Skeleton only -- screens are static renders of hardcoded game.py data.
Switch screens with number keys 1/2/3 or the tab bar at the top of the
window. Quit with the window close button, Esc, or Ctrl+C.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.assets import BODY_FONT, load_font  # noqa: E402
from ui.banner_screen import BannerScreen  # noqa: E402
from ui.echo_pool_screen import EchoPoolScreen  # noqa: E402
from ui.session import GameSession  # noqa: E402
from ui.training_screen import TrainingScreen  # noqa: E402

WINDOW_SIZE = (1000, 700)
TAB_BAR_HEIGHT = 0  # tabs are drawn over the screen content, not a separate band
FPS = 60


class App:
    """Owns the pygame window and switches between screen objects."""

    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Fugu Prototype - UI Skeleton")
        self.clock = pygame.time.Clock()
        self.running = True

        self.session = GameSession()
        self.screens = [
            BannerScreen(self.session),
            TrainingScreen(self.session),
            EchoPoolScreen(self.session),
        ]
        self.active_index = 0
        self.tab_font = load_font(BODY_FONT, 18)

    @property
    def active_screen(self):
        return self.screens[self.active_index]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key in (pygame.K_1, pygame.K_KP1):
                self.active_index = 0
            elif event.key in (pygame.K_2, pygame.K_KP2):
                self.active_index = 1
            elif event.key in (pygame.K_3, pygame.K_KP3):
                self.active_index = 2
            elif event.key == pygame.K_TAB:
                self.active_index = (self.active_index + 1) % len(self.screens)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.pos[1] <= 36:
                self._handle_tab_click(event.pos)
            else:
                handler = getattr(self.active_screen, "handle_event", None)
                if handler is not None:
                    handler(event)
        else:
            handler = getattr(self.active_screen, "handle_event", None)
            if handler is not None:
                handler(event)

    def _handle_tab_click(self, pos) -> None:
        x, y = pos
        if y > 36:
            return
        tab_width = WINDOW_SIZE[0] // len(self.screens)
        index = x // tab_width
        if 0 <= index < len(self.screens):
            self.active_index = index

    def draw_tab_bar(self) -> None:
        tab_width = WINDOW_SIZE[0] // len(self.screens)
        for index, screen in enumerate(self.screens):
            rect = pygame.Rect(index * tab_width, 0, tab_width, 36)
            color = (70, 70, 90) if index == self.active_index else (40, 40, 50)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (10, 10, 14), rect, 1)
            label = self.tab_font.render(f"{index + 1}. {screen.name}", True, (240, 240, 240))
            self.screen.blit(
                label,
                (rect.x + rect.width // 2 - label.get_width() // 2, rect.y + 8),
            )

    def run(self, max_frames: int | None = None) -> None:
        frame_count = 0
        try:
            while self.running:
                for event in pygame.event.get():
                    self.handle_event(event)
                if not self.running:
                    break
                self.active_screen.draw(self.screen)
                self.draw_tab_bar()
                pygame.display.flip()
                self.clock.tick(FPS)
                frame_count += 1
                if max_frames is not None and frame_count >= max_frames:
                    break
        except KeyboardInterrupt:
            self.running = False
        finally:
            pygame.quit()
