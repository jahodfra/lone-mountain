#!/usr/bin/env python3
"""Find the walking belt over Bluetooth LE and dump its services.

    pip install bleak
    python tools/ble_scan.py            # list nearby devices
    python tools/ble_scan.py FS-D2097B  # connect, list services, print FTMS speed for 20 s

Switch the belt on (and disconnect the vendor's phone app) first.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bleak import BleakClient, BleakScanner  # noqa: E402

from hobbit.ftms import FTMS_SERVICE, TREADMILL_DATA, parse_treadmill_data  # noqa: E402


async def main():
    want = sys.argv[1].lower() if len(sys.argv) > 1 else None
    print("Scanning for 8 s...")
    found = await BleakScanner.discover(timeout=8.0, return_adv=True)
    target = None
    for dev, adv in sorted(found.values(), key=lambda x: -(x[1].rssi or -999)):
        name = dev.name or adv.local_name or "?"
        ftms = FTMS_SERVICE in [u.lower() for u in adv.service_uuids]
        print(f"{adv.rssi:4} dBm  {dev.address}  {name:24} {'FTMS' if ftms else ''}  {adv.service_uuids}")
        if want and want in name.lower():
            target = dev
    if not want:
        return
    if target is None:
        print(f"No device matching {want!r}")
        return
    print(f"\nConnecting to {target.name} ...")
    async with BleakClient(target) as client:
        for svc in client.services:
            print(f"[service] {svc.uuid}  {svc.description}")
            for ch in svc.characteristics:
                print(f"    {ch.uuid}  {','.join(ch.properties):40} {ch.description}")
        chars = [c.uuid for s in client.services for c in s.characteristics]
        if TREADMILL_DATA in chars:
            print("\nFTMS Treadmill Data found - printing speed for 20 s (walk on the belt!)")

            def cb(_c, data):
                print(f"  raw={bytes(data).hex()}  speed={parse_treadmill_data(bytes(data))} km/h")

            await client.start_notify(TREADMILL_DATA, cb)
            await asyncio.sleep(20)
        else:
            print("\nNo FTMS Treadmill Data characteristic - send me this output to add the belt's own protocol.")


if __name__ == "__main__":
    asyncio.run(main())
