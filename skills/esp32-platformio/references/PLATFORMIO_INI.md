# platformio.ini 参考

## 三层配置，越靠下优先级越高

1. **platform 默认** — `.platformio\platforms\espressif32\` 里的脚本行为
2. **board 定义** — `.platformio\platforms\espressif32\boards\<board>.json`
3. **platformio.ini 的 `[env:*]`** — 你写的东西覆盖上面两层

`board = esp32-s3-devkitc-1` 的真实内容是（节选）：

```json
"build": {
  "arduino": { "ldscript": "esp32s3_out.ld", "partitions": "default_8MB.csv" },
  "extra_flags": ["-DARDUINO_ESP32S3_DEV", "-DARDUINO_USB_MODE=1"],
  "f_cpu": "240000000L", "flash_mode": "qio", "mcu": "esp32s3", "variant": "esp32s3"
},
"name": "Espressif ESP32-S3-DevKitC-1-N8 (8 MB QD, No PSRAM)",
"upload": { "flash_size": "8MB", "maximum_size": 8388608, "speed": 460800 }
```

注意它自称 **N8 / No PSRAM** —— N16R8 的一切都要靠 ini 覆盖。

## ESP32-S3-N16R8 完整模板

```ini
[platformio]
default_envs = esp32-s3-n16r8

[env:esp32-s3-n16r8]
platform  = espressif32
board     = esp32-s3-devkitc-1
framework = arduino

; --- 模块差异（N16R8 靠这 5 行覆盖 N8 板定义）---
board_build.mcu                 = esp32s3
board_build.flash_mode          = qio
board_build.arduino.memory_type = qio_opi
board_upload.flash_size         = 16MB
board_build.partitions          = default_16MB.csv

; --- 时钟 ---
board_build.f_cpu   = 240000000L
board_build.f_flash = 80000000L

; --- 宏 ---
build_flags =
    -DBOARD_HAS_PSRAM          ; 必须！否则 PSRAM 被内核 undef 掉
    -DARDUINO_USB_MODE=1
    -DARDUINO_USB_CDC_ON_BOOT=0 ; CH343 走 UART0，不用原生 USB CDC

; --- 主机通信 ---
monitor_speed = 115200
upload_speed  = 921600
```

## memory_type 的六个取值

由 `tools\sdk\esp32s3\` 下的预编译库目录决定，命名格式是 `<flash>_<psram>`：

| 取值 | flash | PSRAM | 典型模块 |
|---|---|---|---|
| `qio_qspi` | Quad | Quad SPI | N8R2 |
| `qio_opi` | Quad | **Octal** | **N16R8 / N8R8** |
| `opi_opi` | Octal | Octal | 用 OPI flash 的板子 |
| `opi_qspi` | Octal | Quad | 少见 |
| `dio_qspi` / `dio_opi` | Dual | Quad / Octal | 兼容性优先 |

选错的后果：`opi_*` 系列会让 `_get_board_flash_mode()` 强制改用 `dout` 启动，
并链接到错误的 `sections.ld`，通常直接 bootloop 或 PSRAM 初始化失败。

**怎么判断**：`esptool` 烧录日志出现 `Features: WiFi, BLE, Embedded PSRAM 8MB (AP_3v3)`
说明 PSRAM 在封装内。ESP32-S3 封装内的 8 MB PSRAM 是八线（Octal）的 → `qio_opi`。

## PSRAM 的两个开关（最容易漏）

| 开关 | 作用 | 漏掉的症状 |
|---|---|---|
| `board_build.arduino.memory_type = qio_opi` | 选对预编译 SDK 静态库 | bootloop / PSRAM 初始化失败 |
| `-DBOARD_HAS_PSRAM` | 阻止内核 `#undef CONFIG_SPIRAM` | **能启动、串口正常、PSRAM 恒为 0** |

内核源码 `cores\esp32\esp32-hal-psram.h`：

```c
#ifndef BOARD_HAS_PSRAM
#ifdef CONFIG_SPIRAM_SUPPORT
#undef CONFIG_SPIRAM_SUPPORT
#endif
#ifdef CONFIG_SPIRAM
#undef CONFIG_SPIRAM
#endif
#endif
```

## 分区表

`board_build.partitions` 的值是 `tools\partitions\` 下的文件名。16 MB flash 常用：

| 文件 | app 分区 | 用途 |
|---|---|---|
| `default_16MB.csv` | 2 x 6.25 MB (OTA) | 默认选择 |
| `large_spiffs_16MB.csv` | 小 app + 大 SPIFFS | 要塞文件系统 |
| `app3M_fat9M_16MB.csv` | 2 x 3 MB + 9 MB FAT | 需要 FAT 分区 |
| `huge_app.csv` | 单 app，无 OTA | 不用 OTA 时 |

`default_16MB.csv` 实际内容：

```
# Name,   Type, SubType, Offset,  Size, Flags
nvs,      data, nvs,     0x9000,  0x5000,
otadata,  data, ota,     0xe000,  0x2000,
app0,     app,  ota_0,   0x10000, 0x640000,
app1,     app,  ota_1,   0x650000,0x640000,
spiffs,   data, spiffs,  0xc90000,0x360000,
coredump, data, coredump,0xFF0000,0x10000,
```

编译日志里 `Flash: [ ] 4.3% (used 282965 bytes from 6553600 bytes)` 的
`6553600` = `0x640000` 正是 app0 大小 —— 这行能直接确认分区表生效了。

## 常用 build_flags

```ini
build_flags =
    -DBOARD_HAS_PSRAM          ; PSRAM 必须
    -DCORE_DEBUG_LEVEL=3       ; 0=NONE 1=ERROR 2=WARN 3=INFO 4=DEBUG 5=VERBOSE
    -DARDUINO_USB_CDC_ON_BOOT=0
    -DCONFIG_ARDUINO_LOOP_STACK_SIZE=8192
    -I include                 ; 额外头文件目录
    -D MY_FLAG=42              ; 自己定义的编译期开关
```

`-DCORE_DEBUG_LEVEL` 会和框架自带的定义撞车，出现
`warning: "CORE_DEBUG_LEVEL" redefined`。无害（后出现的生效）；
想彻底干净就加 `build_unflags = -DCORE_DEBUG_LEVEL=0` 先取消框架的定义。

## 多环境与 default_envs

```ini
[platformio]
default_envs = esp32-s3-n16r8        ; 不设的话 pio run 会把每个 env 都编一遍

[env:esp32-s3-n16r8]
board = esp32-s3-devkitc-1
framework = arduino

[env:esp32-s3-n16r8-debug]
extends = env:esp32-s3-n16r8
build_type = debug
build_flags =
    ${env:esp32-s3-n16r8.build_flags}
    -DCORE_DEBUG_LEVEL=5
```

`${env:name.build_flags}` 是 ini 的变量插值语法（不是 shell 展开）。
`build_type = debug` 会换一套编译参数，因此**整个 Arduino 框架要重编**（首次 3–10 分钟）。
只想要详细日志的话，加 `-DCORE_DEBUG_LEVEL=5` 就够了，不必开 `build_type`。

## 其它常用字段

```ini
lib_deps =
    adafruit/Adafruit NeoPixel@^1.12.0
    https://github.com/me/mylib.git
    file://../local_lib

lib_ldf_mode           = chain+   ; 依赖扫描模式，deep+ 太慢时用 chain+
board_build.filesystem = littlefs
extra_scripts          = pre:extra.py
```

## 其它板子模板

```ini
; ESP32-S3 通用（无 PSRAM，或不确定型号时先跑通再说）
[env:esp32-s3]
platform  = espressif32
board     = esp32-s3-devkitc-1
framework = arduino

; ESP32 经典（ESP32-WROOM-32）
[env:esp32dev]
platform  = espressif32
board     = esp32dev
framework = arduino
monitor_speed = 115200
```

## 自查命令

```powershell
# 看某块板到底怎么定义的
Get-Content .\.platformio\platforms\espressif32\boards\esp32-s3-devkitc-1.json

# 列出所有 S3 板
Get-ChildItem .\.platformio\platforms\espressif32\boards\*s3*.json | Select-Object -ExpandProperty Name

# 列出可用分区表
Get-ChildItem .\.platformio\packages\framework-arduinoespressif32\tools\partitions\*.csv

# 确认 memory_type 的合法取值（SDK 库目录名就是取值全集）
Get-ChildItem .\.platformio\packages\framework-arduinoespressif32\tools\sdk\esp32s3 -Directory
```

现成的 R8N16 参考板定义可直接对照：
`.platformio\platforms\espressif32\boards\4d_systems_esp32s3_gen4_r8n16.json` —— 它同时用了
`"memory_type": "qio_opi"`、`"partitions": "default_16MB.csv"` 和
`"-DBOARD_HAS_PSRAM"`，与本项目做法完全一致。
