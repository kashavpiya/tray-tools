param([switch]$NoLaunch)
$ErrorActionPreference = 'Stop'
$installDir = Join-Path $env:LOCALAPPDATA 'TrayTools'
New-Item -ItemType Directory -Force $installDir | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'tools\*.py') $installDir -Force
$venv = Join-Path $installDir '.venv'
python -m venv $venv
if ($LASTEXITCODE -ne 0) { throw 'Python 3.10 or newer is required.' }
$python = Join-Path $venv 'Scripts\python.exe'
$pythonw = Join-Path $venv 'Scripts\pythonw.exe'
& $python -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $python (Join-Path $installDir 'audio_switcher.py') --configure
if ($LASTEXITCODE -ne 0) { throw 'Audio setup failed. Run the installer again.' }
$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
foreach ($tool in @(@('LogitechMouseBattery', 'mouse_battery.py'), @('AudioSwitcher', 'audio_switcher.py'))) {
    $script = Join-Path $installDir $tool[1]
    New-ItemProperty -Path $runKey -Name $tool[0] -Value ('"' + $pythonw + '" "' + $script + '"') -PropertyType String -Force | Out-Null
    if (-not $NoLaunch) { Start-Process $pythonw -ArgumentList ('"' + $script + '"') -WindowStyle Hidden }
}
Write-Host "Installed in $installDir. Both tools will start when you sign in."
