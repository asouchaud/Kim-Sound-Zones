"""A sound zone: a moving shape that emits a binauralised sound.

A zone owns:
  * its geometry (circle / rectangle / regular polygon) and current centre,
  * a movement ``Trajectory``,
  * a mono sound buffer plus a looping read position,
  * overlap-add tail buffers used by the audio engine (allocated on register).

Geometry queries (``contains``, ``gain_at``, ``azimuth_to``) are called from the
game thread; the audio playback helpers (``next_block`` and the ``tail_*``
buffers) are touched only by the audio thread, so the two never race.
"""
from __future__ import annotations

import math

import numpy as np
import pygame

from .config import COLOR_ZONE_ACTIVE, COLOR_ZONE_IDLE
from .trajectories import Static, Trajectory


def regular_polygon(n_sides: int, radius: float) -> list[tuple[float, float]]:
    """Vertex offsets (relative to centre) for a regular polygon."""
    return [
        (radius * math.cos(2 * math.pi * i / n_sides - math.pi / 2),
         radius * math.sin(2 * math.pi * i / n_sides - math.pi / 2))
        for i in range(n_sides)
    ]


def _point_segment_distance(px: float, py: float,
                            a: tuple[float, float],
                            b: tuple[float, float]) -> float:
    """Shortest distance from point (px, py) to the segment a-b."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    seg_len2 = dx * dx + dy * dy
    if seg_len2 == 0.0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / seg_len2
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


class SoundZone:
    def __init__(self, zone_id: int, sound: np.ndarray, shape: str = "circle",
                 trajectory: Trajectory | None = None, *,
                 radius: float = 80.0, width: float = 160.0, height: float = 110.0,
                 polygon: list[tuple[float, float]] | None = None,
                 label: str = ""):
        self.id = zone_id
        self.sound = np.ascontiguousarray(sound, dtype=np.float32)
        self.shape = shape
        self.label = label

        self.radius = float(radius)
        self.width = float(width)
        self.height = float(height)
        self.polygon = polygon or regular_polygon(6, radius)

        self.trajectory = trajectory or Static(0.0, 0.0)
        self.x, self.y = self.trajectory.x, self.trajectory.y

        # --- audio playback state (audio thread only) ---
        self.read_pos = 0
        self.tail_l: np.ndarray | None = None  # allocated by AudioEngine.register
        self.tail_r: np.ndarray | None = None

        # --- live parameters shared with the audio engine ---
        self.active = False
        self.target_gain = 0.0
        self.target_azimuth = 0.0

    # ------------------------------------------------------------------
    # Geometry (game thread)
    # ------------------------------------------------------------------
    @property
    def center(self) -> tuple[float, float]:
        return self.x, self.y

    def update(self, dt: float, bounds: tuple[int, int]) -> None:
        self.x, self.y = self.trajectory.update(dt, bounds)

    def _bounding_radius(self) -> float:
        if self.shape == "circle":
            return self.radius
        if self.shape == "ellipse":
            return max(self.width, self.height) / 2
        if self.shape == "rect":
            return 0.5 * math.hypot(self.width, self.height)
        return max(math.hypot(dx, dy) for dx, dy in self.polygon)

    def contains(self, point: tuple[float, float]) -> bool:
        px, py = point
        dx, dy = px - self.x, py - self.y
        if self.shape == "circle":
            return dx * dx + dy * dy <= self.radius * self.radius
        if self.shape == "ellipse":
            rx = max(1.0, self.width / 2)
            ry = max(1.0, self.height / 2)
            return (dx / rx) ** 2 + (dy / ry) ** 2 <= 1.0
        if self.shape == "rect":
            return abs(dx) <= self.width / 2 and abs(dy) <= self.height / 2
        return self._point_in_polygon(dx, dy)

    def _point_in_polygon(self, dx: float, dy: float) -> bool:
        verts = self.polygon
        inside = False
        n = len(verts)
        j = n - 1
        for i in range(n):
            xi, yi = verts[i]
            xj, yj = verts[j]
            if (yi > dy) != (yj > dy):
                x_cross = (xj - xi) * (dy - yi) / (yj - yi + 1e-12) + xi
                if dx < x_cross:
                    inside = not inside
            j = i
        return inside

    def gain_at(self, point: tuple[float, float]) -> float:
        """Loudness in [0, 1]: louder near the centre, quieter near the edge."""
        if not self.contains(point):
            return 0.0
        dist = math.hypot(point[0] - self.x, point[1] - self.y)
        eff = max(1.0, self._bounding_radius())
        return max(0.3, 1.0 - 0.7 * (dist / eff))

    def distance_to_point(self, point: tuple[float, float]) -> float:
        """Shortest distance from ``point`` to this shape (0 if inside)."""
        px, py = point
        if self.contains(point):
            return 0.0
        if self.shape == "circle":
            return math.hypot(px - self.x, py - self.y) - self.radius
        if self.shape == "ellipse":
            # Radial approximation: distance along the ray from the centre to
            # the point, minus where that ray crosses the ellipse boundary.
            dx, dy = px - self.x, py - self.y
            d = math.hypot(dx, dy)
            if d == 0.0:
                return 0.0
            rx = max(1.0, self.width / 2)
            ry = max(1.0, self.height / 2)
            ux, uy = dx / d, dy / d
            boundary = 1.0 / math.sqrt((ux / rx) ** 2 + (uy / ry) ** 2)
            return max(0.0, d - boundary)
        if self.shape == "rect":
            dx = max(abs(px - self.x) - self.width / 2, 0.0)
            dy = max(abs(py - self.y) - self.height / 2, 0.0)
            return math.hypot(dx, dy)
        # polygon: minimum distance to any edge
        verts = [(self.x + dx, self.y + dy) for dx, dy in self.polygon]
        best = float("inf")
        n = len(verts)
        for i in range(n):
            best = min(best, _point_segment_distance(
                px, py, verts[i], verts[(i + 1) % n]))
        return best

    def intersects_circle(self, point: tuple[float, float], radius: float) -> bool:
        """True if a circle of ``radius`` centred on ``point`` overlaps this zone."""
        return self.distance_to_point(point) <= radius

    def gain_for_listener(self, point: tuple[float, float], radius: float) -> float:
        """Loudness when heard via a listener circle of ``radius``.

        Returns 0 when the listener circle does not overlap the zone. Otherwise
        ramps from a quiet floor at first contact up to full volume as the
        listener reaches the zone's centre.
        """
        if not self.intersects_circle(point, radius):
            return 0.0
        dist = math.hypot(point[0] - self.x, point[1] - self.y)
        contact = max(1.0, radius + self._bounding_radius())
        closeness = max(0.0, min(1.0, 1.0 - dist / contact))
        return 0.3 + 0.7 * closeness

    def azimuth_to(self, point: tuple[float, float]) -> float:
        """Game azimuth (deg) of this zone's centre as seen from ``point``.

        Heading is fixed pointing up, so 0 deg is straight ahead and positive
        is to the player's right.
        """
        dx = self.x - point[0]
        dy = self.y - point[1]
        return math.degrees(math.atan2(dx, -dy))

    # ------------------------------------------------------------------
    # Audio playback (audio thread)
    # ------------------------------------------------------------------
    def next_block(self, frames: int) -> np.ndarray:
        """Return the next ``frames`` mono samples, looping the buffer."""
        n = self.sound.size
        if n == 0:
            return np.zeros(frames, dtype=np.float32)
        out = np.empty(frames, dtype=np.float32)
        pos = self.read_pos
        filled = 0
        while filled < frames:
            chunk = min(frames - filled, n - pos)
            out[filled:filled + chunk] = self.sound[pos:pos + chunk]
            filled += chunk
            pos += chunk
            if pos >= n:
                pos = 0
        self.read_pos = pos
        return out

    # ------------------------------------------------------------------
    # Rendering (game thread)
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface, font: pygame.font.Font | None = None) -> None:
        color = COLOR_ZONE_ACTIVE if self.active else COLOR_ZONE_IDLE
        cx, cy = int(self.x), int(self.y)
        if self.shape == "circle":
            pygame.draw.circle(surface, color, (cx, cy), int(self.radius), 2)
        elif self.shape == "ellipse":
            rect = pygame.Rect(0, 0, max(2, int(self.width)), max(2, int(self.height)))
            rect.center = (cx, cy)
            pygame.draw.ellipse(surface, color, rect, 2)
        elif self.shape == "rect":
            rect = pygame.Rect(0, 0, int(self.width), int(self.height))
            rect.center = (cx, cy)
            pygame.draw.rect(surface, color, rect, 2)
        else:
            pts = [(cx + dx, cy + dy) for dx, dy in self.polygon]
            pygame.draw.polygon(surface, color, pts, 2)

        pygame.draw.circle(surface, color, (cx, cy), 3)
        if font and self.label:
            text = font.render(self.label, True, color)
            surface.blit(text, (cx - text.get_width() // 2, cy - 6))
