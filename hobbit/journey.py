"""The route from Bag End to the Lonely Mountain - and back again.

Distances are approximate, loosely following the usual atlas estimates
(Bag End -> Rivendell ~740 km, Bag End -> Erebor ~1,530 km).
"""

import bisect
from dataclasses import dataclass, field, replace

ROUTE_KM = 1530.0
LEG_M = ROUTE_KM * 1000.0


@dataclass
class Region:
    key: str
    name: str
    start_km: float
    end_km: float
    # ground colours (12-bit): grass A/B, path A/B, verge A/B
    ground: tuple
    hills: float = 4.0            # hill amplitude (m)
    curves: float = 0.004         # max path curvature (1/m)
    sides: tuple = (("grass", "grass", 1),)
    scenery: tuple = ()           # (sprite, weight, xmin, xmax, on, yoff)
    density: float = 0.25         # chance per segment & side of a sprite
    bg_far: str = "hills"
    bg_near: str = "hills"
    bg_far_col: int = 0x6A8
    bg_near_col: int = 0x483
    bg_near_col2: int = 0x372
    far_land: tuple = (0x585, 0x474)
    path_half: float = 1.3        # half width of the path (m)
    gloom: float = 0.0
    cave: float = 0.0             # 1 = underground: the sun and the hour do not reach it
    weather: dict = field(default_factory=lambda: {"clear": 0.7, "cloudy": 0.2, "rain": 0.1})
    back: dict = field(default_factory=dict)    # overrides on the way back (what lies ahead going west)
    index: int = 0


SHIRE_GROUND = (0x6B4, 0x5A3, 0xB97, 0xA86, 0x8C5, 0x493)

REGIONS = [
    Region("hobbiton", "HOBBITON", 0, 2, SHIRE_GROUND, hills=4, curves=0.005,
           scenery=(("hobbit_hole", 5, 2.5, 9, "grass", 0), ("oak", 3, 4, 18, "grass", 0),
                    ("bush", 4, 0.3, 6, "grass", 0), ("flowers", 4, 0.2, 3, "grass", 0),
                    ("fence", 2, 0.4, 0.6, "grass", 0)),
           density=0.22, bg_far="hills", bg_near="hills",
           bg_far_col=0x6A8, bg_near_col=0x5A4, bg_near_col2=0x494),
    Region("shire", "THE SHIRE", 2, 70, SHIRE_GROUND, hills=5, curves=0.004,
           scenery=(("oak", 4, 3, 25, "grass", 0), ("bush", 4, 0.3, 8, "grass", 0),
                    ("flowers", 3, 0.2, 4, "grass", 0), ("fence", 3, 0.4, 0.6, "grass", 0),
                    ("hobbit_hole", 1, 4, 14, "grass", 0), ("grass_tuft", 3, 0.1, 3, "grass", 0)),
           density=0.18, bg_far="hills", bg_near="hills",
           bg_far_col=0x6A8, bg_near_col=0x5A4, bg_near_col2=0x494),
    Region("eastroad", "THE EAST ROAD", 70, 220,
           (0x6A3, 0x593, 0xA96, 0x985, 0x7A4, 0x582), hills=6, curves=0.004,
           scenery=(("oak", 3, 3, 25, "grass", 0), ("pine", 2, 5, 30, "grass", 0),
                    ("bush", 4, 0.3, 8, "grass", 0), ("rock", 2, 0.3, 6, "grass", 0),
                    ("grass_tuft", 4, 0.1, 3, "grass", 0), ("milestone", 1, 0.2, 0.4, "grass", 0)),
           density=0.15, bg_far="hills", bg_near="forest",
           bg_far_col=0x689, bg_near_col=0x472, bg_near_col2=0x362),
    Region("lonelands", "THE LONE-LANDS", 220, 470,
           (0x993, 0x883, 0xA97, 0x986, 0xBA6, 0x873), hills=7, curves=0.003,
           scenery=(("rock", 4, 0.3, 10, "grass", 0), ("boulder", 2, 4, 30, "grass", 0),
                    ("dead_tree", 2, 3, 25, "grass", 0), ("grass_tuft", 5, 0.1, 5, "grass", 0),
                    ("bush", 2, 0.5, 10, "grass", 0)),
           density=0.12, bg_far="castle_hills", bg_near="hills",
           bg_far_col=0x778, bg_near_col=0x885, bg_near_col2=0x774,
           far_land=(0x875, 0x764),
           weather={"clear": 0.4, "cloudy": 0.3, "rain": 0.3}),
    Region("trollshaws", "THE TROLLSHAWS", 470, 725,
           (0x483, 0x372, 0x875, 0x764, 0x594, 0x362), hills=9, curves=0.006,
           scenery=(("pine", 5, 2.5, 30, "grass", 0), ("oak", 3, 2.5, 25, "grass", 0),
                    ("rock", 3, 0.3, 8, "grass", 0), ("bush", 3, 0.3, 6, "grass", 0)),
           density=0.3, bg_far="mountains", bg_near="forest",
           bg_far_col=0x99B, bg_near_col=0x362, bg_near_col2=0x252,
           far_land=(0x464, 0x353),
           weather={"clear": 0.4, "cloudy": 0.3, "rain": 0.3},
           back={"bg_far": "hills", "bg_far_col": 0x578}),
    Region("rivendell", "RIVENDELL VALE", 725, 745,
           (0x5A4, 0x494, 0xCBA, 0xBA9, 0xDDC, 0xAA9), hills=5, curves=0.006,
           sides=(("grass", "gorge", 1),),
           scenery=(("pine", 4, 2, 15, "grass", 0), ("oak", 2, 3, 15, "grass", 0),
                    ("bush", 3, 0.3, 5, "grass", 0), ("flowers", 3, 0.2, 3, "grass", 0),
                    ("pine", 5, 8, 40, "gorge", -22)),
           density=0.3, bg_far="mountains", bg_near="cliffs",
           bg_far_col=0x88A, bg_near_col=0x667, bg_near_col2=0x556,
           far_land=(0x486, 0x264)),
    Region("misty", "THE MISTY MOUNTAINS", 745, 800,
           (0x887, 0x776, 0xA99, 0x988, 0xBBA, 0x776), hills=12, curves=0.007,
           sides=(("wall", "gorge", 3), ("gorge", "wall", 2), ("wall", "grass", 1), ("grass", "gorge", 1)),
           scenery=(("pine_snow", 3, 1, 10, "grass", 0), ("rock", 5, 0.3, 4, "grass", 0),
                    ("boulder", 2, 2, 8, "grass", 0),
                    ("pine_snow", 5, 8, 40, "gorge", -24), ("pine", 3, 10, 50, "gorge", -34)),
           density=0.25, bg_far="mountains", bg_near="mountains",
           bg_far_col=0x99B, bg_near_col=0x778, bg_near_col2=0x667,
           far_land=(0x667, 0x445),
           weather={"clear": 0.2, "cloudy": 0.3, "snow": 0.3, "storm": 0.2}),
    Region("goblintown", "GOBLIN-TOWN", 800, 812,
           (0x433, 0x322, 0x655, 0x544, 0x766, 0x433), hills=3, curves=0.008,
           sides=(("tunnel", "tunnel", 1),),
           scenery=(("torch", 1, 0, 0, "wall", 1.8),),
           density=0.07, bg_far="mountains", bg_near="mountains",
           bg_far_col=0x99B, bg_near_col=0x778, bg_near_col2=0x667,
           far_land=(0x667, 0x445), gloom=0.55, cave=1.0, weather={"clear": 1.0}),
    Region("eastslopes", "THE EASTERN SLOPES", 812, 835,
           (0x786, 0x675, 0xA98, 0x987, 0xBBA, 0x776), hills=11, curves=0.006,
           sides=(("wall", "gorge", 2), ("grass", "gorge", 2), ("grass", "grass", 2)),
           scenery=(("pine", 6, 1.5, 25, "grass", 0), ("rock", 3, 0.3, 5, "grass", 0),
                    ("pine", 6, 8, 40, "gorge", -24)),
           density=0.3, bg_far="flat", bg_near="forest",
           bg_far_col=0x8A9, bg_near_col=0x363, bg_near_col2=0x253,
           far_land=(0x575, 0x353),
           weather={"clear": 0.6, "cloudy": 0.3, "rain": 0.1},
           back={"bg_far": "mountains", "bg_far_col": 0x99B}),
    Region("anduin", "THE VALE OF ANDUIN", 835, 875,
           (0x7B4, 0x6A3, 0xB97, 0xA86, 0x9C5, 0x593), hills=3, curves=0.003,
           scenery=(("oak", 2, 5, 30, "grass", 0), ("bush", 3, 0.5, 10, "grass", 0),
                    ("grass_tuft", 6, 0.1, 6, "grass", 0), ("flowers", 2, 0.2, 5, "grass", 0),
                    ("reeds", 4, 0.0, 3, "water", 0)),
           density=0.15, bg_far="forest", bg_near="hills",
           bg_far_col=0x575, bg_near_col=0x6A4, bg_near_col2=0x594,
           back={"bg_far": "mountains", "bg_far_col": 0x99B}),
    Region("beorn", "BEORN'S LANDS", 875, 940,
           (0x7B4, 0x6B3, 0xB97, 0xA86, 0xDD6, 0x7A3), hills=4, curves=0.004,
           scenery=(("oak", 4, 4, 25, "grass", 0), ("flowers", 8, 0.2, 8, "grass", 0),
                    ("beehive", 1, 2, 8, "grass", 0), ("bush", 2, 0.5, 8, "grass", 0),
                    ("fence", 2, 0.4, 0.6, "grass", 0)),
           density=0.25, bg_far="forest", bg_near="hills",
           bg_far_col=0x243, bg_near_col=0x6A4, bg_near_col2=0x594,
           back={"bg_far": "mountains", "bg_far_col": 0x99B}),
    Region("mirkwood", "MIRKWOOD", 940, 1245,
           (0x231, 0x121, 0x432, 0x321, 0x342, 0x221), hills=3, curves=0.005,
           scenery=(("mirk_tree", 10, 1.2, 14, "grass", 0), ("web", 1, 1.5, 6, "grass", 0),
                    ("bush", 2, 0.3, 4, "grass", 0), ("eyes", 1, 4, 12, "grass", 1.0)),
           density=0.55, bg_far="forest", bg_near="forest",
           bg_far_col=0x232, bg_near_col=0x121, bg_near_col2=0x010,
           far_land=(0x121, 0x010), gloom=0.5,
           weather={"clear": 0.6, "cloudy": 0.3, "rain": 0.1}),
    Region("elvenking", "THE ELVENKING'S HALLS", 1245, 1250,
           (0x353, 0x242, 0x887, 0x776, 0x9A8, 0x565), hills=4, curves=0.004,
           scenery=(("mirk_tree", 6, 2, 14, "grass", 0), ("oak", 3, 3, 14, "grass", 0)),
           density=0.4, bg_far="forest", bg_near="forest",
           bg_far_col=0x353, bg_near_col=0x242, bg_near_col2=0x131,
           far_land=(0x242, 0x131), gloom=0.3),
    Region("forestriver", "THE FOREST RIVER", 1250, 1400,
           (0x483, 0x373, 0x986, 0x875, 0x9A6, 0x573), hills=2, curves=0.004,
           sides=(("grass", "water", 1),),
           scenery=(("oak", 5, 2, 20, "grass", 0), ("pine", 2, 3, 20, "grass", 0),
                    ("bush", 3, 0.3, 5, "grass", 0), ("barrel", 2, 1.5, 8, "water", 0),
                    ("reeds", 4, 0.0, 2, "water", 0)),
           density=0.25, bg_far="flat", bg_near="forest",
           bg_far_col=0x799, bg_near_col=0x463, bg_near_col2=0x353,
           far_land=(0x58A, 0x479)),
    Region("laketown", "THE LONG LAKE", 1400, 1420,
           (0x47A, 0x369, 0xA86, 0x975, 0x753, 0x642), hills=0.5, curves=0.002,
           sides=(("water", "water", 1),),
           scenery=(("reeds", 2, 1, 6, "water", 0), ("barrel", 1, 2, 10, "water", 0)),
           density=0.08, bg_far="mountain_far", bg_near="flat",
           bg_far_col=0x88A, bg_near_col=0x579, bg_near_col2=0x468,
           far_land=(0x58B, 0x47A),
           back={"bg_far": "forest", "bg_far_col": 0x575}),
    Region("riverrunning", "THE RIVER RUNNING", 1420, 1470,
           (0x8A4, 0x793, 0xA97, 0x986, 0x9A5, 0x683), hills=4, curves=0.003,
           sides=(("water", "grass", 1),),
           scenery=(("bush", 3, 0.3, 8, "grass", 0), ("rock", 3, 0.3, 8, "grass", 0),
                    ("grass_tuft", 5, 0.1, 6, "grass", 0), ("reeds", 4, 0.0, 3, "water", 0)),
           density=0.15, bg_far="mountain_far", bg_near="hills",
           bg_far_col=0x88A, bg_near_col=0x794, bg_near_col2=0x683,
           back={"bg_far": "flat", "bg_far_col": 0x7A9}),
    Region("desolation", "THE DESOLATION OF SMAUG", 1470, 1527,
           (0x776, 0x665, 0x998, 0x887, 0x554, 0x887), hills=7, curves=0.004,
           scenery=(("stump", 5, 0.5, 15, "grass", 0), ("dead_tree", 3, 3, 25, "grass", 0),
                    ("rock", 4, 0.3, 10, "grass", 0), ("boulder", 1, 5, 25, "grass", 0)),
           density=0.15, bg_far="mountain_far", bg_near="hills",
           bg_far_col=0x778, bg_near_col=0x665, bg_near_col2=0x554,
           far_land=(0x776, 0x665),
           weather={"clear": 0.4, "cloudy": 0.5, "rain": 0.1},
           back={"bg_far": "flat", "bg_far_col": 0x887,
                 "weather": {"clear": 0.3, "cloudy": 0.4, "snow": 0.3}}),
    Region("erebor", "EREBOR, THE LONELY MOUNTAIN", 1527, 1530,
           (0x776, 0x665, 0x998, 0x887, 0xAA9, 0x776), hills=6, curves=0.004,
           sides=(("wall", "grass", 1), ("grass", "wall", 1)),
           scenery=(("rock", 3, 0.3, 6, "grass", 0), ("boulder", 1, 3, 12, "grass", 0)),
           density=0.1, bg_far="mountains", bg_near="mountains",
           bg_far_col=0x887, bg_near_col=0x665, bg_near_col2=0x554,
           far_land=(0x776, 0x665),
           back={"weather": {"clear": 0.2, "cloudy": 0.4, "snow": 0.4}}),
]
# Wide road in the Shire, narrow tracks in the wild (walkers go in single file)
PATH_WIDTH = {
    "hobbiton": 1.3, "shire": 1.3, "eastroad": 1.25, "lonelands": 0.95, "trollshaws": 0.85,
    "rivendell": 0.9, "misty": 0.75, "goblintown": 0.8, "eastslopes": 0.75, "anduin": 0.95,
    "beorn": 1.05, "mirkwood": 0.8, "elvenking": 0.95, "forestriver": 0.9, "laketown": 1.3,
    "riverrunning": 0.95, "desolation": 0.9, "erebor": 1.2,
}
FOREST_REGIONS = ("mirkwood", "elvenking")
for _i, _r in enumerate(REGIONS):
    _r.index = _i
    _r.path_half = PATH_WIDTH[_r.key]
_STARTS = [r.start_km for r in REGIONS]
# the region as seen walking in each direction (the way back applies `back`)
_VIEWS = {(r.key, 1): r for r in REGIONS}
_VIEWS.update({(r.key, -1): replace(r, **r.back) for r in REGIONS})

# Short stretches that override the region's sides / path.
# (start_km, end_km, left, right, path)   path: None, "stone", "planks", "ford", "blackford", "lake"
FEATURES = [
    (69.95, 70.05, "water", "water", "stone"),      # Brandywine Bridge
    (469.97, 470.03, "water", "water", "stone"),    # The Last Bridge
    (719.98, 720.02, "water", "water", "ford"),     # Ford of Bruinen
    (866.0, 874.0, None, "water", None),            # the Great River by the Carrock
    (805.90, 806.10, None, None, "lake"),           # Gollum's lake beside the tunnel floor
    (1049.98, 1050.02, "blackwater", "blackwater", "blackford"),   # the Enchanted River
    (1400.0, 1420.0, None, None, "planks"),         # Lake-town causeway
    (1529.80, 1529.97, "grass", "grass", None),     # open ground up to the Front Gate
    (1529.97, 1530.0, "tunnel", "tunnel", None),    # inside the Gate: the dark hall
]
# a hall inside a mountain (tunnel sides in an open region): (ground beside the path m, roof m)
HALLS = {"erebor": (3.0, 9.0)}
# Gollum's cave: the right-hand tunnel wall opens wide over the lake
# (start_km, end_km, extra width m)
LAKE_CAVERN = (805.90, 806.10, 13.0)

# Weather the book fixes at a place: (start_km, end_km, weather, direction)
FORCED_WEATHER = [
    (465.0, 471.0, "rain", 1),      # "It was raining, and had been all day"
    (795.0, 800.0, "storm", 1),     # the thunder-battle at the High Pass
]

# Set pieces that only show at night on the way there (the trolls' fire is out by dawn)
NIGHT_ONLY = ("campfire",)
# set pieces seen only on the way there (the Gate is a face across the path, not from inside)
FORWARD_ONLY = ("erebor_gate",)

# (km, name, short name, quote)
LANDMARKS = [
    (0.0, "BAG END", "BAG END", "IN A HOLE IN THE GROUND THERE LIVED A HOBBIT."),
    (2.0, "THE GREEN DRAGON, BYWATER", "BYWATER", "BILBO RAN ALL THE WAY - WITHOUT A POCKET-HANDKERCHIEF."),
    (70.0, "THE BRANDYWINE BRIDGE", "BRANDYWINE", "AND SO THEY LEFT THE SHIRE BEHIND."),
    (300.0, "WEATHERTOP", "WEATHERTOP", "OLD RUINS STOOD ON THE HILLS."),
    (470.0, "THE LAST BRIDGE", "LAST BRIDGE", "IT WAS RAINING, AND HAD BEEN ALL DAY."),
    (600.0, "THE STONE TROLLS", "TROLLS", "DAWN TAKE YOU ALL, AND BE STONE TO YOU!"),
    (720.0, "THE FORD OF BRUINEN", "BRUINEN", "THE EDGE OF THE WILD."),
    (740.0, "RIVENDELL, THE LAST HOMELY HOUSE", "RIVENDELL", "TRA-LA-LA-LALLY, HERE DOWN IN THE VALLEY!"),
    (799.0, "THE HIGH PASS", "HIGH PASS", "FAR OVER THE MISTY MOUNTAINS COLD..."),
    (806.0, "GOLLUM'S LAKE", "GOLLUM", "WHAT HAS IT GOT IN ITS POCKETSES?"),
    (825.0, "THE EAGLES' EYRIE", "EYRIE", "OUT OF THE FRYING-PAN INTO THE FIRE!"),
    (870.0, "THE CARROCK", "CARROCK", "A GREAT ROCK, ALMOST A HILL OF STONE."),
    (890.0, "BEORN'S HOUSE", "BEORN", "HE IS A SKIN-CHANGER."),
    (940.0, "THE FOREST GATE", "FOREST GATE", "DON'T LEAVE THE PATH!"),
    (1050.0, "THE ENCHANTED RIVER", "ENCHANTED RIVER", "DON'T DRINK OR BATHE IN IT."),
    (1150.0, "THE SPIDERS' NESTS", "SPIDERS", "ATTERCOP! ATTERCOP!"),
    (1245.0, "THE ELVENKING'S HALLS", "ELVENKING", "BARRELS OUT OF BOND."),
    (1418.0, "LAKE-TOWN, ESGAROTH", "LAKE-TOWN", "THE KING BENEATH THE MOUNTAIN IS RETURNED!"),
    (1470.0, "THE DESOLATION OF SMAUG", "DESOLATION", "NEVER LAUGH AT LIVE DRAGONS!"),
    (1530.0, "EREBOR, THE LONELY MOUNTAIN", "EREBOR", "SO COMES SNOW AFTER FIRE..."),
]
_LM_KM = [lm[0] for lm in LANDMARKS]

# Unique scenery placed at specific spots: (km, sprite, x metres (signed), yoff)
SET_PIECES = [
    (0.001, "bag_end", 0.0, 0),
    (2.0, "green_dragon", -10.0, 0),
    (300.05, "ruin", -40.0, 0),
    (600.0, "troll", -5.0, 0), (600.004, "troll", -8.5, 0), (600.008, "troll", -6.0, 0),
    (600.005, "campfire", -6.6, 0),
    (806.05, "gollum_eyes", 9.0, 0.25),
    (739.80, "elf_house", -7.0, 0), (739.86, "elf_house", -16.0, 0), (739.93, "elf_house", -8.0, 0),
    (740.02, "elf_house", -12.0, 0), (740.08, "elf_house", -7.5, 0),
    (870.0, "carrock", 40.0, -2),
    (889.95, "beorn_hall", -16.0, 0),
    (940.0, "forest_gate", 0.0, 0),
    (1244.999, "torch", 1.0, 2.5), (1244.9995, "torch", 11.0, 2.5),
    (1245.0, "elf_gate", 6.0, 0),
    (1529.9705, "erebor_gate", 0.0, 0),
]
for _k in range(18):     # Lake-town stilt houses along the causeway
    SET_PIECES.append((1412.0 + _k * 0.35, "stilt_house", (-1) ** _k * (7 + (_k * 3) % 6), 0))
for _k in range(60):     # spider webs and spiders in the trees
    SET_PIECES.append((1148.0 + _k * 0.07, "spider" if _k % 3 else "web",
                       (-1) ** _k * (2.5 + (_k * 7) % 5), 3.5 if _k % 3 else 0))
for _k in range(14):
    SET_PIECES.append((887.0 + _k * 0.45, "beehive", (-1) ** _k * (4 + _k % 4), 0))
SET_PIECES.sort()
_SP_KM = [sp[0] for sp in SET_PIECES]

QUOTES = [
    "IN A HOLE IN THE GROUND THERE LIVED A HOBBIT.",
    "WE ARE PLAIN QUIET FOLK AND HAVE NO USE FOR ADVENTURES.",
    "THE ROAD GOES EVER ON AND ON...",
    "YOU ARE ONLY QUITE A LITTLE FELLOW IN A WIDE WORLD AFTER ALL!",
    "WHERE THERE'S LIFE THERE'S HOPE.",
    "THERE IS MORE IN YOU OF GOOD THAN YOU KNOW.",
    "GOOD MORNING! WHAT DO YOU MEAN?",
    "IT DOES NOT DO TO LEAVE A LIVE DRAGON OUT OF YOUR CALCULATIONS.",
    "ESCAPING GOBLINS TO BE CAUGHT BY WOLVES!",
    "SECOND BREAKFAST IS STILL SOME MILES AWAY.",
    "THE BEST LAID PLANS OF MICE AND HOBBITS...",
    "A SAFE FIRESIDE IS NEVER FAR FROM A HOBBIT'S THOUGHTS.",
]


def route_pos(z):
    """World distance z (m, ever increasing) -> (route metres, direction, journey no)."""
    leg = int(z // LEG_M)
    r = z - leg * LEG_M
    if leg % 2 == 0:
        return r, 1, leg // 2
    return LEG_M - r, -1, leg // 2


def region_at(route_m):
    km = route_m / 1000.0
    i = bisect.bisect_right(_STARTS, km) - 1
    return REGIONS[max(0, min(i, len(REGIONS) - 1))]


def view(region, direction):
    """The region as it looks walking in `direction` (horizon, weather)."""
    return _VIEWS[(region.key, 1 if direction > 0 else -1)]


def forced_weather(route_m, direction):
    km = route_m / 1000.0
    for k0, k1, name, d in FORCED_WEATHER:
        if k0 <= km < k1 and d == direction:
            return name
    return None


def border(route_m, width=300.0):
    """The nearest region border within `width` m: (earlier, later, share of later 0..1), or None."""
    r = region_at(route_m)
    km = route_m / 1000.0
    for edge, other in ((r.start_km, r.index - 1), (r.end_km, r.index + 1)):
        if 0 <= other < len(REGIONS):
            dist = abs(km - edge) * 1000.0
            if dist < width:
                t = 0.5 * (1 - dist / width)
                if other > r.index:
                    return r, REGIONS[other], t
                return REGIONS[other], r, 1 - t
    return None


def blended(route_m, attr, width=300.0):
    """A region attribute smoothly blended across region borders."""
    r = region_at(route_m)
    v = getattr(r, attr)
    km = route_m / 1000.0
    for edge, other in ((r.start_km, r.index - 1), (r.end_km, r.index + 1)):
        if 0 <= other < len(REGIONS):
            dist = abs(km - edge) * 1000.0
            if dist < width:
                t = 0.5 * (1 - dist / width)
                v = v * (1 - t) + getattr(REGIONS[other], attr) * t
    return v


def feature_at(route_m):
    km = route_m / 1000.0
    for f in FEATURES:
        if f[0] <= km < f[1]:
            return f
    return None


def cavern_width(route_m):
    """Extra width (m) of the tunnel on its right-hand side, ramped at both ends."""
    a, b, w = LAKE_CAVERN
    d = min(route_m - a * 1000.0, b * 1000.0 - route_m)
    return 0.0 if d <= 0 else w * min(1.0, d / 16.0)


def set_pieces_between(m0, m1):
    lo, hi = min(m0, m1) / 1000.0, max(m0, m1) / 1000.0
    i = bisect.bisect_left(_SP_KM, lo)
    out = []
    while i < len(SET_PIECES) and SET_PIECES[i][0] < hi:
        out.append(SET_PIECES[i])
        i += 1
    return out


def landmarks_between(m0, m1):
    lo, hi = min(m0, m1) / 1000.0, max(m0, m1) / 1000.0
    return [lm for lm in LANDMARKS if lo < lm[0] < hi]


def next_landmark(route_m, direction):
    km = route_m / 1000.0
    if direction > 0:
        i = bisect.bisect_right(_LM_KM, km + 1e-6)
        if i < len(LANDMARKS):
            return LANDMARKS[i], (LANDMARKS[i][0] - km)
        return LANDMARKS[-1], 0.0
    i = bisect.bisect_left(_LM_KM, km - 1e-6) - 1
    if i >= 0:
        return LANDMARKS[i], km - LANDMARKS[i][0]
    return LANDMARKS[0], 0.0


def company(route_m, direction):
    """Who walks with Bilbo here: list of names."""
    km = route_m / 1000.0
    out = []
    if direction > 0:
        if km < 940.0:              # he leaves at Mirkwood, back only after the Battle
            out.append("gandalf")
        if km >= 2.0:
            out += ["thorin", "balin", "dwalin", "fili", "kili", "bombur"]
    else:
        out.append("gandalf")       # Gandalf sees Bilbo home; the dwarves stay
    return out
