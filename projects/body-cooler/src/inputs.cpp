#include "inputs.h"

Inputs inputs;

// ---------------------------------------------------------------------------
//  水流传感器 ISR
//  32 位对齐的读写在这颗 MCU 上是原子的，所以简单的 volatile 计数就够了，
//  不需要进临界区（ISR 里越短越好）。
// ---------------------------------------------------------------------------
static volatile uint32_t g_flowPulses = 0;

#if ENABLE_FLOW_SENSOR
static void IRAM_ATTR flowIsr() {
  g_flowPulses++;
}
#endif

Inputs::Inputs()
    : m_battV(0.0f), m_battLastMs(0), m_battAccum(0), m_battSamples(0),
      m_flowLpm(0.0f), m_flowTotalL(0.0f), m_pulseTotal(0),
      m_lastPulseTotal(0), m_lastFlowMs(0), m_ppl((uint16_t)FLOW_PULSES_PER_L),
      m_levelOk(true), m_levelRaw(true), m_levelStable(0),
      m_estopLatched(false), m_estopRaw(false), m_estopStable(0),
      m_leakSeen(false) {}

void Inputs::begin() {
#if ENABLE_LEAK_SENSOR
  pinMode(PIN_LEAK_SENSOR, LEAK_ACTIVE_LOW ? INPUT_PULLUP : INPUT_PULLDOWN);
#endif

#if ENABLE_BATT_SENSE
  pinMode(PIN_BATT_ADC, INPUT);
  analogReadResolution(12);
  // 11dB 衰减 -> 量程约 0~2.5V（线性段），配合 6.556:1 分压够 12.6V 用
  analogSetPinAttenuation(PIN_BATT_ADC, ADC_11db);
#endif

#if ENABLE_FLOW_SENSOR
  pinMode(PIN_FLOW, INPUT_PULLUP);   // YF 系列是开集输出，要上拉
  attachInterrupt(digitalPinToInterrupt(PIN_FLOW), flowIsr, FALLING);
#endif

#if ENABLE_LEVEL_SWITCH
  pinMode(PIN_LEVEL, INPUT_PULLUP);
#endif

#if ENABLE_ESTOP
  pinMode(PIN_ESTOP, INPUT_PULLUP);
#endif

  m_lastFlowMs = millis();
}

bool Inputs::batteryValid() const {
#if ENABLE_BATT_SENSE
  // ESP32 自己要从电池取电，能跑起来说明电池至少 7V。
  // 读数低于 6V 只能是分压没接或线断了。
  return m_battV >= BATT_ABSENT_V;
#else
  return false;
#endif
}

void Inputs::setFlowCal(uint16_t ppl) {
  if (ppl > 0) m_ppl = ppl;
}

void Inputs::resetFlowTotal() {
  m_flowTotalL = 0.0f;
  m_pulseTotal = g_flowPulses;
  m_lastPulseTotal = g_flowPulses;
}

void Inputs::clearLatches() {
  m_estopLatched = false;
  m_leakSeen = false;
}

void Inputs::tick(uint32_t now) {
  // ---- 漏水：一旦见过就锁存，只能 clear 复位（水不会瞬间干）----
#if ENABLE_LEAK_SENSOR
  if (digitalRead(PIN_LEAK_SENSOR) == (LEAK_ACTIVE_LOW ? LOW : HIGH)) m_leakSeen = true;
#endif

  // ---- 电池：8 次平均，抑制电机启停时的母线抖动 ----
#if ENABLE_BATT_SENSE
  m_battAccum += analogReadMilliVolts(PIN_BATT_ADC);
  m_battSamples++;
  if (m_battSamples >= 8) {
    float mv = (float)m_battAccum / (float)m_battSamples;
    m_battV = (mv / 1000.0f) * BATT_DIV_FACTOR;
    m_battAccum = 0;
    m_battSamples = 0;
    m_battLastMs = now;
  }
#endif

  // ---- 液位：连续 N 次一致才认，防止背包晃动导致跳变 ----
#if ENABLE_LEVEL_SWITCH
  {
    bool raw = (digitalRead(PIN_LEVEL) == (LEVEL_ACTIVE_LOW ? LOW : HIGH));  // true = 有水
    m_levelRaw = raw;
    if (raw == m_levelOk) {
      m_levelStable = 0;
    } else if (++m_levelStable >= LEVEL_DEBOUNCE_N) {
      m_levelOk = raw;
      m_levelStable = 0;
    }
  }
#endif

  // ---- 急停：常闭按钮，读到触发电平就锁存 ----
#if ENABLE_ESTOP
  {
    bool raw = (digitalRead(PIN_ESTOP) == (ESTOP_ACTIVE_HIGH ? HIGH : LOW));
    m_estopRaw = raw;
    if (raw) {
      if (++m_estopStable >= ESTOP_DEBOUNCE_N) m_estopLatched = true;
    } else {
      m_estopStable = 0;
    }
  }
#endif

  // ---- 水流：1 秒窗口统计脉冲 ----
#if ENABLE_FLOW_SENSOR
  if (now - m_lastFlowMs >= 1000UL) {
    uint32_t total = g_flowPulses;
    uint32_t delta = total - m_lastPulseTotal;
    m_lastPulseTotal = total;
    m_pulseTotal = total;
    m_lastFlowMs = now;

    float liters = (float)delta / (float)m_ppl;
    m_flowLpm = liters * 60.0f;
    m_flowTotalL += liters;

    // 指针式传感器偶尔会抖出个把脉冲，做个小死区
    if (m_flowLpm < 0.02f) m_flowLpm = 0.0f;
  }
#else
  (void)now;
#endif
}
