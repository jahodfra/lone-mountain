"""Dashboard, banners and overlays."""

import sys

from . import font
from . import palette as P
from .consts import W, H, TOP_BAR, SCENE_BOTTOM


def hms(sec, show_sec=True):
    sec = int(sec)
    h, m, s = sec // 3600, (sec // 60) % 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if show_sec else f"{h}:{m:02d}"


def pace(kmh):
    if kmh < 0.5:
        return "--:--"
    mpk = 60.0 / kmh
    return f"{int(mpk)}:{int(round((mpk % 1) * 60)) % 60:02d}"


def top_bar(f, region_name, next_text, clock, status=None):
    f.fill(P.HUD_BG, (0, 0, W, TOP_BAR))
    font.draw(f, region_name, 3, 2, P.HUD_GREEN)
    nx = W - 3 - font.width(next_text)
    font.draw(f, next_text, nx, 2, P.HUD_WHITE)
    left_end = 3 + font.width(region_name)
    cw = font.width(clock)
    cx = (left_end + nx) // 2 - cw // 2
    if cx > left_end + 6 and cx + cw < nx - 6:
        font.draw(f, clock, cx, 2, P.HUD_LABEL)
    if status:
        font.draw(f, status, W - 3 - font.width(status), TOP_BAR + 2, P.HUD_VALUE, shadow=P.HUD_SHADOW)


def panel(f, kmh, target, session_m, total_m, session_s, total_s, kcal):
    y0 = SCENE_BOTTOM
    f.fill(P.HUD_BG, (0, y0, W, H - y0))
    f.fill(P.HUD_LINE, (0, y0, W, 1))
    for x in (80, 160, 242):
        f.fill(P.HUD_DIM, (x, y0 + 3, 1, H - y0 - 6))
    # speed
    font.draw(f, "SPEED", 4, y0 + 3, P.HUD_LABEL)
    if abs(target - kmh) > 0.05:
        font.draw(f, f">{target:.1f}", 40, y0 + 3, P.HUD_DIM)
    font.draw(f, f"{kmh:4.1f}", 0, y0 + 11, P.HUD_BIG, scale=2, shadow=P.HUD_SHADOW)
    font.draw(f, "KM/H", 53, y0 + 17, P.HUD_LABEL)
    # distance
    font.draw(f, "DIST", 85, y0 + 4, P.HUD_LABEL)
    font.draw(f, f"{session_m / 1000:7.2f}", 112, y0 + 4, P.HUD_VALUE)
    font.draw(f, "TOTAL", 85, y0 + 14, P.HUD_LABEL)
    font.draw(f, f"{total_m / 1000:7.1f}", 112, y0 + 14, P.HUD_VALUE)
    # time
    font.draw(f, "TIME", 165, y0 + 4, P.HUD_LABEL)
    font.draw(f, hms(session_s), 192, y0 + 4, P.HUD_VALUE)
    font.draw(f, "ALL", 165, y0 + 14, P.HUD_LABEL)
    font.draw(f, hms(total_s, False) + "H", 192, y0 + 14, P.HUD_VALUE)
    # pace & calories
    font.draw(f, "PACE", 247, y0 + 4, P.HUD_LABEL)
    font.draw(f, pace(kmh), 277, y0 + 4, P.HUD_VALUE)
    font.draw(f, "KCAL", 247, y0 + 14, P.HUD_LABEL)
    font.draw(f, f"{int(kcal):5d}", 277, y0 + 14, P.HUD_VALUE)


def banner(f, title, lines, y=24, blink=False):
    if title and not blink:
        scale = 2 if font.width(title, 2) <= W - 8 else 1
        font.draw_centered(f, title, W // 2, y, P.HUD_TITLE, scale=scale, shadow=P.HUD_SHADOW)
        y += 7 * scale + 5
    for ln in lines:
        font.draw_centered(f, ln, W // 2, y, P.HUD_WHITE, shadow=P.HUD_SHADOW)
        y += 10


def box(f, x, y, w, h):
    f.fill(P.HUD_SHADOW, (x + 2, y + 2, w, h))
    f.fill(P.HUD_BG, (x, y, w, h))
    f.fill(P.HUD_LINE, (x, y, w, 1))
    f.fill(P.HUD_LINE, (x, y + h - 1, w, 1))
    f.fill(P.HUD_LINE, (x, y, 1, h))
    f.fill(P.HUD_LINE, (x + w - 1, y, 1, h))


HELP = [
    ("UP / DOWN", "SPEED +/- 0.5 KM/H"),
    ("1 - 9", "SPEED IN KM/H (0 = STOP)"),
    ("SPACE", "STOP"),
    ("P", "PAUSE"),
    ("F", "FULLSCREEN ON/OFF"),
    ("H", "THIS HELP"),
    ("ESC", "SAVE AND QUIT"),
]
if sys.platform == "emscripten":        # the browser build
    HELP[-1] = ("ESC", "SAVE")
    HELP.insert(-1, ("B", "CONNECT BELT (BLUETOOTH)"))


def help_overlay(f):
    x, y, w = 40, 40, 240
    box(f, x, y, w, 20 + len(HELP) * 11)
    font.draw_centered(f, "CONTROLS", W // 2, y + 5, P.HUD_TITLE)
    for i, (k, v) in enumerate(HELP):
        font.draw(f, k, x + 8, y + 18 + i * 11, P.HUD_VALUE)
        font.draw(f, v, x + 74, y + 18 + i * 11, P.HUD_WHITE)


def title_screen(f, total_km, route_km, leg_text, journeys, blink):
    box(f, 16, 18, W - 32, 150)
    font.draw_centered(f, "THE HOBBIT", W // 2, 26, P.HUD_TITLE, scale=2, shadow=P.HUD_SHADOW)
    font.draw_centered(f, "THERE AND BACK AGAIN", W // 2, 46, P.HUD_BIG)
    font.draw_centered(f, "- A WALKING SIMULATOR -", W // 2, 58, P.HUD_LABEL)
    font.draw_centered(f, leg_text, W // 2, 78, P.HUD_GREEN)
    font.draw_centered(f, f"ROUTE POSITION {route_km:7.1f} KM", W // 2, 90, P.HUD_WHITE)
    font.draw_centered(f, f"WALKED SO FAR  {total_km:7.1f} KM", W // 2, 100, P.HUD_WHITE)
    if journeys:
        font.draw_centered(f, f"JOURNEYS COMPLETED {journeys}", W // 2, 110, P.HUD_VALUE)
    font.draw_centered(f, "UP/DOWN OR 0-9 SET SPEED - H HELP", W // 2, 128, P.HUD_LABEL)
    if not blink:
        font.draw_centered(f, "PRESS SPACE TO SET OFF", W // 2, 146, P.HUD_VALUE)
