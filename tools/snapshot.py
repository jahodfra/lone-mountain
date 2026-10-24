#!/usr/bin/env python3
"""Render still frames at given journey positions (for testing the art).

    python tools/snapshot.py OUT_DIR KM[:HOUR[:WEATHER]] ...
    e.g. python tools/snapshot.py shots 0.3 600:12 790:15:snow 1100:22
Use a km above 1530 for the return leg (e.g. 2000 = 1060 km on the way back).
A screenshots/*.json file (saved with the C key in the game) re-renders that exact frame.
"""

import json

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from hobbit.game import Game  # noqa: E402
from hobbit.state import load_settings  # noqa: E402


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    settings = load_settings()
    settings["speed_source"] = "keyboard"     # no "belt searching" in the top bar
    g = Game(settings, headless=True)
    g.mode = "walk"
    g.kmh = 5.0
    for spec in sys.argv[2:]:
        if spec.endswith(".json"):
            with open(spec) as fh:
                d = json.load(fh)
            g.progress.total_m, g.progress.hour, g.progress.weather = d["total_m"], d["hour"], d["weather"]
            g.t, g.bg_offset, g.phase, g.kmh = d["t"], d["bg_offset"], d["phase"], d["kmh"]
            g.dt, g.banners = 1 / 60, []
            g.draw()
            name = os.path.join(out, os.path.basename(spec)[:-5] + "_rerender.png")
            pygame.image.save(pygame.transform.scale(g.screen, (960, 600)), name)
            print(name)
            continue
        parts = spec.split(":")
        km = float(parts[0])
        g.progress.total_m = km * 1000
        g.progress.hour = float(parts[1]) if len(parts) > 1 else 12.0
        g.progress.weather = parts[2] if len(parts) > 2 else "clear"
        g.t = km
        g.phase = km * 3
        g.dt = 1 / 60
        g.banners = []
        g.draw()
        big = pygame.transform.scale(g.screen, (960, 600))
        name = os.path.join(out, spec.replace(":", "_") + ".png")
        pygame.image.save(big, name)
        print(name)


if __name__ == "__main__":
    main()
