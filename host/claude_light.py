#!/usr/bin/env python3
"""Send a Claude Code state to the AI Traffic Light lamp over USB serial.

Usage:
    python claude_light.py G|Y|R|O [project name]
    python claude_light.py --list          # show serial ports and which one would be used

States: G working, Y waiting for you, R ready (finished), O idle/off.

When Claude Code runs this as a hook it passes a JSON object on stdin. The project
name is then taken from its "cwd" field (the session's folder name), unless a name
is given on the command line.

Environment variables (all optional):
    CLAUDE_LIGHT_PORT        serial port, e.g. COM5 or /dev/ttyUSB0 (default: auto-detect)
    CLAUDE_LIGHT_BAUD        serial speed (default 9600, must match the sketch)
    CLAUDE_LIGHT_BOOT_DELAY  seconds to wait after opening the port (default 2.0).
                             Many boards reset when the port opens and need ~2 s
                             before they listen. Set to 0 if yours does not reset.

The script never fails a hook: any problem is printed to stderr and it exits 0.
"""

import json
import os
import sys
import time

STATES = {"G", "Y", "R", "O"}

# USB vendor IDs of the chips found on common Nano and ESP32 boards.
KNOWN_VIDS = {
    0x1A86: "CH340",
    0x10C4: "CP210x",
    0x0403: "FTDI",
    0x2341: "Arduino",
    0x303A: "Espressif",
}


def log(msg):
    print(f"claude_light: {msg}", file=sys.stderr)


def project_from_hook_input():
    """Return the session folder name from the hook JSON on stdin, or None."""
    if sys.stdin is None or sys.stdin.isatty():
        return None
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (ValueError, OSError):
        return None
    cwd = data.get("cwd") if isinstance(data, dict) else None
    if not cwd:
        return None
    return os.path.basename(os.path.normpath(cwd))


def clean_name(name):
    """Keep the name printable and short enough for one OLED line."""
    name = "".join(ch if 32 <= ord(ch) < 127 else "?" for ch in name)
    return name.strip()[:21]


def find_port(list_ports):
    wanted = os.environ.get("CLAUDE_LIGHT_PORT")
    if wanted:
        return wanted
    for p in list_ports.comports():
        if p.vid in KNOWN_VIDS:
            return p.device
    return None


def list_and_exit(list_ports):
    chosen = find_port(list_ports)
    ports = list(list_ports.comports())
    if not ports:
        print("No serial ports found. Is the board plugged in with a data cable?")
    for p in ports:
        chip = KNOWN_VIDS.get(p.vid, "")
        mark = "  <- would be used" if p.device == chosen else ""
        print(f"{p.device:12} {chip:10} {p.description}{mark}")
    if chosen and chosen not in {p.device for p in ports}:
        print(f"CLAUDE_LIGHT_PORT is set to {chosen}")
    sys.exit(0)


def send(port, line, baud, boot_delay, serial):
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baud
    ser.timeout = 1
    ser.write_timeout = 2
    # Keeping DTR/RTS low avoids the auto-reset on many boards (works on Windows
    # for most CH340/CP2102 boards). The boot delay covers boards that reset anyway.
    ser.dtr = False
    ser.rts = False
    ser.open()
    try:
        if boot_delay > 0:
            time.sleep(boot_delay)
        ser.reset_input_buffer()
        ser.write((line + "\n").encode("ascii", "replace"))
        ser.flush()
    finally:
        ser.close()


def main(argv):
    try:
        import serial
        from serial.tools import list_ports
    except ImportError:
        log("pyserial is not installed. Run: python -m pip install pyserial")
        return 0

    if len(argv) >= 2 and argv[1] == "--list":
        list_and_exit(list_ports)

    if len(argv) < 2 or argv[1].upper() not in STATES:
        log("usage: claude_light.py G|Y|R|O [project name]   or   claude_light.py --list")
        return 0

    state = argv[1].upper()
    if len(argv) > 2:
        project = " ".join(argv[2:])
    else:
        project = project_from_hook_input() or os.path.basename(os.getcwd())
    line = f"{state} {clean_name(project)}".strip()

    port = find_port(list_ports)
    if not port:
        log("no lamp found (set CLAUDE_LIGHT_PORT or run with --list)")
        return 0

    try:
        baud = int(os.environ.get("CLAUDE_LIGHT_BAUD", "9600"))
        boot_delay = float(os.environ.get("CLAUDE_LIGHT_BOOT_DELAY", "2.0"))
        send(port, line, baud, boot_delay, serial)
    except (serial.SerialException, OSError, ValueError) as exc:
        log(f"could not send to {port}: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
