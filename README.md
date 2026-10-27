# AI Traffic Light

A small desk lamp that shows what Claude Code is doing, so you can look away from the screen
and still know when it needs you.

| Lamp | Screen | Meaning |
|---|---|---|
| Steady green | `WORKING` | Claude Code is busy on your prompt. |
| Breathing yellow | `WAITING` | Claude Code needs you: a permission or a question. |
| Steady red | `READY` | Claude Code has finished. Your turn. |
| Off | `IDLE` | No session running. |

The screen also shows the project name and how long the lamp has been in its current state.

It is built from an Arduino-compatible board (Arduino Nano or ESP32), a WS2812B LED ring and a
0.96 inch SSD1306 OLED screen, all connected with push-on jumper wires. No soldering is needed
for the board and the screen.

> This is a personal hobby project. It is not affiliated with or endorsed by Anthropic or Arduino.

## How it works

```
Claude Code hook  ->  host/claude_light.py  ->  USB serial  ->  board  ->  LED ring + OLED
```

Claude Code runs a hook at key moments: you send a prompt, it asks for permission, it stops.
Each hook calls the Python script with one letter, and the script sends a one-line message
such as `G athlete paper` to the board over USB. The board changes the ring colour and the screen.

## Repository layout

| Path | Content |
|---|---|
| [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md) | Step-by-step build: what to buy, assembly, testing, enclosure, troubleshooting. |
| [docs/BLUEPRINT.md](docs/BLUEPRINT.md) | Full blueprint: design, parts list, wiring, enclosure, timeline, roadmap. |
| [firmware/sketch/sketch.ino](firmware/sketch/sketch.ino) | Board firmware. The same file runs on the Nano and the ESP32. |
| [simulation/](simulation/) | Ready Wokwi projects for the Nano and the ESP32. |
| [host/claude_light.py](host/claude_light.py) | Python script that the hooks call to send the state. |
| [host/hooks-example.json](host/hooks-example.json) | Hook settings to paste into Claude Code. |

## Quick start

For the full walk-through from buying parts to a finished prototype, follow
[docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md). The short version:

1. **Try it in the simulator.** Follow [simulation/README.md](simulation/README.md). No hardware or account needed.
2. **Buy the parts.** See the shopping list in [docs/BLUEPRINT.md](docs/BLUEPRINT.md#2-shopping-list).
3. **Flash the board.** Open `firmware/sketch` in the Arduino IDE, install the three libraries listed
   in [simulation/libraries.txt](simulation/libraries.txt), pick your board and upload.
4. **Connect Claude Code.** Install the host script and the hooks, see [host/README.md](host/README.md).

## License

MIT, see [LICENSE](LICENSE). The Adafruit libraries used by the firmware keep their own licenses
(BSD for GFX and SSD1306, LGPL for NeoPixel) and are referenced, not copied.
