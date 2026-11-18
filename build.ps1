$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    python -m pip install -r requirements.txt 'pyinstaller==6.22.3'
    if ($LASTEXITCODE -ne 0) { throw 'Build dependency installation failed.' }
    foreach ($app in @(@('MouseBattery', 'mouse_battery.py'), @('AudioSwitcher', 'audio_switcher.py'))) {
        python -m PyInstaller --noconfirm --clean --onefile --windowed --name $app[0] (Join-Path 'tools' $app[1])
        if ($LASTEXITCODE -ne 0) { throw "Build failed: $($app[0])" }
    }
    python build_notices.py
    if ($LASTEXITCODE -ne 0) { throw 'License notice collection failed.' }
    Write-Host 'Executables are in dist\'
} finally {
    Pop-Location
}
