// =============================================================================
//  controller.h  --  水泵间歇控温状态机
//
//  核心约束：365 隔膜泵是有刷电机，不能用 PWM 平滑调速。
//  只能「整段开 / 整段关」，靠时间比例做慢 PWM（周期 10s~数分钟量级），
//  这样既避开 PWM 对电机的伤害，也不会有 PWM 高频噪声和电刷额外损耗。
//
//  三层保护：
//    1) 安全联锁（最高优先级，可打断最短运行时间）：过冷 / 无水 -> 立即停泵
//    2) 最短启动/停机时间：保护继电器触点与泵阀片，限制每小时启动次数
//    3) 需求控制：回差启停 或 时间比例
// =============================================================================
#pragma once
#include <Arduino.h>
#include "config.h"
#include "tempsensor.h"

enum CoolState : uint8_t {
  ST_STANDBY = 0,   // 待机（总开关关 / 手动强制关）
  ST_MONITOR,       // 监控中，泵停，等待体表升温到开泵阈值
  ST_REST,          // 泵停，但在等最短停机时间结束
  ST_PUMPING,       // 泵运行中
  ST_FAULT,         // 安全停机（过冷 / 无水 / 传感器全失效）
};

enum CoolWarn : uint32_t {
  WARN_NONE            = 0,
  WARN_SKIN_HIGH       = 1u << 0,   // 体表过高：冷却无效，注意中暑
  WARN_SKIN_LOW        = 1u << 1,   // 体表过低：过冷保护
  WARN_WATER_LOW       = 1u << 2,   // 水温过低：防冷损伤
  WARN_WATER_HIGH      = 1u << 3,   // 水温过高：冰袋化了 / 没水
  WARN_NO_SKIN_SENSOR  = 1u << 4,   // 体表探头全部无效
  WARN_NO_WATER_SENSOR = 1u << 5,   // 水温探头无效
  WARN_NO_SENSOR       = 1u << 6,   // 总线上一个探头都没有
  WARN_DRY_RUN         = 1u << 7,   // 疑似干转 / 水没进泵
  WARN_ICE_MELT        = 1u << 8,   // 冰袋失效，该换了
  WARN_SENSOR_FAULT    = 1u << 9,   // 读数全部异常
  WARN_LEAK            = 1u << 10,  // 漏水（需 clear 命令手动复位）
  WARN_ESTOP           = 1u << 11,  // 急停按钮按下（锁存，需 clear）
  WARN_LEVEL_LOW       = 1u << 12,  // 罐里液位过低 -> 防干转
  WARN_BATT_LOW        = 1u << 13,  // 电池电压偏低，该准备换电池
  WARN_BATT_CRIT       = 1u << 14,  // 电池电压过低 -> 强制停泵保护电芯
  WARN_NO_FLOW         = 1u << 15,  // 泵在转但水流传感器读不到水
};

#define FORCE_AUTO  (-1)
#define FORCE_OFF   (0)
#define FORCE_ON    (1)

class PumpController {
 public:
  PumpController();

  void begin();                     // 上电先保证泵不转，再配置 IO
  void tick();                      // 每 DEF_TICK_MS 调一次

  // --- 运行控制 ---
  void   setEnabled(bool on);       // 总开关：false = 停泵待机（会落盘）
  bool   enabled() const { return m_enabled; }
  // 继电器触发电平：true=高电平触发，false=低电平触发
  void   setRelayPolarity(bool activeHigh, bool persist = true);
  bool   relayActiveHigh() const { return settings.activeHigh; }
  int    onLevel() const;           // IN 引脚「吸合」时的原始电平
  int    offLevel() const;          // IN 引脚「不吸合」时的原始电平
  void   startRelayTest(uint8_t toggles);   // 裸电平来回翻，用来实测模块极性
  void   setOpenDrain(bool on);             // 开漏驱动：释放时引脚高阻，靠外部 10k 上拉到 5V
  bool   openDrain() const { return settings.openDrain; }
  bool   relayTestRunning() const { return m_testLeft > 0; }
  void   setMode(uint8_t m);
  uint8_t mode() const { return settings.mode; }
  void   forcePump(int8_t v);       // FORCE_AUTO / FORCE_OFF / FORCE_ON
  int8_t forceState() const { return m_force; }
  void   clearFault();

  // --- 状态查询 ---
  CoolState   state() const { return m_state; }
  const char* stateName() const;
  uint32_t    warnings() const { return m_warn; }
  bool        pumpOn() const { return m_relayOn; }
  uint32_t    currentOnMs() const { return m_curOnMs; }
  uint32_t    totalRunSec() const { return m_totalRunMs / 1000UL; }
  uint32_t    startCount() const { return m_startCount; }
  float       duty10min() const;    // 最近 10 分钟实际运行占空比
  float       lastDuty() const { return m_lastDuty; }
  bool        safetyLatched() const { return m_safetyLatched; }
  // 为什么现在是这个状态：给串口 status 用的「一句话解释」
  const char* reason() const { return m_reason; }
  const char* latchReason() const { return m_latchReason; }

  static String warnString(uint32_t w);

  // --- 设定值持久化 ---
  bool loadSettings();
  bool saveSettings();
  bool loadStats();
  bool saveStats();
  void resetSettings();

  Settings& cfg() { return settings; }
  void      applyDefaults();

 private:
  void    evaluateWarnings(uint32_t now);
  void    updateSafetyLatch(uint32_t now);
  void    updateRunGuard(uint32_t now);   // 防烧泵：水流缺失 / 连续运行超时
  void    guardLatch(const char* why, uint32_t now);
  bool    decide(uint32_t now);
  bool    dutyMode(float skin, uint32_t now);
  void    setRelay(bool on);
  void    trackRuntime(uint32_t now);
  void    dutyWindow(uint32_t now);

  static const uint32_t BUCKET_MS = 10000UL;   // 10s 一个桶
  static const uint8_t  BUCKETS   = 60;        // 60 个桶 = 10 分钟滑窗

  Settings  settings;
  CoolState m_state;
  uint32_t  m_warn;
  bool      m_enabled;
  int8_t    m_force;

  bool      m_relayOn;
  bool      m_prevOn;
  bool      m_safetyLatched;
  char      m_reason[64];        // 本 tick 的判决原因
  char      m_latchReason[64];   // 最近一次触发安全联锁的原因
  bool      m_guardLatched;      // 泵自我保护已触发（停泵中）
  uint32_t  m_guardUntil;        // 到点自动解除并重试
  char      m_guardReason[64];   // 触发原因
  int8_t    m_testLeft;          // 继电器极性实测剩余翻转次数
  bool      m_testOn;            // 实测当前电平
  uint32_t  m_testNext;          // 下次翻转时刻

  uint32_t  m_lastTick;
  uint32_t  m_onSince;        // 本段运行起点
  uint32_t  m_offSince;       // 本段停机起点
  uint32_t  m_curOnMs;
  uint32_t  m_totalRunMs;
  uint32_t  m_startCount;
  uint32_t  m_iceRunStart;    // 连续运行起点（用于冰袋评估）
  float     m_lastDuty;

  bool      m_statsDirty;     // 统计有待落盘
  uint32_t  m_statsLastSave;  // 上次落盘时刻
  uint32_t  m_benchStart;     // 台架测试周期起点
  uint32_t  m_benchDone;      // 已跑完的循环数

  uint8_t   m_bucketIdx;
  uint32_t  m_bucketAcc;
  uint32_t  m_bucketRun[BUCKETS];
};

extern PumpController pump;
