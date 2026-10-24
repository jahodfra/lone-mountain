"""Procedural track: every 2 m road segment is derived from its route position.

Because everything is a pure function of the route position, the same
scenery reappears in reverse on the way back from the Lonely Mountain.
"""

import math
import random

from . import journey as J
from .consts import SEG, VERGE, LIP, WALL_GAP, TUNNEL_HEIGHT


def _hash(n):
    n = (n ^ 61) ^ (n >> 16)
    n = (n + (n << 3)) & 0xFFFFFFFF
    n ^= n >> 4
    n = (n * 0x27D4EB2D) & 0xFFFFFFFF
    n ^= n >> 15
    return n


def _rand(n):
    return _hash(n & 0xFFFFFFFF) / 0xFFFFFFFF


def _vnoise(x, seed):
    """Smooth 1-D value noise in [-1, 1]."""
    i = math.floor(x)
    f = x - i
    a = _rand(i * 7919 + seed) * 2 - 1
    b = _rand((i + 1) * 7919 + seed) * 2 - 1
    t = f * f * (3 - 2 * f)
    return a + (b - a) * t


def height(route_m):
    amp = J.blended(route_m, "hills")
    d = route_m
    return amp * (0.6 * math.sin(d / 173.0 + 1.3) + 0.3 * math.sin(d / 71.0 + 0.2)
                  + 0.1 * math.sin(d / 37.0))


def curvature(route_m):
    amp = J.blended(route_m, "curves")
    n = _vnoise(route_m / 260.0, 17)
    # dead zone: leaves straight stretches between bends
    n = math.copysign(max(0.0, abs(n) - 0.25) / 0.75, n)
    return amp * n


class Segment:
    __slots__ = ("i", "z", "route", "dir", "y", "k", "region", "left", "right",
                 "path", "sprites", "tunnel", "half", "face", "face_open", "cap_front", "cap_back", "cliffs", "gap", "roof")

    def __init__(self, i):
        self.i = i
        self.z = i * SEG


class World:
    def __init__(self):
        self.cache = {}

    def segment(self, i):
        s = self.cache.get(i)
        if s is None:
            s = self._make(i)
            self.cache[i] = s
        return s

    def trim(self, below):
        if len(self.cache) > 2000:
            for k in [k for k in self.cache if k < below]:
                del self.cache[k]

    def _sides(self, region, route_m):
        block = int(route_m // 400)
        opts = region.sides
        if len(opts) == 1:
            return opts[0][0], opts[0][1]
        total = sum(o[2] for o in opts)
        r = _rand(block * 31 + region.index) * total
        for o in opts:
            r -= o[2]
            if r <= 0:
                return o[0], o[1]
        return opts[-1][0], opts[-1][1]

    def route_sides(self, route):
        """(left, right, path) facing the forward direction of the journey."""
        left, right = self._sides(J.region_at(route), route)
        path = None
        f = J.feature_at(route)
        if f:
            left, right, path = f[2] or left, f[3] or right, f[4]
        return left, right, path

    def travel_sides(self, z):
        """(left, right) as seen walking, at world distance z."""
        route, direction, _ = J.route_pos(max(0.0, z))
        left, right, _ = self.route_sides(route)
        return (right, left) if direction < 0 else (left, right)

    def _make(self, i):
        s = Segment(i)
        route, direction, _ = J.route_pos(s.z)
        s.route, s.dir = route, direction
        s.y = height(route)
        s.k = curvature(route) * direction
        region = J.region_at(route)
        s.region = region
        s.half = J.blended(route, "path_half")
        left, right, path = self.route_sides(route)
        if direction < 0:
            left, right = right, left
        s.left, s.right, s.path = left, right, path
        # ground between path edge and tunnel/rock wall, per side (wide over Gollum's lake)
        wide = J.cavern_width(route)
        s.gap = (WALL_GAP, WALL_GAP + wide) if direction > 0 else (WALL_GAP + wide, WALL_GAP)
        s.roof = TUNNEL_HEIGHT
        if left == "tunnel" and region.key in J.HALLS:
            g, s.roof = J.HALLS[region.key]
            s.gap = (g, g)
        # rock walls are the sides of mountain masses: they get an end face where they
        # start (facing the walker) and where they end (hiding what is behind them)
        prev, nxt = self.travel_sides(s.z - SEG), self.travel_sides(s.z + SEG)
        s.cap_front = tuple((left, right)[k] == "wall" and prev[k] != "wall" for k in (0, 1))
        s.cap_back = tuple((left, right)[k] == "wall" and nxt[k] != "wall" for k in (0, 1))
        s.cliffs = any("gorge" in o[:2] for o in region.sides)
        s.tunnel = left == "tunnel"
        s.sprites = self._scenery(s, region)
        # a solid face across the view where the path enters a mountain or a forest
        s.face, s.face_open = None, 0.0
        prev = J.region_at(J.route_pos(s.z - SEG)[0])
        keys = [sp[0] for sp in s.sprites]
        if s.tunnel and self.travel_sides(s.z - SEG)[0] != "tunnel":
            s.face = "tunnel"
        elif region.key in J.FOREST_REGIONS and prev.key not in J.FOREST_REGIONS:
            s.face = "forest"
            s.face_open = 11.5 if "forest_gate" in keys else s.half + VERGE + 1.2
        return s

    def _scenery(self, s, region):
        out = []
        rseg = int(s.route // SEG)
        rng = random.Random(rseg * 2654435761 % 4294967296)
        scen = region.scenery
        for side, stype in ((-1, s.left), (1, s.right)):
            if not scen or rng.random() > region.density:
                continue
            on = "wall" if stype == "tunnel" else stype
            choices = [e for e in scen if e[4] == on]
            if not choices:
                continue
            total = sum(e[1] for e in choices)
            r = rng.random() * total
            for e in choices:
                r -= e[1]
                if r <= 0:
                    break
            key, _, xmin, xmax, _, yoff = e
            if on == "wall":
                x = s.half + VERGE + s.gap[side > 0] - 0.05
            else:
                base = s.half + VERGE + (LIP if on == "gorge" else 0)
                x = base + rng.uniform(xmin, xmax)
            out.append((key, rng.randint(0, 7), side * x, yoff, rng.uniform(0.85, 1.15), rng.random() < 0.5))
        # bridge parapets / causeway posts
        if s.path in ("stone", "planks") and rseg % 2 == 0:
            key = "stone_post" if s.path == "stone" else "post"
            for side in (-1, 1):
                out.append((key, 0, side * (s.half + 0.05), 0, 1.0, False))
        # milestones every km on the East Road and in the Shire
        if region.key in ("shire", "eastroad") and int(s.route) % 1000 < SEG and s.right == "grass":
            out.append(("milestone", 0, s.half + VERGE + 0.4, 0, 1.0, False))
        # unique set pieces
        for km, key, x, yoff in J.set_pieces_between(s.route, s.route + SEG * s.dir):
            if key in J.FORWARD_ONLY and s.dir < 0:
                continue
            out.append((key, int(km * 1000), x * s.dir, yoff, 1.0, False))
        # signposts a little before each landmark (in either direction)
        before = s.route + 250.0 * s.dir
        for lm in J.landmarks_between(before, before + SEG * s.dir):
            out.append(("sign:" + lm[2], 0, -(s.half + VERGE + 1.2), 0, 1.0, False))
        return out
