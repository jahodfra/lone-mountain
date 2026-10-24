"""Pluggable speed sources.

The game only asks a source for `target_kmh` (and whether it is `direct`,
i.e. already a real measured speed that should not be smoothed).
"""

import pygame

from .consts import MAX_KMH

PRESETS = {n: float(n) for n in range(10)}     # digit = km/h, 0 = stop


def clamp(v):
    return max(0.0, min(MAX_KMH, round(v * 10) / 10.0))


class KeyboardSource:
    name = "KEYBOARD"
    direct = False

    def __init__(self, step=0.5):
        self.step = step
        self.target_kmh = 0.0

    @property
    def status(self):
        return "KEYS"

    def start(self):
        pass

    def stop(self):
        pass

    def handle_key(self, key):
        if key in (pygame.K_UP, pygame.K_KP_PLUS, pygame.K_PLUS, pygame.K_EQUALS):
            self.target_kmh = clamp(self.target_kmh + self.step)
        elif key in (pygame.K_DOWN, pygame.K_KP_MINUS, pygame.K_MINUS):
            self.target_kmh = clamp(self.target_kmh - self.step)
        elif key == pygame.K_SPACE:
            self.target_kmh = 0.0
        elif pygame.K_0 <= key <= pygame.K_9:
            self.target_kmh = PRESETS[key - pygame.K_0]
        elif pygame.K_KP0 <= key <= pygame.K_KP9:
            self.target_kmh = PRESETS[key - pygame.K_KP0]
        else:
            return False
        return True


def make_source(settings):
    kind = settings.get("speed_source", "keyboard")
    kb = KeyboardSource(settings.get("speed_step", 0.5))
    if kind == "ftms":
        from .ftms import FTMSSource
        return FTMSSource(settings, fallback=kb)
    return kb
