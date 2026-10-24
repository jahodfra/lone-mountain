#!/usr/bin/env python3
"""The Hobbit - There and Back Again: a walking simulator.

    python walk.py              # fullscreen (see config.toml)
    python walk.py --windowed   # in a window
"""

import argparse

from hobbit.game import Game
from hobbit.state import load_settings


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--windowed", action="store_true", help="run in a window instead of fullscreen")
    args = ap.parse_args()
    Game(load_settings(), windowed=args.windowed).run()


if __name__ == "__main__":
    main()
