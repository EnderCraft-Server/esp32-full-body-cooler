# 故障排查

按「症状」查表，再到下面找详细解释。带 ★ 的是本项目实际踩过的坑。

## 速查表

| 症状 | 最可能原因 | 一句话修复 |
|---|---|---|
| ★ `requires an interactive terminal on stdin` | 用了 `pio device monitor` | 改用 `scripts/serial_capture.py` |
| ★ `'class EspClass' has no member named 'getCoreVersion'` | 该 API 在 arduino-esp32 2.x 不存在 | 用 `ESP_ARDUINO_VERSION_MAJOR` 宏 |
| ★ PSRAM 恒为 0，其它一切正常 | 只设了 `memory_type`，漏了 `-DBOARD_HAS_PSRAM` | 加 `-DBOARD_HAS_PSRAM` |
| ★ `PermissionError: [Errno 13] Permission denied ... tmpXXXX` | 沙箱里 `mkdtemp` 的 DACL 顶掉了能力 ACE | 装 `sitecustomize.py` 补丁 |
| ★ 下载卡在 `Downloading 0%` 几分钟不动 | 直连 registry 被限速到 ~17 kB/s | 配置 `.pio-proxy` |
| ★ `Got unexpected extra argument` | `-d` 写在了子命令前面 | 写成 `run -d <dir><` |
| ★ `A parameter cannot be found that matches parameter name 'e'` | 包装脚本声明了 `param()` | 包装脚本不要有 param 块 |
| `Looking for upload port...` 之后失败或选错口 | CH343 不匹配板定义的 hwids | 显式 `--upload-port COM5` |
| `Failed to connect to ESP32-S3: Timed out waiting for packet header` | 没进下载模式 / 口被占用 | 见下文「连不上」 |
| 串口输出乱码 | 波特率不对 | `monitor_speed` / `--baud` 对齐 115200 |
| 上电后反复重启 | memory_type 选错 / 分区表越界 | 见下文「bootloop」 |
| `Sketch too big` / 分区放不下 | app 分区太小 | 换 `default_16MB.csv` 或 `huge_app.csv` |
| `warning: "CORE_DEBUG_LEVEL" redefined` | 框架和自己都定义了 | 无害；或加 `build_unflags` |
| `This command is deprecated ... use 'pio pkg install'` | `platform install` 已弃用 | 或用 `pio pkg install -g -p espressif32` |
| ★ `File contains no section headers` | platformio.ini 存成了**带 BOM** 的 UTF-8 | 用无 BOM 的 UTF-8 重写 |

## ★ 连不上板子（Failed to connect / Timed out）

按顺序排查：

1. **口对不对**：`--upload-port COM5`。CH343 是 `VID_1A86 PID_55D3`，
   不是 Espressif 的 `303A`，板定义里的 hwids 匹配不到它。
2. **口被占用**：串口监视器、另一个 pio 进程、VSCode 串口插件都会占住口。被占用通常报
   `could not open port ... Access is denied`。
3. **没进下载模式**：ESP32-S3 靠 CH343 的 DTR/RTS 自动进下载模式。精简板若省掉了自动复位电路，
   就要手动：**按住 BOOT → 点一下 RST → 松开 BOOT**，再立刻重跑上传。
4. **供电/线材**：劣质线会让烧录中途掉线。换线，或插机箱后面的 USB 口。
5. **降速**：`upload_speed = 115200`（默认 921600）。

手动复位时序就是这两根线：

```python
ser.setDTR(False)
ser.setRTS(True)     # RTS -> EN 拉低 = 复位
time.sleep(0.12)
ser.setRTS(False)
```

## ★ bootloop / 一上电就重启

八成是 `memory_type` 选错。日志里会出现：

```
rst:0x3 (RTC_SW_SYS_RST),boot:0x8 (SPI_FAST_FLASH_BOOT)
invalid header: 0xffffffff
```

对照 `.platformio\packages\framework-arduinoespressif32\tools\sdk\esp32s3\` 下的目录名
（`qio_opi` / `qio_qspi` / `opi_opi` …）挑一个。
封装内 8 MB PSRAM 的 ESP32-S3 → `qio_opi`。

改完必须 `-t clean`：memory_type 会换掉 `sections.ld` 和静态库，
增量编译可能留下不一致的目标文件。

## ★ PSRAM 显示 0 / `psramFound()` 为 false

两个开关缺一不可，见 `references/PLATFORMIO_INI.md` 的「PSRAM 的两个开关」。确认顺序：

```powershell
# 1. 烧录日志里有没有 Embedded PSRAM 8MB -> 证明板子硬件确实有
.\scripts\pio.ps1 run -d .\projects\hello-s3 -t upload --upload-port COM5 | Select-String "PSRAM|Chip is"

# 2. ini 里三个字段都在
Select-String -Path .\projects\hello-s3\platformio.ini -Pattern "memory_type|BOARD_HAS_PSRAM|flash_size"
```

## ★ flash 容量不对（显示 8 MB 或 4 MB）

`esp_flash_get_size()` 返回的是运行时探测值，一般可信。如果显示 8 MB，要么板子真不是
16 MB，要么 `board_upload.flash_size` 没设对。两个字段都要对上：
`board_upload.flash_size = 16MB` 与 `board_build.partitions = default_16MB.csv`。

最硬的自检是 esptool 烧录日志：

```
Chip is ESP32-S3 (QFN56) (revision v0.2)
Features: WiFi, BLE, Embedded PSRAM 8MB (AP_3v3)
```

## ★ File contains no section headers（platformio.ini 带 BOM）

```
InvalidProjectConfError: Invalid 'platformio.ini' (project configuration file):
'File contains no section headers.
```

Windows PowerShell 5.1 的 `Set-Content -Encoding UTF8` 会写入 **UTF-8 BOM**（`EF BB BF`），
PlatformIO 的 ini 解析器看到开头是 BOM 而不是 `[`，就认定整份文件没有任何 section。文件内容看起来
完全正常，只有头三个字节不对 —— 用十六进制看一眼即可确认：

```powershell
$b = [System.IO.File]::ReadAllBytes('.\projects\my-app\platformio.ini')
($b[0..2] | ForEach-Object { $_.ToString('X2') }) -join ' '   # EF BB BF = 有 BOM，要修
```

修法：用无 BOM 的 UTF-8 重写（`Out-File -Encoding utf8NoBOM` 是 PowerShell 7+ 才有的，
5.1 上要用 .NET）：

```powershell
$text  = Get-Content '.\projects\my-app\platformio.ini' -Raw
$noBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Resolve-Path '.\projects\my-app\platformio.ini'), $text, $noBom)
```

`scripts/new_project.ps1` 已经用 `WriteAllText + UTF8Encoding($false)` 生成文件，
不会踩这个坑。本机 `pwsh` 实为 Windows PowerShell 5.1，所以这条要一直留意。

## ★ 沙箱环境：temp 目录 PermissionError

```
PermissionError: [Errno 13] Permission denied: 'D:\...\.tmp\tmpab12cd\x.txt'
```

这是 DSH 文件沙箱特有的：沙箱靠父目录上一条**可继承的能力 ACE** 授予写权限，而 CPython 的
`tempfile.mkdtemp()` 会按 mode `0o700` 向 Windows 请求一条**显式 DACL**，
把继承来的 ACE 顶掉了 —— 刚建好的目录自己都写不进去。pip / ensurepip 全靠私有临时目录暂存文件，
于是直接崩。

`scripts/dsh_sandbox_shim.py` 把 `os.mkdir` 的 mode 强制回默认值修好这件事，
`bootstrap.ps1` 会把它装成 venv 的 `sitecustomize.py`（每个进程自动加载）。
这一步**必须早于 ensurepip**，否则 pip 自己都装不上。

## ★ 下载慢 / 看起来卡住

直连 `dl.registry.platformio.org` 实测 ~17 kB/s，走本地代理 ~248 kB/s（14 倍）。
代理地址写在 `.pio-proxy`（一行，如 `http://127.0.0.1:7897`），
`pio.ps1` 先探测端口再决定用不用，端口不通自动回退直连。

另外：`Out-String` 这类管道会把输出全部缓冲住，看起来像"卡死"，其实在正常下载。
要看实时进度就别套 `Out-String`。

## ★ 包装脚本参数传不进去

```powershell
# 错：声明了 param 块 -> PowerShell 抢走 -e / -t 并报绑定失败
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$PioArgs)
& $python -m platformio @PioArgs
```

正确做法是**不写 param 块**，直接用 `$args`：

```powershell
& $python -m platformio @args
```

实测：无 param 块时 `run -e x -t upload -v` 六个 token 原样进 `$args`。

## ★ 串口工具报 requires an interactive terminal

pio 的 monitor 在非 TTY 环境直接拒绝运行。用技能自带的：

```powershell
.\.venv\Scripts\python.exe .\scripts\serial_capture.py --port COM5 --seconds 10 --reset
.\.venv\Scripts\python.exe .\scripts\serial_capture.py --port COM5 --seconds 5 --expect "boot OK"
```

`--expect` 让它能当断言用：找到退出 0，没找到退出 1，完全无数据退出 3。

## API 版本坑（arduino-esp32 2.0.17）

| 想做的事 | 2.0.17 里的写法 |
|---|---|
| Arduino 内核版本 | `ESP_ARDUINO_VERSION_MAJOR/MINOR/PATCH`（**没有** `getCoreVersion()`） |
| 芯片型号 | `ESP.getChipModel()` |
| 芯片核数 | `ESP.getChipCores()` |
| 芯片修订号 | `ESP.getChipRevision()` — S3 + IDF 4.4 上恒为 0，**不可信**，以 esptool 日志为准 |
| PSRAM | `ESP.getPsramSize()` / `ESP.getFreePsram()` |
| flash 容量 | `esp_flash_get_size(NULL, &size)`（需 `#include <esp_flash.h><`） |
| MAC | `esp_read_mac(mac, ESP_MAC_WIFI_STA)`（需 `#include <esp_mac.h><`） |

## 万一还是不行

从干净状态重建（会重下 ~700 MB，确认代理可用）：

```powershell
Remove-Item -Recurse -Force .venv, .platformio
.\scripts\bootstrap.ps1
.\scripts\pio.ps1 run -d .\projects\hello-s3 -t upload --upload-port COM5
.\.venv\Scripts\python.exe .\scripts\serial_capture.py --port COM5 --seconds 8 --reset
```
