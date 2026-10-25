"""Lotus-style pseudo-3D renderer (back-to-front painter's algorithm)."""

import math
import random

import pygame

from . import journey as J
from . import palette as P
from . import sprites as SP
from .consts import (W, TOP_BAR, SCENE_BOTTOM, HORIZON, SEG, DRAW_SEGS, CAM_HEIGHT,
                     PLAYER_AHEAD, CAM_DEPTH, PX, VERGE, WALL_GAP, NEAR,
                     LIP, WALL_HEIGHT)
from .world import height

LIM = 30000
EDGE_SPRITES = ("post", "stone_post", "torch")   # meant to sit right at the path edge
MASK_KEY = 255           # spare palette index, used as a colorkey when dithering layers together
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
FORDS = ("ford", "blackford")
HALL_BEYOND = 8.0     # m of Erebor's hall drawn past the turning point
SKIRT_FADE = (120.0, 320.0)   # m: rock under a gorge path dithers away into the valley


def _c(v):
    return max(-LIM, min(LIM, int(v)))


class Boundary:
    __slots__ = ("seg", "zrel", "X", "y", "h", "s", "cx", "gy")


class Renderer:
    def __init__(self, frame, sprite_defs):
        self.f = frame
        self.S = sprite_defs
        self.scaled_cache = {}
        self.bg_cache = {}
        self.blend_cache = {}
        self.masks = {}
        self.skirt_tmp = SP.new(W, SCENE_BOTTOM)
        self.skirt_tmp.set_colorkey(MASK_KEY)
        self.backdrop = SP.new(W, SCENE_BOTTOM)
        self.backdrop.set_colorkey(None)
        rng = random.Random(42)
        self.stars = [(rng.randrange(640), rng.randrange(TOP_BAR, HORIZON - 20)) for _ in range(70)]
        self.clouds = [(rng.randrange(640), rng.randrange(TOP_BAR + 6, 52), k) for k in range(8)]
        self.rain = [[rng.uniform(0, W), rng.uniform(TOP_BAR, SCENE_BOTTOM)] for _ in range(150)]
        self.valley = self._valley()
        self.canopy = self._canopy()

    # --- helpers -----------------------------------------------------------
    def scaled(self, surf, h, flipx=False):
        h = max(1, int(h))
        if h == surf.get_height() and not flipx:
            return surf
        key = (id(surf), h, flipx)
        s = self.scaled_cache.get(key)
        if s is None:
            if len(self.scaled_cache) > 4000:
                self.scaled_cache.clear()
            w = max(1, int(round(surf.get_width() * h / surf.get_height())))
            s = pygame.transform.scale(surf, (w, h))
            if flipx:
                s = pygame.transform.flip(s, True, False)
            s.set_colorkey(P.TRANSP)
            self.scaled_cache[key] = s
        return s

    def sprite_def(self, key):
        if key.startswith("sign:"):
            return SP.sign(key[5:])
        return self.S[key]

    # --- background --------------------------------------------------------
    def _layer(self, kind, seed, near, slots):
        rng = random.Random(seed)
        hgt = 90
        s = SP.new(640, hgt)
        ph = [rng.uniform(0, math.tau) for _ in range(8)]
        far_col, near_col, near2_col = slots
        col = near_col if near else far_col
        heights = []
        for x in range(640):
            u = x / 640.0 * math.tau
            if kind in ("hills", "castle_hills"):
                base, amp = (10, 9) if near else (18, 10)
                h = base + amp * (0.5 * math.sin(2 * u + ph[0]) + 0.3 * math.sin(5 * u + ph[1])
                                  + 0.2 * math.sin(11 * u + ph[2]))
            elif kind in ("mountains", "cliffs", "mountain_far"):
                if kind == "mountain_far":
                    base, amp = 6, 8
                elif near:
                    base, amp = 16, 26
                else:
                    base, amp = 30, 34
                h = base
                for f, a, p in ((3, 0.45, ph[0]), (7, 0.3, ph[1]), (17, 0.17, ph[2]), (37, 0.08, ph[3])):
                    h += amp * a * (1 - abs(math.sin(f * u / 2 + p))) * 1.6 - amp * a * 0.5
            elif kind == "forest":
                base, amp = (14, 5) if near else (20, 6)
                h = base + amp * math.sin(3 * u + ph[0]) + 4 * abs(((x * 7) % 9) - 4.5) / 4.5 \
                    + 3 * math.sin(13 * u + ph[1])
            else:  # flat
                h = 3 + 1.5 * math.sin(4 * u + ph[0])
            heights.append(max(1, min(hgt - 1, int(h))))
        for x, h in enumerate(heights):
            top = hgt - h
            pygame.draw.line(s, col, (x, top), (x, hgt - 1))
            if near:
                for y in range(top + 3, hgt):
                    if (x + y) % 2 or y > top + 8:
                        s.set_at((x, y), near2_col)
            elif kind in ("mountains", "cliffs") and h > 40:
                snow = top + max(2, (h - 40) // 2)
                for y in range(top, min(snow, hgt)):
                    if y < snow - 1 or (x + y) % 2:
                        s.set_at((x, y), P.HAZE_FAR_SNOW)
        if kind == "castle_hills":
            # "old castles with an evil look" on the tops of some hills
            for x in range(6, 634):
                if heights[x] >= max(heights[x - 6:x + 7]) and rng.random() < 0.5:
                    w, th = rng.randint(3, 5), rng.randint(5, 9)
                    top = hgt - heights[x] - th
                    s.fill(col, (x - w // 2, top, w, th + 1))
                    for cx in range(x - w // 2, x - w // 2 + w, 2):
                        s.set_at((cx, top - 1), col)
        if kind == "cliffs" and near:
            # Rivendell: streams falling from notches in the valley walls down to its floor
            last = -99
            for x in range(8, 632):
                h = heights[x]
                if x - last > 40 and 9 < h <= min(heights[x - 8:x + 9]):
                    last = x
                    for y in range(hgt - h + 1, hgt):
                        s.set_at((x, y), P.HAZE_FAR_SNOW)
                        if (y // 2) % 2:
                            s.set_at((x + 1, y), P.HAZE_FAR_SNOW)
                    for y in range(hgt - 3, hgt):       # mist where it lands
                        for dx in range(-2, 4):
                            if (x + dx + y) % 2:
                                s.set_at((x + dx, y), P.HAZE_FAR_SNOW)
        return s

    def _valley(self):
        """Valley floor seen from above: fades darker towards the viewer, with
        patches of wood and rock that grow with closeness (scrolls with the view)."""
        rng = random.Random(9)
        h = SCENE_BOTTOM - HORIZON
        s = SP.new(640, h)
        s.set_colorkey(None)
        bayer = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
        for y in range(h):
            t = min(1.0, max(0.0, (y - 2) / 60.0)) * 16
            for x in range(640):
                s.set_at((x, y), P.FAR_LAND2 if bayer[y % 4][x % 4] < t else P.FAR_LAND)
        for _ in range(140):
            y = int(h * rng.random() ** 0.8)
            x = rng.randrange(640)
            size = 0.8 + y / 22.0
            rx, ry = size * rng.uniform(1.5, 3.0), max(0.6, size * 0.4)
            col = P.FAR_LAND2 if y < 30 else P.FAR_LAND
            for yy in range(int(y - ry), int(y + ry) + 1):
                for xx in range(int(x - rx), int(x + rx) + 1):
                    if 0 <= yy < h and ((xx - x) / rx) ** 2 + ((yy - y) / ry) ** 2 <= 1 and (xx + yy) % 2 == 0:
                        s.set_at((xx % 640, yy), col)
        return s

    def _canopy(self):
        rng = random.Random(5)
        s = SP.new(640, 70)
        for x in range(640):
            u = x / 640 * math.tau
            edge = int(44 + 12 * math.sin(3 * u) + 6 * math.sin(11 * u + 1) + rng.randint(-3, 3))
            for y in range(edge):
                s.set_at((x, y), P.BLACK if (x + y) % 2 or y < edge - 8 else P.GREEN_D)
            if rng.random() < 0.12:
                pygame.draw.line(s, P.GREEN_D, (x, edge), (x, edge + rng.randint(4, 30)))
        return s

    def layers(self, region):
        key = (region.key, region.bg_far, region.bg_near)
        r = self.bg_cache.get(key)
        if r is None:
            slots = P.HAZE_SETS[region.index % 2]
            r = (self._layer(region.bg_far, region.index * 13 + 1, False, slots),
                 self._layer(region.bg_near, region.index * 13 + 7, True, slots))
            self.bg_cache[key] = r
        return r

    def _mask(self, level):
        """MASK_KEY where the Bayer threshold is >= level, transparent elsewhere."""
        m = self.masks.get(level)
        if m is None:
            tile = SP.new(4, 4)
            for y in range(4):
                for x in range(4):
                    if BAYER[y][x] >= level:
                        tile.set_at((x, y), MASK_KEY)
            m = SP.new(640, SCENE_BOTTOM + 4)
            for y in range(0, SCENE_BOTTOM + 4, 4):
                for x in range(0, 640, 4):
                    m.blit(tile, (x, y))
            self.masks[level] = m
        return m

    def blended_layers(self, earlier, later, share):
        """Background layers dithered between two neighbouring regions (share of `later`)."""
        level = int(round(share * 16))
        if level <= 0:
            return self.layers(earlier)
        if level >= 16:
            return self.layers(later)
        key = (earlier.key, earlier.bg_far, later.key, later.bg_far, level)
        r = self.blend_cache.get(key)
        if r is None:
            if len(self.blend_cache) > 64:
                self.blend_cache.clear()
            out = []
            for a, b in zip(self.layers(earlier), self.layers(later)):
                comp = a.copy()
                over = b.copy()
                over.set_colorkey(None)
                over.blit(self._mask(level), (0, 0))
                over.set_colorkey(MASK_KEY)
                comp.blit(over, (0, 0))
                comp.set_colorkey(P.TRANSP)
                out.append(comp)
            r = self.blend_cache[key] = tuple(out)
        return r

    def draw_background(self, st):
        f = self.f
        band_h = HORIZON / P.SKY_BANDS
        for b in range(P.SKY_BANDS):
            y0 = int(b * band_h)
            f.fill(P.SKY0 + b, (0, y0, W, int((b + 1) * band_h) - y0 + 1))
        bgx = int(st.bg_offset) % 640
        # stars (only visible at night through the palette)
        night = st.hour < 6.0 or st.hour > 19.0
        for sx, sy in (self.stars if night else ()):
            x = (sx - bgx) % 640
            if x < W:
                f.set_at((x, sy), P.STAR)
        # sun & moon
        hour = st.hour
        if 5.5 <= hour <= 19.5:
            t = (hour - 5.5) / 14.0
            x = int((80 + t * 480 - bgx) % 640)
            y = int(HORIZON - 6 - math.sin(t * math.pi) * 62)
            if x < W + 8:
                pygame.draw.circle(f, P.SUN, (x, y), 6)
        else:
            t = ((hour - 19.5) % 24) / 10.0
            x = int((380 + t * 480 - bgx) % 640)
            y = int(HORIZON - 6 - math.sin(t * math.pi) * 58)
            if x < W + 8:
                pygame.draw.circle(f, P.MOON, (x, y), 5)
                pygame.draw.circle(f, P.SKY0 + 4, (x + 3, y - 1), 4)
        # clouds
        clouds = self.S["clouds"].variants
        n = {"clear": 3, "cloudy": 6}.get(st.weather, 8)
        for cx, cy, k in self.clouds[:n]:
            x = int((cx - bgx * 0.6 + st.t * 2.0) % 700) - 60
            f.blit(clouds[k], (x, cy))
        if st.border:
            far, near = self.blended_layers(*st.border)
        else:
            far, near = self.layers(st.region)
        fy = HORIZON - far.get_height()
        f.blit(far, (-bgx, fy))
        f.blit(far, (640 - bgx, fy))
        self.draw_lonely_mountain(st)
        self.draw_home_hill(st)
        nbgx = int(st.bg_offset * 1.3) % 640
        ny = HORIZON - near.get_height() + 1
        f.blit(near, (-nbgx, ny))
        f.blit(near, (640 - nbgx, ny))
        # far land below the horizon (seen past crests and down into gorges)
        vx = int(st.bg_offset * 1.6) % 640
        f.blit(self.valley, (-vx, HORIZON))
        f.blit(self.valley, (640 - vx, HORIZON))
        # the forest roof closes over the sky as the gloom deepens
        k = min(1.0, max(0.0, (st.gloom - 0.1) / 0.2))
        if k > 0:
            cy = TOP_BAR - int((1 - k) * self.canopy.get_height())
            f.blit(self.canopy, (-bgx, cy))
            f.blit(self.canopy, (640 - bgx, cy))
        # birds and dragons
        km = st.route / 1000.0
        if 813 <= km <= 845:
            eagle = self.S["eagle"]
            for k in range(3):
                a = st.t * 0.2 + k * 2.1
                x = 160 + 120 * math.sin(a)
                y = 26 + 12 * math.sin(st.t * 0.37 + k)
                img = eagle.frame(0, st.t + k)
                if math.cos(a) < 0:
                    img = SP.flip(img)
                f.blit(img, (int(x) - 10, int(y)))
        # Smaug only leaves the Mountain in the dark; by day it smokes
        if st.direction > 0 and 1470 <= km < 1530 and st.night > 0.3:
            sm = self.S["smaug"]
            a = st.t * 0.11
            x = 160 + 140 * math.sin(a)
            y = 22 + 10 * math.sin(st.t * 0.23)
            img = sm.frame(0, st.t)
            face = -1
            if math.cos(a) > 0:
                img = SP.flip(img)
                face = 1
            f.blit(img, (int(x) - 24, int(y)))
            if int(st.t * 0.7) % 3 == 0:       # a burst of fire now and then
                hx, hy = int(x) + face * 22, int(y) + 10
                for k in range(14):
                    px = hx + face * k
                    py = hy + int(k * 0.5) + (k * 7) % 3 - 1
                    f.set_at((px, py), P.FLAME2 if k < 5 else P.FLAME)
                    if k > 4 and k % 2:
                        f.set_at((px, py + 1), P.FLAME)

    def draw_lonely_mountain(self, st):
        if st.direction < 0:
            return
        d = (J.LEG_M - st.route) / 1000.0
        if d > 280:
            return
        if d > 80:
            h = 6 + 30 * (280 - d) / 200
        else:
            h = 36 + 84 * (1 - d / 80) ** 1.6
        cx = 160 + st.aim
        base = HORIZON
        top = base - h
        if d < 30:      # close up: the textured mountain
            img = self.scaled(self.S["lonely_mountain"].variants[0], h)
            self.f.blit(img, (int(cx - img.get_width() * 152 / 312), int(base - img.get_height())))
            if st.night <= 0.3:
                self.draw_smoke(st, cx, h)
            return
        col = P.MOUNTAIN
        pts = [(cx - h * 1.9, base), (cx - h * 0.9, base - h * 0.45), (cx - h * 0.35, top + h * 0.12),
               (cx, top), (cx + h * 0.3, top + h * 0.1), (cx + h * 0.8, base - h * 0.5), (cx + h * 2.0, base)]
        pygame.draw.polygon(self.f, col, [(_c(x), _c(y)) for x, y in pts])
        if st.night <= 0.3 and d < 60:
            self.draw_smoke(st, cx, h)

    def draw_smoke(self, st, cx, h):
        """While Smaug lives, smoke and steam drift out of the Front Gate by day."""
        s = max(0.4, h / 60.0)
        for k in range(10):
            r = (1.5 + k * 0.9) * s
            x = cx + (k * 2.0 + 2 * math.sin(st.t * 0.5 + k)) * s
            y = HORIZON - (3 + k * 4.5) * s
            for py in range(int(y - r * 0.7), int(y + r * 0.7) + 1):
                for px in range(int(x - r), int(x + r) + 1):
                    inside = ((px - x) / r) ** 2 + ((py - y) / (r * 0.7)) ** 2 <= 1
                    # thinning out as it rises
                    if inside and (k < 4 or (px + py + k) % 2) and TOP_BAR <= py < HORIZON and 0 <= px < W:
                        self.f.set_at((px, py), P.CLOUD_SH)

    def draw_home_hill(self, st):
        """On the way back: Bilbo's own Hill rises ahead over the last km, Bag End's windows in it."""
        if st.direction > 0 or st.route > 6000:
            return
        d = st.route / 1000.0
        h = 6 + 16 * (1 - d / 6) ** 1.5
        cx = 160 + st.aim
        pts = [(cx - h * 3.2, HORIZON), (cx - h * 1.6, HORIZON - h * 0.6), (cx - h * 0.5, HORIZON - h),
               (cx + h * 0.6, HORIZON - h * 0.95), (cx + h * 1.8, HORIZON - h * 0.45), (cx + h * 3.4, HORIZON)]
        pygame.draw.polygon(self.f, P.GREEN_M, [(_c(x), _c(y)) for x, y in pts])
        pygame.draw.lines(self.f, P.GREEN_L, False, [(_c(x), _c(y)) for x, y in pts[1:-1]])
        r = max(1, int(h / 9))
        dy = HORIZON - int(h * 0.45)
        pygame.draw.circle(self.f, P.GREEN_D, (int(cx), dy), r)
        for wx in (-3, 3, 6):
            self.f.set_at((int(cx + wx * r), dy), P.WINDOW)

    # --- road ----------------------------------------------------------------
    def project(self, st, world):
        base_i = int(st.cam_z // SEG)
        seg0 = world.segment(base_i)
        r = (base_i + 1) * SEG - st.cam_z
        X = 0.5 * seg0.k * r * r
        slope = seg0.k * r
        # the segment the camera stands in starts behind it; draw_world clips it
        back = Boundary()
        back.seg = seg0
        back.zrel = seg0.z - st.cam_z
        back.X, back.y, back.h = 0.0, seg0.y, seg0.half
        back.s, back.cx, back.gy = 0.0, 160.0, 0.0
        pts = [back]
        self.dead_end = False
        for n in range(DRAW_SEGS + 1):
            seg = world.segment(base_i + 1 + n)
            b = Boundary()
            b.seg = seg
            b.zrel = seg.z - st.cam_z
            b.X = X
            b.y = seg.y
            b.h = seg.half
            b.s = CAM_DEPTH / b.zrel
            b.cx = 160 + b.s * X * PX
            b.gy = HORIZON - b.s * (seg.y - st.cam_y) * PX
            pts.append(b)
            if seg.dir != seg0.dir and seg0.dir > 0 and seg.route <= J.LEG_M - HALL_BEYOND:
                # inside Erebor: the way back starts here and is not drawn ahead; the hall
                # goes on a little past the turn so Bilbo, walking ahead, stays in it
                self.dead_end = True
                break
            X += slope * SEG + 0.5 * seg.k * SEG * SEG
            slope += seg.k * SEG
        world.trim(base_i - 10)
        return pts

    @staticmethod
    def lx(b, lat):
        return b.cx + lat * b.s * PX

    @staticmethod
    def ly(b, h, cam_y):
        return HORIZON - b.s * (b.y + h - cam_y) * PX

    @staticmethod
    def edge(b, side, extra=0.0):
        """Screen x of a line running parallel to the path, `extra` m beyond its edge."""
        return b.cx + side * (b.h + extra) * b.s * PX

    @staticmethod
    def clip(b0, b1, cam_y):
        """Boundary on the near plane, between b0 (behind it) and b1 (in front)."""
        t = (NEAR - b0.zrel) / (b1.zrel - b0.zrel)
        b = Boundary()
        b.seg = b0.seg
        b.zrel = NEAR
        b.X = b0.X + (b1.X - b0.X) * t
        b.y = b0.y + (b1.y - b0.y) * t
        b.h = b0.h + (b1.h - b0.h) * t
        b.s = CAM_DEPTH / NEAR
        b.cx = 160 + b.s * b.X * PX
        b.gy = HORIZON - b.s * (b.y - cam_y) * PX
        return b

    def draw_world(self, st, world, characters):
        f = self.f
        pts = self.project(st, world)
        reach = self.skirt_reach(pts, st.cam_y)
        self.backdrop.blit(f, (0, 0))       # sky, hills and valley floor: what far rock fades into
        cam_y = st.cam_y
        poly = pygame.draw.polygon
        if self.dead_end and len(pts) > 1:      # the back wall of the hall inside the Gate
            b = pts[-1]
            l, r = self.edge(b, -1, VERGE + b.seg.gap[0]), self.edge(b, 1, VERGE + b.seg.gap[1])
            top = self.ly(b, b.seg.roof, cam_y)
            poly(f, P.BLACK, [(_c(l), _c(top)), (_c(r), _c(top)), (_c(r), _c(b.gy)), (_c(l), _c(b.gy))])
        # characters sorted far to near, keyed by segment slot
        slots = {}
        for ch in characters:
            n = int((ch["zrel"] - pts[0].zrel) // SEG)
            if 0 <= n < len(pts) - 1:
                slots.setdefault(n, []).append(ch)
        for n in range(len(pts) - 2, -1, -1):
            b0, b1 = pts[n], pts[n + 1]
            seg = b0.seg
            if b1.zrel <= NEAR:
                continue
            clipped = b0.zrel < NEAR
            if clipped:
                b0 = self.clip(b0, b1, cam_y)
            gset = P.GROUND_SET[seg.region.index % 2]
            avg_grass, avg_path, avg_verge = P.GROUND_AVG[seg.region.index % 2]
            stripe = (seg.i // 2) % 2
            vstripe = seg.i % 2
            y0, y1 = b0.gy, b1.gy
            # far away a stripe gets thinner than ~2 px: draw it in one (average) colour, no moire
            far1 = y0 - y1 < 2.0        # stripes that change every segment
            far2 = y0 - y1 < 1.0        # stripes that change every 2 segments
            far3 = y0 - y1 < 0.67       # every 3 segments (tunnel bands)
            if seg.cliffs and not clipped:
                self.draw_skirt(seg, b0, cam_y, reach[n])
            if any(seg.cap_back):
                self.draw_caps(seg, seg.cap_back, b1, cam_y)
            visible = y1 < y0 and y1 < SCENE_BOTTOM
            if visible:
                grass = avg_grass if far2 else gset + (P.G_A if stripe else P.G_B)
                iy0, iy1 = _c(y0), _c(y1)
                for k, (side, stype) in enumerate(((-1, seg.left), (1, seg.right))):
                    e0, e1 = self.edge(b0, side, VERGE), self.edge(b1, side, VERGE)
                    if stype in ("grass", "wall"):
                        far_edge = side * LIM
                        poly(f, grass, [(_c(e0), iy0), (far_edge, iy0), (far_edge, iy1), (_c(e1), iy1)])
                    elif stype in ("water", "blackwater"):
                        far_edge = side * LIM
                        wave = (seg.i + int(st.t * 1.5)) % 4 == 0 and not far1
                        if stype == "water":
                            wc = P.WATER_L if wave else P.WATER_D
                        else:
                            wc = P.BLUE_D if wave else P.BLACK
                        poly(f, wc,
                             [(_c(e0), iy0), (far_edge, iy0), (far_edge, iy1), (_c(e1), iy1)])
                        if seg.path not in FORDS:   # banks under a bridge; a ford runs through the water
                            bk0, bk1 = self.edge(b0, side, VERGE + 0.35), self.edge(b1, side, VERGE + 0.35)
                            poly(f, P.BROWN_L if stripe or far2 else P.TAN,
                                 [(_c(e0), iy0), (_c(bk0), iy0), (_c(bk1), iy1), (_c(e1), iy1)])
                    elif stype == "gorge":
                        # rock lip, then the cliff top sloping away into the gorge
                        lip = VERGE + LIP
                        l0, l1 = self.edge(b0, side, lip), self.edge(b1, side, lip)
                        poly(f, P.ROCK_L if stripe or far2 else P.ROCK_M,
                             [(_c(e0), iy0), (_c(l0), iy0), (_c(l1), iy1), (_c(e1), iy1)])
                        o0, o1 = self.edge(b0, side, lip + 1.4), self.edge(b1, side, lip + 1.4)
                        d0, d1 = self.ly(b0, -3.0, cam_y), self.ly(b1, -3.0, cam_y)
                        poly(f, P.ROCK_M if stripe or far2 else P.ROCK_D,
                             [(_c(l0), iy0), (_c(o0), _c(d0)), (_c(o1), _c(d1)), (_c(l1), iy1)])
                    else:   # tunnel: ground strip up to the tunnel wall (or Gollum's dark water)
                        w0 = self.edge(b0, side, VERGE + b0.seg.gap[k])
                        w1 = self.edge(b1, side, VERGE + b1.seg.gap[k])
                        floor = grass
                        if seg.path == "lake" and seg.gap[k] > WALL_GAP:
                            floor = P.WATER_D if (seg.i + int(st.t * 1.5)) % 4 == 0 and not far1 else P.BLUE_D
                        poly(f, floor, [(_c(e0), iy0), (_c(w0), iy0), (_c(w1), iy1), (_c(e1), iy1)])
                # path
                p0, p1 = b0.s * b0.h * PX, b1.s * b1.h * PX
                if seg.path == "stone":
                    pc = P.GREY_L if stripe and not far2 else P.GREY_M
                elif seg.path == "planks":
                    pc = P.BROWN_L if vstripe and not far1 else P.BROWN_M
                elif seg.path == "ford":
                    pc = P.WATER_L if (seg.i + int(st.t * 2)) % 3 or far1 else P.WHITE
                elif seg.path == "blackford":
                    pc = P.BLACK if (seg.i + int(st.t * 2)) % 3 or far1 else P.GREY_D
                else:
                    pc = avg_path if far2 else gset + (P.P_A if stripe else P.P_B)
                poly(f, pc, [(_c(b0.cx - p0), iy0), (_c(b0.cx + p0), iy0),
                             (_c(b1.cx + p1), iy1), (_c(b1.cx - p1), iy1)])
                if seg.path == "ford":       # the river itself, not grass, along the ford
                    vc = P.WATER_D
                elif seg.path == "blackford":
                    vc = P.BLACK
                else:
                    vc = avg_verge if far1 else gset + (P.V_A if vstripe else P.V_B)
                for side in (-1, 1):
                    poly(f, vc, [(_c(b0.cx + side * p0), iy0), (_c(self.edge(b0, side, VERGE)), iy0),
                                 (_c(self.edge(b1, side, VERGE)), iy1), (_c(b1.cx + side * p1), iy1)])
            # walls and tunnel
            if seg.left in ("wall", "tunnel") or seg.right in ("wall", "tunnel"):
                self.draw_walls(st, seg, b0, b1, cam_y, stripe, far3)
            # characters inside this segment
            for ch in sorted(slots.get(n, ()), key=lambda c: -c["zrel"]):
                self.draw_character(st, ch, b0, b1, cam_y)
            if clipped:
                continue        # the segment's own sprites and face are behind the camera
            if any(seg.cap_front):
                self.draw_caps(seg, seg.cap_front, b0, cam_y)
            if seg.face:
                self.draw_face(seg, b0, cam_y)
            # scenery sprites standing at this segment
            if seg.sprites:
                for key, var, x, yoff, sc, fl in seg.sprites:
                    if key in J.NIGHT_ONLY and (st.night < 0.5 or st.direction < 0):
                        continue
                    d = self.sprite_def(key)
                    img = d.frame(var, st.t)
                    hp = b0.s * d.height * sc * PX
                    if hp < 1.0 or hp > 900:
                        continue
                    if x and key not in EDGE_SPRITES:
                        # keep the whole sprite off the path, not just its centre
                        half = d.height * sc * img.get_width() / img.get_height() / 2
                        x = math.copysign(max(abs(x), seg.half + VERGE + half), x)
                    sx = self.lx(b0, x)
                    sy = self.ly(b0, yoff, cam_y)
                    if sy - hp > SCENE_BOTTOM:
                        continue
                    im = self.scaled(img, hp, fl)
                    if -im.get_width() < sx < W + im.get_width():
                        f.blit(im, (int(sx - im.get_width() / 2), int(sy - im.get_height())))

    def draw_walls(self, st, seg, b0, b1, cam_y, stripe, far=False):
        f = self.f
        tunnel = seg.tunnel
        g0, g1 = b0.gy, b1.gy
        if tunnel:
            t0, t1 = self.ly(b0, b0.seg.roof, cam_y), self.ly(b1, b1.seg.roof, cam_y)
        band = 0 if far else (seg.i // 3) % 2
        # one rock colour for cliff walls: alternating bands look like fence pickets far away
        face = (P.BROWN_D if band else P.ROCK_D) if tunnel else P.ROCK_M
        snowy = seg.region.key == "misty"
        gap0, gap1 = b0.seg.gap, b1.seg.gap
        for k, (side, stype) in enumerate(((-1, seg.left), (1, seg.right))):
            if stype not in ("wall", "tunnel"):
                continue
            if not tunnel:
                t0, t1 = self.ly(b0, WALL_HEIGHT, cam_y), self.ly(b1, WALL_HEIGHT, cam_y)
            w0, w1 = self.edge(b0, side, VERGE + gap0[k]), self.edge(b1, side, VERGE + gap1[k])
            pygame.draw.polygon(f, face, [(_c(w0), _c(g0)), (_c(w0), _c(t0)), (_c(w1), _c(t1)), (_c(w1), _c(g1))])
            if not tunnel:
                if seg.i % 7 == 0 and b0.zrel < 80:      # seams only close by (far they look like a fence)
                    pygame.draw.line(f, P.ROCK_D, (_c(w0), _c(g0)), (_c(w0), _c(t0)))
                lip = P.SNOW if snowy else P.ROCK_L
                d0 = max(1, int(b0.s * 0.5 * PX))
                pygame.draw.polygon(f, lip, [(_c(w0), _c(t0)), (_c(w0), _c(t0 + d0)),
                                             (_c(w1), _c(t1 + d0)), (_c(w1), _c(t1))])
        if tunnel:
            l0, r0 = self.edge(b0, -1, VERGE + gap0[0]), self.edge(b0, 1, VERGE + gap0[1])
            l1, r1 = self.edge(b1, -1, VERGE + gap1[0]), self.edge(b1, 1, VERGE + gap1[1])
            pygame.draw.polygon(f, P.GREY_D if band else P.BLACK,
                                [(_c(l0), _c(t0)), (_c(r0), _c(t0)), (_c(r1), _c(t1)), (_c(l1), _c(t1))])
            if seg.i % 5 == 0 and not far and max(seg.gap) == WALL_GAP:   # goblin pit-props (they alias far away)
                bw = max(1, int(b0.s * 0.35 * PX))
                f.fill(P.BROWN_M, (_c(l0), _c(t0), bw, _c(g0 - t0)))
                f.fill(P.BROWN_M, (_c(r0 - bw), _c(t0), bw, _c(g0 - t0)))
                f.fill(P.BROWN_M, (_c(l0), _c(t0), _c(r0 - l0), bw))

    @staticmethod
    def skirt_edges(seg):
        """(lateral, height) of the skirt's top corners: the cliff foot on a gorge side,
        far away level with the path on any other."""
        return [(side * (seg.half + VERGE + LIP + 1.4), -3.0) if stype == "gorge" else (side * 3000.0, 0.0)
                for side, stype in ((-1, seg.left), (1, seg.right))]

    def skirt_reach(self, pts, cam_y):
        """For each segment slot: where (screen x, left and right) the skirt of the next
        nearer segment ends, and the screen row below which it covers everything between -
        this one's skirt is in view only beyond that."""
        reach = []
        lo, hi, cut = float(LIM), float(-LIM), LIM
        for n in range(len(pts) - 1):
            reach.append((lo, hi, cut))
            b = pts[n]
            if b.seg.cliffs and b.zrel >= NEAR:
                (xl, hl), (xr, hr) = self.skirt_edges(b.seg)
                lo, hi = self.lx(b, xl), self.lx(b, xr)
                cut = _c(max(self.ly(b, hl, cam_y), self.ly(b, hr, cam_y)))
        return reach

    def fill_uncovered(self, colour, xl, xr, yl, yr, bottom, reach):
        """Fill a quad with vertical sides (top corners (xl, yl) and (xr, yr), flat bottom)
        - but not where the nearer skirt will paint over it anyway: in a gorge every skirt
        reaches the screen bottom, and drawing each in full fills the screen ~70 times."""
        lo, hi, cut = reach
        ixl, ixr, ib = _c(xl), _c(xr), _c(bottom)
        mid = min(ib, max(cut + 1, _c(yl), _c(yr)))
        pygame.draw.polygon(self.f, colour, [(ixl, _c(yl)), (ixr, _c(yr)), (ixr, mid), (ixl, mid)])
        if mid < ib:     # the sides sticking out past the nearer skirt go all the way down
            for x0, x1 in ((ixl, min(ixr, _c(lo))), (max(ixl, _c(hi)), ixr)):
                if x1 >= x0:
                    self.f.fill(colour, (x0, mid, x1 - x0 + 1, ib - mid + 1))

    def draw_skirt(self, seg, b, cam_y, reach):
        """Rock under the path down to the valley floor, so a path seen across a
        gorge stands on a cliff instead of hanging in the air."""
        (xl, hl), (xr, hr) = self.skirt_edges(seg)
        sxl, sxr = self.lx(b, xl), self.lx(b, xr)
        scr = [(_c(sxl), _c(self.ly(b, hl, cam_y))), (_c(sxr), _c(self.ly(b, hr, cam_y))),
               (_c(sxr), _c(self.ly(b, -250, cam_y))), (_c(sxl), _c(self.ly(b, -250, cam_y)))]
        # far away the rock fades out, leaving the valley behind it (so where drawing ends
        # the valley floor simply goes on). Every skirt reaches the screen bottom, so a sudden
        # change would show as a vertical line down the valley: dither instead, but only in
        # the strip of this skirt that sticks out past the nearer ones (the rest gets covered)
        near, far = SKIRT_FADE
        level = int(max(0.0, min(1.0, (b.zrel - near) / (far - near))) * 16)
        if level < 16:
            strips = []
            if level > 0:
                xs, ys = [x for x, _ in scr], [y for _, y in scr]
                box = pygame.Rect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
                lo, hi, _ = reach
                for x0, x1 in ((sxl - 1, lo + 1), (hi - 1, sxr + 1)):
                    strip = box.clip(pygame.Rect(_c(x0), box.y, _c(x1) - _c(x0) + 1, box.h))
                    strip = strip.clip(self.f.get_rect())
                    if strip.w > 0 and strip.h > 0:
                        tmp = self.skirt_tmp
                        tmp.set_colorkey(None)
                        tmp.blit(self.backdrop, strip.topleft, strip)
                        tmp.blit(self._mask(level), strip.topleft, strip)
                        tmp.set_colorkey(MASK_KEY)
                        strips.append(strip)
            bottom = self.ly(b, -250, cam_y)
            self.fill_uncovered(P.ROCK_D, sxl, sxr, self.ly(b, hl, cam_y), self.ly(b, hr, cam_y), bottom, reach)
            # beside the path on open ground (not cliff or rock wall) the hillside goes on:
            # ground coloured, so a road dropping out of sight behind a crest meets ground,
            # like the ground beside it
            rocky = ("gorge", "wall")
            if seg.left not in rocky or seg.right not in rocky:
                edge = seg.half + VERGE
                gl = xl if seg.left not in rocky else edge
                gr = xr if seg.right not in rocky else -edge
                top = self.ly(b, 0.0, cam_y)
                self.fill_uncovered(P.GROUND_AVG[seg.region.index % 2][0], self.lx(b, gl), self.lx(b, gr),
                                    top, top, bottom, reach)
            for strip in strips:        # let the valley show through `level` of 16 pixels
                self.f.blit(self.skirt_tmp, strip.topleft, strip)

    # end face of a rock wall: the mountain it belongs to (lateral beyond the wall, height)
    CAP = [(0, -250), (0, WALL_HEIGHT), (6, WALL_HEIGHT + 6), (30, WALL_HEIGHT + 14), (90, WALL_HEIGHT + 40),
           (300, WALL_HEIGHT + 75), (3000, WALL_HEIGHT + 130), (3000, -250)]

    def draw_caps(self, seg, which, b, cam_y):
        snowy = seg.region.key == "misty"
        o = seg.half + VERGE + WALL_GAP
        for k, side in enumerate((-1, 1)):
            if not which[k]:
                continue
            scr = [(_c(self.lx(b, side * (o + x))), _c(self.ly(b, h, cam_y))) for x, h in self.CAP]
            pygame.draw.polygon(self.f, P.ROCK_D, scr)
            pygame.draw.lines(self.f, P.SNOW if snowy else P.ROCK_L, False, scr[1:-1], 2)

    # mountain outline (lateral m from the path centre, height m), one side
    ROCK_FACE = [(0, 48), (12, 46), (30, 40), (55, 52), (110, 72), (400, 115), (3000, 170), (3000, -250)]

    def draw_face(self, seg, b, cam_y):
        """Mountain side or forest edge filling the view up to the screen edges."""
        f = self.f
        for side in (-1, 1):
            if seg.face == "tunnel":
                wo = seg.half + VERGE + seg.gap[side > 0]
                pts = [(wo, 0), (wo, seg.roof), (0, seg.roof + 1.5)] + self.ROCK_FACE + [(wo + 3, -40)]
                body, rim = P.ROCK_D, P.ROCK_M
            else:   # forest edge: jagged treeline
                o = seg.face_open
                pts = [(o, 0), (o, 15)]
                x = o
                for k in range(60):
                    x += 2.5 + (k * 7) % 4
                    pts.append((x, 17 + (k * 5) % 7 if k % 2 else 22 + (k * 3) % 5))
                pts += [(3000, 22), (3000, -250), (o + 3, -40)]
                body, rim = P.GREEN_D, P.GREEN_M
            scr = [(_c(self.lx(b, side * x)), _c(self.ly(b, h, cam_y))) for x, h in pts]
            pygame.draw.polygon(f, body, scr)
            first = 3 if seg.face == "tunnel" else 1
            pygame.draw.lines(f, rim, False, scr[first:-2], 2 if seg.face != "forest" else 1)
            if seg.face == "forest":     # trunks along the bottom of the treeline
                low = [(o, -40), (o, 5), (3000, 5), (3000, -40)]
                pygame.draw.polygon(f, P.BROWN_D, [(_c(self.lx(b, side * x)), _c(self.ly(b, h, cam_y)))
                                                   for x, h in low])
                for k in range(40):
                    x = o + 1.5 + k * 3.1 + (k * 7) % 3
                    pygame.draw.line(f, P.BLACK, (_c(self.lx(b, side * x)), _c(self.ly(b, 0, cam_y))),
                                     (_c(self.lx(b, side * x)), _c(self.ly(b, 7, cam_y))))

    def draw_character(self, st, ch, b0, b1, cam_y):
        z = ch["zrel"]
        t = (z - b0.zrel) / (b1.zrel - b0.zrel)
        X = b0.X + (b1.X - b0.X) * t
        y = b0.y + (b1.y - b0.y) * t
        s = CAM_DEPTH / z
        sx = 160 + s * (X + ch["x"]) * PX
        sy = HORIZON - s * (y - cam_y) * PX + ch.get("bob", 0)
        d = self.S[ch["name"]]
        img = d.variants[ch["frame"] % len(d.variants)]
        hp = s * d.height * PX
        if abs(hp - img.get_height()) > 1.5:
            img = self.scaled(img, hp)
        self.f.blit(img, (int(sx - img.get_width() / 2), int(sy - img.get_height())))

    # --- weather -------------------------------------------------------------
    def draw_weather(self, st, dt):
        if st.region.key == "goblintown" or st.weather not in ("rain", "storm", "snow"):
            return
        f = self.f
        if st.weather == "snow":
            for i, p in enumerate(self.rain[:int(110 * st.precip)]):
                p[1] += (22 + (i % 5) * 6) * dt
                p[0] += math.sin(st.t * 0.8 + i) * 12 * dt - 6 * dt
                if p[1] > SCENE_BOTTOM:
                    p[1] = TOP_BAR
                    p[0] = random.uniform(0, W)
                p[0] %= W
                f.set_at((int(p[0]), int(p[1])), P.SNOW)
                if i % 3 == 0:
                    f.set_at((int(p[0]) + 1, int(p[1])), P.SNOW)
        else:
            n = 150 if st.weather == "storm" else 90
            if st.region.key == "mirkwood":
                n //= 3
            n = int(n * st.precip)
            for p in self.rain[:n]:
                p[1] += 240 * dt
                p[0] -= 50 * dt
                if p[1] > SCENE_BOTTOM:
                    p[1] = random.uniform(TOP_BAR, TOP_BAR + 30)
                    p[0] = random.uniform(0, W + 40)
                x, y = int(p[0]) % W, int(p[1])
                pygame.draw.line(f, P.BLUE_L, (x, y), (x - 1, y + 4))
        if st.bolt:
            pts = st.bolt
            pygame.draw.lines(f, P.WHITE, False, pts, 1)


class FrameState:
    """Everything the renderer needs for one frame."""

    def __init__(self):
        self.cam_z = 0.0
        self.cam_y = 0.0
        self.route = 0.0
        self.direction = 1
        self.region = J.REGIONS[0]
        self.bg_offset = 0.0
        self.aim = 0.0
        self.t = 0.0
        self.hour = 10.8
        self.weather = "clear"
        self.precip = 1.0       # 0..1 while rain or snow sets in
        self.night = 0.0
        self.gloom = 0.0
        self.border = None      # (earlier, later, share of later) near a region border
        self.bolt = None


def camera_y(cam_z):
    route = J.route_pos(cam_z + PLAYER_AHEAD)[0]
    return height(route) + CAM_HEIGHT
