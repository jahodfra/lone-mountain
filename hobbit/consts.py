"""Screen and world constants."""

W, H = 320, 200          # native Amiga-ish resolution
TOP_BAR = 10             # height of the top HUD strip
SCENE_BOTTOM = 176       # bottom HUD panel starts here
HORIZON = 84             # screen row of the horizon when the camera is level

SEG = 2.0                # metres per road segment
DRAW_SEGS = 230          # how many segments ahead are drawn (~460 m)
CAM_HEIGHT = 2.6         # camera height above the path (m)
PLAYER_AHEAD = 5.0       # Bilbo walks this far in front of the camera (m)
CAM_DEPTH = 1.0          # 1 / tan(fov/2), 90 degree field of view
PX = 160.0               # pixels per world unit at depth 1

VERGE = 0.3              # width of the coloured path edge (m)
WALL_GAP = 0.9           # ground between the path edge and a rock wall (m)
NEAR = 0.3               # near clipping plane (m)
WALL_HEIGHT = 14.0
TUNNEL_HEIGHT = 5.0
LIP = 0.6                # rock lip at a gorge edge (m)

FPS = 60
MAX_KMH = 12.0
