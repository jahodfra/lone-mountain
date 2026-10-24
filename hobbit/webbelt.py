"""Bluetooth treadmill speed in the browser (pygbag build), via Web Bluetooth.

The same Fitness Machine Service as ftms.py, but the browser does the Bluetooth:
a small JavaScript bridge (window.hobbitBelt) connects, keeps the latest speed and
queues control-point writes. Browsers only open the device picker on a key press or
click, so the bridge listens for the B key itself. Chrome / Edge / Opera only.
"""

import struct

import platform     # pygbag's bridge to the page (platform.window is the JS window)

from .ftms import FTMS_SERVICE, TREADMILL_DATA, CONTROL_POINT

BRIDGE = """
(() => {
  if (window.hobbitBelt) return;
  const SERVICE = "%(service)s", DATA = "%(data)s", CONTROL = "%(control)s";
  const belt = window.hobbitBelt = {
    state: navigator.bluetooth ? "PRESS B" : "NO WEB BT",
    kmh: -1, control: false, device: null, cp: null, queue: Promise.resolve(),
    async connect() {
      if (!navigator.bluetooth) return;
      try {
        belt.state = "PICK BELT";
        belt.device = await navigator.bluetooth.requestDevice({
          filters: [{services: [SERVICE]}, {namePrefix: "%(prefix)s"}],
          optionalServices: [SERVICE]});
        belt.device.addEventListener("gattserverdisconnected", () => {
          belt.kmh = -1; belt.cp = null; belt.state = "LOST";
          setTimeout(belt.open, 2000);    // the belt is already allowed: no picker needed
        });
        await belt.open();
      } catch (e) {
        belt.state = (e.name || "ERROR").toUpperCase().slice(0, 12);
      }
    },
    async open() {
      if (!belt.device || belt.device.gatt.connected) return;
      try {
        belt.state = "CONNECTING";
        const server = await belt.device.gatt.connect();
        const service = await server.getPrimaryService(SERVICE);
        const data = await service.getCharacteristic(DATA);
        data.addEventListener("characteristicvaluechanged", ev => {
          const v = ev.target.value;
          if (v.byteLength < 4 || (v.getUint16(0, true) & 1)) return;   // "More Data": no speed
          belt.kmh = v.getUint16(2, true) / 100;
        });
        await data.startNotifications();
        try { belt.cp = await service.getCharacteristic(CONTROL); } catch (e) { belt.cp = null; }
        if (belt.cp && belt.control) belt.write("00");
        belt.state = "OK";
      } catch (e) {
        belt.state = (e.name || "ERROR").toUpperCase().slice(0, 12);
        setTimeout(belt.open, 3000);
      }
    },
    write(hex) {        // one GATT write at a time, in order
      const bytes = new Uint8Array(hex.match(/../g).map(h => parseInt(h, 16)));
      belt.queue = belt.queue.then(() => belt.cp && belt.cp.writeValueWithResponse(bytes))
        .catch(e => {   // asking for control may fail harmlessly (some belts never need it)
          if (hex !== "00") belt.state = ("CTRL " + (e.name || "")).toUpperCase().slice(0, 12);
        });
    },
  };
  window.addEventListener("keydown", ev => {
    if (ev.code === "KeyB" && !(belt.device && belt.device.gatt.connected)) belt.connect();
  }, true);
})();
"""


class WebBluetoothSource:
    name = "FTMS"

    def __init__(self, settings, fallback):
        self.allow_control = settings.get("ftms_allow_control", False)
        self.prefix = settings.get("ftms_device_name", "") or "FS-"
        self.fallback = fallback
        self.belt_kmh = None
        self._bridge = None
        self._wanted = None      # last speed asked for with the keys
        self._pending = None     # speed to set once a started belt is moving

    @property
    def direct(self):
        return self.belt_kmh is not None

    @property
    def target_kmh(self):
        self._poll()
        return self.belt_kmh if self.belt_kmh is not None else self.fallback.target_kmh

    @property
    def status(self):
        return "BELT " + (str(self._bridge.state) if self._bridge is not None else "NO BRIDGE")

    def start(self):
        try:
            platform.window.eval(BRIDGE % {"service": FTMS_SERVICE, "data": TREADMILL_DATA,
                                           "control": CONTROL_POINT, "prefix": self.prefix})
            self._bridge = platform.window.hobbitBelt
            self._bridge.control = bool(self.allow_control)
        except Exception:
            self._bridge = None

    def stop(self):
        pass

    def _poll(self):
        if self._bridge is None:
            return
        v = float(self._bridge.kmh)
        self.belt_kmh = v if v >= 0 else None
        if v < 0:
            self._wanted = self._pending = None
        elif self._pending is not None and v > 0.05:
            # the belt finished its start countdown: now set the requested speed
            k, self._pending = self._pending, None
            self._command(k)
        elif self._pending is None and self._wanted is not None and abs(v - self._wanted) < 0.05:
            self._wanted = None

    def handle_key(self, key):
        if self.belt_kmh is None:
            return self.fallback.handle_key(key)
        if not self.allow_control:
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
            self._command(target)
        return handled

    def _write(self, payload):
        self._bridge.write(payload.hex())

    def _command(self, kmh):
        """FTMS control point: stop, start (+ speed once moving) or set speed."""
        if kmh <= 0:
            self._pending = None
            self._write(bytes([0x08, 0x01]))            # stop
        elif (self.belt_kmh or 0.0) < 0.05:
            self._pending = kmh
            self._write(bytes([0x00]))                  # request control (lost after a stop)
            self._write(bytes([0x07]))                  # start / resume
        else:
            self._write(bytes([0x02]) + struct.pack("<H", int(round(kmh * 100))))
