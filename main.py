"""Binaural Sound Zones - a small pygame world with real-time 3D audio.

Launch the game to open a setup menu where you build your world by clicking:
choose the shape, size, speed, movement and sound of each zone, set how far the
listener can hear, then press Start. Walk the cross (WASD / arrow keys) so that
its hearing circle overlaps a zone - you will hear that zone's sound,
binauralised with the KEMAR HRTF so it appears to come from the zone's
direction. Use headphones!
"""
from __future__ import annotations

import sys

import pygame

from game.audio_engine import AudioEngine
from game.config import (COLOR_BG, COLOR_GRID, COLOR_TEXT, COLOR_TEXT_DIM, FPS,
                         SCREEN_HEIGHT, SCREEN_WIDTH, WINDOW_TITLE)
from game.hrtf import BinauralHRTF
from game.menu import MenuResult, run_menu
from game.player import Player
from game.setup import SoundCatalog, build_zone_from_spec


def _make_fonts() -> dict:
    return {
        "title": pygame.font.SysFont("consolas", 30, bold=True),
        "head": pygame.font.SysFont("consolas", 20, bold=True),
        "body": pygame.font.SysFont("consolas", 18),
        "small": pygame.font.SysFont("consolas", 14),
    }


def main() -> None:
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    fonts = _make_fonts()

    # Loading screen while the (somewhat slow) HRTF dataset is read.
    screen.fill(COLOR_BG)
    msg = fonts["head"].render("Loading HRTF data...", True, COLOR_TEXT)
    screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2,
                      SCREEN_HEIGHT // 2 - msg.get_height() // 2))
    pygame.display.flip()

    hrtf = BinauralHRTF()
    engine = AudioEngine(hrtf)
    catalog = SoundCatalog()

    try:
        engine.start()
    except Exception as exc:  # pragma: no cover - depends on audio hardware
        print(f"Could not open audio output: {exc}", file=sys.stderr)

    try:
        while True:
            result = run_menu(screen, clock, fonts, catalog)
            if result is None:
                break
            if run_game(screen, clock, fonts, engine, catalog, result) == "quit":
                break
    finally:
        engine.stop()
        pygame.quit()


def run_game(screen, clock, fonts, engine, catalog, result: MenuResult) -> str:
    """Play one session. Returns "menu" (Esc) or "quit" (window closed)."""
    engine.clear()
    bounds = (SCREEN_WIDTH, SCREEN_HEIGHT)

    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                    listener_radius=result.listener_radius)
    zones = []
    for i, spec in enumerate(result.specs):
        zone = build_zone_from_spec(i, spec, catalog, bounds)
        engine.register(zone)
        zones.append(zone)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                engine.clear()
                return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        player.handle_input(keys, dt)

        for zone in zones:
            zone.update(dt, bounds)
            active = zone.intersects_circle(player.pos, player.listener_radius)
            gain = zone.gain_for_listener(player.pos, player.listener_radius)
            azimuth = zone.azimuth_to(player.pos)
            engine.update_zone(zone, active, azimuth, gain)

        _render_game(screen, fonts, player, zones)
        pygame.display.flip()

    engine.clear()
    return "menu"


def _render_game(screen, fonts, player, zones) -> None:
    screen.fill(COLOR_BG)

    step = 50
    for x in range(0, SCREEN_WIDTH, step):
        pygame.draw.line(screen, COLOR_GRID, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, step):
        pygame.draw.line(screen, COLOR_GRID, (0, y), (SCREEN_WIDTH, y))

    for zone in zones:
        zone.draw(screen, fonts["small"])

    player.draw(screen)

    body = fonts["body"]
    small = fonts["small"]
    screen.blit(body.render("Move: WASD / Arrows", True, COLOR_TEXT), (12, 10))
    screen.blit(small.render(
        "Headphones required - each zone is binauralised to its direction. "
        "Esc: back to menu", True, COLOR_TEXT_DIM), (12, 36))

    active = [z.label for z in zones if z.active]
    status = "Hearing: " + (", ".join(active) if active else "-")
    screen.blit(body.render(status, True, COLOR_TEXT), (12, SCREEN_HEIGHT - 28))


if __name__ == "__main__":
    main()
