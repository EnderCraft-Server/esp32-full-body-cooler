<#
.SYNOPSIS
    PlatformIO launcher pinned to this workspace.

.DESCRIPTION
    Runs PlatformIO Core from the workspace-local virtualenv and redirects every
    scratch location (core dir, temp, pip cache) into the workspace itself, so
    nothing leaks into the user profile.

    This script deliberately declares NO param() block.  PowerShell then hands
    every argument -- including pio's own flags such as -e / -t / -v -- straight
    through $args untouched.  With a param() block, PowerShell would try to bind
    -e and -t as script parameters and fail before pio ever sees them.

.EXAMPLE
    cd projects\hello-s3
    ..\..\scripts\pio.ps1 run -e esp32-s3-n16r8

.EXAMPLE
    .\scripts\pio.ps1 run -d projects\hello-s3 -t upload
#>

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot

$env:PLATFORMIO_CORE_DIR                 = Join-Path $Root '.platformio'
$env:TEMP                                = Join-Path $Root '.tmp'
$env:TMP                                 = $env:TEMP
$env:PIP_CACHE_DIR                       = Join-Path $Root '.tmp\pip-cache'
$env:PLATFORMIO_SETTING_ENABLE_TELEMETRY = 'No'
$env:PYTHONUTF8                          = '1'
$env:PYTHONIOENCODING                    = 'utf-8'
$env:PYTHONUNBUFFERED                    = '1'

# --- Optional outbound proxy ------------------------------------------------
# PlatformIO pulls ~700 MB of toolchains from dl.registry.platformio.org, which
# is frequently throttled to well under 20 kB/s on some networks.  Put the
# proxy URL in <workspace>\.pio-proxy (one line, e.g. http://127.0.0.1:7897)
# and package downloads are routed through it.  An explicitly set HTTPS_PROXY
# always wins; a configured-but-dead proxy falls back to a direct connection.
$ProxyFile = Join-Path $Root '.pio-proxy'
if (-not $env:HTTPS_PROXY -and (Test-Path -LiteralPath $ProxyFile)) {
    $proxy = (Get-Content -LiteralPath $ProxyFile -Raw).Trim()
    if ($proxy) {
        try {
            $uri = [uri]$proxy
            $probe = New-Object System.Net.Sockets.TcpClient
            $probe.Connect($uri.Host, $uri.Port)
            $probe.Close()
            $env:HTTP_PROXY  = $proxy
            $env:HTTPS_PROXY = $proxy
        } catch {
            Write-Warning "[pio] proxy $proxy is not reachable - connecting directly"
        }
    }
}

foreach ($d in @($env:TEMP, $env:PIP_CACHE_DIR, $env:PLATFORMIO_CORE_DIR)) {
    if (-not (Test-Path -LiteralPath $d)) {
        New-Item -ItemType Directory -Force -Path $d | Out-Null
    }
}

$python = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw "Workspace virtualenv is missing: $python  ->  run .\scripts\bootstrap.ps1"
}

& $python -m platformio @args
exit $LASTEXITCODE
