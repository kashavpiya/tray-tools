"""Windows notification-area battery display, using the local Logitech G HUB API."""
import ctypes
from contextlib import closing
import json
import os
from pathlib import Path
import sys
import threading
import time
import winreg
import websocket
import pystray
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
STOP = threading.Event()
REFRESH = threading.Event()
mutex = ctypes.windll.kernel32.CreateMutexW(None, False, 'Local\\LogitechMouseBatteryTray')
if ctypes.windll.kernel32.GetLastError() == 183:
    sys.exit(0)

def artwork(value=None, charging=False):
    image = Image.new('RGBA', (64, 64))
    draw = ImageDraw.Draw(image)
    color = '#64dfaa' if charging else '#ff7777' if value is not None and value <= 20 else '#ffffff'
    text = '--' if value is None else str(value)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 44 if len(text) < 3 else 33)
    draw.text((32, 28), text, font=font, fill=color, anchor='mm', stroke_width=1)
    draw.rounded_rectangle((5, 55, 59, 61), radius=3, fill='#4d5663')
    if value:
        draw.rounded_rectangle((5, 55, 5 + max(3, int(54 * value / 100)), 61), radius=3, fill=color)
    return image

def request(ws, path):
    token = str(time.monotonic_ns())
    ws.send(json.dumps(dict(msgId=token, verb='GET', path=path, origin='local')))
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        reply = json.loads(ws.recv())
        if reply.get('msgId') == token:
            if reply.get('result', {}).get('code') != 'SUCCESS':
                raise RuntimeError('G HUB request failed')
            return reply.get('payload', {})
    raise TimeoutError('G HUB response timed out')

def update(icon):
    while not STOP.is_set():
        try:
            with closing(websocket.create_connection('ws://localhost:9010', timeout=5, origin='file://', subprotocols=['json'])) as ws:
                devices = request(ws, '/devices/list').get('deviceInfos', [])
                mice = [d for d in devices if d.get('deviceType') == 'MOUSE' and d.get('capabilities', {}).get('hasBatteryStatus')]
                if not mice:
                    raise RuntimeError('No Logitech wireless mouse found')
                mouse = next((d for d in mice if d.get('state') == 'ACTIVE'), mice[0])
                name = mouse.get('displayName', 'Logitech mouse')
                if mouse.get('state') != 'ACTIVE':
                    icon.icon = artwork()
                    icon.title = f'{name}: sleeping or disconnected'
                    state = dict(name=name, percentage=None, status='sleeping or disconnected')
                else:
                    battery = request(ws, '/battery/' + mouse['id'] + '/state')
                    value = battery.get('percentage')
                    if not isinstance(value, (int, float)) or not 0 <= value <= 100:
                        raise RuntimeError('Battery percentage unavailable')
                    value = round(value)
                    charging = battery.get('charging', False)
                    icon.icon = artwork(value, charging)
                    icon.title = f'{name}: {value}%' + (' (charging)' if charging else '')
                    state = dict(name=name, percentage=value, charging=charging)
                state['updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
                (BASE / 'status.json').write_text(json.dumps(state, indent=2))
        except Exception as error:
            icon.icon = artwork()
            icon.title = 'Mouse battery unavailable: open G HUB and wake your mouse'
            (BASE / 'status.json').write_text(json.dumps(dict(percentage=None, error=str(error), updated=time.strftime('%Y-%m-%d %H:%M:%S')), indent=2))
        REFRESH.wait(30)
        REFRESH.clear()

def quit_app(icon, item):
    STOP.set()
    REFRESH.set()
    icon.stop()

def startup_enabled():
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
        try:
            winreg.QueryValueEx(key, 'LogitechMouseBattery')
            return True
        except FileNotFoundError:
            return False

def toggle_startup(icon, item):
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
        if startup_enabled():
            winreg.DeleteValue(key, 'LogitechMouseBattery')
        else:
            winreg.SetValueEx(key, 'LogitechMouseBattery', 0, winreg.REG_SZ, f'"{Path(sys.executable).with_name("pythonw.exe")}" "{Path(__file__).resolve()}"')

def open_ghub(icon, item):
    os.startfile(r'C:\Program Files\LGHUB\lghub.exe')

icon = pystray.Icon('LogitechMouseBattery', artwork(), 'Mouse battery: connecting', menu=pystray.Menu(
    pystray.MenuItem('Refresh battery', lambda icon, item: REFRESH.set(), default=True),
    pystray.MenuItem('Open Logitech G HUB', open_ghub),
    pystray.MenuItem('Start when I sign in', toggle_startup, checked=lambda item: startup_enabled()),
    pystray.MenuItem('Exit', quit_app),
))

def setup(icon):
    icon.visible = True
    threading.Thread(target=update, args=(icon,), daemon=True).start()

if __name__ == '__main__':
    icon.run(setup)
