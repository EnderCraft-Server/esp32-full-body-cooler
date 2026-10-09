# ESP32 全身降温器（背包式水冷） — `esp32-full-body-cooler`

用 ESP32-S3 主控 + 冰袋 + 365 隔膜泵 + 贴身软管循环水，做一件可以背着走的全身降温马甲。

```
冰袋 + 水 -> PET 密封罐 -> 365 泵 -> 8x11 软管（贴身循环）-> 回 PET 罐
                    ^                                  |
                    +---- DS18B20 水温 / 体表温度 ------+
                                  |
            ESP32-S3 -> 继电器 -> 泵间歇启停（慢 PWM）
```

**核心约束**：365 隔膜泵是有刷电机，**不能用 PWM 平滑调速**，只能整段启停。
固件用「回差 + 最短启停时间」做间歇控制 —— 本质是周期以秒/分钟计的慢 PWM。

---

## 仓库结构

```
esp32-full-body-cooler/
├── projects/
│   ├── body-cooler/          ★ 主项目（固件 + 文档 + CAD）
│   │   ├── src/              main / tempsensor / controller / inputs / console
│   │   ├── include/          config.h 是唯一的引脚与参数来源
│   │   ├── docs/             接线、密封、BOM、PCB 简报等 14 篇
│   │   ├── cad/              防折螺旋护套（3D 打印件）+ 生成脚本
│   │   └── wiring.html       交互式接线图（可隐藏单个元件、电流动画）
│   └── hello-s3/             参考工程：芯片自检 + PSRAM 读写测试
├── scripts/                  PlatformIO 工作区工具（见下）
├── skills/esp32-platformio/  可复用的 ESP32 开发 Skill
└── .pio-proxy                本地代理地址（一行），pio.ps1 自动探测启用
```

工作区是**自包含**的：Python venv、PlatformIO core dir、下载缓存、TEMP 全都在文件夹里，
不往用户目录写东西 —— 删掉整个文件夹即彻底卸载。

---

## 快速开始

```powershell
# 编译
.\scripts\pio.ps1 run -d .\projects\body-cooler

# 编译 + 烧录（串口必须显式指定）
.\scripts\pio.ps1 run -d .\projects\body-cooler -t upload --upload-port COM6

# 看串口（pio device monitor 在无 TTY 环境下不可用，用这个）
.venv\Scripts\python.exe .\scripts\serial_term.py --port COM6      # 交互式，能发命令
.venv\Scripts\python.exe .\scripts\serial_capture.py --port COM6 --seconds 10 --reset

# 脚本化发命令并抓回复
.venv\Scripts\python.exe .\scripts\serial_cmd.py --port COM6 --step "scan" --step "status@2"
```

`-d` 必须写在子命令**后面**。

**首次或换机器**：

```powershell
.\scripts\bootstrap.ps1        # 从零重建 venv + PlatformIO（约 700 MB）
```

---

## 硬件要点（踩过坑的，别再踩）

| 事项 | 结论 |
|---|---|
| **继电器触发电平** | 模块是**低电平触发(L)**：IN 短接 GND 吸合 |
| **继电器驱动方式** | 必须**开漏**：吸合推低 0V，释放引脚**高阻**。**绝不能推 3.3V** —— 模块 VCC 是 5V，光耦 LED 阴极接 IN，3.3V 时仍有微弱电流把继电器维持住，表现就是「说 pump=OFF 却一直转」 |
| **泵的电流路径** | `电池+ → 保险丝 → 继电器 COM → NO → 泵+ → 泵− → 电池−`，中间**不能有任何降压板** |
| **续流二极管** | 必须装，1N5822 反向并联在泵两端，阴极朝泵+ |
| **泵保护** | 软管一折就瘪 → 憋压 → 烧泵（已烧 2 台）。三道防线：水流传感器 / `maxrun` 连续运行上限 / **KSD9700 70°C 串在泵电源线上** |
| **贴身软管** | 6×8 硅胶管壁厚只有 1mm，压一下就瘪且撑不开。用 `cad/` 里的**防折螺旋护套**，或嵌进开槽 EVA 垫 |
| **DS18B20 角色映射** | NVS 键名上限 **15 字符**，早期版本用 `role_<16位ROM>`（21 字符）静默写入失败 → 重启后角色丢失 → 安全联锁锁死泵 |

完整踩坑记录见 `projects/body-cooler/docs/BENCH-TEST.md`。

---

## 文档索引

入口：**`projects/body-cooler/README.md`** —— 其中的
**「接线口述（控制端 + 输入端）」**一节是完整的分步接线说明（含逐条接线表，不含电容）。

| 文档 | 内容 |
|---|---|
| `docs/PROJECT-STATUS.md` | 当前状态、已完成 / 待办 |
| `docs/BENCH-TEST.md` | ★ 台架测试、事故记录、上电前检查表 |
| `docs/WIRING-GUIDE.md` | 接线总览与电路原理 |
| `docs/GPIO-MAP.md` | GPIO 完整映射（含禁用脚说明） |
| `docs/SEALING-REVIEW.md` | ★ 密封、冷凝、软管被吸瘪的排查 |
| `docs/BOM.md` | 采购清单（具体型号 + 搜索关键词 + 避坑） |
| `docs/PCB-BRIEF.md` | 给硬件工程师的 PCB 设计简报 |
| `docs/diagrams/` | 原理图与示意图（PNG + 生成脚本） |
| `hardware/README.md` | ★ 原理图源文件：嘉立创EDA 导入步骤、网络名一览、元件清单 |
| `cad/README.md` | ★ 3D 打印件：防折螺旋护套 + 转角导弯件 |

---

## 工具链版本

| 组件 | 版本 |
|---|---|
| Python | 3.14.7 |
| PlatformIO Core | 6.2.0 |
| platform | `espressif32@7.1.3` |
| framework | arduino-esp32 2.0.17（ESP-IDF 4.4.7） |
| 编译器 | xtensa-esp32s3 GCC 8.4.0 |
| 烧录器 | esptool 4.11.0 |
| 目标板 | ESP32-S3 **N16R8** — 16 MB QIO flash + 8 MB OPI PSRAM |

---

## 工作区工具（`scripts/`）

| 脚本 | 作用 |
|---|---|
| `pio.ps1` | 唯一的 pio 入口，自动配好所有环境变量与代理 |
| `env.ps1` | 在当前会话 dot-source 出 pio 函数 |
| `bootstrap.ps1` | 从零重建整个环境 |
| `serial_term.py` / `term.ps1` | 交互式串口终端（收 + 发） |
| `serial_capture.py` / `monitor.ps1` | 非交互串口抓取 |
| `serial_cmd.py` | 脚本化发命令并抓回复，支持 `cmd@秒数` |
| `new_project.ps1` | 按模板新建工程 |
| `dsh_sandbox_shim.py` | 修沙箱下 `tempfile.mkdtemp()` 的 PermissionError |

**两个环境适配点，别当成多余代码删掉**：

1. `dsh_sandbox_shim.py` — 沙箱通过父目录的可继承 ACE 授予写权限，
   而 Python 的 `tempfile.mkdtemp()` 会写入显式 DACL 把继承的 ACE 顶掉，
   导致 pip / ensurepip 无法暂存文件。补丁由 `bootstrap.ps1` 装成 venv 的
   `sitecustomize.py`，必须早于 `ensurepip`。
2. `.pio-proxy` — 直连 `dl.registry.platformio.org` 实测 ~17 kB/s，
   走本地代理 ~248 kB/s。`pio.ps1` 探测端口可达后自动启用，不通则回退直连。
