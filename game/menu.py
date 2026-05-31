"""The setup screen shown when the game launches.

Everything is mouse-driven so that someone who has never used a computer game
(or code) can build their world by clicking:

  * pick a shape / size / speed / motion / sound with the ``<`` and ``>`` arrows,
  * click "Add zone" to drop it into the list on the right,
  * set how big the listener's hearing circle is,
  * click "Start" to play.

The menu returns a :class:`MenuResult` (the chosen zone specs + listener radius)
or ``None`` if the player closed the window / pressed Esc.
"""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from .config import (COLOR_ACCENT, COLOR_BG, COLOR_BUTTON, COLOR_BUTTON_HOVER,
                     COLOR_BUTTON_TEXT, COLOR_PANEL, COLOR_TEXT, COLOR_TEXT_DIM,
                     FPS, LISTENER_RADIUS, SCREEN_HEIGHT, SCREEN_WIDTH,
                     user_sounds_dir)
from .setup import MOTIONS, SHAPES, SIZES, SPEEDS, SoundCatalog, ZoneSpec

LISTENER_SIZES = ["small", "medium", "large"]


@dataclass
class MenuResult:
    specs: list[ZoneSpec]
    listener_radius: float


def run_menu(screen: pygame.Surface, clock: pygame.time.Clock,
             fonts: dict, catalog: SoundCatalog) -> MenuResult | None:
    title_font = fonts["title"]
    head_font = fonts["head"]
    body_font = fonts["body"]
    small_font = fonts["small"]

    idx = {"shape": 0, "size": 1, "speed": 1, "motion": 1, "sound": 0}
    listener_idx = 1
    specs: list[ZoneSpec] = []

    running = True
    while running:
        clicks: list[tuple[int, int]] = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicks.append(event.pos)
        mouse = pygame.mouse.get_pos()

        def hit(rect: pygame.Rect) -> bool:
            return any(rect.collidepoint(c) for c in clicks)

        def text(s, font, color, x, y, center=False):
            surf = font.render(s, True, color)
            rect = surf.get_rect()
            if center:
                rect.center = (x, y)
            else:
                rect.topleft = (x, y)
            screen.blit(surf, rect)
            return rect

        def button(rect, label, enabled=True, accent=False, font=body_font):
            hover = rect.collidepoint(mouse) and enabled
            if not enabled:
                color = (40, 42, 52)
            elif accent:
                color = (110, 220, 180) if hover else COLOR_ACCENT
            else:
                color = COLOR_BUTTON_HOVER if hover else COLOR_BUTTON
            pygame.draw.rect(screen, color, rect, border_radius=8)
            tcol = (20, 24, 28) if accent else COLOR_BUTTON_TEXT
            if not enabled:
                tcol = COLOR_TEXT_DIM
            text(label, font, tcol, rect.centerx, rect.centery, center=True)
            return enabled and hit(rect)

        def spinner(label, key, options, y):
            text(label, body_font, COLOR_TEXT_DIM, 60, y + 8)
            left = pygame.Rect(210, y, 34, 34)
            box = pygame.Rect(250, y, 170, 34)
            right = pygame.Rect(426, y, 34, 34)
            pygame.draw.rect(screen, (20, 22, 30), box, border_radius=8)
            text(options[idx[key]], body_font, COLOR_TEXT,
                 box.centerx, box.centery, center=True)
            if button(left, "<"):
                idx[key] = (idx[key] - 1) % len(options)
            if button(right, ">"):
                idx[key] = (idx[key] + 1) % len(options)

        screen.fill(COLOR_BG)

        # Panels
        left_panel = pygame.Rect(30, 96, 480, 540)
        right_panel = pygame.Rect(530, 96, 440, 540)
        pygame.draw.rect(screen, COLOR_PANEL, left_panel, border_radius=12)
        pygame.draw.rect(screen, COLOR_PANEL, right_panel, border_radius=12)

        # Header
        text("Binaural Sound Zones", title_font, COLOR_TEXT, SCREEN_WIDTH // 2, 32,
             center=True)
        text("Build your world, then press Start. Use headphones!",
             small_font, COLOR_TEXT_DIM, SCREEN_WIDTH // 2, 66, center=True)

        # Left panel: configure a new zone
        text("Create a sound zone", head_font, COLOR_ACCENT, 60, 110)
        sound_names = catalog.names()
        if idx["sound"] >= len(sound_names):
            idx["sound"] = 0
        spinner("Shape", "shape", SHAPES, 158)
        spinner("Size", "size", SIZES, 200)
        spinner("Speed", "speed", SPEEDS, 242)
        spinner("Motion", "motion", MOTIONS, 284)
        spinner("Sound", "sound", sound_names, 326)

        if button(pygame.Rect(60, 380, 400, 44), "Add this zone", accent=True):
            specs.append(ZoneSpec(
                shape=SHAPES[idx["shape"]],
                size=SIZES[idx["size"]],
                speed=SPEEDS[idx["speed"]],
                motion=MOTIONS[idx["motion"]],
                sound=sound_names[idx["sound"]],
            ))

        if button(pygame.Rect(60, 432, 195, 36), "Refresh sounds"):
            catalog.refresh()
        text(f"Your .wav folder: {user_sounds_dir()}", small_font,
             COLOR_TEXT_DIM, 60, 478)
        text("(drop .wav files there, then Refresh)", small_font,
             COLOR_TEXT_DIM, 60, 498)

        # Listener size
        text("Listener hearing range", head_font, COLOR_ACCENT, 60, 540)
        text("Size", body_font, COLOR_TEXT_DIM, 60, 586)
        l_left = pygame.Rect(210, 578, 34, 34)
        l_box = pygame.Rect(250, 578, 170, 34)
        l_right = pygame.Rect(426, 578, 34, 34)
        pygame.draw.rect(screen, (20, 22, 30), l_box, border_radius=8)
        text(LISTENER_SIZES[listener_idx], body_font, COLOR_TEXT,
             l_box.centerx, l_box.centery, center=True)
        if button(l_left, "<"):
            listener_idx = (listener_idx - 1) % len(LISTENER_SIZES)
        if button(l_right, ">"):
            listener_idx = (listener_idx + 1) % len(LISTENER_SIZES)

        # Right panel: list of added zones
        text(f"Your zones ({len(specs)})", head_font, COLOR_ACCENT, 560, 110)
        if not specs:
            text("No zones yet.", body_font, COLOR_TEXT_DIM, 560, 156)
            text("Pick options on the left and", small_font, COLOR_TEXT_DIM,
                 560, 188)
            text("click \"Add this zone\".", small_font, COLOR_TEXT_DIM, 560, 208)
        else:
            y = 152
            for i, spec in enumerate(specs[-12:], start=1):
                text(f"{i}. {spec.summary()}", small_font, COLOR_TEXT, 560, y)
                y += 30

        remove_enabled = len(specs) > 0
        if button(pygame.Rect(560, 540, 180, 38), "Remove last",
                  enabled=remove_enabled):
            if specs:
                specs.pop()
        if button(pygame.Rect(760, 540, 180, 38), "Clear all",
                  enabled=remove_enabled):
            specs.clear()

        # Start
        start_enabled = len(specs) > 0
        if button(pygame.Rect(SCREEN_WIDTH // 2 - 130, 648, 260, 44),
                  "Start", enabled=start_enabled, accent=True, font=head_font):
            return MenuResult(
                specs=list(specs),
                listener_radius=LISTENER_RADIUS[LISTENER_SIZES[listener_idx]],
            )
        if not start_enabled:
            text("Add at least one zone to start", small_font, COLOR_TEXT_DIM,
                 SCREEN_WIDTH // 2, 700 - 14, center=True)

        pygame.display.flip()
        clock.tick(FPS)

    return None
