# 硬件与串口

## 找 COM 口

```powershell
# 最省事：列出所有串口名
[System.IO.Ports.SerialPort]::GetPortNames()

# 端口 -> 设备映射（WMI 被沙箱挡住时的替代方案）
Get-ItemProperty 'HKLM:\HARDWARE\DEVICEMAP\SERIALCOMM'
```

后者输出形如：

```
\Device\Serial0 : COM1
\Device\Serial2 : COM5
```

`Get-CimInstance Win32_PnPEntity` 和 `Win32_SerialPort` 在沙箱里会报
`拒绝访问 (0x80041003)`，用上面的注册表读法代替。

要拿「这个 COM 口是什么芯片」，读 USB 枚举注册表：

```powershell
Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Enum\USB' |
  Where-Object PSChildName -match '1A86|303A|10C4' |
  Select-Object -ExpandProperty PSChildName
```

更完整的一条（拿到友好名，直接带 COM 号）：

```powershell
Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Enum\USB\VID_1A86&PID_55D3' | ForEach-Object {
  $p = Get-ItemProperty $_.PSPath
  "{0}  ->  {1}" -f $_.PSChildName, $p.FriendlyName
}
```

## 常见 USB 转串口芯片对照

| VID / PID | 芯片 | 说明 |
|---|---|---|
| `1A86 / 55D3` | **CH343** | 本板使用；WCH 高速 UART 桥 |
| `1A86 / 7523` | CH340 | 最常见的廉价桥 |
| `1A86 / 55D4` | CH9102 | CH340 的替代 |
| `10C4 / EA60` | CP2102 | Silicon Labs |
| `303A / 1001` | **ESP32-S3 原生 USB** | USB-Serial-JTAG 外设，不是 UART 桥 |

**本机实况**：`USB-Enhanced-SERIAL CH343 (COM5)` —— ESP32-S3 通过 **UART 桥**连接。

### 原生 USB 与 UART 桥的区别（很重要）

| | UART 桥（本板 CH343） | 原生 USB（`303A`） |
|---|---|---|
| 下载通道 | UART0，靠 DTR/RTS 自动复位 | USB-Serial-JTAG 外设 |
| 板定义 hwids 能否匹配 | **不能**（板定义写的是 `303A/1001`） | 能 |
| 固件 `Serial` 输出 | 直接就是 UART0，开箱即用 | 需 `ARDUINO_USB_CDC_ON_BOOT=1` |
| 上传参数 | 必须显式 `--upload-port` | 可自动识别 |

所以本板 `build_flags` 里是 `-DARDUINO_USB_CDC_ON_BOOT=0`。

## 复位 / 进下载模式

自动复位电路：**RTS → EN（复位）**，**DTR → GPIO0（启动模式）**。esptool 会自动组合这两根线；
进不去就手动 **按住 BOOT → 点 RST → 松 BOOT**。

用 pyserial 主动复位（`serial_capture.py --reset` 就是这么做的）：

```python
ser.setDTR(False)
ser.setRTS(True)      # 拉低 EN = 复位
time.sleep(0.12)
ser.setRTS(False)     # 松开 = 运行
time.sleep(0.05)
```

## 板载 LED

ESP32-S3-DevKitC-1 的板载 WS2812 RGB LED：

| 板版本 | GPIO |
|---|---|
| v1.1 | **48** |
| v1.0 | 38 |

`projects/hello-s3` 默认 `-DLED_PIN=48`（在 `build_flags` 里改）。
它是 **WS2812 可寻址灯**，不是普通 LED：`digitalWrite` 只能亮/灭/闪，
要颜色得用 `neopixelWrite(pin, r, g, b)` 或 Adafruit_NeoPixel 库。
第三方克隆板的 LED 引脚可能完全不同，不亮属正常。

## 用 esptool 独立确认板子身份

不确定手上是什么板时，只读信息不烧录：

```powershell
.\.venv\Scripts\python.exe .\.platformio\packages\tool-esptoolpy\esptool.py --port COM5 --no-stub flash_id
```

日志里 `Embedded PSRAM 8MB (AP_3v3)` 这一条就是判断 PSRAM 有无的唯一依据。

## 波特率

| 用途 | 值 |
|---|---|
| 应用串口输出（`Serial.begin()`） | 115200 |
| pio 监视器 `monitor_speed` | 115200 |
| 上传 `upload_speed` | 921600（不稳就降到 115200 / 460800） |

`upload_speed` 和 `monitor_speed` 是**两回事**：前者是烧录时临时协商的高速率，
后者是你读日志用的。
