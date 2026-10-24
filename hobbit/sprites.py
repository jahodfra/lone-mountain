"""Pixel-art sprites, generated in code on 8-bit palette surfaces.

Characters are ASCII pixel maps; scenery is drawn procedurally with
dithering (seeded, so it is identical every run).
"""

import math
import random

import pygame

from . import font
from . import palette as P


# --- helpers ---------------------------------------------------------------

def new(w, h):
    s = pygame.Surface((w, h), depth=8)
    s.set_palette(P.BASE)
    s.fill(P.TRANSP)
    s.set_colorkey(P.TRANSP)
    return s


def put(s, x, y, c):
    if 0 <= x < s.get_width() and 0 <= y < s.get_height():
        s.set_at((int(x), int(y)), c)


def dither_ellipse(s, cx, cy, rx, ry, c1, c2=None, pattern=0):
    """Filled ellipse; c2 given -> checkerboard dither of c1/c2."""
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            dx, dy = (x - cx) / max(rx, 0.5), (y - cy) / max(ry, 0.5)
            if dx * dx + dy * dy <= 1.0:
                c = c1 if c2 is None or (x + y + pattern) % 2 else c2
                put(s, x, y, c)


def dither_poly(s, pts, c1, c2):
    tmp = new(s.get_width(), s.get_height())
    pygame.draw.polygon(tmp, 1, pts)
    w, h = s.get_size()
    for y in range(h):
        for x in range(w):
            if tmp.get_at_mapped((x, y)) == 1:
                s.set_at((x, y), c1 if (x + y) % 2 else c2)


def outline(s, colour=P.BLACK):
    w, h = s.get_size()
    src = [[s.get_at_mapped((x, y)) for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if src[y][x] == P.TRANSP:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < w and 0 <= yy < h and src[yy][xx] not in (P.TRANSP, colour):
                        s.set_at((x, y), colour)
                        break
    return s


def from_ascii(rows, cmap):
    w = max(len(r) for r in rows)
    s = new(w, len(rows))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            c = cmap.get(ch, P.TRANSP)
            if c != P.TRANSP:
                s.set_at((x, y), c)
    return s


def flip(s):
    f = pygame.transform.flip(s, True, False)
    f.set_colorkey(P.TRANSP)
    return f


def recolour(s, mapping):
    out = s.copy()
    out.set_colorkey(P.TRANSP)
    arr = pygame.PixelArray(out)
    for a, b in mapping.items():
        arr.replace(a, b)
    del arr
    return out


class SpriteDef:
    def __init__(self, variants, height_m, anim_fps=0.0):
        self.variants = variants
        self.height = height_m
        self.anim_fps = anim_fps

    def frame(self, variant, t):
        if self.anim_fps:
            return self.variants[int(t * self.anim_fps) % len(self.variants)]
        return self.variants[variant % len(self.variants)]


# --- characters ------------------------------------------------------------

_BILBO_MAP = {
    'k': P.BLACK, 'h': P.BROWN_M, 'H': P.BROWN_D, 's': P.SKIN, 'S': P.BROWN_L,
    'w': P.TAN, 'r': P.RED, 'R': P.RED_D, 'b': P.BROWN_L, 'B': P.BROWN_M,
}
_BILBO_TOP = [
    "......kkkk......",
    "....kkhhhhkk....",
    "...khhHhhHhhk...",
    "..khHhhhhhhHhk..",
    "..khhhHhhHhhhk..",
    ".kskhHhhhhhHksk.",
    ".kssHhhHhhhhssk.",
    "..kkhhhhHhhhkk..",
    "....kHhhhhHk....",
    ".....kssssk.....",
    "...kkwwwwwwkk...",
    "..kwwkrrrrkwwk..",
    ".kwwwkrRrrkwwwk.",
    ".kwwkrrrrRrkwwk.",
    ".kwwkrRrrrrkwwk.",
    ".kwwkrrrRrrkwwk.",
    ".kwwkrrrrrrkwwk.",
    ".kskkRRRRRRkksk.",
    ".kssBBBBBBBBssk.",
    "..kkbbbbbbbbkk..",
]
_BILBO_STAND = [
    "...kbbbbbbbbk...",
    "...kbbbbkbbbk...",
    "...kbbbkkbbbk...",
    "...kbbbkkbbbk...",
    "...kbbbkkbbbk...",
    "...kBbbkkbbBk...",
    "...kkkkkkkkkk...",
    "....kssk.kssk...",
    "....kssk.kssk...",
    "...khhhk.khhhk..",
    "..khhhhk.khhhhk.",
    "..kSSSk...kSSSk.",
    "...kkk.....kkk..",
    "................",
]
_BILBO_STEP = [
    "...kbbbbbbbbk...",
    "...kbbbbkbbbk...",
    "...kbbbkkbbbk...",
    "...kbbbkkbbbk...",
    "...kbbbkkBbBk...",
    "...kBbbkkkkkk...",
    "...kkkkk.kssk...",
    "....kssk.khhk...",
    "....kssk.kSSSk..",
    "...khhhk..kkk...",
    "..khhhhk........",
    "..kSSSk.........",
    "...kkk..........",
    "................",
]


def _bilbo():
    stand = from_ascii(_BILBO_TOP + _BILBO_STAND, _BILBO_MAP)
    step_body = from_ascii(_BILBO_TOP + _BILBO_STEP, _BILBO_MAP)
    # step frames are 1px higher (the planted leg is straight): one spare row on top keeps the head whole
    w, h = stand.get_width(), stand.get_height() + 1
    step = new(w, h)
    step.blit(step_body, (0, 0))
    standing = new(w, h)
    standing.blit(stand, (0, 1))
    return [step, standing, flip(step), standing]


def _gandalf(step):
    s = new(20, 48)
    # cloak
    pygame.draw.polygon(s, P.GREY_M, [(5, 12), (14, 12), (17, 42), (1, 42)])
    for x0, x1 in ((7, 5), (10, 10), (12, 14)):
        pygame.draw.line(s, P.GREY_D, (x0, 16), (x1, 41))
    # hair and silver scarf
    s.fill(P.GREY_L, (5, 12, 9, 6))
    for x in range(5, 14, 2):
        put(s, x, 18, P.GREY_L)
    s.fill(P.WHITE, (6, 12, 7, 1))
    # tall pointed blue hat
    pygame.draw.polygon(s, P.BLUE_M, [(10, 0), (5, 10), (14, 10)])
    pygame.draw.polygon(s, P.BLUE_D, [(10, 0), (10, 10), (14, 10)])
    s.fill(P.BLUE_D, (2, 10, 16, 2))
    # boots: step 0 = both down, 1 = right foot lifted, 2 = left foot lifted
    # (drawn separately, not mirrored, so the staff stays in his right hand)
    for x0, lifted in ((4, step == 2), (10, step == 1)):
        if lifted:
            s.fill(P.BROWN_D, (x0, 40, 5, 3))
        else:
            s.fill(P.BLACK, (x0, 42, 5, 5))
    # staff
    pygame.draw.line(s, P.BROWN_M, (18, 5), (18, 46))
    s.fill(P.BROWN_D, (17, 3, 3, 3))
    return outline(s)


def _dwarf(hood, step, fat=False, tassel=P.GOLD, beard=P.GREY_L):
    w = 20 if fat else 16
    cx = w // 2
    s = new(w, 30)
    bw = 8 if fat else 6
    # cloak
    pygame.draw.polygon(s, hood, [(cx - bw + 1, 10), (cx + bw - 1, 10), (cx + bw + 1, 25), (cx - bw - 1, 25)])
    # beard tips peeking out at the sides
    put(s, cx - bw, 12, beard); put(s, cx - bw, 13, beard)
    put(s, cx + bw - 1, 12, beard); put(s, cx + bw - 1, 13, beard)
    # pack and bedroll
    s.fill(P.BROWN_M, (cx - 4, 12, 8, 9))
    s.fill(P.BROWN_D, (cx - 4, 15, 8, 1))
    s.fill(P.TAN, (cx - 5, 10, 10, 2))
    # hood
    pygame.draw.polygon(s, hood, [(cx, 0), (cx - 5, 9), (cx + 5, 9)])
    s.fill(hood, (cx - 5, 6, 10, 4))
    put(s, cx, 0, tassel); put(s, cx, 1, tassel)
    # boots
    for x0, lifted in ((cx - 5, step == 2), (cx + 1, step == 1)):
        if lifted:
            s.fill(P.BROWN_D, (x0, 23, 4, 3))
        else:
            s.fill(P.BROWN_D, (x0, 25, 4, 4))
    return outline(s)


COMPANY_LOOK = {
    "thorin": dict(hood=P.BLUE_L, tassel=P.WHITE),
    "balin": dict(hood=P.RED, beard=P.WHITE),
    "dwalin": dict(hood=P.GREEN_D, beard=P.BROWN_L),
    "fili": dict(hood=P.BLUE_M, beard=P.YELLOW),
    "kili": dict(hood=P.BLUE_M, beard=P.YELLOW),
    "bombur": dict(hood=P.GREEN_Y, fat=True),
}
COMPANY_HEIGHT = {"gandalf": 1.95, "bombur": 1.3}


def _company():
    out = {}
    g = [_gandalf(k) for k in range(3)]
    out["gandalf"] = [g[1], g[0], g[2], g[0]]
    for name, look in COMPANY_LOOK.items():
        d = [_dwarf(step=k, **look) for k in range(3)]
        out[name] = [d[1], d[0], d[2], d[0]]
    return out


# --- scenery ---------------------------------------------------------------

def oak(rng):
    s = new(40, 54)
    s.fill(P.BROWN_D, (17, 30, 6, 23))
    s.fill(P.BROWN_M, (18, 30, 2, 23))
    put(s, 15, 52, P.BROWN_D); put(s, 24, 52, P.BROWN_D)
    pygame.draw.line(s, P.BROWN_D, (20, 34), (11, 24), 2)
    pygame.draw.line(s, P.BROWN_D, (20, 32), (29, 22), 2)
    blobs = [(rng.randint(10, 29), rng.randint(9, 28), rng.randint(7, 11)) for _ in range(7)]
    for cx, cy, r in blobs:
        dither_ellipse(s, cx + 1, cy + 1, r, r * 0.85, P.GREEN_D)
    for cx, cy, r in blobs:
        dither_ellipse(s, cx - 1, cy - 1, r - 2, (r - 2) * 0.85, P.GREEN_M, P.GREEN_D)
    for cx, cy, r in blobs[:4]:
        dither_ellipse(s, cx - r / 3, cy - r / 3, r / 2.5, r / 3, P.GREEN_L, P.GREEN_M)
    return s


def pine(rng, snow=False):
    s = new(28, 62)
    s.fill(P.BROWN_D, (13, 50, 3, 12))
    cx = 14
    tiers = 5
    for t in range(tiers):
        top = 1 + t * 10
        bot = top + 15
        hw = 4 + t * 2.4 + rng.random()
        pygame.draw.polygon(s, P.GREEN_D, [(cx, top), (cx - hw, bot), (cx + hw, bot)])
        pygame.draw.polygon(s, P.GREEN_M, [(cx, top), (cx - hw, bot), (cx, bot)])
        if snow:
            pygame.draw.line(s, P.SNOW, (cx, top), (cx - hw * 0.8, top + 12), 2)
            put(s, cx + 2, top + 5, P.SNOW)
    return s


def mirk_tree(rng):
    s = new(48, 98)
    base = rng.randint(-2, 2)
    pygame.draw.polygon(s, P.BROWN_D, [(14 + base, 97), (34 + base, 97), (29, 26), (19, 26)])
    for x in range(16, 33, 3):
        pygame.draw.line(s, P.BLACK, (x + base // 2, 96), (x // 2 + 12, 30))
    for i in range(10):
        cx, cy = rng.randint(4, 44), rng.randint(4, 30)
        r = rng.randint(6, 11)
        dither_ellipse(s, cx, cy, r, r * 0.8, P.GREEN_D, P.BLACK, i)
    for i in range(9):
        x = rng.randint(4, 44)
        pygame.draw.line(s, P.GREEN_D, (x, 25), (x, 25 + rng.randint(6, 26)))
    return s


def dead_tree(rng):
    s = new(32, 48)
    pygame.draw.polygon(s, P.GREY_D, [(13, 47), (19, 47), (17, 14), (15, 14)])
    pygame.draw.line(s, P.BLACK, (18, 46), (17, 16))

    def branch(x, y, ang, ln, depth):
        if depth == 0 or ln < 2:
            return
        x2, y2 = x + math.cos(ang) * ln, y - math.sin(ang) * ln
        pygame.draw.line(s, P.GREY_D if depth > 1 else P.BLACK, (x, y), (x2, y2), max(1, depth))
        branch(x2, y2, ang + rng.uniform(0.3, 0.7), ln * 0.65, depth - 1)
        branch(x2, y2, ang - rng.uniform(0.3, 0.7), ln * 0.65, depth - 1)

    branch(16, 18, math.pi / 2, 11, 4)
    branch(16, 28, math.pi * 0.8, 7, 3)
    branch(16, 25, math.pi * 0.2, 7, 3)
    return s


def bush(rng):
    s = new(24, 14)
    dither_ellipse(s, 12, 9, 11, 5, P.GREEN_D)
    dither_ellipse(s, 11, 7, 8, 4, P.GREEN_M, P.GREEN_D)
    for _ in range(3):
        dither_ellipse(s, rng.randint(6, 16), rng.randint(4, 7), 2, 1.5, P.GREEN_L, P.GREEN_M)
    return s


def rock(rng, w=16, h=10):
    s = new(w, h)
    pts = []
    for i in range(9):
        a = math.pi * i / 8
        r = rng.uniform(0.75, 1.0)
        pts.append((w / 2 + math.cos(a) * w / 2 * r, h - 1 - math.sin(a) * (h - 1) * r))
    pygame.draw.polygon(s, P.ROCK_M, pts)
    pygame.draw.lines(s, P.ROCK_L, False, pts[4:], 1)
    pygame.draw.lines(s, P.ROCK_D, False, pts[:4], 1)
    s.fill(P.ROCK_D, (1, h - 1, w - 2, 1))
    return s


def flowers(rng):
    s = new(10, 6)
    for _ in range(6):
        x = rng.randint(0, 9)
        y = rng.randint(1, 3)
        pygame.draw.line(s, P.GREEN_M, (x, y), (x, 5))
        put(s, x, y, rng.choice([P.YELLOW, P.RED, P.WHITE, P.PURPLE_M]))
    return s


def grass_tuft(rng):
    s = new(8, 6)
    for x in range(1, 8, 2):
        h = rng.randint(2, 5)
        pygame.draw.line(s, rng.choice([P.GREEN_L, P.GREEN_M, P.OLIVE]), (x, 5), (x + rng.randint(-1, 1), 5 - h))
    return s


def reeds(rng):
    s = new(10, 16)
    for x in range(1, 10, 2):
        h = rng.randint(8, 15)
        pygame.draw.line(s, rng.choice([P.OLIVE, P.GREEN_Y]), (x, 15), (x, 15 - h))
        if rng.random() < 0.5:
            s.fill(P.BROWN_D, (x, 15 - h, 1, 3))
    return s


def fence():
    s = new(12, 12)
    s.fill(P.BROWN_D, (5, 0, 2, 12))
    s.fill(P.BROWN_M, (0, 3, 12, 2))
    s.fill(P.BROWN_M, (0, 7, 12, 2))
    put(s, 5, 0, P.BROWN_M)
    return s


def milestone():
    s = new(8, 10)
    dither_ellipse(s, 4, 3, 3.5, 3, P.GREY_L)
    s.fill(P.GREY_L, (1, 3, 7, 7))
    s.fill(P.GREY_M, (5, 3, 2, 7))
    s.fill(P.GREY_D, (2, 4, 3, 1))
    return s


def hobbit_hole(door, w=64, h=36, lit=True):
    s = new(w, h)
    dither_ellipse(s, w / 2, h, w / 2 - 1, h - 1, P.GREEN_D)
    dither_ellipse(s, w / 2 - 1, h, w / 2 - 3, h - 4, P.GREEN_M, P.GREEN_D)
    dither_ellipse(s, w / 2 - 6, h * 0.45, w / 4, h / 6, P.GREEN_L, P.GREEN_M)
    cx, cy, r = w // 2, h - h // 4, h // 4 + 1
    dither_ellipse(s, cx, cy, r + 2, r + 2, P.BROWN_M)
    dither_ellipse(s, cx, cy, r, r, door)
    s.fill(P.BROWN_D, (cx - r - 3, h - 2, 2 * r + 6, 2))
    s.fill(P.GOLD, (cx - 1, cy - 1, 2, 2))
    for wx in (w // 2 - r * 2 - 4, w // 2 + r * 2 + 4):
        dither_ellipse(s, wx, cy - 2, 4, 4, P.BROWN_M)
        dither_ellipse(s, wx, cy - 2, 3, 3, P.WINDOW if lit else P.BLUE_D)
        put(s, wx, cy - 2, P.BROWN_M)
    s.fill(P.GREY_M, (w * 3 // 4, 2, 3, 6))
    return s


def green_dragon():
    s = new(56, 46)
    s.fill(P.TAN, (4, 18, 48, 28))
    for x in range(4, 53, 8):
        s.fill(P.BROWN_D, (x, 18, 1, 28))
    s.fill(P.BROWN_D, (4, 30, 48, 1))
    pygame.draw.polygon(s, P.RED_D, [(1, 19), (10, 4), (46, 4), (55, 19)])
    pygame.draw.line(s, P.BROWN_D, (1, 19), (55, 19))
    s.fill(P.GREY_D, (40, 0, 4, 6))
    s.fill(P.BROWN_D, (24, 34, 8, 12))
    for x in (8, 16, 38, 46):
        s.fill(P.WINDOW, (x - 1, 22, 5, 5))
        s.fill(P.WINDOW, (x - 1, 35, 5, 5))
    # the sign of the dragon
    pygame.draw.line(s, P.BROWN_D, (52, 22), (56, 22))
    s.fill(P.GREEN_M, (51, 23, 5, 6))
    put(s, 53, 25, P.YELLOW)
    return outline(s)


def signpost(text):
    tw = font.width(text)
    w = tw + 10
    s = new(w, 30)
    s.fill(P.BROWN_M, (w // 2 - 1, 10, 3, 20))
    s.fill(P.BROWN_D, (w // 2 + 1, 10, 1, 20))
    pygame.draw.polygon(s, P.TAN, [(0, 0), (w - 5, 0), (w - 1, 5), (w - 5, 10), (0, 10)])
    pygame.draw.polygon(s, P.BROWN_D, [(0, 0), (w - 5, 0), (w - 1, 5), (w - 5, 10), (0, 10)], 1)
    font.draw(s, text, 3, 2, P.BROWN_D)
    return s


def ruin():
    s = new(44, 80)
    rng = random.Random(7)
    top = [(12, 20), (15, 10), (18, 14), (21, 4), (25, 9), (28, 16), (31, 12), (31, 80), (12, 80)]
    pygame.draw.polygon(s, P.ROCK_M, top)
    for y in range(14, 80, 4):
        for x in range(12 + (y // 4) % 2 * 3, 31, 6):
            put(s, x, y, P.ROCK_D)
    s.fill(P.ROCK_D, (26, 10, 5, 70))
    s.fill(P.BLACK, (19, 30, 2, 6))
    s.fill(P.BLACK, (23, 50, 2, 6))
    for _ in range(8):
        rx = rng.randint(2, 40)
        dither_ellipse(s, rx, 78, rng.randint(2, 5), 2, P.ROCK_M, P.ROCK_D)
    return s


def troll(rng):
    s = new(30, 36)
    lean = rng.randint(-2, 2)
    dither_ellipse(s, 15, 22, 11, 10, P.ROCK_M, P.ROCK_D)
    s.fill(P.ROCK_D, (8, 28, 5, 8))
    s.fill(P.ROCK_D, (17, 28, 5, 8))
    hx = 15 + lean
    dither_ellipse(s, hx, 9, 6, 6, P.ROCK_M)
    dither_ellipse(s, hx + 1, 12, 2, 3, P.ROCK_L)          # big nose
    put(s, hx - 2, 8, P.BLACK); put(s, hx + 3, 8, P.BLACK)
    up = rng.random() < 0.5
    pygame.draw.line(s, P.ROCK_D, (5, 16), (2, 6 if up else 30), 3)
    pygame.draw.line(s, P.ROCK_D, (25, 16), (28, 31), 3)
    for _ in range(14):
        put(s, rng.randint(6, 24), rng.randint(14, 30), P.GREEN_D)
    return outline(s)


def elf_house():
    s = new(56, 48)
    s.fill(P.GREY_L, (4, 18, 48, 30))
    s.fill(P.WHITE, (4, 18, 48, 2))
    for x in (4, 20, 35, 50):
        s.fill(P.WHITE, (x, 18, 2, 30))
    for x in (10, 26, 41):
        s.fill(P.WINDOW, (x, 26, 6, 12))
        dither_ellipse(s, x + 2.5, 26, 3, 3, P.WINDOW)
    pygame.draw.polygon(s, P.BLUE_M, [(0, 19), (14, 6), (42, 6), (56, 19)])
    pygame.draw.line(s, P.GOLD, (0, 19), (56, 19))
    s.fill(P.GREY_L, (24, 0, 8, 8))
    pygame.draw.polygon(s, P.BLUE_M, [(23, 1), (28, -4), (33, 1)])
    return s


def waterfall(frame):
    s = new(22, 90)
    for y in range(90):
        for x in range(4, 18):
            v = (y - frame * 4 + (x * 5) % 7) % 8
            put(s, x, y, P.WHITE if v < 2 else P.BLUE_L if v < 5 else P.WATER_L)
    s.fill(P.ROCK_D, (0, 0, 4, 90))
    s.fill(P.ROCK_D, (18, 0, 4, 90))
    dither_ellipse(s, 11, 86, 11, 4, P.WHITE, P.BLUE_L, frame)
    return s


def torch(frame):
    s = new(7, 15)
    s.fill(P.BROWN_D, (3, 7, 2, 8))
    pts = [(3, 0 + frame), (6, 6), (4, 8), (2, 8), (1, 5)]
    pygame.draw.polygon(s, P.FLAME, pts)
    s.fill(P.FLAME2, (3, 4, 2, 3))
    return s


def web():
    s = new(26, 26)
    c = 13
    for k in range(8):
        a = k * math.pi / 4
        pygame.draw.line(s, P.GREY_L, (c, c), (c + math.cos(a) * 12, c + math.sin(a) * 12))
    for r in (4, 8, 12):
        pts = [(c + math.cos(k * math.pi / 4) * r, c + math.sin(k * math.pi / 4) * r) for k in range(8)]
        pygame.draw.lines(s, P.GREY_M, True, pts)
    return s


def spider():
    s = new(18, 30)
    pygame.draw.line(s, P.GREY_L, (9, 0), (9, 16))
    for side in (-1, 1):
        for k in range(4):
            y = 19 + k * 2
            pygame.draw.lines(s, P.BLACK, False, [(9, y), (9 + side * 5, y - 3), (9 + side * 8, y + 3)])
    dither_ellipse(s, 9, 23, 4, 4, P.BLACK, P.GREY_D)
    dither_ellipse(s, 9, 18, 2, 2, P.BLACK)
    put(s, 8, 18, P.EYES); put(s, 10, 18, P.EYES)      # glow in the dark
    return s


def eyes():
    s = new(7, 2)
    s.fill(P.EYES, (0, 0, 2, 1))
    s.fill(P.EYES, (5, 0, 2, 1))
    return s


def gollum_eyes():
    """Two big round pale eyes, "lamp-like", out on the dark lake."""
    s = new(12, 5)
    for cx in (2, 9):
        dither_ellipse(s, cx, 2, 2.4, 2.4, P.EYES)
        put(s, cx, 2, P.BLACK)
    return s


def campfire(frame):
    """The trolls' fire of beech logs, with a mutton spit."""
    s = new(24, 16)
    pygame.draw.line(s, P.BROWN_D, (1, 15), (22, 12), 2)
    pygame.draw.line(s, P.BROWN_D, (2, 12), (22, 15), 2)
    pts = [(5, 14), (8, 6 - frame), (11, 9), (13, 2 + frame), (16, 8), (18, 5 - frame), (20, 14)]
    pygame.draw.polygon(s, P.FLAME, pts)
    pygame.draw.polygon(s, P.FLAME2, [(9, 14), (12, 8 + frame), (14, 10), (16, 14)])
    pygame.draw.line(s, P.GREY_D, (2, 4), (22, 4))
    s.fill(P.BROWN_M, (10, 3, 5, 3))
    s.fill(P.GREY_D, (1, 4, 1, 12))
    s.fill(P.GREY_D, (22, 4, 1, 12))
    return s


def beehive():
    s = new(10, 12)
    for i, (w, c) in enumerate(((3, P.GOLD), (4, P.BROWN_L), (5, P.GOLD), (5, P.BROWN_L))):
        s.fill(c, (5 - w, 1 + i * 2, w * 2, 2))
    s.fill(P.BLACK, (4, 7, 2, 2))
    s.fill(P.BROWN_D, (1, 9, 8, 1))
    s.fill(P.BROWN_D, (2, 10, 1, 2))
    s.fill(P.BROWN_D, (7, 10, 1, 2))
    return s


def beorn_hall():
    s = new(96, 44)
    s.fill(P.BROWN_M, (4, 18, 88, 26))
    for x in range(4, 92, 4):
        s.fill(P.BROWN_D, (x, 18, 1, 26))
    dither_poly(s, [(0, 20), (14, 2), (82, 2), (96, 20)], P.GOLD, P.BROWN_L)
    pygame.draw.line(s, P.BROWN_D, (0, 20), (96, 20))
    s.fill(P.BROWN_D, (42, 28, 12, 16))
    s.fill(P.BLACK, (47, 28, 1, 16))
    for x in (14, 28, 64, 78):
        s.fill(P.WINDOW, (x, 25, 5, 6))
    return outline(s)


def carrock():
    s = new(64, 60)
    pts = [(4, 59), (8, 30), (16, 14), (28, 6), (40, 8), (50, 18), (58, 34), (61, 59)]
    pygame.draw.polygon(s, P.ROCK_M, pts)
    pygame.draw.polygon(s, P.ROCK_D, [(40, 8), (50, 18), (58, 34), (61, 59), (42, 59)])
    dither_ellipse(s, 30, 9, 12, 4, P.GREEN_M, P.GREEN_D)
    for y in range(40, 58, 3):
        pygame.draw.line(s, P.ROCK_L, (10, y), (22, y - 6))
    dither_ellipse(s, 32, 59, 31, 2, P.WHITE, P.WATER_L)
    return s


def forest_gate():
    s = new(128, 96)
    rng = random.Random(3)
    for x0 in (6, 98):
        pygame.draw.polygon(s, P.BROWN_D, [(x0, 95), (x0 + 24, 95), (x0 + 19, 20), (x0 + 5, 20)])
        for x in range(x0 + 3, x0 + 22, 4):
            pygame.draw.line(s, P.BLACK, (x, 94), (x0 + 12, 26))
    for i in range(26):
        cx = rng.randint(2, 126)
        cy = rng.randint(4, 26 if 30 < cx < 98 else 34)
        r = rng.randint(7, 12)
        dither_ellipse(s, cx, cy, r, r * 0.7, P.GREEN_D, P.BLACK, i)
    for i in range(16):
        x = rng.randint(4, 124)
        pygame.draw.line(s, P.GREEN_D, (x, 28), (x, 28 + rng.randint(6, 22)))
    return s


def elf_gate():
    s = new(64, 48)
    dither_ellipse(s, 32, 48, 32, 46, P.GREEN_D, P.ROCK_D)
    s.fill(P.ROCK_L, (20, 18, 24, 30))
    dither_ellipse(s, 32, 18, 12, 10, P.ROCK_L)
    s.fill(P.GREY_M, (23, 20, 18, 28))
    dither_ellipse(s, 32, 20, 9, 7, P.GREY_M)
    s.fill(P.GREY_D, (32, 14, 1, 34))
    return s


def stilt_house(rng):
    s = new(40, 52)
    for x in (5, 17, 30):
        s.fill(P.BROWN_D, (x, 32, 3, 20))
    s.fill(P.BROWN_M, (2, 31, 36, 3))
    s.fill(P.BROWN_L, (5, 16, 30, 15))
    for x in range(5, 35, 3):
        s.fill(P.BROWN_M, (x, 16, 1, 15))
    roof = rng.choice([P.RED_D, P.BROWN_D, P.GREY_D])
    pygame.draw.polygon(s, roof, [(1, 17), (20, 3), (39, 17)])
    s.fill(P.WINDOW, (10, 20, 5, 5))
    s.fill(P.WINDOW, (26, 20, 5, 5))
    s.fill(P.BROWN_D, (18, 21, 5, 10))
    return s


def barrel():
    s = new(10, 8)
    dither_ellipse(s, 5, 4, 5, 4, P.BROWN_M)
    s.fill(P.GREY_D, (2, 0, 1, 8))
    s.fill(P.GREY_D, (7, 0, 1, 8))
    s.fill(P.WATER_L, (0, 7, 10, 1))
    return s


def stump(rng):
    s = new(12, 10)
    s.fill(P.GREY_D, (3, 2, 6, 8))
    s.fill(P.BLACK, (6, 2, 3, 8))
    pygame.draw.polygon(s, P.GREY_D, [(3, 2), (4, 0), (6, 2), (8, 0), (9, 2)])
    put(s, 2, 9, P.BLACK); put(s, 9, 9, P.BLACK)
    return s


def post():
    s = new(3, 12)
    s.fill(P.BROWN_M, (0, 0, 3, 12))
    s.fill(P.BROWN_D, (2, 0, 1, 12))
    return s


def stone_post():
    s = new(4, 8)
    s.fill(P.GREY_L, (0, 0, 4, 8))
    s.fill(P.GREY_M, (3, 0, 1, 8))
    return s


def erebor_gate():
    """The Front Gate: pillars and a carved arch round the opening into the hall.
    4 px per metre; the doorway (transparent) is the hall's 9 x 9 m, gabled like a tunnel mouth."""
    s = new(160, 110)
    dither_poly(s, [(0, 109), (10, 50), (40, 20), (80, 0), (120, 20), (150, 50), (159, 109)], P.ROCK_M, P.ROCK_D)
    rng = random.Random(11)
    for _ in range(30):
        x, y = rng.randint(10, 150), rng.randint(20, 100)
        pygame.draw.line(s, P.ROCK_D, (x, y), (x + rng.randint(-8, 8), y + rng.randint(2, 8)))
    s.fill(P.ROCK_L, (52, 56, 56, 54))
    dither_ellipse(s, 80, 58, 30, 12, P.ROCK_L)
    for x in (46, 108):
        s.fill(P.ROCK_L, (x, 50, 6, 60))
        s.fill(P.ROCK_D, (x + 4, 50, 2, 60))
    pygame.draw.polygon(s, P.TRANSP, [(62, 109), (62, 74), (80, 68), (98, 74), (98, 109)])
    return s


def lonely_mountain():
    """Erebor seen close up: lit west face, shadowed east face, ridges and gullies."""
    w, h = 312, 80
    s = new(w, h)
    pk = 152
    outline = [(0, h), (82, h - 36), (110, h - 70), (pk, 0), (176, h - 72), (214, h - 40), (w, h)]
    dither_poly(s, outline, P.ROCK_M, P.ROCK_L)
    dither_poly(s, [(pk, 0), (176, h - 72), (214, h - 40), (w, h), (190, h)], P.ROCK_D, P.ROCK_M)
    rng = random.Random(1941)
    marks = new(w, h)
    for _ in range(26):                     # gullies running down the slopes
        x = rng.randint(70, 240)
        y = rng.randint(14, 50)
        pygame.draw.line(marks, P.ROCK_D, (x, y), (x + rng.randint(-14, 14), y + rng.randint(10, 28)))
    pygame.draw.lines(marks, P.ROCK_L, False, [(pk, 0), (128, 30), (96, 60), (70, h)], 2)   # western ridge
    # only on the mountain itself, never out in the sky
    for y in range(h):
        for x in range(w):
            c = marks.get_at_mapped((x, y))
            if c != P.TRANSP and s.get_at_mapped((x, y)) != P.TRANSP:
                s.set_at((x, y), c)
    s.set_colorkey(P.TRANSP)
    return s


def bag_end():
    return hobbit_hole(P.GREEN_M, 84, 46)


def eagle(frame):
    s = new(21, 9)
    dither_ellipse(s, 10, 4, 4, 2, P.BROWN_D)
    put(s, 6, 3, P.GOLD); put(s, 5, 3, P.GOLD)
    if frame == 0:
        pygame.draw.lines(s, P.BROWN_D, False, [(9, 4), (4, 0), (0, 1)], 2)
        pygame.draw.lines(s, P.BROWN_D, False, [(11, 4), (16, 0), (20, 1)], 2)
    else:
        pygame.draw.lines(s, P.BROWN_D, False, [(9, 4), (4, 7), (0, 8)], 2)
        pygame.draw.lines(s, P.BROWN_D, False, [(11, 4), (16, 7), (20, 8)], 2)
    s.fill(P.BROWN_M, (13, 4, 3, 1))
    return s


def smaug(frame):
    s = new(48, 22)
    dither_ellipse(s, 24, 13, 10, 4, P.RED, P.RED_D)
    s.fill(P.GOLD, (17, 15, 14, 1))
    pygame.draw.lines(s, P.RED_D, False, [(15, 12), (9, 9), (4, 10)], 3)
    dither_ellipse(s, 3, 10, 3, 2, P.RED)
    put(s, 2, 9, P.YELLOW)
    pygame.draw.lines(s, P.RED_D, False, [(33, 13), (40, 15), (44, 12), (47, 14)], 2)
    if frame == 0:
        pygame.draw.polygon(s, P.RED_D, [(20, 11), (26, 0), (36, 2), (30, 11)])
        pygame.draw.lines(s, P.BLACK, False, [(20, 11), (26, 0), (36, 2)])
    else:
        pygame.draw.polygon(s, P.RED_D, [(20, 13), (26, 21), (36, 20), (30, 13)])
        pygame.draw.lines(s, P.BLACK, False, [(20, 13), (26, 21), (36, 20)])
    return s


def cloud(rng):
    w = rng.randint(30, 56)
    s = new(w, 14)
    for _ in range(5):
        cx = rng.randint(8, w - 8)
        dither_ellipse(s, cx, rng.randint(6, 8), rng.randint(6, 10), rng.randint(3, 5), P.CLOUD)
    for x in range(w):
        for y in range(9, 14):
            if s.get_at_mapped((x, y)) == P.CLOUD and (x + y) % 2:
                s.set_at((x, y), P.CLOUD_SH)
    return s


# --- registry --------------------------------------------------------------

def build():
    rng = random.Random(1937)
    S = {}
    S["oak"] = SpriteDef([oak(rng) for _ in range(4)], 9.0)
    S["pine"] = SpriteDef([pine(rng) for _ in range(3)], 12.0)
    S["pine_snow"] = SpriteDef([pine(rng, True) for _ in range(3)], 11.0)
    S["mirk_tree"] = SpriteDef([mirk_tree(rng) for _ in range(4)], 18.0)
    S["dead_tree"] = SpriteDef([dead_tree(rng) for _ in range(3)], 6.0)
    S["bush"] = SpriteDef([bush(rng) for _ in range(4)], 1.3)
    S["rock"] = SpriteDef([rock(rng) for _ in range(4)], 0.8)
    S["boulder"] = SpriteDef([rock(rng, 32, 22) for _ in range(3)], 3.0)
    S["flowers"] = SpriteDef([flowers(rng) for _ in range(4)], 0.45)
    S["grass_tuft"] = SpriteDef([grass_tuft(rng) for _ in range(4)], 0.45)
    S["reeds"] = SpriteDef([reeds(rng) for _ in range(3)], 1.4)
    S["fence"] = SpriteDef([fence()], 1.1)
    S["milestone"] = SpriteDef([milestone()], 0.8)
    S["hobbit_hole"] = SpriteDef([hobbit_hole(c) for c in (P.GREEN_D, P.RED_D, P.BLUE_M, P.YELLOW)], 5.0)
    S["bag_end"] = SpriteDef([bag_end()], 6.0)
    S["green_dragon"] = SpriteDef([green_dragon()], 9.0)
    S["ruin"] = SpriteDef([ruin()], 32.0)
    S["troll"] = SpriteDef([troll(rng) for _ in range(3)], 3.6)
    S["elf_house"] = SpriteDef([elf_house()], 10.0)
    S["waterfall"] = SpriteDef([waterfall(f) for f in range(2)], 30.0, anim_fps=6)
    S["torch"] = SpriteDef([torch(f) for f in range(2)], 0.7, anim_fps=7)
    S["web"] = SpriteDef([web()], 3.0)
    S["spider"] = SpriteDef([spider()], 2.2)
    S["eyes"] = SpriteDef([eyes()], 0.12)
    S["gollum_eyes"] = SpriteDef([gollum_eyes()], 0.45)
    S["campfire"] = SpriteDef([campfire(f) for f in range(2)], 1.4, anim_fps=5)
    S["beehive"] = SpriteDef([beehive()], 0.8)
    S["beorn_hall"] = SpriteDef([beorn_hall()], 9.0)
    S["carrock"] = SpriteDef([carrock()], 40.0)
    S["forest_gate"] = SpriteDef([forest_gate()], 22.0)
    S["elf_gate"] = SpriteDef([elf_gate()], 18.0)
    S["stilt_house"] = SpriteDef([stilt_house(rng) for _ in range(3)], 8.0)
    S["barrel"] = SpriteDef([barrel()], 0.7)
    S["stump"] = SpriteDef([stump(rng) for _ in range(2)], 0.9)
    S["post"] = SpriteDef([post()], 1.1)
    S["stone_post"] = SpriteDef([stone_post()], 0.8)
    S["erebor_gate"] = SpriteDef([erebor_gate()], 27.5)
    S["lonely_mountain"] = SpriteDef([lonely_mountain()], 0)
    S["eagle"] = SpriteDef([eagle(0), eagle(1)], 0, anim_fps=3)
    S["smaug"] = SpriteDef([smaug(0), smaug(1)], 0, anim_fps=2)
    S["clouds"] = SpriteDef([cloud(rng) for _ in range(8)], 0)
    S["bilbo"] = SpriteDef(_bilbo(), 1.06)
    for name, frames in _company().items():
        S[name] = SpriteDef(frames, COMPANY_HEIGHT.get(name, 1.35))
    return S


_sign_cache = {}


def sign(text):
    d = _sign_cache.get(text)
    if d is None:
        d = _sign_cache[text] = SpriteDef([signpost(text)], 2.6)
    return d
