#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Non-interactive serial command runner for the ESP32 console.

Opens the port, optionally captures the boot banner, then sends one command at a
time and prints everything that comes back.  Built for scripted verification of
the firmware console (scan / map / save / status / diag ...) when no interactive
TTY is available.

Each step is written as  "command"  or  "command@seconds"  so every step can
have its own wait.  (A single global --after option is a trap: argparse keeps
only the LAST occurrence, so every earlier step silently inherits it.)

Usage:
    python serial_cmd.py --port COM6 --boot --gap 2 \
        --step "scan" --step "map skin_chest 0" --step "status@20"
"""

import argparse
import sys
import time

import serial


def drain(ser, seconds, sink, quiet=False):
    """Read whatever arrives for 'seconds' and append it to sink. Returns bytes."""
    t0 = time.time()
    deadline = t0 + seconds
    nbytes = 0
    while time.time() < deadline:
        data = ser.read(4096)
        if data:
            nbytes += len(data)
            sink.append(data.decode("utf-8", errors="replace"))
    if not quiet:
        print("[waited %.2fs, got %d bytes]" % (time.time() - t0, nbytes))
    return nbytes


def reset_board(ser):
    """Pulse the ESP32 auto-reset circuit (RTS->EN)."""
    ser.setDTR(False)
    ser.setRTS(True)
    time.sleep(0.12)
    ser.setRTS(False)
    time.sleep(0.05)


def parse_step(text, default_gap):
    """'status@20' -> ('status', 20.0)."""
    if "@" in text:
        cmd, _, secs = text.rpartition("@")
        try:
            return cmd.strip(), float(secs)
        except ValueError:
            pass
    return text.strip(), default_gap


def main():
    ap = argparse.ArgumentParser(description="Send console commands to an ESP32 and show replies.")
    ap.add_argument("--port", required=True)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--boot", action="store_true", help="pulse reset and capture the boot banner first")
    ap.add_argument("--boot-wait", type=float, default=4.0, help="seconds to read the boot banner")
    ap.add_argument("--gap", type=float, default=1.5, help="default seconds to wait after each step")
    ap.add_argument("--step", action="append", default=[],
                    help="command to send, optionally 'cmd@seconds' (repeatable)")
    ap.add_argument("--quiet-drain", action="store_true", help="do not print per-step wait stats")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        ser = serial.Serial(args.port, args.baud, timeout=0.1)
    except serial.SerialException as exc:
        print("ERROR: cannot open %s: %s" % (args.port, exc), file=sys.stderr)
        return 2

    out = []
    try:
        if args.boot:
            reset_board(ser)
            drain(ser, args.boot_wait, out, quiet=True)
        else:
            drain(ser, 0.4, out, quiet=True)

        for raw in args.step:
            cmd, wait = parse_step(raw, args.gap)
            if cmd:                      # 空命令 = 纯等待（'@40'），用来跨过最短停机窗口
                ser.write((cmd + "\r\n").encode("ascii", errors="replace"))
                ser.flush()
                print(">>> %s   (wait %.1fs)" % (cmd, wait))
            else:
                print(">>> (sleep)   (wait %.1fs)" % wait)
            drain(ser, wait, out, quiet=args.quiet_drain)
            while out:
                sys.stdout.write(out.pop(0))
                sys.stdout.flush()
    finally:
        ser.close()

    sys.stdout.write("".join(out))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
