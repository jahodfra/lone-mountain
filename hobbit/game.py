"""Main loop: input, simulation, rendering."""

import json
import math
import os
import random
import sys
import time

import pygame

from . import font
from . import hud
from . import journey as J
from . import palette as P
from . import sprites as SP
from .consts import W, H, HORIZON, PLAYER_AHEAD, PX, FPS, TOP_BAR
from .render import Renderer, FrameState, camera_y
from .speed import make_source
from .state import Progress
from .world import World

OVERCAST = {"clear": 0.0, "cloudy": 0.45, "rain": 0.8, "storm": 1.0, "snow": 0.7}
WEATHER_EASE_S = 20.0    # real seconds for the sky to change when the weather turns
AIM_PX = 120.0           # px: the Mountain / the Hill never get further than this off the middle


def kcal_per_min(kmh, kg):
    """ACSM walking / running equations (flat ground)."""
    if kmh < 0.3:
        return 1.0 * kg * 3.5 / 1000 * 5      # resting (standing on the belt)
    m_min = kmh * 1000 / 60
    vo2 = (0.1 * m_min if kmh < 8.0 else 0.2 * m_min) + 3.5
    return vo2 * kg / 1000 * 5


class Game:
    def __init__(self, settings, windowed=False, headless=False):
        self.settings = settings
        pygame.init()
        self.fullscreen = settings["fullscreen"] and not windowed and not headless
        if headless or sys.platform == "emscripten":    # in the browser the page scales the canvas
            self.screen = pygame.display.set_mode((W, H))
        else:
            flags = pygame.SCALED | (pygame.FULLSCREEN if self.fullscreen else 0)
            self.screen = pygame.display.set_mode((W, H), flags, vsync=1)
        pygame.display.set_caption("The Hobbit - There and Back Again")
        pygame.mouse.set_visible(not self.fullscreen)
        pygame.key.set_repeat(350, 110)
        self.frame = pygame.Surface((W, H), depth=8)
        self.frame.set_palette(P.BASE)
        self.sprites = SP.build()
        self.renderer = Renderer(self.frame, self.sprites)
        self.world = World()
        self.progress = Progress.load()
        self.source = make_source(settings)
        self.kg = float(settings["weight_kg"])
        self.clock = pygame.time.Clock()

        self.mode = "title"
        self.paused = False
        self.show_help = False
        self.kmh = 0.0
        self.session_m = 0.0
        self.session_s = 0.0
        self.kcal = 0.0
        self.phase = 0.0
        self.t = 0.0
        self.bg_offset = 0.0
        self.aim = 0.0          # px: where the road's goal (the Mountain, the Hill) is off the middle
        self.weather_clock = 0.0
        self.overcast = None    # eases toward the current weather's overcast
        self.flash = 0.0
        self.bolt = None
        self.bolt_t = 0.0
        self.banners = []       # [title, lines, seconds_left]
        self.last_save = time.time()
        self.next_quote_km = 3
        self.started = time.strftime("%Y-%m-%d %H:%M")
        self.st = FrameState()
        self.want_shot = False

    # --- banners -------------------------------------------------------------
    def say(self, title, text="", secs=7.0):
        lines = []
        for part in text.split("\n"):
            if part:
                lines += font.wrap(part, 48)
        self.banners.append([title, lines, secs])

    def landmark_banner(self, lm, direction, arriving_home=False):
        km, name, short, quote = lm
        if arriving_home:
            self.say("BAG END", "THERE AND BACK AGAIN!\nTHE JOURNEY IS COMPLETE. HOME AT LAST.", 12)
            return
        self.say(name, quote)
        if direction > 0 and km == 940.0:
            self.say("", "GANDALF LEAVES THE COMPANY AT THE EDGE OF MIRKWOOD.", 6)
        if direction > 0 and km == 1530.0:
            self.say("", "THE QUEST IS DONE. NOW BACK AGAIN, WITH GANDALF.", 8)

    # --- simulation ----------------------------------------------------------
    def update(self, dt, dt_real):
        self.t += dt
        src = self.source
        target = src.target_kmh
        if src.direct:
            self.kmh = target
        else:
            step = 3.0 * dt
            self.kmh += max(-step, min(step, target - self.kmh))
            if abs(self.kmh - target) < 0.01:
                self.kmh = target

        if self.paused or self.mode != "walk":
            return
        prog = self.progress
        dz = self.kmh / 3.6 * dt_real
        before = prog.total_m
        prog.total_m += dz
        # hidden test key: hold Tab to travel 10x faster (extra distance is not
        # counted as walked today, it only moves you along the route)
        if pygame.key.get_pressed()[pygame.K_TAB]:
            prog.total_m += dz * 9
        dz_route = prog.total_m - before
        self.session_m += dz
        self.session_s += dt_real
        prog.total_s += dt_real
        self.kcal += kcal_per_min(self.kmh, self.kg) * dt_real / 60
        prog.hour = (prog.hour + dt_real * 24.0 / (self.settings["day_length_minutes"] * 60.0)) % 24.0

        # bend of the road turns the background
        seg = self.world.segment(int(prog.total_m // 2.0))
        turn = seg.k * dz_route * PX
        self.bg_offset += turn
        # the goal on the horizon (the Mountain, the Hill) turns with the background, so it
        # stands still against the hills on a straight; in bends it also drifts back towards
        # the middle, the further out the more, so the winding road keeps leading to it
        self.aim -= turn + self.aim * abs(turn) / AIM_PX

        # walking cadence (steps per second) -> animation phase
        if self.kmh > 0.2:
            cadence = 1.3 + 0.09 * self.kmh if self.kmh < 7.5 else 2.3 + 0.06 * self.kmh
            self.phase += cadence * 2 * dt

        # landmarks
        r0, d0, j0 = J.route_pos(before)
        r1, d1, j1 = J.route_pos(prog.total_m)
        if d0 == d1:
            for lm in J.landmarks_between(r0, r1):
                self.landmark_banner(lm, d1)
        elif d0 > 0:        # reached the Lonely Mountain, turning for home
            self.landmark_banner(J.LANDMARKS[-1], 1)
        else:               # back at Bag End
            self.landmark_banner(J.LANDMARKS[0], -1, arriving_home=True)

        km_before, km_now = int(self.session_m - dz) // 1000, int(self.session_m) // 1000
        if km_now > km_before:
            self.say("", f"{km_now} KM WALKED TODAY", 4)
            if km_now >= self.next_quote_km:
                self.next_quote_km = km_now + 3
                self.say("", random.choice(J.QUOTES), 8)

        # weather changes every 6 game hours
        self.weather_clock += dt_real * 24.0 / (self.settings["day_length_minutes"] * 60.0)
        region = J.view(J.region_at(r1), d1)
        forced = J.forced_weather(r1, d1)
        if forced:
            prog.weather = forced
        elif self.weather_clock > 6.0 or prog.weather not in region.weather:
            self.weather_clock = 0.0
            ws = list(region.weather.items())
            x = random.random() * sum(w for _, w in ws)
            for name, w in ws:
                x -= w
                if x <= 0:
                    prog.weather = name
                    break

        target = OVERCAST.get(prog.weather, 0.0)
        if self.overcast is None:
            self.overcast = target
        self.overcast += (target - self.overcast) * min(1.0, dt_real / WEATHER_EASE_S * 3)

        if prog.weather == "storm" and self.overcast > 0.85 and random.random() < dt / 9.0:
            self.flash = 1.0
            x = random.randint(40, 280)
            pts, y = [(x, TOP_BAR)], TOP_BAR
            while y < HORIZON - 10:
                y += random.randint(5, 12)
                x += random.randint(-8, 8)
                pts.append((x, y))
            self.bolt, self.bolt_t = pts, 0.2

        if time.time() - self.last_save > 15:
            self.save()

    def jump_km(self, km):
        """Test helper: move along the journey without walking (session stats unchanged)."""
        self.progress.total_m = max(0.0, self.progress.total_m + km * 1000)
        route, direction, _ = J.route_pos(self.progress.total_m)
        self.banners = []       # messages about the place we just left no longer apply
        self.aim = 0.0
        self.banners.insert(0, [f"JUMP {km:+d} KM", [f"{J.region_at(route).name} - ROUTE KM {route / 1000:.1f}"
                                                     + ("" if direction > 0 else " (BACK)")], 2.0])

    def screenshot(self):
        """Save the current frame (native + 4x) and the state needed to re-render it."""
        from .state import ROOT
        folder = os.path.join(ROOT, "screenshots")
        os.makedirs(folder, exist_ok=True)
        route, direction, _ = J.route_pos(self.progress.total_m)
        base = os.path.join(folder, time.strftime("%Y%m%d-%H%M%S") + f"_km{route / 1000:.3f}")
        pygame.image.save(self.screen, base + ".png")
        pygame.image.save(pygame.transform.scale(self.screen, (W * 4, H * 4)), base + "_4x.png")
        state = {"total_m": self.progress.total_m, "route_km": route / 1000, "direction": direction,
                 "region": J.region_at(route).name, "hour": self.progress.hour,
                 "weather": self.progress.weather, "t": self.t, "bg_offset": self.bg_offset,
                 "aim": self.aim,
                 "phase": self.phase, "kmh": self.kmh}
        with open(base + ".json", "w") as fh:
            json.dump(state, fh, indent=1)
        self.say("", "SCREENSHOT SAVED", 1.5)

    def save(self):
        self.progress.save(self.session_record())
        self.last_save = time.time()

    def session_record(self):
        return {"start": self.started, "m": round(self.session_m, 1), "s": round(self.session_s),
                "kcal": round(self.kcal)}

    # --- drawing -------------------------------------------------------------
    def characters(self, direction, route):
        frame = int(self.phase) % 4 if self.kmh > 0.2 else 1
        bob = -1 if (frame in (0, 2) and self.kmh >= 7.5) else 0
        chars = [{"name": "bilbo", "zrel": PLAYER_AHEAD, "x": 0.0, "frame": frame, "bob": bob}]
        names = J.company(route, direction)
        if "gandalf" in names:          # Gandalf leads from the front
            names.remove("gandalf")
            names.append("gandalf")
        for i, name in enumerate(names):
            zrel = PLAYER_AHEAD + 4.0 + i * 3.2
            # on narrow tracks the company closes up into single file
            half = self.world.segment(int((self.progress.total_m + zrel) // 2.0)).half
            spread = max(0.0, min(1.0, (half - 0.85) / 0.4))
            sway = math.sin(self.t * 0.3 + i * 1.7)
            lat = spread * ((0.55 if i % 2 else -0.55) + 0.25 * sway) + (1 - spread) * 0.12 * sway
            f = int(self.phase + i * 1.3) % 4 if self.kmh > 0.2 else 1
            chars.append({"name": name, "zrel": zrel, "x": lat, "frame": f})
        return chars

    def draw(self):
        prog = self.progress
        st = self.st
        st.cam_z = prog.total_m
        st.cam_y = camera_y(st.cam_z)
        st.route, st.direction, journeys = J.route_pos(st.cam_z)
        st.region = J.view(J.region_at(st.route), st.direction)
        b = J.border(st.route)
        st.border = (J.view(b[0], st.direction), J.view(b[1], st.direction), b[2]) if b else None
        cave = J.blended(st.route, "cave", width=40.0)
        st.night = 1.0 if cave > 0.5 else P.daylight(prog.hour)[3]
        st.gloom = J.blended(st.route, "gloom")
        st.bg_offset = self.bg_offset
        st.aim = self.aim
        st.t = self.t
        st.hour = prog.hour
        st.weather = prog.weather
        target = OVERCAST.get(prog.weather, 0.0)
        overcast = target if self.overcast is None else self.overcast
        st.precip = min(1.0, overcast / target) if target else 0.0
        st.bolt = self.bolt if self.bolt_t > 0 else None

        r = self.renderer
        r.draw_background(st)
        r.draw_world(st, self.world, self.characters(st.direction, st.route))
        r.draw_weather(st, self.dt)

        lm, dist = J.next_landmark(st.route, st.direction)
        if st.direction < 0 and lm[0] == 0.0:
            nxt = f"HOME {dist:.1f} KM"
        else:
            nxt = f"{lm[2]} {dist:.1f} KM"
        hh = int(prog.hour)
        mm = int((prog.hour % 1) * 60)
        status = self.source.status if self.source.name != "KEYBOARD" else None
        hud.top_bar(self.frame, st.region.name, nxt, f"{hh:02d}:{mm:02d}", status)
        hud.panel(self.frame, self.kmh, self.source.target_kmh, self.session_m, prog.total_m,
                  self.session_s, prog.total_s, self.kcal)

        blink = int(self.t * 3) % 2 == 0
        if self.mode == "title":
            leg = "THERE..." if st.direction > 0 else "...AND BACK AGAIN"
            hud.title_screen(self.frame, prog.total_m / 1000, st.route / 1000, leg, journeys, blink)
        elif self.banners:
            b = self.banners[0]
            hud.banner(self.frame, b[0], b[1])
        if self.paused:
            hud.banner(self.frame, "PAUSED", ["PRESS P TO CONTINUE"], y=70)
        if self.show_help:
            hud.help_overlay(self.frame)
        if self.settings.get("show_fps"):
            font.draw(self.frame, f"{self.clock.get_fps():.0f}", 3, TOP_BAR + 2, P.HUD_WHITE)

        nxt_region = J.region_at(max(0.0, min(J.LEG_M - 1, st.route + st.direction * 470)))
        bg_other = None
        if st.border:
            bg_other = st.border[1] if st.border[0].key == st.region.key else st.border[0]
        pal = P.build(prog.hour, st.region, nxt_region, st.region.index % 2, gloom=st.gloom,
                      overcast=overcast, flash=self.flash,
                      flame_phase=math.sin(self.t * 11) * math.sin(self.t * 7.3),
                      bg_other=bg_other, cave=cave)
        self.frame.set_palette(pal)
        self.screen.blit(self.frame, (0, 0))
        self.frame.set_palette(P.BASE)

    # --- events --------------------------------------------------------------
    def handle(self, ev):
        if ev.type == pygame.QUIT:
            return False
        if ev.type != pygame.KEYDOWN:
            return True
        k = ev.key
        if k == pygame.K_ESCAPE:
            if self.show_help:
                self.show_help = False
                return True
            if sys.platform == "emscripten":    # a web page cannot quit: just save
                self.save()
                return True
            return False
        # hidden test commands: [ / ] = back / ahead 1 km, with Shift 10 km
        # (physical key positions, so they work on any keyboard layout; also PageUp/PageDown)
        sc = getattr(ev, "scancode", None)
        jump = 0
        if sc == pygame.KSCAN_RIGHTBRACKET or k == pygame.K_PAGEUP:
            jump = 1
        elif sc == pygame.KSCAN_LEFTBRACKET or k == pygame.K_PAGEDOWN:
            jump = -1
        if jump:
            self.jump_km(jump * (10 if ev.mod & pygame.KMOD_SHIFT else 1))
            return True
        if k in (pygame.K_c, pygame.K_F12):     # hidden: screenshot
            self.want_shot = True
            return True
        if k == pygame.K_f:
            if sys.platform == "emscripten":    # the page itself handles F (hobbit/web.py)
                return True
            pygame.display.toggle_fullscreen()
            self.fullscreen = not self.fullscreen
            pygame.mouse.set_visible(not self.fullscreen)
        elif k == pygame.K_h:
            self.show_help = not self.show_help
        elif self.mode == "title":
            if k in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.mode = "walk"
                route, direction, _ = J.route_pos(self.progress.total_m)
                lm, dist = J.next_landmark(route, direction)
                where = J.region_at(route).name
                if self.progress.total_m < 1:
                    self.say("BAG END", "IN A HOLE IN THE GROUND THERE LIVED A HOBBIT.\n"
                                        "HURRY - THE DWARVES WAIT AT THE GREEN DRAGON!", 8)
                else:
                    self.say(where, f"{dist:.1f} KM TO {lm[1]}", 6)
            elif self.source.handle_key(k):
                pass
        elif k == pygame.K_p:
            self.paused = not self.paused
        else:
            self.source.handle_key(k)
        return True

    def run(self):
        self.source.start()
        self.dt = 0.0
        try:
            while self.step():
                pass
        finally:
            self.finish()

    async def run_async(self):
        """The same loop for the browser build (pygbag): yield to the page every frame."""
        import asyncio
        self.source.start()
        self.dt = 0.0
        try:
            while self.step():
                await asyncio.sleep(0)
        finally:
            self.finish()

    def step(self):
        """One frame; False when the game should end."""
        running = True
        ms = self.clock.tick(FPS)
        dt_real = min(ms / 1000.0, 2.0)
        self.dt = min(dt_real, 0.1)
        for ev in pygame.event.get():
            if not self.handle(ev):
                running = False
        self.update(self.dt, dt_real)
        if self.banners:
            self.banners[0][2] -= self.dt
            if self.banners[0][2] <= 0:
                self.banners.pop(0)
        self.flash = max(0.0, self.flash - self.dt * 5)
        self.bolt_t -= self.dt
        self.draw()
        if self.want_shot:
            self.want_shot = False
            self.screenshot()
        pygame.display.flip()
        return running

    def finish(self):
        self.source.stop()
        self.save()
        pygame.quit()
        print(f"Session: {self.session_m / 1000:.2f} km in {hud.hms(self.session_s)}, "
              f"~{self.kcal:.0f} kcal. Total: {self.progress.total_m / 1000:.2f} km.")
