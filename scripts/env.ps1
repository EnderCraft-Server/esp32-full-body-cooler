<#
.SYNOPSIS
    Activate the workspace PlatformIO environment in the CURRENT PowerShell session.

.DESCRIPTION
    Dot-source it so the variables persist:

        . .\scripts\env.ps1

    Afterwards `pio` is available as a function bound to this workspace.
#>

$Root = Split-Path -Parent $PSScriptRoot

$env:PLATFORMIO_CORE_DIR                 = Join-Path $Root '.platformio'
$env:TEMP                                = Join-Path $Root '.tmp'
$env:TMP                                 = $env:TEMP
$env:PIP_CACHE_DIR                       = Join-Path $Root '.tmp\pip-cache'
$env:PLATFORMIO_SETTING_ENABLE_TELEMETRY = 'No'
$env:PYTHONUTF8                          = '1'
$env:PYTHONIOENCODING                    = 'utf-8'

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
            Write-Host "[pio] routing downloads through $proxy"
        } catch {
            Write-Warning "[pio] proxy $proxy is not reachable - connecting directly"
        }
    }
}

foreach ($d in @($env:TEMP, $env:PIP_CACHE_DIR, $env:PLATFORMIO_CORE_DIR)) {
    if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
}

function global:pio {
    & (Join-Path $Root '.venv\Scripts\python.exe') -m platformio @args
}

Set-Alias -Name platformio -Value pio -Scope Global -Force

Write-Host "[pio] workspace : $Root"
Write-Host "[pio] core dir  : $env:PLATFORMIO_CORE_DIR"
Write-Host "[pio] python    : $Root\.venv\Scripts\python.exe"