# term.ps1 -- 交互式串口终端（能收也能发）
# 用法:  .\scripts\term.ps1 --port COM6
$ws = Split-Path -Parent $PSScriptRoot
$py = Join-Path $ws '.venv\Scripts\python.exe'
$t  = Join-Path $PSScriptRoot 'serial_term.py'
if (-not (Test-Path $py)) { Write-Error "找不到 venv python: $py"; exit 1 }
& $py $t @args