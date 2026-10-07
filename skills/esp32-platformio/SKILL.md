---
name: esp32-platformio
description: 用 PlatformIO 开发 ESP32 / ESP32-S3 固件。自包含工作区（项目内 venv + 本地 PlatformIO core dir）、platformio.ini 配置（含 ESP32-S3-N16R8 的 16MB QIO flash + 8MB OPI PSRAM 双重开关）、编译/上传/串口抓取、CH343 串口桥与 COM 口识别、沙箱与代理环境适配、编译上传故障排查。
whenToUse: 用户要新建/编译/上传/调试 ESP32 系列固件（尤其 ESP32-S3-N16R8），要改 platformio.ini、配置 PSRAM 或 flash 分区、串口看不到输出、上传失败、或要求"把程序烧进板子/让板子跑起来"时使用。
---

# ESP32 开发（PlatformIO）

本技能把「写代码 → 编译 → 烧录 → 看串口」这条链路固定下来。工作区在
`D:\dsh_Workspaces\ESP32`，**自包含**：Python venv、PlatformIO core dir、临时目录全部在项目内，
不往用户目录写任何东西，删掉文件夹即彻底卸载。

## 环境事实（已在本机实测）

| 项目 | 值 |
|---|---|
| 工作区 | `D:\dsh_Workspaces\ESP32` |
| 启动器 | `scripts\pio.ps1`（唯一入口，自动设好所有环境变量） |
| Python | 3.14.7（`.venv`，venv 用 `--without-pip` 创建后打补丁） |
| PlatformIO Core | 6.2.0 |
| 平台 | `espressif32@7.1.3` → arduino-esp32 **2.0.17**（ESP-IDF 4.4.7，xtensa GCC 8.4） |
| 串口桥 | CH343（VID `1A86` PID `55D3`）→ **COM5** |
| 目标板 | ESP32-S3 (QFN56) rev v0.2，**16 MB flash + 8 MB OPI PSRAM** |
| 工程目录 | `projects\` |

## 快速上手

所有命令都从工作区根目录执行；`-d` 必须写在子命令**后面**。

```powershell
# 编译（默认环境 esp32-s3-n16r8）
.\scripts\pio.ps1 run -d .\projects\hello-s3

# 编译 + 烧录（串口必须显式给，见下文「上传口」）
.\scripts\pio.ps1 run -d .\projects\hello-s3 -t upload --upload-port COM5

# 看串口（不要用 pio device monitor，见下文）
.\.venv\Scripts\python.exe .\scripts\serial_capture.py --port COM5 --seconds 10

# 清干净重来
.\scripts\pio.ps1 run -d .\projects\hello-s3 -t clean
```

产物在 `projects\<名>\.pio\build\<env>\firmware.bin`（和 `firmware.elf`）。

## 五个必须知道的坑

### 1. 不要用 pio device monitor（脚本 / agent 环境里）

pio device monitor 要求 stdin 是交互式终端，在管道、CI 或 agent 环境里会直接报错：

```
UserSideException: requires an interactive terminal on stdin
```

改用技能自带的 `scripts/serial_capture.py`（pyserial 直接读口，可指定时长、可断言关键字）：

```powershell
.\.venv\Scripts\python.exe .\scripts\serial_capture.py --port COM5 --seconds 10 --reset
.\.venv\Scripts\python.exe .\scripts\serial_capture.py --port COM5 --seconds 5 --expect "boot OK"
```

### 2. 上传口必须显式指定

板子通过板载 **CH343 UART 桥**连接，不是 ESP32-S3 原生 USB。而 `esp32-s3-devkitc-1`
板定义里的 `hwids` 是 `0x303A/0x1001`（Espressif 原生 USB），**匹配不到 CH343**，
自动选口可能失败或选错。永远显式写 `--upload-port COM5`。

### 3. PowerShell 包装脚本不能有 param() 块

`scripts/pio.ps1` 故意**不声明 param()**。一旦声明，PowerShell 会把
`-e` / `-t` / `-v` 当成自己的参数名去绑定并报错，pio 根本收不到。
无 param 块时所有参数原样进 `$args`，再用 `@args` 透传。

### 4. PSRAM 需要两个开关，缺一不可

`board_build.arduino.memory_type = qio_opi` 只负责选对预编译 SDK 库；
Arduino 内核还会因为 `esp32-hal-psram.h` 里这段把 PSRAM 整个编译掉：

```c
#ifndef BOARD_HAS_PSRAM
#undef CONFIG_SPIRAM
#endif
```

**所以必须再加 `-DBOARD_HAS_PSRAM`**。漏掉它的症状极具迷惑性：固件正常启动、
串口一切正常，只有 `ESP.getPsramSize()` 返回 0。

### 5. 依赖下载走代理（否则慢 14 倍）

`dl.registry.platformio.org` 在本机直连只有 **~17 kB/s**，走本地代理
（`127.0.0.1:7897`）是 **~248 kB/s**。代理地址写在 `.pio-proxy` 里，
`pio.ps1` 会探测端口可达性后自动启用；端口不通则自动回退直连。
首次装平台约 700 MB，务必确认代理生效。

## 新建工程

```powershell
.\scripts\new_project.ps1 -Name my-app -Template s3-n16r8
cd projects\my-app
..\..\scripts\pio.ps1 run
```

可选模板：`s3-n16r8`（默认）、`s3-generic`、`esp32-classic`。
`projects\hello-s3` 是参考实现，可直接复制改写。

## 改 platformio.ini 的套路

```ini
[platformio]
default_envs = esp32-s3-n16r8      ; 不然 pio run 会把所有 env 都编一遍

[env:esp32-s3-n16r8]
platform  = espressif32
board     = esp32-s3-devkitc-1     ; 通用 S3 板定义，N16R8 靠下面几行覆盖
framework = arduino

board_build.mcu                 = esp32s3
board_build.flash_mode          = qio
board_build.arduino.memory_type = qio_opi     ; 16MB QIO flash + 8MB OPI PSRAM
board_upload.flash_size         = 16MB
board_build.partitions          = default_16MB.csv
build_flags = -DBOARD_HAS_PSRAM               ; 见坑 4

monitor_speed = 115200
upload_speed  = 921600
```

完整字段说明、其它板子模板、分区表选择见 `references/PLATFORMIO_INI.md`。

## 怎么确认真的成了

串口打印里必须有这三行（`projects/hello-s3` 的 `main.cpp` 会逐项自检）：

```
flash size      : 16 MB
psram           : 8386279 bytes total, 8386035 bytes free
[ OK ] 1 MB PSRAM read/write test passed
```

esptool 烧录日志里还会有 `Features: WiFi, BLE, Embedded PSRAM 8MB (AP_3v3)`，
这是判断"这块板到底是不是 N16R8"最可靠的依据。

## 故障排查

遇到报错先查 `references/TROUBLESHOOTING.md`，覆盖：找不到串口 / 上传超时 /
Failed to connect / PSRAM 为 0 / flash 容量不对 / 分区表放不下 /
`pio run` 参数不识别 / 下载卡住 / 沙箱 PermissionError / 串口乱码。

## 硬件细节

COM 口识别（WMI 被沙箱挡住时用注册表）、复位时序、板载 RGB LED 引脚、
原生 USB 与 UART 桥的区别，见 `references/HARDWARE.md`。

## 文件清单（本技能 bundle）

```
SKILL.md
references/PLATFORMIO_INI.md     配置字段、memory_type 取值、分区表、其它板子模板
references/TROUBLESHOOTING.md    症状 -> 原因 -> 修复 速查表（带实测踩坑）
references/HARDWARE.md           COM 口识别、CH343、复位时序、板载 LED、波特率
scripts/serial_capture.py        非交互串口抓取，可直接当断言用
scripts/new_project.ps1          按模板新建工程（模板内嵌在脚本里）
scripts/pio.ps1                  工作区 pio 入口的副本
scripts/dsh_sandbox_shim.py      沙箱补丁的副本
```

工作区的 `pio.ps1` / `env.ps1` / `bootstrap.ps1` 住在
`D:\dsh_Workspaces\ESP32\scripts\`，跟环境一起走。`scripts\` 下那两份副本
只是为了让技能 bundle 单独拿出来也能读，改的时候记得同步。
