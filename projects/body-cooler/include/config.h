// =============================================================================
//  config.h  --  引脚分配 / 可调参数 / 编译期开关
//
//  板子：ESP32-S3 DevKitC-1 (N16R8)
//
//  【硬性禁用的引脚】这些碰了就出问题：
//    GPIO 0 / 45 / 46  strapping 脚，上电电平决定启动模式
//    GPIO 3            JTAG 源选择 strapping
//    GPIO 19 / 20      原生 USB D- / D+
//    GPIO 26 ~ 32      内部 SPI flash
//    GPIO 33 ~ 37      OPI PSRAM（N16R8 用了就丢 8MB PSRAM）
//    GPIO 43 / 44      UART0，接板载 CH343 串口桥
//
//  【可用引脚】1 2 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 21 38 39 40 41 42 47 48
//  一共 25 个。详细映射见 docs/GPIO-MAP.md
// =============================================================================
#pragma once
#include <Arduino.h>

// ============================ 板级版本 ======================================
// rev1 = 已经烧录验证过的基础接线
// rev2 = rev1 + 新增输入（电池电压 / 水流 / 液位 / 急停 / I2C）
//
// **rev2 不移动任何 rev1 已有引脚**，是纯超集 —— 升级不需要重新接线，
// 只是在空闲引脚上多接几根线。
#define BOARD_REV  2

// ================================ 引脚 ======================================
// ---- rev1 已有（rev2 完全沿用，不要改）----
#define PIN_ONEWIRE        4    // DS18B20 单总线（5 个探头并联），4.7k 上拉到 3V3
#define PIN_RELAY_PUMP     5    // 继电器 1 -> 365 隔膜泵
#define PIN_RELAY_AUX1     6    // 继电器 2 -> 备用（风扇 / 二号泵）
#define PIN_RELAY_AUX2     7    // 继电器 3 -> 备用
#define PIN_RELAY_AUX3     15   // 继电器 4 -> 备用
#define PIN_RELAY_AUX4     16   // 继电器 5 -> 备用 / 主电源总闸
#define PIN_BUZZER         17   // 有源蜂鸣器（可选，不接也行）
#define PIN_LEAK_SENSOR    18   // 漏水检测
#define PIN_STATUS_LED     48   // 板载 WS2812 状态灯

// ---- rev2 新增（全部落在 rev1 没用的空闲脚上）----
#define PIN_BATT_ADC       1    // ADC1_CH0 电池电压分压
#define PIN_AUX_ADC        2    // ADC1_CH1 备用模拟输入（泵电流 / 压力）
#define PIN_I2C_SDA        8    // I2C 数据（OLED / INA219 / SHT30）
#define PIN_I2C_SCL        9    // I2C 时钟
#define PIN_FLOW           10   // 水流传感器（霍尔脉冲）
#define PIN_LEVEL          11   // 液位开关（浮子簧片）
#define PIN_ESTOP          21   // 总电源开关状态检测（可选，不用可空着）
#define PIN_BTN_A          38   // 按键 A（模式 / 配网）
#define PIN_BTN_B          39   // 按键 B（手动强制降温）

// 注意：GPIO 1 ~ 10 同时是 ADC1_CH0 ~ CH9。
// 电池采样必须走 ADC1 —— ESP32-S3 的 ADC2 在 WiFi 开启时不可用。
#define PIN_IS_ADC1(p)  ((p) >= 1 && (p) <= 10)

// ESP32-S3-DevKitC-1 v1.0 板载的是 WS2812 彩灯（GPIO48），普通 digitalWrite
// 点不亮它。如果你的板子是普通单色 LED，把这里改成 0。
#define LED_IS_WS2812      1

// ============================ 继电器有效电平 ================================
// 5V 光耦继电器模块分「高电平触发(H)」和「低电平触发(L)」两种，外形几乎一样，
// 有些模块板上还有跳线帽可以切换。
//
//   RELAY_ACTIVE_HIGH = 0  ->  ESP32 输出 LOW  = 泵开（低电平触发模块 L）★本项目
//   RELAY_ACTIVE_HIGH = 1  ->  ESP32 输出 HIGH = 泵开（高电平触发模块 H）
//
// ★ 实测确认：把模块的 IN 和 GND 短接，继电器吸合 -> 低电平触发(L)。本项目用 0。
//
// ★ 这里只是「出厂默认值」。运行时会从 NVS 读，串口 `relay high` / `relay low`
//   可以当场切换并保存，不用重新编译。
//
// ★ 安全电阻（复位期间 GPIO 是高阻，IN 悬空可能误吸合）：
//     低电平触发模块 -> IN 用 10k 上拉到 VCC(5V)   ★本项目
//     高电平触发模块 -> IN 用 10k 下拉到 GND
// ★★ 低电平触发模块必须用【开漏驱动】，不要用推挽：
//       吸合 = 引脚推低 0V        释放 = 引脚变高阻（悬空）
//   **绝对不要在释放时推 3.3V** —— 模块 VCC 是 5V，光耦 LED 的阴极接在 IN 上，
//   IN 停在 3.3V 时 LED 上还有 5-3.3-1.2≈0.5V 的压差，微弱电流足以把继电器维持住，
//   表现就是「固件说 pump=OFF，泵却一直转」。ESP32 又推不出 5V，推挽永远关不干净。
//   引脚高阻时 LED 没有回路 -> 彻底截止。
//
//   建议配一只 10k：模块 IN ──[10k]── 模块 VCC(5V)，把悬空状态明确拉到 5V，抗电机干扰。
//   串口 `relay pp` 可以切回推挽（高电平触发模块才需要推挽）。
#define RELAY_ACTIVE_HIGH  0

// ============================ 可选输入总开关 ================================
// 这些功能默认全部关闭：**没接线时引脚悬空会误报，板子会一直停在 FAULT**。
// 接好一根线、验证过读数，再打开对应的开关。
#define ENABLE_LEAK_SENSOR  0   // 漏水检测
#define ENABLE_BATT_SENSE   0   // 电池电压
#define ENABLE_FLOW_SENSOR  0   // 水流传感器
#define ENABLE_LEVEL_SWITCH 0   // 液位开关
#define ENABLE_ESTOP        0   // 急停按钮

// ============================ 漏水检测 ======================================
// 背包底部放两根相距 2~3mm 的裸铜线（不要镀锡，锡会钝化）。遇水导通 -> 立即
// 停泵并在串口/蜂鸣器报警。锂电池和水在同一个背包里，这条线值 2 毛钱。
#define LEAK_ACTIVE_LOW     1   // 1 = 遇水把引脚拉低（配内部上拉）

// ============================ 电池电压检测 ==================================
// 3S 锂电 12.6V 满 / 11.1V 标称 / 9.0V 空。分压到 2V 以内再进 ADC：
//   BAT+ ---[R1 100k]---+---[R2 18k]--- GND
//                       |
//                       +--- GPIO1（并在 R2 上跨一个 100nF，降低采样阻抗）
// 分压比 = (100 + 18) / 18 = 6.556  ->  12.6V 对应 1.92V，留足余量
#define BATT_DIV_R1_KOHM   100.0f
#define BATT_DIV_R2_KOHM    18.0f
#define BATT_DIV_FACTOR    ((BATT_DIV_R1_KOHM + BATT_DIV_R2_KOHM) / BATT_DIV_R2_KOHM)

#define BATT_FULL_V        12.60f   // 3S 满电
#define BATT_WARN_V        10.50f   // 3.50V/cell，该准备换电池了
#define BATT_STOP_V         9.60f   // 3.20V/cell，强制停泵保护电芯
#define BATT_ABSENT_V       6.00f   // 读不到这个值就是分压没接（ESP32 自己都要
                                    // 7V 以上才转得起来，不可能真这么低）
#define BATT_RECOVER_V      0.40f   // 恢复回差

// ============================ 水流传感器 ====================================
// YF-S401（0.3~6 L/min，5880 脉冲/升）或 YF-S201（1~30 L/min，450 脉冲/升）。
//
// 重要：这类传感器是 5V 供电、输出 5V 方波，**ESP32-S3 的 IO 不吃 5V**。
// 而且不能简单串个分压就完事 —— 分压电阻本身就是负载，会把高电平拽下来：
//     GPIO 高电平 = 5 * R2 / (Rpu + R1 + R2)
// 所以必须自己补一个强上拉，再分压：
//
//     5V ---[2.2k]---+--- 传感器 OUT
//                    |
//                  [10k] R1
//                    |
//                    +-------- GPIO10
//                    |
//                  [20k] R2
//                    |
//                   GND
//     5 * 20 / (2.2 + 10 + 20) = 3.11V   <- 高于 2.475V 门限，留了余量
//
// 接好后一定要用万用表量 GPIO10 对 GND 的**高电平**，要在 2.8V 以上。
// 低于 2.6V 说明上拉不够强（常见于只靠传感器内部上拉），补上那只 2.2k。
#define FLOW_PULSES_PER_L      5880.0f
#define DEF_FLOW_PPL            5880    // 默认标定值，可用 flowcal 命令改并 savecfg
#define FLOW_MIN_LPM             0.20f  // 低于此值视为没水在动
#define FLOW_CHECK_MS          15000UL  // 泵跑满这么久还没水流 -> 判干转/憋压

// ============================ 泵自我保护（防烧泵）============================
// 软管被压瘪 / 堵住 / 没水 -> 隔膜泵憋压 -> 电机过热 -> 阀片熔化。
// 已经烧掉 2 台泵了，所以这里做两道软件保护，都比「人盯着」可靠：
//   ① 水流传感器判据：泵开着但 FLOW_CHECK_MS 内读不到水 -> 立刻停泵（最灵，需要装传感器）
//   ② 连续运行硬上限：不管水流怎样，连转 maxRunMs 就强制停机休息（不用传感器，兜底）
// 触发后强制休息 guardRestMs，到点自动重试一次；发 clear 可以立即解除。
#define DEF_MAX_RUN_MS    (10UL * 60UL * 1000UL)  // 连续运行上限 10 分钟（0 = 关闭）
#define DEF_GUARD_REST_MS     (60UL * 1000UL)     // 触发保护后强制休息 60 秒再试

// ============================ 液位开关 ======================================
// 浮子簧片开关，装在罐底上方约 10mm。接法：一端 GND，一端 GPIO11（内部上拉）。
#define LEVEL_ACTIVE_LOW    1   // 1 = 读低表示"有水"
#define LEVEL_DEBOUNCE_N    3   // 连续 N 次一致才认（1.5 秒）

// ============================ 急停按钮 ======================================
// **常闭（NC）**按钮：不按时接通 GND，按下或线断了就断开（被上拉拉高）。
// 这样"线断了"和"按下了"是同一种结果 —— 失效安全。
// 建议同时把按钮串在泵的 12V 回路里，做成硬线 + 软件双重保护。
#define ESTOP_ACTIVE_HIGH   1   // 1 = 读高表示急停触发
#define ESTOP_DEBOUNCE_N    2

// ============================ DS18B20 参数 ==================================
#define ONEWIRE_MAX_DEVICES     8     // 单总线最多挂几个（实际 5 个）
#define DS18B20_RESOLUTION      12    // 9..12，12 位 = 0.0625C / 750ms
#define SENSOR_SETTLE_MS        800   // 12 位转换等待时间（留 50ms 余量）

// ============================ 故障判定 ======================================
#define DS18B20_POWERON_DEFAULT  85.0f  // 上电默认值 / 转换未完成时的哨兵值
#define SENSOR_FAULT_LIMIT_NORMAL  80.0f
#define SENSOR_FAULT_LIMIT_LOW    -60.0f
#define SENSOR_BAD_STREAK        2     // 连续 N 次读到坏值才算故障

// ============================ 默认设定值 ====================================
// 体表目标温度：33C 是「凉而不冷」的舒适区，与 37C 核心体温有明显梯度
#define DEF_TARGET_C        33.0f
#define DEF_BAND_C           1.0f    // 回差：33.5 开泵 / 32.5 停泵
#define DEF_SKIN_LOW_C      30.0f    // 体表低于此值 -> 强制停泵（防冷损伤）
#define DEF_SKIN_HIGH_C     38.0f    // 体表高于此值 -> 报警（冷却失效 / 中暑风险）
#define DEF_WATER_MIN_C      8.0f    // 水温低于此值 -> 停泵（防过冷 / 防冷凝结冰）
#define DEF_WATER_MAX_C     32.0f    // 水温高于此值 -> 报警：冰袋化了，冷却无效
#define DEF_MIN_ON_MS      20000UL   // 最短连续运行 20s（保护继电器触点与泵阀片）
#define DEF_MIN_OFF_MS     30000UL   // 最短停机 30s
#define DEF_ICE_CHECK_MS  480000UL   // 连续运行 8min 后评估冰袋是否还有效
#define DEF_FLOW_LPM         1.5f    // 标称流量 L/min（接了水流传感器后会被实测值覆盖）
#define DEF_TICK_MS           500UL  // 控制周期

// 时间比例（占空比）模式参数
#define DEF_DUTY_CYCLE_MS 180000UL   // 一个"慢 PWM"周期 3 分钟
#define DEF_DUTY_MIN       0.15f     // 最小占空比
#define DEF_DUTY_MAX       1.00f

// 控制模式
#define MODE_HYSTERESIS  0           // 回差启停（正常控温）
#define MODE_DUTY        1           // 时间比例（间歇占空比）
#define MODE_BENCH       2           // ★ 台架测试：不看传感器，固定周期开/停

// ============================ 台架测试模式 ==================================
// 只接了 继电器 + 水泵 + 电池、还没接温度探头时用这个模式。
// 它【完全绕过安全联锁】—— 不管有没有探头、水温多少，都按固定节拍开关泵。
//
// 重要：泵绝对不能长时间干转。空转超过几分钟，隔膜泵的阀片和膜片就废了。
//       测试时务必让泵有水可抽（哪怕放一盆水循环）。
#define DEF_BENCH_ON_MS   30000UL    // 开泵 30 秒
#define DEF_BENCH_OFF_MS  30000UL    // 停泵 30 秒
// ★ 安全上限：跑满这么多个循环后自动停泵并回到待机。
//   一次事故之后改的默认值 —— 台架测试绝不能无人看管地一直转下去。
//   5 个循环 = 5 分钟。要跑更久就把它调大，但人必须在旁边。
#define DEF_BENCH_CYCLES  5

// ============================ 运行时设定 ====================================
struct Settings {
  float    targetC;      // 体表目标温度
  float    bandC;        // 回差
  float    skinLowC;     // 体表下限保护
  float    skinHighC;    // 体表上限报警
  float    waterMinC;    // 水温下限保护
  float    waterMaxC;    // 水温上限报警
  float    flowLpm;      // 标称流量，用于估算制冷功率
  uint32_t minOnMs;      // 最短运行时间
  uint32_t minOffMs;     // 最短停机时间
  uint32_t iceCheckMs;   // 冰袋有效性评估窗口
  uint16_t flowPpl;      // 水流传感器标定：每升脉冲数
  uint32_t benchOnMs;    // 台架测试：开泵时长
  uint32_t benchOffMs;   // 台架测试：停泵时长
  uint32_t maxRunMs;     // 连续运行硬上限（0 = 关闭）
  uint32_t guardRestMs;  // 触发保护后强制休息时长，到点自动重试
  uint8_t  mode;         // MODE_HYSTERESIS / MODE_DUTY / MODE_BENCH
  bool     activeHigh;   // 继电器触发电平：true=高电平触发，false=低电平触发
  bool     openDrain;    // true=开漏驱动（释放时把脚变高阻，靠外部 10k 上拉到模块 5V）
  bool     enabled;      // 控温总开关，持久化（上次 enable off 关掉的，重启后依然是 off）
};

inline Settings settingsDefaults() {
  Settings s;
  s.targetC    = DEF_TARGET_C;
  s.bandC      = DEF_BAND_C;
  s.skinLowC   = DEF_SKIN_LOW_C;
  s.skinHighC  = DEF_SKIN_HIGH_C;
  s.waterMinC  = DEF_WATER_MIN_C;
  s.waterMaxC  = DEF_WATER_MAX_C;
  s.flowLpm    = DEF_FLOW_LPM;
  s.minOnMs    = DEF_MIN_ON_MS;
  s.minOffMs   = DEF_MIN_OFF_MS;
  s.iceCheckMs = DEF_ICE_CHECK_MS;
  s.flowPpl    = DEF_FLOW_PPL;
  s.benchOnMs  = DEF_BENCH_ON_MS;
  s.benchOffMs = DEF_BENCH_OFF_MS;
  s.maxRunMs   = DEF_MAX_RUN_MS;
  s.guardRestMs = DEF_GUARD_REST_MS;
  s.mode       = MODE_HYSTERESIS;  // 默认正常控温；台架测试用串口 mode 2 切过去
  s.activeHigh = (RELAY_ACTIVE_HIGH != 0);
  // ★ 低电平触发 = 开漏驱动：吸合才推低，不吸合就把脚变高阻（悬空），绝不推 3.3V。
  //   5V 光耦模块的 LED 阴极接在 IN 上，推 3.3V 会让 LED 还有微弱电流 -> 放不掉。
  s.openDrain  = (RELAY_ACTIVE_HIGH == 0);
  s.enabled    = true;
  return s;
}

// 传感器角色
enum SensorRole : uint8_t {
  ROLE_WATER_OUT = 0,   // 罐出水口 / 泵入口（系统最冷点）
  ROLE_WATER_RET = 1,   // 回水口（系统最热点）-> 与出水口的温差 = 带走的热量
  ROLE_SKIN_CHEST = 2,  // 胸前体表
  ROLE_SKIN_BACK = 3,   // 后背体表
  ROLE_AMBIENT = 4,     // 背包内环境（监控罐外壁结露）
  ROLE_COUNT = 5,
  ROLE_NONE = 0xFF
};

inline const char* roleName(uint8_t r) {
  switch (r) {
    case ROLE_WATER_OUT:  return "WATER_OUT";
    case ROLE_WATER_RET:  return "WATER_RET";
    case ROLE_SKIN_CHEST: return "SKIN_CHEST";
    case ROLE_SKIN_BACK:  return "SKIN_BACK";
    case ROLE_AMBIENT:    return "AMBIENT";
    default:              return "UNASSIGNED";
  }
}
