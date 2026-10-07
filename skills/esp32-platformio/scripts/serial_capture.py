#!/usr/bin/env python3
"""Non-interactive serial capture for ESP32 boards.

'pio device monitor' needs an interactive TTY on stdin, so it cannot be used
from a script, a CI job, or an agent harness.  This does the same job with
pyserial: it reads the port for a fixed number of seconds and prints what it
got.

Usage:
    python serial_capture.py --port COM5 --seconds 10
    python serial_capture.py --port COM5 --seconds 12 --reset
    python serial_capture.py --port COM5 --seconds 5 --expect "boot OK"
"""

import argparse
import sys
import time

import serial


def reset_board(ser: "serial.Serial") -> None:
    """Pulse the classic ESP32 auto-reset circuit (RTS->EN, DTR->GPIO0)."""
    ser.setDTR(False)
    ser.setRTS(True)
    time.sleep(0.12)
    ser.setRTS(False)
    time.sleep(0.05)


def main() -> int:
    ap = argparse.ArgumentParser(description="Capture serial output from an ESP32.")
    ap.add_argument("--port", required=True, help="serial port, e.g. COM5")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--seconds", type=float, default=10.0, help="how long to read")
    ap.add_argument("--reset", action="store_true", help="pulse reset before reading")
    ap.add_argument("--expect", default=None, help="exit 1 unless this text appears")
    args = ap.parse_args()

    try:
        ser = serial.Serial(args.port, args.baud, timeout=0.2)
    except serial.SerialException as exc:
        print(f"ERROR: cannot open {args.port}: {exc}", file=sys.stderr)
        return 2

    try:
        if args.reset:
            reset_board(ser)
            time.sleep(0.05)
            ser.reset_input_buffer()

        deadline = time.time() + args.seconds
        chunks: list[str] = []

        while time.time() < deadline:
            data = ser.read(4096)
            if data:
                chunks.append(data.decode("utf-8", errors="replace"))

        text = "".join(chunks)
        sys.stdout.write(text)
        sys.stdout.flush()

        if not text.strip():
            print(f"[serial_capture] no data from {args.port} in {args.seconds}s",
                  file=sys.stderr)
            return 3

        if args.expect:
            if args.expect in text:
                print(f"[serial_capture] OK: found {args.expect!r}", file=sys.stderr)
                return 0
            print(f"[serial_capture] FAIL: {args.expect!r} not found", file=sys.stderr)
            return 1
        return 0
    finally:
        ser.close()


if __name__ == "__main__":
    raise SystemExit(main())
