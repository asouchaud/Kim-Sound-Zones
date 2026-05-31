"""The player character: a cross that walks around the 2D world."""
from __future__ import annotations

import pygame

from .config import (COLOR_LISTENER, COLOR_PLAYER, PLAYER_SIZE, PLAYER_SPEED,
                     SCREEN_HEIGHT, SCREEN_WIDTH)


class Player:
    """A simple top-down avatar drawn as a cross.

    The heading is fixed pointing "up" (north / negative screen-y). Sound zone
    azimuths are computed relative to this heading, so a zone directly above the
    player is straight ahead (0 deg) and a zone to the right is +90 deg.

    The player also carries a "listener zone": a circle of ``listener_radius``
    pixels around it. A sound is heard only while its zone overlaps this circle.
    """

    def __init__(self, x: float, y: float, listener_radius: float = 120.0):
        self.x = float(x)
        self.y = float(y)
        self.speed = PLAYER_SPEED
        self.listener_radius = float(listener_radius)
        # Heading as a unit vector; "up" on screen is (0, -1).
        self.heading = (0.0, -1.0)

    @property
    def pos(self) -> tuple[float, float]:
        return self.x, self.y

    def handle_input(self, keys, dt: float) -> None:
        dx = 0.0
        dy = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1.0

        if dx or dy:
            length = (dx * dx + dy * dy) ** 0.5
            dx, dy = dx / length, dy / length
            self.x += dx * self.speed * dt
            self.y += dy * self.speed * dt
            self._clamp_to_screen()

    def _clamp_to_screen(self) -> None:
        self.x = max(PLAYER_SIZE, min(SCREEN_WIDTH - PLAYER_SIZE, self.x))
        self.y = max(PLAYER_SIZE, min(SCREEN_HEIGHT - PLAYER_SIZE, self.y))

    def draw(self, surface: pygame.Surface) -> None:
        cx, cy = int(self.x), int(self.y)
        r = int(self.listener_radius)

        # Listener zone: a soft translucent disc plus an outline.
        if r > 0:
            halo = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*COLOR_LISTENER, 28), (r, r), r)
            surface.blit(halo, (cx - r, cy - r))
            pygame.draw.circle(surface, COLOR_LISTENER, (cx, cy), r, 1)

        s = PLAYER_SIZE
        pygame.draw.line(surface, COLOR_PLAYER, (cx - s, cy), (cx + s, cy), 3)
        pygame.draw.line(surface, COLOR_PLAYER, (cx, cy - s), (cx, cy + s), 3)
