"""The setup screen shown when the game launches.

Everything is mouse-driven so that someone who has never used a computer game
(or code) can build their world by clicking and dragging:

  * drag the Width / Height / Speed sliders to size and move each oval,
  * pick a Motion with the arrows,
  * scroll the Sound list and click the sound you want,
  * click "Add this zone" to drop it into the list on the right,
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
from .setup import (HEIGHT_RANGE, MOTIONS, ROTATION_RANGE, SPEED_RANGE,
                     WIDTH_RANGE, SoundCatalog, ZoneSpec)

LISTENER_SIZES = ["small", "medium", "large"]
ROW_H = 26


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

    vals = {"width": 120.0, "height": 120.0, "rotation": 0.0, "speed": 100.0}
    motion_idx = 1
    sound_idx = 0
    sound_scroll = 0
    listener_idx = 1
    specs: list[ZoneSpec] = []
    drag = {"slider": None}

    running = True
    while running:
        clicks: list[tuple[int, int]] = []
        wheel = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicks.append(event.pos)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                drag["slider"] = None
            if event.type == pygame.MOUSEWHEEL:
                wheel += event.y
        mouse = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()[0]
        if not pressed:
            drag["slider"] = None

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

        def slider(label, key, y, vmin, vmax, suffix=""):
            text(label, body_font, COLOR_TEXT_DIM, 60, y)
            track = pygame.Rect(210, y + 12, 190, 6)
            grab = pygame.Rect(track.x - 8, y, track.width + 16, 30)
            for c in clicks:
                if grab.collidepoint(c):
                    drag["slider"] = key
            if drag["slider"] == key and pressed:
                frac = (mouse[0] - track.x) / track.width
                frac = max(0.0, min(1.0, frac))
                vals[key] = vmin + frac * (vmax - vmin)
            frac = (vals[key] - vmin) / (vmax - vmin)
            hx = int(track.x + frac * track.width)
            pygame.draw.rect(screen, (20, 22, 30), track, border_radius=3)
            pygame.draw.rect(screen, COLOR_ACCENT,
                             pygame.Rect(track.x, track.y, hx - track.x,
                                         track.height), border_radius=3)
            pygame.draw.circle(screen, COLOR_BUTTON_TEXT, (hx, track.y + 3), 8)
            text(f"{int(vals[key])}{suffix}", small_font, COLOR_TEXT, 412, y + 2)

        def spinner(label, options, index, y, x0=60):
            text(label, body_font, COLOR_TEXT_DIM, x0, y + 6)
            left = pygame.Rect(x0 + 150, y, 34, 32)
            box = pygame.Rect(x0 + 188, y, 150, 32)
            right = pygame.Rect(x0 + 342, y, 34, 32)
            pygame.draw.rect(screen, (20, 22, 30), box, border_radius=8)
            text(options[index], body_font, COLOR_TEXT,
                 box.centerx, box.centery, center=True)
            if button(left, "<"):
                index = (index - 1) % len(options)
            if button(right, ">"):
                index = (index + 1) % len(options)
            return index

        def sound_list(rect, names, selected, scroll):
            visible = rect.height // ROW_H
            max_scroll = max(0, len(names) - visible)
            if rect.collidepoint(mouse) and wheel:
                scroll -= wheel
            scroll = max(0, min(max_scroll, scroll))

            pygame.draw.rect(screen, (20, 22, 30), rect, border_radius=8)
            pygame.draw.rect(screen, (60, 66, 86), rect, 1, border_radius=8)
            for i in range(visible):
                ni = scroll + i
                if ni >= len(names):
                    break
                row = pygame.Rect(rect.x + 3, rect.y + 3 + i * ROW_H,
                                  rect.width - 6, ROW_H - 2)
                if ni == selected:
                    pygame.draw.rect(screen, COLOR_ACCENT, row, border_radius=5)
                    tcol = (20, 24, 28)
                elif row.collidepoint(mouse):
                    pygame.draw.rect(screen, COLOR_BUTTON_HOVER, row,
                                     border_radius=5)
                    tcol = COLOR_BUTTON_TEXT
                else:
                    tcol = COLOR_TEXT
                text(names[ni], body_font, tcol, row.x + 8, row.y + 3)
                if hit(row):
                    selected = ni

            # Scroll up / down buttons next to the list.
            up = pygame.Rect(rect.right + 8, rect.y, 34, 34)
            down = pygame.Rect(rect.right + 8, rect.bottom - 34, 34, 34)
            if button(up, "^", enabled=scroll > 0):
                scroll = max(0, scroll - 1)
            if button(down, "v", enabled=scroll < max_scroll):
                scroll = min(max_scroll, scroll + 1)
            return selected, scroll

        screen.fill(COLOR_BG)

        left_panel = pygame.Rect(30, 96, 480, 540)
        right_panel = pygame.Rect(530, 96, 440, 540)
        pygame.draw.rect(screen, COLOR_PANEL, left_panel, border_radius=12)
        pygame.draw.rect(screen, COLOR_PANEL, right_panel, border_radius=12)

        text("Binaural Sound Zones", title_font, COLOR_TEXT, SCREEN_WIDTH // 2, 32,
             center=True)
        text("Build your world, then press Start. Use headphones!",
             small_font, COLOR_TEXT_DIM, SCREEN_WIDTH // 2, 66, center=True)

        # Left panel: configure a new zone
        text("Create a sound zone (oval)", head_font, COLOR_ACCENT, 60, 106)
        sound_names = catalog.names()
        if sound_idx >= len(sound_names):
            sound_idx = 0

        slider("Width", "width", 138, *WIDTH_RANGE, suffix=" px")
        slider("Height", "height", 170, *HEIGHT_RANGE, suffix=" px")
        slider("Rotation", "rotation", 202, *ROTATION_RANGE, suffix=" deg")
        slider("Speed", "speed", 234, *SPEED_RANGE, suffix=" px/s")
        motion_idx = spinner("Motion", MOTIONS, motion_idx, 266)

        text("Sound (scroll & click)", body_font, COLOR_TEXT_DIM, 60, 304)
        sound_idx, sound_scroll = sound_list(
            pygame.Rect(60, 326, 384, 132), sound_names, sound_idx, sound_scroll)

        if button(pygame.Rect(60, 464, 388, 40), "Add this zone", accent=True):
            specs.append(ZoneSpec(
                width=round(vals["width"]),
                height=round(vals["height"]),
                angle=round(vals["rotation"]),
                speed=round(vals["speed"]),
                motion=MOTIONS[motion_idx],
                sound=sound_names[sound_idx],
            ))

        if button(pygame.Rect(60, 512, 180, 30), "Refresh sounds"):
            catalog.refresh()
        text(f"Sounds folder: {user_sounds_dir()}", small_font,
             COLOR_TEXT_DIM, 60, 550)
        text("(drop .wav or .mp3 files there, then Refresh)", small_font,
             COLOR_TEXT_DIM, 60, 568)

        # Right panel: listener size + the list of added zones
        text("Listener hearing range", head_font, COLOR_ACCENT, 560, 108)
        listener_idx = spinner("Size", LISTENER_SIZES, listener_idx, 138, x0=560)

        text(f"Your zones ({len(specs)})", head_font, COLOR_ACCENT, 560, 190)
        if not specs:
            text("No zones yet. Set the options", small_font, COLOR_TEXT_DIM,
                 560, 230)
            text("on the left and click", small_font, COLOR_TEXT_DIM, 560, 250)
            text("\"Add this zone\".", small_font, COLOR_TEXT_DIM, 560, 270)
        else:
            y = 226
            for i, spec in enumerate(specs[-11:], start=1):
                text(f"{i}. {spec.summary()}", small_font, COLOR_TEXT, 560, y)
                y += 28

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
