# Run the lamp in the Wokwi simulator

No hardware and no account needed. Pick the board you plan to buy: [nano](nano/) or [esp32](esp32/).

1. Go to [wokwi.com](https://wokwi.com) and under "Start from scratch" choose **Arduino Nano** or **ESP32**.
2. Replace the content of the `sketch.ino` tab with [firmware/sketch/sketch.ino](../firmware/sketch/sketch.ino).
   The same file works for both boards.
3. Replace the content of the `diagram.json` tab with `nano/diagram.json` or `esp32/diagram.json`.
   The ring and the screen appear already wired.
4. Click the small arrow next to the tabs, choose **New file**, name it `libraries.txt` and paste
   [libraries.txt](libraries.txt). This tells Wokwi which libraries to load.
5. Press the green play button.

The screen starts on `IDLE` with the ring off. Then type in the serial monitor at the bottom and
press Enter:

```
Y athlete paper
R veteran paper
G clickstream
O
```

| You type | Ring | Screen |
|---|---|---|
| `Y athlete paper` | breathing yellow | `WAITING`, athlete paper |
| `R veteran paper` | steady red | `READY`, veteran paper |
| `G clickstream` | steady green | `WORKING`, clickstream |
| `O` | off | `IDLE` |

The first letter sets the state and the rest is the project name. This is exactly the message the
Python script sends from the Claude Code hooks, so a simulation that behaves well means the real
device will behave the same.

If you move parts around in Wokwi, the wires follow. If a wire looks detached, check the pin names
in the wiring tables of [docs/BLUEPRINT.md](../docs/BLUEPRINT.md#3-wiring).
