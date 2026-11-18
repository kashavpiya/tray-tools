"""One-click notification-area audio output switcher. Run with --configure first."""
import ctypes
import json
import logging
import os
from pathlib import Path
import sys
import threading
import subprocess
import winreg
import comtypes
import pystray
from PIL import Image, ImageDraw
from pycaw.pycaw import AudioUtilities
from pycaw.constants import ERole

FROZEN = getattr(sys, 'frozen', False)
BASE = Path(os.environ['LOCALAPPDATA']) / 'TrayTools' / 'AudioSwitcher' if FROZEN else Path(__file__).resolve().parent
BASE.mkdir(parents=True, exist_ok=True)
CONFIG = BASE / 'audio_config.json'

def startup_command():
    if FROZEN:
        return f'"{sys.executable}"'
    return f'"{Path(sys.executable).with_name("pythonw.exe")}" "{Path(__file__).resolve()}"'

def configure_gui():
    import tkinter as tk
    from tkinter import ttk, messagebox
    root = tk.Tk()
    root.title('Audio Switcher setup')
    root.geometry('620x260')
    root.resizable(False, False)
    devices = AudioUtilities.GetAllDevices(data_flow=0, device_state=1)
    saved = False
    if len(devices) < 2:
        messagebox.showerror('Audio Switcher', 'Connect at least two audio outputs, then open Audio Switcher again.', parent=root)
        root.destroy()
        return False
    frame = ttk.Frame(root, padding=24)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Choose the two outputs to switch between.').pack(anchor='w', pady=(0, 14))
    names = [d.FriendlyName for d in devices]
    ttk.Label(frame, text='Speakers (first output)').pack(anchor='w')
    first = ttk.Combobox(frame, values=names, state='readonly', width=80)
    first.pack(fill='x', pady=(3, 12))
    first.current(0)
    ttk.Label(frame, text='Headphones (second output)').pack(anchor='w')
    second = ttk.Combobox(frame, values=names, state='readonly', width=80)
    second.pack(fill='x', pady=(3, 12))
    second.current(1)
    try:
        previous = json.loads(CONFIG.read_text())
        ids = [d.id for d in devices]
        if previous['speakers'] in ids:
            first.current(ids.index(previous['speakers']))
        if previous['headphones'] in ids:
            second.current(ids.index(previous['headphones']))
    except (OSError, ValueError, KeyError):
        pass
    def save():
        nonlocal saved
        if first.current() == second.current():
            messagebox.showerror('Choose different outputs', 'Select two different audio outputs.', parent=root)
            return
        CONFIG.write_text(json.dumps(dict(speakers=devices[first.current()].id, headphones=devices[second.current()].id), indent=2))
        saved = True
        root.destroy()
    ttk.Button(frame, text='Save', command=save).pack(anchor='e')
    root.mainloop()
    return saved

def configure():
    devices = AudioUtilities.GetAllDevices(data_flow=0, device_state=1)
    for index, device in enumerate(devices, 1):
        print(f'{index}. {device.FriendlyName}')
    if len(devices) < 2:
        raise SystemExit('Connect at least two audio outputs first.')
    def choose(prompt):
        while True:
            try:
                index = int(input(prompt))
                if 1 <= index <= len(devices):
                    return devices[index - 1].id
            except ValueError:
                pass
            print('Enter a number from the list.')
    first = choose('Speakers (first output): ')
    second = choose('Headphones (second output): ')
    if first == second:
        raise SystemExit('Choose two different outputs. Run --configure again.')
    CONFIG.write_text(json.dumps(dict(speakers=first, headphones=second), indent=2))
    print('Saved. Restart Audio Switcher to use these outputs.')

if '--configure' in sys.argv or '--configure-gui' in sys.argv:
    if FROZEN or '--configure-gui' in sys.argv:
        configure_gui()
    else:
        configure()
    sys.exit(0)
if '--self-test' in sys.argv:
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    devices = AudioUtilities.GetAllDevices(data_flow=0, device_state=1)
    result = dict(devices=len(devices), default_available=AudioUtilities.GetSpeakers() is not None, tkinter=True)
    root.destroy()
    (BASE / 'self-test.json').write_text(json.dumps(result))
    sys.exit(0)
if not CONFIG.exists() and not configure_gui():
    sys.exit(0)
settings = json.loads(CONFIG.read_text())
SPEAKERS = settings['speakers']
HEADPHONES = settings['headphones']
TARGETS = {SPEAKERS: 'Speakers', HEADPHONES: 'Headphones'}
STOP = threading.Event()
LOCK = threading.RLock()
RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
logging.basicConfig(filename=BASE / 'audio_switcher.log', level=logging.WARNING)

def artwork(headphones=False, unknown=False):
    im = Image.new('RGBA', (64, 64))
    d = ImageDraw.Draw(im)
    color = '#a1aab7' if unknown else '#72dbff' if headphones else '#ffffff'
    if headphones:
        d.arc((10, 7, 54, 57), 180, 360, fill=color, width=7)
        d.rounded_rectangle((7, 28, 20, 53), radius=5, fill=color)
        d.rounded_rectangle((44, 28, 57, 53), radius=5, fill=color)
    else:
        d.rounded_rectangle((7, 24, 22, 43), radius=3, fill=color)
        d.polygon([(18, 24), (35, 11), (35, 55), (18, 43)], fill=color)
        d.arc((24, 15, 55, 51), -65, 65, fill=color, width=5)
        d.arc((22, 6, 64, 60), -60, 60, fill=color, width=4)
    return im

def current():
    device = AudioUtilities.GetSpeakers()
    return device.id if device else None

def update(icon):
    global SPEAKERS, HEADPHONES, TARGETS
    settings = json.loads(CONFIG.read_text())
    SPEAKERS, HEADPHONES = settings['speakers'], settings['headphones']
    TARGETS = {SPEAKERS: 'Speakers', HEADPHONES: 'Headphones'}
    device_id = current()
    name = TARGETS.get(device_id, 'Another audio output')
    icon.icon = artwork(device_id == HEADPHONES, device_id not in TARGETS)
    icon.title = f'Audio: {name} — click to switch'
    (BASE / 'status.json').write_text(json.dumps(dict(output=name, device_id=device_id), indent=2))
    icon.update_menu()

def select(icon, target):
    comtypes.CoInitialize()
    try:
        with LOCK:
            active = {d.id for d in AudioUtilities.GetAllDevices(data_flow=0, device_state=1)}
            if target not in active:
                icon.notify(f'{TARGETS[target]} is disconnected or disabled.', 'Audio Switcher')
                return
            AudioUtilities.SetDefaultDevice(target, roles=[ERole.eConsole, ERole.eMultimedia, ERole.eCommunications])
            if current() != target:
                raise RuntimeError('Windows did not confirm the selected output')
            update(icon)
    except Exception:
        logging.exception('Could not switch output')
        icon.notify('Could not switch audio. Check that the device is connected.', 'Audio Switcher')
    finally:
        comtypes.CoUninitialize()

def toggle(icon, item):
    comtypes.CoInitialize()
    try:
        select(icon, SPEAKERS if current() == HEADPHONES else HEADPHONES)
    finally:
        comtypes.CoUninitialize()

def startup():
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        try:
            winreg.QueryValueEx(key, 'AudioSwitcher')
            return True
        except FileNotFoundError:
            return False

def toggle_startup(icon, item):
    enabled = startup()
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        if enabled:
            winreg.DeleteValue(key, 'AudioSwitcher')
        else:
            winreg.SetValueEx(key, 'AudioSwitcher', 0, winreg.REG_SZ,
                startup_command())

def change_outputs(icon, item):
    command = [sys.executable, '--configure'] if FROZEN else [str(Path(sys.executable).with_name('pythonw.exe')), str(Path(__file__).resolve()), '--configure-gui']
    subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)

def quit_app(icon, item):
    STOP.set()
    icon.stop()

def monitor(icon):
    comtypes.CoInitialize()
    try:
        while not STOP.is_set():
            try:
                with LOCK:
                    update(icon)
            except Exception:
                logging.exception('Could not read output')
                icon.title = 'Audio Switcher: waiting for Windows audio'
            STOP.wait(3)
    finally:
        comtypes.CoUninitialize()

def main():
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, 'Local\\AudioSwitcherTray')
    if ctypes.windll.kernel32.GetLastError() == 183:
        return
    icon = pystray.Icon('AudioSwitcher', artwork(), 'Audio Switcher: starting', menu=pystray.Menu(
        pystray.MenuItem('Switch speakers / headphones', toggle, default=True),
        pystray.MenuItem('Speakers', lambda icon, item: select(icon, SPEAKERS)),
        pystray.MenuItem('Headphones', lambda icon, item: select(icon, HEADPHONES)),
        pystray.MenuItem('Choose audio outputs...', change_outputs),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Start when I sign in', toggle_startup, checked=lambda item: startup()),
        pystray.MenuItem('Windows sound settings', lambda icon, item: os.startfile('ms-settings:sound')),
        pystray.MenuItem('Exit', quit_app),
    ))
    def setup(icon):
        icon.visible = True
        threading.Thread(target=monitor, args=(icon,), daemon=True).start()
    icon.run(setup)
    ctypes.windll.kernel32.CloseHandle(mutex)

if __name__ == '__main__':
    main()
