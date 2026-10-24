# The Hobbit – There and Back Again: a walking simulator

A Lotus III / Pitstop II-style pseudo-3D walking view at 320×200 with an Amiga-style palette, stretched to fullscreen.
You walk Bilbo (followed by Gandalf and the Company) from Bag End to the Lonely Mountain (~1,530 km) and then back home.
Your distance is saved between sessions, so the whole trip is walked over many sessions.

## Run

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python walk.py              # fullscreen
.venv/bin/python walk.py --windowed   # in a window
```

## Controls

| Key | Action |
| --- | --- |
| ↑ / ↓ | speed ±0.5 km/h (0–12) |
| 1–9 | set that speed in km/h (0 = stop) |
| Space | stop |
| P | pause (distance does not count) |
| F | toggle fullscreen |
| H | help |
| Esc | save and quit |

The HUD shows speed, session and total distance, session and total time, pace, and calories.
The top bar shows the region, the in-game clock and the next landmark.

## The journey

Hobbiton → the Shire → the East Road → the Lone-lands (Weathertop) → the Trollshaws (the stone trolls) →
Ford of Bruinen → Rivendell (gorge edge) → the Misty Mountains (rock walls and gorges, snow, thunderstorm at the High Pass) →
Goblin-town (tunnel) → the Eagles' Eyrie → the Vale of Anduin (the Carrock) → Beorn's house → Mirkwood (spiders, glowing eyes at night) →
the Elvenking's halls → the Forest River → Lake-town causeway → the Desolation of Smaug (Smaug circling) → Erebor's front gate.
Then the same road back with Gandalf; the dwarves stay at the Mountain.

The day/night cycle runs at 1 game hour per real minute by default (`day_length_minutes` in `config.toml`).

## Settings

Edit `config.toml`: body weight, fullscreen, day length, speed step and speed source.
Progress lives in `save.json` (delete it to start over).

## Bluetooth walking belt (FS-D2097B / ZenRun)

Confirmed working on the FS-D2097B: it speaks standard FTMS.

1. `.venv/bin/pip install bleak`
2. `.venv/bin/python tools/ble_scan.py`, then `.venv/bin/python tools/ble_scan.py FS-D2097B`.
   This shows whether the belt speaks the standard FTMS protocol and prints live speed.
3. If it does, set `speed_source = "ftms"` in `config.toml`.
   The belt's speed then drives the walk; the keyboard is the fallback until it connects.
4. With `ftms_allow_control = true` the keys drive the belt: a speed key starts a stopped belt
   (it runs its countdown, then goes to the chosen speed), Space or 0 stops it.

If the belt uses its own protocol instead of FTMS, the scan output is what's needed to add it (`hobbit/ftms.py`).

## Browser version

```sh
.venv/bin/pip install pygbag
PATH=$PWD/.venv/bin:$PATH tools/build_web.sh serve   # http://localhost:8000
PATH=$PWD/.venv/bin:$PATH tools/build_web.sh         # build only: build/hobbit/build/web/
```

Put `build/hobbit/build/web/` on any https host (GitHub Pages, Netlify...).

**GitHub Pages:** `.github/workflows/pages.yml` builds and publishes the browser version on every
push to `main` or `master` (or by hand from the Actions tab). Once, in the repository on GitHub:
Settings → Pages → Source: **GitHub Actions**. The game is then at `https://<user>.github.io/<repo>/`.
The progress is kept in the browser's local storage; Esc saves (a page cannot quit). F toggles fullscreen.

Press **B** to connect the belt (Web Bluetooth, `hobbit/webbelt.py`): Chrome, Edge or Opera on
Windows, macOS, ChromeOS or Android; on Linux Chrome may need "Experimental Web Platform features" turned on in `chrome://flags`.
Firefox and Safari have no Web Bluetooth, so there only the keys work.
The browser shows its own device list; after a page reload pick the belt again.
The keys drive the belt as with `ftms_allow_control = true`.
Bluetooth also needs a page of its own: it does not work inside an embedding page such as itch.io's.

## Test keys (hidden)

| Key | Action |
| --- | --- |
| `]` / `[` | jump ahead / back 1 km (Shift: 10 km), also PageUp / PageDown |
| hold Tab | walk 10x faster (only moves you along the route; not counted in today's stats) |
| C or F12 | screenshot to `screenshots/` (native, 4x, and a `.json` to re-render it with `tools/snapshot.py`) |

## Code map

- `hobbit/journey.py` – route, regions, landmarks, set pieces, quotes
- `hobbit/world.py` – procedural 2 m road segments (curves, hills, sides, scenery)
- `hobbit/render.py` – pseudo-3D renderer, background, sky and weather
- `hobbit/sprites.py` – all pixel art, generated in code
- `hobbit/palette.py` – 12-bit palette; day/night, gloom and lightning are done by swapping palettes
- `hobbit/speed.py`, `hobbit/ftms.py` – speed sources
- `tools/snapshot.py` – render still frames at any km, for testing
