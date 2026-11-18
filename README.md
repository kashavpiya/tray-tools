# Tray Tools

Small Windows utilities that live beside the clock.

| Tool | What it does |
| --- | --- |
| Mouse Battery | Shows a Logitech wireless mouse's battery percentage in the tray. Refreshes every 30 seconds and reconnects when G HUB returns. |
| Audio Switcher | Click once to toggle between two chosen audio outputs. The icon shows speakers or headphones. |

## Install

### Download the apps

Get `MouseBattery.exe` and `AudioSwitcher.exe` from the [latest release](https://github.com/kashavpiya/tray-tools/releases/latest). Python is bundled, so you can run these files directly on Windows x64.

Keep the executables in a permanent folder before enabling **Start when I sign in** from each tray menu. On its first launch, Audio Switcher opens a device picker. To change your pair later, right-click its icon and choose **Choose audio outputs...**. Settings are saved under `%LOCALAPPDATA%\TrayTools\AudioSwitcher`; Mouse Battery stores status under `%LOCALAPPDATA%\TrayTools\MouseBattery`.

These initial builds are unsigned, so Windows may show an unrecognized publisher prompt. Mouse Battery still needs G HUB running. Only launch one copy of each tool; exit older Python versions from their tray menus first.

### Run from source

Requires Windows 10/11 and Python 3.10 or newer, with `python` available in your terminal. Tested with Python 3.14. Mouse Battery also requires Logitech G HUB running locally.

Download or clone this repository, then open PowerShell in its folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Choose the two audio outputs when prompted. For SteelSeries setups, choose the Sonar Gaming output for headphones. The installer copies the apps into `%LOCALAPPDATA%\TrayTools`, creates a Python virtual environment, installs dependencies, and enables startup for your Windows account. Administrator access is not required.

If you already run an older copy, exit it from its tray menu before installing. The installer replaces the startup entries for these tools.

Windows may put the icons in the overflow menu. Drag them from **^** onto the taskbar to keep them visible.

## Use

- **Mouse Battery:** Hover for the percentage and charging state. Right-click to refresh, open G HUB, change startup, or exit. `--` means the mouse is asleep, disconnected, or unavailable.
- **Audio Switcher:** Left-click to toggle outputs. Right-click to select one directly, open sound settings, change startup, or exit. It changes the default playback output for media and communications; your microphone stays as configured.

To change the audio pair, exit Audio Switcher, then run:

```powershell
& "$env:LOCALAPPDATA\TrayTools\.venv\Scripts\python.exe" "$env:LOCALAPPDATA\TrayTools\audio_switcher.py" --configure
& "$env:LOCALAPPDATA\TrayTools\.venv\Scripts\pythonw.exe" "$env:LOCALAPPDATA\TrayTools\audio_switcher.py"
```

## Compatibility and limitations

Mouse Battery has been tested with the Logitech PRO X SUPERLIGHT 2. It uses G HUB's unofficial local WebSocket interface, which Logitech may change. Other G HUB wireless mice may work. Bluetooth-only devices and Logi Options+ are not supported by this implementation.

Audio Switcher has been tested with Realtek speakers and SteelSeries Sonar Gaming. Apps with an explicitly selected output may keep using that output. Sonar routing must already point to your headphones.

The tools write local status and diagnostic files beside their scripts. Device IDs, settings and logs are excluded from Git. Mouse Battery connects only to G HUB on localhost; Audio Switcher uses Windows audio APIs. Dependency installation requires internet access.

## Remove

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```

This stops this installation and removes its startup entries. The script leaves installed files in place so you can delete them yourself.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tools\audio_switcher.py --configure
.\.venv\Scripts\python.exe tools\audio_switcher.py
.\.venv\Scripts\python.exe tools\mouse_battery.py
```

Uses [pystray](https://github.com/moses-palmer/pystray), [Pillow](https://github.com/python-pillow/Pillow), [pycaw](https://github.com/AndreMiras/pycaw), and [websocket-client](https://github.com/websocket-client/websocket-client). These projects have their own licenses. G HUB protocol behavior was investigated with reference to [LogiBAT](https://github.com/someweirdhuman/LogiBAT).

Build executables on Windows with `powershell -ExecutionPolicy Bypass -File .\build.ps1`. The build installs pinned dependencies and PyInstaller, then puts the two executables in `dist\`. Release assets include third-party license notices.

MIT licensed. Contributions and bug reports are welcome. Keep personal device IDs and diagnostic files out of pull requests.
