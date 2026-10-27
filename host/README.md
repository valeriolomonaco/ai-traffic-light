# Connect the lamp to Claude Code

## 1. Install the serial library

```bash
python -m pip install -r host/requirements.txt
```

## 2. Check the lamp is found

Plug the board in with a data cable, then:

```bash
python host/claude_light.py --list
```

The board's port is marked `<- would be used`. If nothing is marked, set the port yourself,
for example `COM5` on Windows, in the environment variable `CLAUDE_LIGHT_PORT`.

Send a test state by hand:

```bash
python host/claude_light.py Y "athlete paper"
```

## 3. Add the hooks

Copy the `hooks` block of [hooks-example.json](hooks-example.json) into your Claude Code user settings
file, `~/.claude/settings.json` (on Windows `C:\Users\<you>\.claude\settings.json`). If that file already
has a `hooks` block, merge the events into it rather than replacing it.

Replace `PATH/TO/ai-traffic-light` with the folder where you cloned this repository, using forward
slashes, for example `D:/0 GITHUBS/AI-TRAFFIC-LIGHT/ai-traffic-light`. Keep the escaped quotes
around the path because it may contain spaces.

| Hook event | Letter | Lamp |
|---|---|---|
| `SessionStart` | `R` | red, ready for your first prompt |
| `UserPromptSubmit` | `G` | green while Claude Code works |
| `Notification` (permission or question) | `Y` | breathing yellow, it needs you |
| `Stop` | `R` | red, finished, your turn |
| `SessionEnd` | `O` | off |

Restart Claude Code after editing the settings. The project name on the screen is the folder name
of the session.

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `CLAUDE_LIGHT_PORT` | auto | Serial port of the lamp. |
| `CLAUDE_LIGHT_BAUD` | `9600` | Must match `BAUD` in the sketch. |
| `CLAUDE_LIGHT_BOOT_DELAY` | `2.0` | Seconds to wait after opening the port. |

**About the two-second wait.** Many boards restart when a program opens their USB port, and they
need about two seconds before they listen. The script tries to avoid the restart, and waits anyway
to be safe, so each hook takes about two seconds. To check whether your board restarts, set the
delay to 0 and send a few states by hand. If the lamp still follows every command, keep it at 0.

## Notes

- The script never blocks or fails Claude Code. If the lamp is unplugged it prints a short
  message and exits normally.
- One lamp shows one state. With several Claude Code sessions open, it shows the latest event
  from any of them, and the project name tells you which one.
- After you approve a permission, the lamp stays yellow until Claude Code finishes. For green
  again right after approval, add a `PostToolUse` hook that sends `G`. It runs after every tool
  call, so only add it once the boot delay is 0.
