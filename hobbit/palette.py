"""Amiga-style palette.

Everything is drawn into an 8-bit surface using palette indices.  The 32
"core" colours are 12-bit (4 bits per channel) like the Amiga OCS chipset.
Indices above 32 are "copper" / dynamic slots (sky gradient, haze, the
current region's ground colours, HUD) that are recomputed every frame.
Day/night, gloom and lightning are palette swaps, never redraws.
"""


def c12(h):
    """0xRGB (4 bits per channel) -> (r, g, b)."""
    return (((h >> 8) & 15) * 17, ((h >> 4) & 15) * 17, (h & 15) * 17)


# --- core 32 colours -------------------------------------------------------
TRANSP = 0
BLACK, WHITE, GREY_D, GREY_M, GREY_L = 1, 2, 3, 4, 5
SKIN, BROWN_D, BROWN_M, BROWN_L, TAN = 6, 7, 8, 9, 10
GREEN_D, GREEN_M, GREEN_L, GREEN_Y = 11, 12, 13, 14
BLUE_D, BLUE_M, BLUE_L = 15, 16, 17
RED_D, RED, YELLOW, ORANGE = 18, 19, 20, 21
PURPLE_D, PURPLE_M = 22, 23
ROCK_D, ROCK_M, ROCK_L, SNOW = 24, 25, 26, 27
WATER_D, WATER_L, GOLD, OLIVE = 28, 29, 30, 31

CORE = {
    TRANSP: 0x000, BLACK: 0x000, WHITE: 0xFFF,
    GREY_D: 0x445, GREY_M: 0x889, GREY_L: 0xBBC,
    SKIN: 0xEB9, BROWN_D: 0x421, BROWN_M: 0x753, BROWN_L: 0xA86, TAN: 0xDCA,
    GREEN_D: 0x241, GREEN_M: 0x472, GREEN_L: 0x7A3, GREEN_Y: 0xAC6,
    BLUE_D: 0x236, BLUE_M: 0x46A, BLUE_L: 0x8BE,
    RED_D: 0x812, RED: 0xD32, YELLOW: 0xFD5, ORANGE: 0xE82,
    PURPLE_D: 0x324, PURPLE_M: 0x657,
    ROCK_D: 0x544, ROCK_M: 0x877, ROCK_L: 0xBAA, SNOW: 0xEEF,
    WATER_D: 0x247, WATER_L: 0x59C, GOLD: 0xC92, OLIVE: 0x683,
}

# --- dynamic slots ---------------------------------------------------------
SKY0 = 32                # 16 copper bands, 32..47 (top -> horizon)
SKY_BANDS = 16
STAR = 48                # sky coloured by day, white at night
WINDOW = 49              # dark glass by day, lit yellow at night
FLAME = 50               # torches, emissive
FLAME2 = 51
HAZE_FAR = 52
HAZE_FAR_SNOW = 53
HAZE_NEAR = 54
HAZE_NEAR2 = 55
FAR_LAND = 56
FAR_LAND2 = 57
# two ground sets (region parity) of 6 colours each
GROUND_SET = (58, 64)
G_A, G_B, P_A, P_B, V_A, V_B = range(6)
# per ground set: the average of each stripe pair (grass, path, verge), used far away
# where a stripe would be thinner than a pixel or two and turn into moire
GROUND_AVG = ((90, 91, 92), (93, 94, 95))
CLOUD = 70
CLOUD_SH = 71
SUN = 72
MOON = 73
EYES = 74
# a second set of background haze colours: neighbouring regions use alternate sets
# (by index parity) so their layers can be dithered together across a border
HAZE_FAR_B, HAZE_NEAR_B, HAZE_NEAR2_B = 75, 76, 77
HAZE_SETS = ((HAZE_FAR, HAZE_NEAR, HAZE_NEAR2), (HAZE_FAR_B, HAZE_NEAR_B, HAZE_NEAR2_B))
MOUNTAIN = 78            # the Lonely Mountain on the horizon
# HUD colours are never lit / tinted
HUD_BG, HUD_LINE, HUD_LABEL, HUD_VALUE, HUD_BIG, HUD_TITLE, HUD_SHADOW, HUD_WHITE, HUD_GREEN, HUD_DIM = range(80, 90)

HUD_COLOURS = {
    HUD_BG: 0x000, HUD_LINE: 0x557, HUD_LABEL: 0x99B, HUD_VALUE: 0xFD5,
    HUD_BIG: 0xF82, HUD_TITLE: 0xFE8, HUD_SHADOW: 0x102, HUD_WHITE: 0xFFF,
    HUD_GREEN: 0x8D6, HUD_DIM: 0x446,
}

EMISSIVE = {FLAME, FLAME2, EYES}


def base_palette():
    """The palette every surface carries while drawing.

    Every entry must be unique so that SDL maps 8-bit blits 1:1.
    """
    pal = []
    for i in range(256):
        if i in CORE and i != TRANSP:
            pal.append(c12(CORE[i]))
        else:
            pal.append((i, 1, 3))      # placeholder, unique
    return pal


BASE = base_palette()


# --- lighting --------------------------------------------------------------
# (hour, light rgb multiplier, sky top, sky horizon)
_KEYS = [
    (0.0, (0.34, 0.40, 0.62), 0x002, 0x124),
    (4.5, (0.34, 0.40, 0.62), 0x002, 0x124),
    (6.0, (0.85, 0.70, 0.70), 0x237, 0xF97),
    (7.5, (1.00, 1.00, 1.00), 0x26C, 0xADF),
    (17.5, (1.00, 1.00, 1.00), 0x26C, 0xADF),
    (19.3, (1.00, 0.72, 0.62), 0x214, 0xE73),
    (21.0, (0.34, 0.40, 0.62), 0x002, 0x124),
    (24.0, (0.34, 0.40, 0.62), 0x002, 0x124),
]


def _lerp(a, b, t):
    return a + (b - a) * t


def _lerp3(a, b, t):
    return (_lerp(a[0], b[0], t), _lerp(a[1], b[1], t), _lerp(a[2], b[2], t))


def _q(v):
    """Quantise a 0..255 channel to the 12-bit Amiga grid."""
    v = max(0, min(255, v))
    return int(round(v / 17.0)) * 17


def _q3(c):
    return (_q(c[0]), _q(c[1]), _q(c[2]))


def daylight(hour):
    """Return (light multiplier rgb, sky top rgb, sky horizon rgb, night 0..1)."""
    hour = (round(hour * 6) / 6.0) % 24.0      # step every 10 game minutes
    for (h0, l0, t0, z0), (h1, l1, t1, z1) in zip(_KEYS, _KEYS[1:]):
        if h0 <= hour <= h1:
            t = 0.0 if h1 == h0 else (hour - h0) / (h1 - h0)
            light = _lerp3(l0, l1, t)
            top = _lerp3(c12(t0), c12(t1), t)
            hor = _lerp3(c12(z0), c12(z1), t)
            night = max(0.0, min(1.0, (1.0 - light[0]) / 0.66))
            return light, top, hor, night
    return _KEYS[0][1], c12(_KEYS[0][2]), c12(_KEYS[0][3]), 1.0


def _mul(c, m):
    return (c[0] * m[0], c[1] * m[1], c[2] * m[2])


CAVE_LIGHT = (0.62, 0.55, 0.5)     # underground: the same at noon and at midnight


def build(hour, region, next_region, parity, gloom=0.0, overcast=0.0,
          flash=0.0, flame_phase=0.0, bg_other=None, cave=0.0):
    """Compute the 256-entry display palette for this frame.

    `bg_other` is the neighbouring region whose horizon is being blended in.
    """
    light, top, hor, night = daylight(hour)
    if cave:
        light = _lerp3(light, CAVE_LIGHT, cave)
        night = _lerp(night, 1.0, cave)      # eyes glow in the dark
    # overcast weather greys the sky and dims the land
    if overcast:
        grey = (110, 110, 125)
        top = _lerp3(top, _mul(grey, light), overcast * 0.8)
        hor = _lerp3(hor, _mul((150, 150, 160), light), overcast * 0.8)
        light = _lerp3(light, (light[0] * 0.8, light[1] * 0.8, light[2] * 0.85), overcast)
    if gloom:
        g = 1.0 - gloom
        light = (light[0] * g, light[1] * (g + 0.05), light[2] * g)
        top = _lerp3(top, (10, 25, 15), min(1.0, gloom * 1.6))
        hor = _lerp3(hor, (30, 55, 35), min(1.0, gloom * 1.6))
    light = tuple(max(0.16, x) for x in light)

    pal = list(BASE)
    for i, hexc in CORE.items():
        if i == TRANSP:
            continue
        pal[i] = _q3(_mul(c12(hexc), light))

    for b in range(SKY_BANDS):
        t = (b / (SKY_BANDS - 1)) ** 1.4
        pal[SKY0 + b] = _q3(_lerp3(top, hor, t))
    pal[STAR] = _q3(_lerp3(pal[SKY0 + 3], (225, 225, 240), night * (1 - overcast)))
    pal[WINDOW] = _q3(_lerp3(_mul(c12(0x223), light), c12(0xFD6), night))
    f = 0.5 + 0.5 * flame_phase
    pal[FLAME] = _q3(_lerp3(c12(0xE60), c12(0xFB2), f))
    pal[FLAME2] = _q3(_lerp3(c12(0xFC4), c12(0xFF8), f))
    pal[EYES] = c12(0xDE2) if night > 0.5 else _q3(_mul(c12(0x220), light))
    pal[SUN] = _q3(_lerp3(c12(0xFF9), c12(0xF95), max(0.0, 1 - light[1]) * 2))
    pal[MOON] = c12(0xDDC)
    cloud = _lerp3(_mul(c12(0xFFF), light), hor, 0.25)
    pal[CLOUD] = _q3(_lerp3(cloud, (150, 150, 160), overcast * 0.6))
    pal[CLOUD_SH] = _q3(_lerp3(_mul(c12(0xAAC), light), top, 0.3))

    # region colours: haze blends toward the horizon colour
    r = region
    for reg in (region, bg_other):
        if reg is not None:
            far, near, near2 = HAZE_SETS[reg.index % 2]
            pal[far] = _q3(_lerp3(_mul(c12(reg.bg_far_col), light), hor, 0.45))
            pal[near] = _q3(_lerp3(_mul(c12(reg.bg_near_col), light), hor, 0.2))
            pal[near2] = _q3(_lerp3(_mul(c12(reg.bg_near_col2), light), hor, 0.2))
    pal[HAZE_FAR_SNOW] = _q3(_lerp3(_mul(c12(0xEEF), light), hor, 0.3))
    pal[MOUNTAIN] = _q3(_lerp3(_mul(c12(0x667), light), hor, 0.35))
    # below the horizon the near hills/mountains continue down into a darker valley floor
    pal[FAR_LAND] = pal[HAZE_SETS[r.index % 2][2]]
    pal[FAR_LAND2] = _q3(_lerp3(_mul(c12(r.far_land[1]), light), hor, 0.12))

    for reg, par in ((region, parity), (next_region, 1 - parity)):
        base = GROUND_SET[par]
        for k, hexc in enumerate(reg.ground):
            pal[base + k] = _q3(_mul(c12(hexc), light))
        for k, avg in enumerate(GROUND_AVG[par]):
            pal[avg] = _q3(_lerp3(pal[base + 2 * k], pal[base + 2 * k + 1], 0.5))

    for i, hexc in HUD_COLOURS.items():
        pal[i] = c12(hexc)

    if flash:
        for i in range(0, 80):
            c = pal[i]
            pal[i] = _q3(_lerp3(c, (235, 235, 255), flash))
    return pal
