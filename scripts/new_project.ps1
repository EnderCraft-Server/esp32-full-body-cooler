<#
.SYNOPSIS
    Scaffold a new PlatformIO project inside the workspace.

.EXAMPLE
    .\scripts\new_project.ps1 -Name blink-led
    .\scripts\new_project.ps1 -Name esp32-test -Template esp32-classic
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string] $Name,

    [ValidateSet('s3-n16r8', 's3-generic', 'esp32-classic')]
    [string] $Template = 's3-n16r8',

    [string] $Workspace = 'D:\dsh_Workspaces\ESP32',

    [switch] $Force
)

$ErrorActionPreference = 'Stop'

$ProjectDir = Join-Path (Join-Path $Workspace 'projects') $Name

if ((Test-Path -LiteralPath $ProjectDir) -and -not $Force) {
    throw "project already exists: $ProjectDir  (pass -Force to overwrite)"
}

$IniS3N16R8 = @'
; ESP32-S3-N16R8  --  16 MB QIO flash + 8 MB OPI PSRAM
[platformio]
default_envs = esp32-s3-n16r8

[env:esp32-s3-n16r8]
platform  = espressif32
board     = esp32-s3-devkitc-1
framework = arduino

; Stock board def assumes 8 MB flash and NO PSRAM -- override both.
board_build.mcu                 = esp32s3
board_build.flash_mode          = qio
board_build.arduino.memory_type = qio_opi
board_upload.flash_size         = 16MB
board_build.partitions          = default_16MB.csv

board_build.f_cpu   = 240000000L
board_build.f_flash = 80000000L

; BOARD_HAS_PSRAM is REQUIRED: without it esp32-hal-psram.h #undef's
; CONFIG_SPIRAM and psramFound() stays false even though memory_type is right.
build_flags =
    -DBOARD_HAS_PSRAM
    -DARDUINO_USB_MODE=1
    -DARDUINO_USB_CDC_ON_BOOT=0
    -DLED_PIN=48

monitor_speed = 115200
upload_speed  = 921600
'@

$IniS3Generic = @'
; Generic ESP32-S3 (no PSRAM assumed) -- safe starting point
[platformio]
default_envs = esp32-s3

[env:esp32-s3]
platform  = espressif32
board     = esp32-s3-devkitc-1
framework = arduino

monitor_speed = 115200
upload_speed  = 921600
'@

$IniEsp32Classic = @'
; Classic ESP32 (ESP32-WROOM-32 / esp32dev)
[platformio]
default_envs = esp32dev

[env:esp32dev]
platform  = espressif32
board     = esp32dev
framework = arduino

monitor_speed = 115200
upload_speed  = 921600
'@

$MainCpp = @'
#include <Arduino.h>

/*
 * Bring-up sketch: confirm the toolchain, then print a heartbeat.
 * Build :  ..\..\scripts\pio.ps1 run
 * Upload:  ..\..\scripts\pio.ps1 run -t upload --upload-port COM5
 * Serial:  ..\..\.venv\Scripts\python.exe ..\..\scripts\serial_capture.py --port COM5 --seconds 10
 */

#ifndef LED_PIN
#define LED_PIN 48
#endif

void setup() {
  Serial.begin(115200);
  delay(1500);
  pinMode(LED_PIN, OUTPUT);

  Serial.println();
  Serial.println(F("--- boot ---"));
  Serial.printf("chip       : %s (%d cores)\n", ESP.getChipModel(), ESP.getChipCores());
  Serial.printf("cpu        : %u MHz\n", (unsigned)getCpuFrequencyMhz());
  Serial.printf("arduino    : %d.%d.%d\n", ESP_ARDUINO_VERSION_MAJOR,
                ESP_ARDUINO_VERSION_MINOR, ESP_ARDUINO_VERSION_PATCH);
  Serial.printf("flash      : %u MB\n", (unsigned)(ESP.getFlashChipSize() / (1024 * 1024)));
  Serial.printf("psram      : %u bytes\n", (unsigned)ESP.getPsramSize());
  Serial.println(F("--- running ---"));
}

void loop() {
  static uint32_t tick = 0;
  static bool on = false;

  on = !on;
  digitalWrite(LED_PIN, on ? HIGH : LOW);
  Serial.printf("tick %lu  heap=%u  psram=%u\n", (unsigned long)tick++,
                (unsigned)ESP.getFreeHeap(), (unsigned)ESP.getFreePsram());
  delay(1000);
}
'@

$Gitignore = @'
.pio/
.vscode/
*.pyc
__pycache__/
'@

New-Item -ItemType Directory -Force -Path (Join-Path $ProjectDir 'src') | Out-Null

switch ($Template) {
    's3-n16r8'      { $ini = $IniS3N16R8 }
    's3-generic'    { $ini = $IniS3Generic }
    'esp32-classic' { $ini = $IniEsp32Classic }
}

# Write UTF-8 WITHOUT a BOM.  Windows PowerShell 5.1's "-Encoding UTF8" emits a
# BOM, and PlatformIO's ini parser then fails with
# "File contains no section headers" because it never sees the leading '['.
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $ProjectDir 'platformio.ini'), $ini,      $Utf8NoBom)
[System.IO.File]::WriteAllText((Join-Path $ProjectDir 'src\main.cpp'),  $MainCpp,  $Utf8NoBom)
[System.IO.File]::WriteAllText((Join-Path $ProjectDir '.gitignore'),    $Gitignore, $Utf8NoBom)

Write-Host "[new_project] created $ProjectDir  (template: $Template)"
Write-Host ""
Write-Host "Next:"
Write-Host "    cd $ProjectDir"
Write-Host "    ..\..\scripts\pio.ps1 run"
Write-Host "    ..\..\scripts\pio.ps1 run -t upload --upload-port COM5"
