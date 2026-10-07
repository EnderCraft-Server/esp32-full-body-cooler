<#
.SYNOPSIS
    Build the ESP32 / PlatformIO environment in this workspace from scratch.

.DESCRIPTION
    Idempotent.  Re-run it after deleting .venv and/or .platformio to rebuild
    everything.  Nothing is installed into the user profile: the virtualenv, the
    PlatformIO core directory and all scratch space live inside this folder.

    Steps
      1. python -m venv --without-pip .venv
      2. drop the DSH sandbox shim in as sitecustomize.py   (must be step 2 --
         ensurepip itself stages through a private temp dir)
      3. bootstrap pip with ensurepip
      4. pip install platformio
      5. pio platform install espressif32   (~700 MB of toolchains)
#>
[CmdletBinding()]
param(
    [string] $Python = 'python',
    [switch] $SkipPlatform
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root '.venv'
$Py   = Join-Path $Venv 'Scripts\python.exe'

Write-Host "[bootstrap] workspace : $Root"

# --- 1. virtualenv ----------------------------------------------------------
if (-not (Test-Path -LiteralPath $Py)) {
    Write-Host "[bootstrap] creating virtualenv (--without-pip)"
    & $Python -m venv --without-pip $Venv
    if ($LASTEXITCODE -ne 0) { throw "venv creation failed" }
} else {
    Write-Host "[bootstrap] virtualenv already present"
}

# --- 2. sandbox shim --------------------------------------------------------
# CPython's tempfile.mkdtemp() asks Windows for an explicit DACL derived from
# mode 0o700.  That explicit DACL drops the DSH sandbox's inheritable write
# capability ACE, so every later write into the directory fails with EACCES and
# pip / ensurepip cannot stage files at all.  Installing the shim as
# sitecustomize.py patches os.mkdir for every process using this interpreter.
$SitePackages = Join-Path $Venv 'Lib\site-packages'
New-Item -ItemType Directory -Force -Path $SitePackages | Out-Null
$ShimSource = Join-Path $PSScriptRoot 'dsh_sandbox_shim.py'
$ShimTarget = Join-Path $SitePackages 'sitecustomize.py'
Copy-Item $ShimSource $ShimTarget -Force
Write-Host "[bootstrap] sandbox shim installed as sitecustomize.py"

# --- 3. pip -----------------------------------------------------------------
& $Py -m pip --version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[bootstrap] bootstrapping pip"
    & $Py -m ensurepip --upgrade
    if ($LASTEXITCODE -ne 0) { throw "ensurepip failed" }
}
Write-Host "[bootstrap] pip: $(& $Py -m pip --version)"

# --- 4. PlatformIO Core -----------------------------------------------------
& $Py -m pip install --upgrade platformio
if ($LASTEXITCODE -ne 0) { throw "pip install platformio failed" }

# --- 5. espressif32 platform -------------------------------------------------
if (-not $SkipPlatform) {
    Write-Host "[bootstrap] installing espressif32 platform (this downloads ~700 MB)"
    & (Join-Path $PSScriptRoot 'pio.ps1') platform install espressif32
    if ($LASTEXITCODE -ne 0) { throw "platform install failed" }
}

Write-Host ""
Write-Host "[bootstrap] done.  Verify with:"
Write-Host "    .\scripts\pio.ps1 --version"
Write-Host "    .\scripts\pio.ps1 run -d .\projects\hello-s3"
