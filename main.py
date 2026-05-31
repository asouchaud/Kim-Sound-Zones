"""Binaural Sound Zones - a small pygame world with real-time 3D audio.

Walk the cross (WASD / arrow keys) into the moving shapes. While you are inside
a zone you hear its sound, binauralised with the KEMAR HRTF so it appears to
come from the direction of the zone's centre. Use headphones!
"""
from __future__ import annotations

import sys

import pygame

from game import sounds
from game.audio_engine import AudioEngine
from game.config import (COLOR_BG, COLOR_GRID, COLOR_TEXT, COLOR_TEXT_DIM, FPS,
                         SCREEN_HEIGHT, SCREEN_WIDTH, WINDOW_TITLE)
from game.hrtf import BinauralHRTF
from game.player import Player
from game.sound_zone import SoundZone, regular_polygon
from game.trajectories import Circular, LinearBounce, RandomWalk, Static


def build_zones() -> list[SoundZone]:
    """Create a handful of zones with different shapes, motions and sounds."""
    return [
        SoundZone(
            0, sounds.tone(220.0, harmonics=4), shape="circle",
            trajectory=LinearBounce(250, 200, 70, 45), radius=90,
            label="A 220Hz",
        ),
        SoundZone(
            1, sounds.tone(440.0, harmonics=3), shape="rect",
            trajectory=Circular(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5,
                                radius=200, angular_speed=0.5),
            width=170, height=120, label="A4 440Hz",
        ),
        SoundZone(
            2, sounds.pink_noise(seed=7), shape="polygon",
            trajectory=RandomWalk(700, 480, speed=80, seed=3),
            polygon=regular_polygon(6, 85), label="noise",
        ),
        SoundZone(
            3, sounds.chirp(180.0, 900.0), shape="circle",
            trajectory=Static(SCREEN_WIDTH * 0.8, SCREEN_HEIGHT * 0.25),
            radius=80, label="chirp",
        ),
    ]


def main() -> None:
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 16)
    big_font = pygame.font.SysFont("consolas", 22)

    # Loading screen while the (somewhat slow) HRTF dataset is read.
    screen.fill(COLOR_BG)
    msg = big_font.render("Loading HRTF data...", True, COLOR_TEXT)
    screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2,
                      SCREEN_HEIGHT // 2 - msg.get_height() // 2))
    pygame.display.flip()

    hrtf = BinauralHRTF()
    engine = AudioEngine(hrtf)

    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    zones = build_zones()
    for zone in zones:
        engine.register(zone)

    try:
        engine.start()
    except Exception as exc:  # pragma: no cover - depends on audio hardware
        print(f"Could not open audio output: {exc}", file=sys.stderr)

    bounds = (SCREEN_WIDTH, SCREEN_HEIGHT)
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        player.handle_input(keys, dt)

        for zone in zones:
            zone.update(dt, bounds)
            inside = zone.contains(player.pos)
            gain = zone.gain_at(player.pos) if inside else 0.0
            azimuth = zone.azimuth_to(player.pos)
            engine.update_zone(zone, inside, azimuth, gain)

        _render(screen, font, big_font, player, zones)
        pygame.display.flip()

    engine.stop()
    pygame.quit()


def _render(screen, font, big_font, player, zones) -> None:
    screen.fill(COLOR_BG)

    step = 50
    for x in range(0, SCREEN_WIDTH, step):
        pygame.draw.line(screen, COLOR_GRID, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, step):
        pygame.draw.line(screen, COLOR_GRID, (0, y), (SCREEN_WIDTH, y))

    for zone in zones:
        zone.draw(screen, font)

    player.draw(screen)

    lines = [
        "Move: WASD / Arrows    Quit: Esc",
        "Headphones required - sound is binauralised to each zone's direction.",
    ]
    for i, text in enumerate(lines):
        color = COLOR_TEXT if i == 0 else COLOR_TEXT_DIM
        screen.blit(font.render(text, True, color), (12, 10 + i * 20))

    active = [z.label or str(z.id) for z in zones if z.active]
    status = "In zone: " + (", ".join(active) if active else "-")
    screen.blit(font.render(status, True, COLOR_TEXT),
                (12, SCREEN_HEIGHT - 26))


if __name__ == "__main__":
    main()
