"""Collect licenses for the Windows binaries from the build environment."""
from importlib import metadata
from pathlib import Path
import sys

destination = Path(__file__).parent / 'dist' / 'THIRD_PARTY_NOTICES.txt'
sections = ['Tray Tools binary distribution: third-party notices\n']
for name in ['Pillow', 'pystray', 'websocket-client', 'pycaw', 'comtypes', 'psutil', 'six', 'pyinstaller']:
    dist = metadata.distribution(name)
    sections.append(f'\n{"=" * 72}\n{name} {dist.version}\n')
    found = False
    for item in dist.files or []:
        if any(word in item.name.lower() for word in ('license', 'copying')) and dist.locate_file(item).is_file():
            sections.append(dist.locate_file(item).read_text(encoding='utf-8', errors='replace'))
            found = True
    if not found:
        raise RuntimeError(f'No bundled license found for {name}')
python_license = Path(sys.base_prefix) / 'LICENSE.txt'
sections.extend(['\nPython runtime and bundled components\n', python_license.read_text(encoding='utf-8')])
for license_file in (Path(sys.base_prefix) / 'tcl').rglob('license.terms'):
    sections.extend(['\nTcl/Tk license\n', license_file.read_text(encoding='utf-8')])
destination.parent.mkdir(exist_ok=True)
destination.write_text('\n'.join(sections), encoding='utf-8')
print('Wrote THIRD_PARTY_NOTICES.txt')
