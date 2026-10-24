"""Settings (config.toml) and saved progress (save.json)."""

import json
import os
import sys
import time
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "config.toml")
SAVE = os.path.join(ROOT, "save.json")
WEB = sys.platform == "emscripten"      # the browser build: the save lives in localStorage
WEB_KEY = "hobbit_save"

DEFAULTS = {
    "weight_kg": 75.0,
    "fullscreen": True,
    "day_length_minutes": 24.0,
    "speed_step": 0.5,
    "speed_source": "keyboard",
    "ftms_device_name": "FS-",
    "ftms_allow_control": False,
    "show_fps": False,
}


def load_settings():
    s = dict(DEFAULTS)
    if os.path.exists(CONFIG):
        with open(CONFIG, "rb") as fh:
            s.update(tomllib.load(fh))
    return s


class Progress:
    def __init__(self):
        self.total_m = 0.0
        self.total_s = 0.0
        self.hour = 10.75           # Bilbo left Bag End in a hurry before 11 a.m.
        self.weather = "clear"
        self.sessions = []

    @classmethod
    def load(cls):
        p = cls()
        d = None
        if WEB:
            import platform
            raw = platform.window.localStorage.getItem(WEB_KEY)
            d = json.loads(str(raw)) if raw else None
        elif os.path.exists(SAVE):
            with open(SAVE) as fh:
                d = json.load(fh)
        if d:
            p.total_m = float(d.get("total_m", 0.0))
            p.total_s = float(d.get("total_s", 0.0))
            p.hour = float(d.get("hour", p.hour))
            p.weather = d.get("weather", p.weather)
            p.sessions = d.get("sessions", [])
        return p

    def save(self, session=None):
        sessions = list(self.sessions)
        if session and session["m"] > 1:
            sessions.append(session)
        d = {"total_m": self.total_m, "total_s": self.total_s, "hour": self.hour,
             "weather": self.weather, "sessions": sessions[-500:],
             "saved": time.strftime("%Y-%m-%d %H:%M:%S")}
        if WEB:
            import platform
            platform.window.localStorage.setItem(WEB_KEY, json.dumps(d))
            return
        tmp = SAVE + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(d, fh, indent=1)
        os.replace(tmp, SAVE)
