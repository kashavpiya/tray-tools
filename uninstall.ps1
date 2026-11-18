$ErrorActionPreference = 'Stop'
$installDir = Join-Path $env:LOCALAPPDATA 'TrayTools'
Get-CimInstance Win32_Process -Filter "name='pythonw.exe'" | Where-Object {
    $_.ExecutablePath -eq (Join-Path $installDir '.venv\Scripts\pythonw.exe') -and
    ($_.CommandLine -like '*mouse_battery.py*' -or $_.CommandLine -like '*audio_switcher.py*')
} | ForEach-Object { Stop-Process -Id $_.ProcessId }
foreach ($name in 'LogitechMouseBattery','AudioSwitcher') {
    $key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
    $value = Get-ItemPropertyValue -Path $key -Name $name -ErrorAction SilentlyContinue
    if ($value -and $value.Contains($installDir)) { Remove-ItemProperty -Path $key -Name $name }
}
Write-Host "Startup entries removed and tools stopped. You can delete $installDir manually."
