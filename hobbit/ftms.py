"""Bluetooth LE treadmill speed via the standard Fitness Machine Service (FTMS).

Reading speed and setting speed confirmed on an FS-D2097B (ZenRun) belt.  Many walking pads with an "FS-..."
controller (FitShow) expose FTMS; if yours does not, run
`python tools/ble_scan.py` and we can add its own protocol.

Requires: pip install bleak
"""

import asyncio
import struct
import threading

FTMS_SERVICE = "00001826-0000-1000-8000-00805f9b34fb"
TREADMILL_DATA = "00002acd-0000-1000-8000-00805f9b34fb"
CONTROL_POINT = "00002ad9-0000-1000-8000-00805f9b34fb"


def parse_treadmill_data(data: bytes):
    """Return instantaneous speed in km/h, or None if not in this packet."""
    if len(data) < 4:
        return None
    flags = struct.unpack_from("<H", data, 0)[0]
    if flags & 0x0001:          # "More Data": speed field not present
        return None
    return struct.unpack_from("<H", data, 2)[0] / 100.0


class FTMSSource:
    name = "FTMS"

    def __init__(self, settings, fallback):
        self.device_name = settings.get("ftms_device_name", "")
        self.allow_control = settings.get("ftms_allow_control", False)
        self.fallback = fallback
        self.belt_kmh = None
        self.state = "SEARCHING"
        self._stop = False
        self._loop = None
        self._client = None
        self._thread = None
        self._wanted = None      # last speed asked for with the keys
        self._pending = None     # speed to set once a started belt is moving

    @property
    def direct(self):
        return self.belt_kmh is not None

    @property
    def target_kmh(self):
        return self.belt_kmh if self.belt_kmh is not None else self.fallback.target_kmh

    @property
    def status(self):
        return "BELT " + self.state

    def start(self):
        try:
            import bleak  # noqa: F401
        except ImportError:
            self.state = "NO BLEAK"
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop = True

    def handle_key(self, key):
        if self.belt_kmh is None:
            return self.fallback.handle_key(key)
        if not (self.allow_control and self._client is not None):
            return False
        # step from the speed we last asked for (the belt may still be accelerating)
        base = self._wanted if self._wanted is not None else self.belt_kmh
        before = self.fallback.target_kmh
        self.fallback.target_kmh = base
        handled = self.fallback.handle_key(key)
        target = self.fallback.target_kmh
        self.fallback.target_kmh = before
        if handled:
            self._wanted = target
            asyncio.run_coroutine_threadsafe(self._command(target), self._loop)
        return handled

    # --- background thread ---------------------------------------------------
    def _run(self):
        self._loop = asyncio.new_event_loop()
        self._loop.run_until_complete(self._main())

    async def _main(self):
        from bleak import BleakClient, BleakScanner
        while not self._stop:
            try:
                self.state = "SEARCHING"
                dev = await self._find(BleakScanner)
                if dev is None:
                    await asyncio.sleep(3)
                    continue
                self.state = "CONNECTING"
                async with BleakClient(dev) as client:
                    self._client = client
                    await client.start_notify(TREADMILL_DATA, self._on_data)
                    if self.allow_control:
                        try:
                            await client.write_gatt_char(CONTROL_POINT, bytes([0x00]), response=True)
                        except Exception:
                            pass
                    self.state = "OK"
                    while client.is_connected and not self._stop:
                        await asyncio.sleep(0.5)
            except Exception as e:      # keep retrying, show the problem in the HUD
                self.state = type(e).__name__.upper()[:12]
            self._client = None
            self.belt_kmh = None
            await asyncio.sleep(2)

    async def _find(self, scanner):
        devices = await scanner.discover(timeout=5.0, return_adv=True)
        for dev, adv in devices.values():
            name = (dev.name or adv.local_name or "")
            if self.device_name and self.device_name.lower() in name.lower():
                return dev
            if FTMS_SERVICE in [u.lower() for u in adv.service_uuids]:
                return dev
        return None

    def _on_data(self, _char, data):
        v = parse_treadmill_data(bytes(data))
        if v is None:
            return
        self.belt_kmh = v
        if self._pending is not None and v > 0.05:
            # the belt finished its start countdown: now set the requested speed
            k, self._pending = self._pending, None
            asyncio.run_coroutine_threadsafe(self._command(k), self._loop)
        elif self._pending is None and self._wanted is not None and abs(v - self._wanted) < 0.05:
            self._wanted = None

    async def _write(self, payload):
        await self._client.write_gatt_char(CONTROL_POINT, payload, response=True)

    async def _command(self, kmh):
        """FTMS control point: stop, start (+ speed once moving) or set speed."""
        if self._client is None:
            return
        try:
            if kmh <= 0:
                self._pending = None
                await self._write(bytes([0x08, 0x01]))          # stop
            elif (self.belt_kmh or 0.0) < 0.05:
                self._pending = kmh
                try:
                    await self._write(bytes([0x00]))            # request control (lost after a stop)
                except Exception:
                    pass
                await self._write(bytes([0x07]))                # start / resume
            else:
                await self._write(bytes([0x02]) + struct.pack("<H", int(round(kmh * 100))))
        except Exception as e:
            self.state = "CTRL " + type(e).__name__.upper()[:7]
