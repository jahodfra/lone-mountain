"""Browser entry point (pygbag): tools/build_web.sh packs this with the hobbit package."""

import asyncio

from hobbit import web
from hobbit.game import Game
from hobbit.state import DEFAULTS


async def main():
    web.setup()
    settings = dict(DEFAULTS, fullscreen=False, speed_source="ftms", ftms_allow_control=True)
    await Game(settings, windowed=True).run_async()


asyncio.run(main())
