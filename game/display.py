"""Window creation, maximize, and fullscreen toggle.

The game can start maximized (fills your monitor) or in a smaller window.
Press F11 at any time to switch between the two.
"""
from __future__ import annotations

import pygame

from . import config


class Display:
    """Owns the pygame window and keeps ``config.SCREEN_WIDTH/HEIGHT`` in sync."""

    def __init__(self, start_maximized: bool = True,
                 windowed_size: tuple[int, int] | None = None):
        self.windowed_size = windowed_size or (
            config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        self.maximized = start_maximized
        self.screen: pygame.Surface | None = None

    def create(self) -> pygame.Surface:
        pygame.display.set_caption(config.WINDOW_TITLE)
        size = self._desktop_size() if self.maximized else self.windowed_size
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        self._sync_config()
        return self.screen

    def toggle(self) -> pygame.Surface:
        """Switch between maximized and windowed; returns the active surface."""
        self.maximized = not self.maximized
        return self.create()

    def handle_resize(self, event: pygame.event.Event) -> pygame.Surface:
        """Keep layout in sync when the user drags the window edge."""
        self.maximized = False
        self.screen = pygame.display.set_mode(
            (event.w, event.h), pygame.RESIZABLE)
        self._sync_config()
        return self.screen

    @staticmethod
    def _desktop_size() -> tuple[int, int]:
        info = pygame.display.Info()
        return max(800, info.current_w), max(600, info.current_h)

    @staticmethod
    def _sync_config() -> None:
        surf = pygame.display.get_surface()
        if surf is not None:
            config.SCREEN_WIDTH, config.SCREEN_HEIGHT = surf.get_size()
