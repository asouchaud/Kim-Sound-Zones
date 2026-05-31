"""Movement patterns for sound zones.

Each trajectory is a small stateful object with an ``update(dt, bounds)`` method
that advances time and returns the current ``(x, y)`` centre of the zone.
``bounds`` is ``(width, height)`` of the play area so trajectories can bounce or
wrap as needed.
"""
from __future__ import annotations

import math
import random


class Trajectory:
    """Base class. Subclasses update ``self.x`` / ``self.y`` and return them."""

    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)

    def update(self, dt: float, bounds: tuple[int, int]) -> tuple[float, float]:
        return self.x, self.y


class Static(Trajectory):
    """A zone that never moves."""


class LinearBounce(Trajectory):
    """Moves in a straight line and bounces off the edges of the play area."""

    def __init__(self, x: float, y: float, vx: float, vy: float, margin: float = 40.0):
        super().__init__(x, y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.margin = float(margin)

    def update(self, dt: float, bounds: tuple[int, int]) -> tuple[float, float]:
        w, h = bounds
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x < self.margin:
            self.x = self.margin
            self.vx = abs(self.vx)
        elif self.x > w - self.margin:
            self.x = w - self.margin
            self.vx = -abs(self.vx)
        if self.y < self.margin:
            self.y = self.margin
            self.vy = abs(self.vy)
        elif self.y > h - self.margin:
            self.y = h - self.margin
            self.vy = -abs(self.vy)
        return self.x, self.y


class Circular(Trajectory):
    """Orbits a fixed centre at a constant angular speed."""

    def __init__(self, cx: float, cy: float, radius: float,
                 angular_speed: float = 0.8, phase: float = 0.0):
        self.cx = float(cx)
        self.cy = float(cy)
        self.radius = float(radius)
        self.angular_speed = float(angular_speed)  # radians per second
        self.angle = float(phase)
        super().__init__(cx + radius * math.cos(phase),
                         cy + radius * math.sin(phase))

    def update(self, dt: float, bounds: tuple[int, int]) -> tuple[float, float]:
        self.angle += self.angular_speed * dt
        self.x = self.cx + self.radius * math.cos(self.angle)
        self.y = self.cy + self.radius * math.sin(self.angle)
        return self.x, self.y


class RandomWalk(Trajectory):
    """Drifts around, occasionally changing direction; bounces off edges."""

    def __init__(self, x: float, y: float, speed: float = 90.0,
                 turn_interval: float = 1.2, margin: float = 40.0,
                 seed: int | None = None):
        super().__init__(x, y)
        self.speed = float(speed)
        self.turn_interval = float(turn_interval)
        self.margin = float(margin)
        self._rng = random.Random(seed)
        self._timer = 0.0
        self._heading = self._rng.uniform(0, 2 * math.pi)

    def update(self, dt: float, bounds: tuple[int, int]) -> tuple[float, float]:
        w, h = bounds
        self._timer += dt
        if self._timer >= self.turn_interval:
            self._timer = 0.0
            self._heading += self._rng.uniform(-1.2, 1.2)

        self.x += math.cos(self._heading) * self.speed * dt
        self.y += math.sin(self._heading) * self.speed * dt

        if self.x < self.margin or self.x > w - self.margin:
            self._heading = math.pi - self._heading
            self.x = max(self.margin, min(w - self.margin, self.x))
        if self.y < self.margin or self.y > h - self.margin:
            self._heading = -self._heading
            self.y = max(self.margin, min(h - self.margin, self.y))
        return self.x, self.y
