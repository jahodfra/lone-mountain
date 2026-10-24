#!/usr/bin/env python3
"""Render frames before/at every important place of the journey.

    python tools/journey_shots.py [OUT_DIR]      (default: screenshots/journey)
Writes PNGs (4x) plus places.txt listing them.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

from hobbit import journey as J  # noqa: E402
from hobbit.game import Game  # noqa: E402
from hobbit.state import load_settings  # noqa: E402

OFFSETS = (-0.300, -0.060, 0.010)     # km relative to the place


def places():
    pts = {}
    for lm in J.LANDMARKS:
        pts.setdefault(round(lm[0], 2), lm[1])
    for r in J.REGIONS[1:]:
        pts.setdefault(round(r.start_km, 2), "START OF " + r.name)
    for f in J.FEATURES:
        pts.setdefault(round(f[0], 2), "FEATURE " + (f[4] or f[3] or f[2]))
    out, last = [], None
    for km in sorted(pts):           # merge places closer than 1 km
        if last is not None and km - last < 1.0:
            continue
        out.append((km, pts[km], 1))
        last = km
    # the way back through the mountains (mirrored scenery)
    for km, name in ((825.0, "BACK: EAGLES' EYRIE"), (812.0, "BACK: GOBLIN-TOWN EXIT"),
                     (760.0, "BACK: MISTY MOUNTAINS"), (745.0, "BACK: RIVENDELL VALE")):
        out.append((km, name, -1))
    return out


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "screenshots", "journey")
    os.makedirs(out, exist_ok=True)
    st = load_settings()
    st["speed_source"] = "keyboard"
    g = Game(st, headless=True)
    g.mode, g.kmh, g.dt = "walk", 5.0, 1 / 60
    lines = []
    for i, (km, name, direction) in enumerate(places()):
        for off in OFFSETS:
            route = km + off * direction
            if not 0 <= route <= J.ROUTE_KM:
                continue
            z = route * 1000 if direction > 0 else (2 * J.LEG_M - route * 1000)
            g.progress.total_m, g.progress.hour, g.progress.weather = z, 12.0, "clear"
            g.t, g.phase, g.banners = route, route * 3, []
            g.draw()
            fn = f"{i:02d}_{km:07.2f}_{'back_' if direction < 0 else ''}{int(off * 1000):+05d}m.png"
            pygame.image.save(pygame.transform.scale(g.screen, (1280, 800)), os.path.join(out, fn))
            lines.append(f"{fn}  route {route:8.3f} km  {name}")
    with open(os.path.join(out, "places.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
