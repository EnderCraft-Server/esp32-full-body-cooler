# monitor.ps1 -- 打开串口看日志
# 自动用工作区 venv 里的 python（系统 python 装了个假的 serial 包，不能用）
#
# 用法：
#   .\scripts\monitor.ps1                     # COM6，默认 10 秒
#   .\scripts\monitor.ps1 -Port COM5 -Seconds 20
#   .\scripts\monitor.ps1 -Reset              # 先复位再抓（能抓到启动横幅）
#
# 想交互式发命令（scan / status 等）：用 Arduino IDE 的串口监视器，或 PuTTY

$ws  = Split-Path -Parent $PSScriptRoot
$py  = Join-Path $ws '.venv\Scripts\python.exe'
$cap = Join-Path $PSScriptRoot 'serial_capture.py'

if (-not (Test-Path $py))  { Write-Error "找不到 venv python: $py"; exit 1 }
if (-not (Test-Path $cap)) { Write-Error "找不到脚本: $cap"; exit 1 }

& $py $cap '-Port' $args 2>&1 | Out-Null   # 占位，实际直接用 @args
& $py $cap @args