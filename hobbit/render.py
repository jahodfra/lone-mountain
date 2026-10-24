"""Lotus-style pseudo-3D renderer (back-to-front painter's algorithm)."""

import math
import random

import pygame

from . import journey as J
from . import palette as P
from . import sprites as SP
from .consts import (W, TOP_BAR, SCENE_BOTTOM, HORIZON, SEG, DRAW_SEGS, CAM_HEIGHT,
                     PLAYER_AHEAD, CAM_DEPTH, PX, VERGE, WALL_GAP, NEAR,
                     TUNNEL_HEIGHT, LIP, WALL_HEIGHT)
from .world import height

LIM = 30000
EDGE_SPRITES = ("post", "stone_post", "torch")   # meant to sit right at the path edge


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
    def _layer(self, kind, seed, near):
        rng = random.Random(seed)
        hgt = 90
        s = SP.new(640, hgt)
        ph = [rng.uniform(0, math.tau) for _ in range(8)]
        col = P.HAZE_NEAR if near else P.HAZE_FAR
        heights = []
        for x in range(640):
            u = x / 640.0 * math.tau
            if kind == "hills":
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
                        s.set_at((x, y), P.HAZE_NEAR2)
            elif kind in ("mountains", "cliffs") and h > 40:
                snow = top + max(2, (h - 40) // 2)
                for y in range(top, min(snow, hgt)):
                    if y < snow - 1 or (x + y) % 2:
                        s.set_at((x, y), P.HAZE_FAR_SNOW)
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
            col = P.FAR_LAND2 if y < 30 else P.HAZE_NEAR2
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
        r = self.bg_cache.get(region.key)
        if r is None:
            r = (self._layer(region.bg_far, region.index * 13 + 1, False),
                 self._layer(region.bg_near, region.index * 13 + 7, True))
            self.bg_cache[region.key] = r
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
        far, near = self.layers(st.region)
        fy = HORIZON - far.get_height()
        f.blit(far, (-bgx, fy))
        f.blit(far, (640 - bgx, fy))
        self.draw_lonely_mountain(st)
        nbgx = int(st.bg_offset * 1.3) % 640
        ny = HORIZON - near.get_height() + 1
        f.blit(near, (-nbgx, ny))
        f.blit(near, (640 - nbgx, ny))
        # far land below the horizon (seen past crests and down into gorges)
        vx = int(st.bg_offset * 1.6) % 640
        f.blit(self.valley, (-vx, HORIZON))
        f.blit(self.valley, (640 - vx, HORIZON))
        if st.region.gloom >= 0.3:
            f.blit(self.canopy, (-bgx, TOP_BAR))
            f.blit(self.canopy, (640 - bgx, TOP_BAR))
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
        if st.direction > 0 and 1470 <= km < 1530:
            sm = self.S["smaug"]
            a = st.t * 0.11
            x = 160 + 140 * math.sin(a)
            y = 22 + 10 * math.sin(st.t * 0.23)
            img = sm.frame(0, st.t)
            if math.cos(a) > 0:
                img = SP.flip(img)
            f.blit(img, (int(x) - 24, int(y)))

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
        cx = 160 + 70 * math.sin(st.bg_offset / 400.0)
        base = HORIZON
        top = base - h
        if d < 30:      # close up: the textured mountain
            img = self.scaled(self.S["lonely_mountain"].variants[0], h)
            self.f.blit(img, (int(cx - img.get_width() * 152 / 312), int(base - img.get_height())))
            return
        col = P.HAZE_FAR
        pts = [(cx - h * 1.9, base), (cx - h * 0.9, base - h * 0.45), (cx - h * 0.35, top + h * 0.12),
               (cx, top), (cx + h * 0.3, top + h * 0.1), (cx + h * 0.8, base - h * 0.5), (cx + h * 2.0, base)]
        pygame.draw.polygon(self.f, col, [(_c(x), _c(y)) for x, y in pts])

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
        cam_y = st.cam_y
        poly = pygame.draw.polygon
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
            stripe = (seg.i // 2) % 2
            vstripe = seg.i % 2
            y0, y1 = b0.gy, b1.gy
            if seg.cliffs and not clipped:
                self.draw_skirt(seg, b0, cam_y)
            if any(seg.cap_back):
                self.draw_caps(seg, seg.cap_back, b1, cam_y)
            visible = y1 < y0 and y1 < SCENE_BOTTOM
            if visible:
                grass = gset + (P.G_A if stripe else P.G_B)
                iy0, iy1 = _c(y0), _c(y1)
                for side, stype in ((-1, seg.left), (1, seg.right)):
                    e0, e1 = self.edge(b0, side, VERGE), self.edge(b1, side, VERGE)
                    if stype in ("grass", "wall"):
                        far_edge = side * LIM
                        poly(f, grass, [(_c(e0), iy0), (far_edge, iy0), (far_edge, iy1), (_c(e1), iy1)])
                    elif stype == "water":
                        far_edge = side * LIM
                        wave = (seg.i + int(st.t * 1.5)) % 4 == 0
                        poly(f, P.WATER_L if wave else P.WATER_D,
                             [(_c(e0), iy0), (far_edge, iy0), (far_edge, iy1), (_c(e1), iy1)])
                        bk0, bk1 = self.edge(b0, side, VERGE + 0.35), self.edge(b1, side, VERGE + 0.35)
                        poly(f, P.BROWN_L if stripe else P.TAN,
                             [(_c(e0), iy0), (_c(bk0), iy0), (_c(bk1), iy1), (_c(e1), iy1)])
                    elif stype == "gorge":
                        # rock lip, then the cliff top sloping away into the gorge
                        lip = VERGE + LIP
                        l0, l1 = self.edge(b0, side, lip), self.edge(b1, side, lip)
                        poly(f, P.ROCK_L if stripe else P.ROCK_M,
                             [(_c(e0), iy0), (_c(l0), iy0), (_c(l1), iy1), (_c(e1), iy1)])
                        o0, o1 = self.edge(b0, side, lip + 1.4), self.edge(b1, side, lip + 1.4)
                        d0, d1 = self.ly(b0, -3.0, cam_y), self.ly(b1, -3.0, cam_y)
                        poly(f, P.ROCK_M if stripe else P.ROCK_D,
                             [(_c(l0), iy0), (_c(o0), _c(d0)), (_c(o1), _c(d1)), (_c(l1), iy1)])
                    else:   # tunnel: ground strip up to the tunnel wall
                        w0, w1 = self.edge(b0, side, VERGE + WALL_GAP), self.edge(b1, side, VERGE + WALL_GAP)
                        poly(f, grass, [(_c(e0), iy0), (_c(w0), iy0), (_c(w1), iy1), (_c(e1), iy1)])
                # path
                p0, p1 = b0.s * b0.h * PX, b1.s * b1.h * PX
                if seg.path == "stone":
                    pc = P.GREY_L if stripe else P.GREY_M
                elif seg.path == "planks":
                    pc = P.BROWN_L if vstripe else P.BROWN_M
                elif seg.path == "ford":
                    pc = P.WATER_L if (seg.i + int(st.t * 2)) % 3 else P.WHITE
                else:
                    pc = gset + (P.P_A if stripe else P.P_B)
                poly(f, pc, [(_c(b0.cx - p0), iy0), (_c(b0.cx + p0), iy0),
                             (_c(b1.cx + p1), iy1), (_c(b1.cx - p1), iy1)])
                vc = gset + (P.V_A if vstripe else P.V_B)
                for side in (-1, 1):
                    poly(f, vc, [(_c(b0.cx + side * p0), iy0), (_c(self.edge(b0, side, VERGE)), iy0),
                                 (_c(self.edge(b1, side, VERGE)), iy1), (_c(b1.cx + side * p1), iy1)])
            # walls and tunnel
            if seg.left in ("wall", "tunnel") or seg.right in ("wall", "tunnel"):
                self.draw_walls(st, seg, b0, b1, cam_y, stripe)
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

    def draw_walls(self, st, seg, b0, b1, cam_y, stripe):
        f = self.f
        tunnel = seg.tunnel
        g0, g1 = b0.gy, b1.gy
        if tunnel:
            t0, t1 = self.ly(b0, TUNNEL_HEIGHT, cam_y), self.ly(b1, TUNNEL_HEIGHT, cam_y)
        band = (seg.i // 3) % 2
        # one rock colour for cliff walls: alternating bands look like fence pickets far away
        face = (P.BROWN_D if band else P.ROCK_D) if tunnel else P.ROCK_M
        snowy = seg.region.key == "misty"
        gap = VERGE + WALL_GAP
        for k, (side, stype) in enumerate(((-1, seg.left), (1, seg.right))):
            if stype not in ("wall", "tunnel"):
                continue
            if not tunnel:
                t0, t1 = self.ly(b0, WALL_HEIGHT, cam_y), self.ly(b1, WALL_HEIGHT, cam_y)
            w0, w1 = self.edge(b0, side, gap), self.edge(b1, side, gap)
            pygame.draw.polygon(f, face, [(_c(w0), _c(g0)), (_c(w0), _c(t0)), (_c(w1), _c(t1)), (_c(w1), _c(g1))])
            if not tunnel:
                if seg.i % 7 == 0 and b0.zrel < 80:      # seams only close by (far they look like a fence)
                    pygame.draw.line(f, P.ROCK_D, (_c(w0), _c(g0)), (_c(w0), _c(t0)))
                lip = P.SNOW if snowy else P.ROCK_L
                d0 = max(1, int(b0.s * 0.5 * PX))
                pygame.draw.polygon(f, lip, [(_c(w0), _c(t0)), (_c(w0), _c(t0 + d0)),
                                             (_c(w1), _c(t1 + d0)), (_c(w1), _c(t1))])
        if tunnel:
            l0, r0 = self.edge(b0, -1, gap), self.edge(b0, 1, gap)
            l1, r1 = self.edge(b1, -1, gap), self.edge(b1, 1, gap)
            pygame.draw.polygon(f, P.GREY_D if band else P.BLACK,
                                [(_c(l0), _c(t0)), (_c(r0), _c(t0)), (_c(r1), _c(t1)), (_c(l1), _c(t1))])
            if seg.i % 5 == 0:       # goblin pit-props
                bw = max(1, int(b0.s * 0.35 * PX))
                f.fill(P.BROWN_M, (_c(l0), _c(t0), bw, _c(g0 - t0)))
                f.fill(P.BROWN_M, (_c(r0 - bw), _c(t0), bw, _c(g0 - t0)))
                f.fill(P.BROWN_M, (_c(l0), _c(t0), _c(r0 - l0), bw))

    def draw_skirt(self, seg, b, cam_y):
        """Rock under the path down to the valley floor, so a path seen across a
        gorge stands on a cliff instead of hanging in the air."""
        pts = []
        for side, stype in ((-1, seg.left), (1, seg.right)):
            if stype == "gorge":
                pts.append((side * (seg.half + VERGE + LIP + 1.4), -3.0))
            else:
                pts.append((side * 3000.0, 0.0))
        (xl, hl), (xr, hr) = pts
        scr = [(self.lx(b, xl), self.ly(b, hl, cam_y)), (self.lx(b, xr), self.ly(b, hr, cam_y)),
               (self.lx(b, xr), self.ly(b, -250, cam_y)), (self.lx(b, xl), self.ly(b, -250, cam_y))]
        # far away the rock fades into the valley haze (no hard edge where drawing ends)
        col = P.ROCK_D if b.zrel < 200 else P.FAR_LAND2
        pygame.draw.polygon(self.f, col, [(_c(x), _c(y)) for x, y in scr])

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
            # a darker crease where the face meets the wall
            pygame.draw.line(self.f, P.BLACK, scr[0], scr[1])

    # mountain outline (lateral m from the path centre, height m), one side
    ROCK_FACE = [(0, 48), (12, 46), (30, 40), (55, 52), (110, 72), (400, 115), (3000, 170), (3000, -250)]

    def draw_face(self, seg, b, cam_y):
        """Mountain side or forest edge filling the view up to the screen edges."""
        f = self.f
        for side in (-1, 1):
            if seg.face == "tunnel":
                wo = seg.half + VERGE + WALL_GAP
                pts = [(wo, 0), (wo, TUNNEL_HEIGHT), (0, TUNNEL_HEIGHT + 1.5)] + self.ROCK_FACE + [(wo + 3, -40)]
                body, rim = P.ROCK_D, P.ROCK_M
            elif seg.face == "rock":
                o = seg.face_open
                pts = [(o, 0), (o, 30), (o + 15, 50), (o + 60, 75)] + self.ROCK_FACE[4:] + [(o + 3, -40)]
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
            for i, p in enumerate(self.rain[:110]):
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
        self.t = 0.0
        self.hour = 10.8
        self.weather = "clear"
        self.bolt = None


def camera_y(cam_z):
    route = J.route_pos(cam_z + PLAYER_AHEAD)[0]
    return height(route) + CAM_HEIGHT
