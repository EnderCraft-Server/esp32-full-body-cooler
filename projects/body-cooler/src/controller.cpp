#include "controller.h"
#include "inputs.h"
#include <Preferences.h>

PumpController pump;

static const char* NVS_CFG   = "bc_cfg";
static const char* NVS_STATS = "bc_stats";

PumpController::PumpController()
    : m_state(ST_STANDBY), m_warn(WARN_NONE), m_enabled(true), m_force(FORCE_AUTO),
      m_relayOn(false), m_prevOn(false), m_safetyLatched(false),
      m_lastTick(0), m_onSince(0), m_offSince(0), m_curOnMs(0),
      m_totalRunMs(0), m_startCount(0), m_iceRunStart(0), m_lastDuty(0.0f),
      m_statsDirty(false), m_statsLastSave(0),
      m_benchStart(0), m_benchDone(0), m_bucketIdx(0), m_bucketAcc(0) {
  m_reason[0] = 0;
  snprintf(m_latchReason, sizeof(m_latchReason), "未触发");
  m_testLeft = 0; m_testOn = false; m_testNext = 0;
  m_guardLatched = false; m_guardUntil = 0;
  snprintf(m_guardReason, sizeof(m_guardReason), "未触发");
  applyDefaults();
  for (uint8_t i = 0; i < BUCKETS; i++) m_bucketRun[i] = 0;
}

void PumpController::applyDefaults() {
  settings = settingsDefaults();
}

// ---------------------------------------------------------------------------
//  启动：关键顺序 —— 必须先写输出电平，再切成 OUTPUT。
//  ESP32 复位后 GPIO 默认是高阻输入，如果先 pinMode 再 digitalWrite，
//  中间那几微秒继电器可能被误触发，泵会「啪」地抽一下。
// ---------------------------------------------------------------------------
void PumpController::begin() {
  // ★ 先把 NVS 里的设定读出来（尤其是触发电平），再配置 IO ——
  //   否则会先按编译期默认电平驱动一次 IN，极性选错时泵会「啪」地抽一下。
  loadSettings();
  loadStats();

  const int off = offLevel();

  if (settings.openDrain && !settings.activeHigh) {
    // 开漏：上电就停在高阻，外部 10k 会把 IN 拉到 5V -> 继电器不吸合
    pinMode(PIN_RELAY_PUMP, INPUT);
    m_enabled = settings.enabled;
    m_relayOn = false; m_prevOn = false;
    m_offSince = millis(); m_lastTick = millis();
    return;
  }

  // 低电平触发时，先把内部上拉打开再切输出：
  // 从复位到这一步之间 GPIO 是高阻，内部上拉能让 IN 保持高 -> 继电器不吸合。
  // 高电平触发时反过来用内部下拉，让 IN 保持低。
  if (settings.activeHigh) {
    pinMode(PIN_RELAY_PUMP, INPUT_PULLDOWN);
    digitalWrite(PIN_RELAY_PUMP, off);
  } else {
    pinMode(PIN_RELAY_PUMP, INPUT_PULLUP);
    digitalWrite(PIN_RELAY_PUMP, off);
  }
  digitalWrite(PIN_RELAY_PUMP, off);
  pinMode(PIN_RELAY_PUMP, OUTPUT);
  digitalWrite(PIN_RELAY_PUMP, off);

  const int auxPins[4] = {PIN_RELAY_AUX1, PIN_RELAY_AUX2, PIN_RELAY_AUX3, PIN_RELAY_AUX4};
  for (int i = 0; i < 4; i++) {
    pinMode(auxPins[i], settings.activeHigh ? INPUT_PULLDOWN : INPUT_PULLUP);
    digitalWrite(auxPins[i], off);
    pinMode(auxPins[i], OUTPUT);
    digitalWrite(auxPins[i], off);
  }

  m_enabled = settings.enabled;
  m_relayOn = false;
  m_prevOn = false;
  m_offSince = millis();
  m_lastTick = millis();
}

// 泵/继电器当前应该输出的原始电平（IN 引脚电平）
int PumpController::offLevel() const { return settings.activeHigh ? LOW : HIGH; }
int PumpController::onLevel()  const { return settings.activeHigh ? HIGH : LOW; }

void PumpController::setRelay(bool on) {
  m_relayOn = on;

  // 开漏驱动：只对低电平触发模块有意义。
  //   吸合 -> 把脚推成 OUTPUT LOW（灌电流，能吃掉光耦 LED 的电流）
  //   释放 -> 把脚变回高阻 INPUT，让外部 10k 上拉把 IN 拉到模块的 5V
  // 为什么要这样：模块 VCC 是 5V，光耦 LED 的阴极接 IN。
  //   IN 停在 3.3V 时，LED 上还有 5-3.3-Vf 的压差，可能有微弱电流 -> 继电器放不掉。
  //   只有把 IN 真正拉到 5V 才能彻底截止。ESP32 推不出 5V，但高阻 + 上拉可以。
  if (settings.openDrain && !settings.activeHigh) {
    if (on) {
      pinMode(PIN_RELAY_PUMP, OUTPUT);
      digitalWrite(PIN_RELAY_PUMP, LOW);
    } else {
      pinMode(PIN_RELAY_PUMP, INPUT);   // 高阻，别用内部上拉（只有 3.3V，不够）
    }
    return;
  }

  pinMode(PIN_RELAY_PUMP, OUTPUT);
  digitalWrite(PIN_RELAY_PUMP, on ? onLevel() : offLevel());
}

void PumpController::setOpenDrain(bool on) {
  settings.openDrain = on;
  setRelay(false);          // 立刻按新驱动方式放到「释放」
  saveSettings();
}

// 切换触发电平：先无条件把 IN 拉到「不吸合」电平，再改设定、落盘。
// 这样即使原来极性选错导致继电器一直吸合，一条命令就能立刻放掉。
void PumpController::startRelayTest(uint8_t toggles) {
  m_testLeft = (int8_t)toggles;
  m_testOn   = false;
  m_testNext = millis();
  setRelay(false);          // 先停在「释放」电平
  Serial.printf("[RELAY TEST] 开始：每 5 秒把 GPIO%d(IN) 翻一次，共 %u 次。\n",
                PIN_RELAY_PUMP, (unsigned)toggles);
  Serial.println(F("[RELAY TEST] 记下「哪一次听到咔哒/泵动」以及万用表读数 -> 决定 relay high 还是 low"));
  Serial.println(F("[RELAY TEST] 如果一次咔哒都没有（一直吸着或一直松着）-> IN 那根线没接在 GPIO5 上"));
  Serial.println(F("[RELAY TEST]   -> 拔下来直接插到 ESP32 的 GND 脚试：吸合就说明模块和 ESP32 共地正常"));
}

void PumpController::setRelayPolarity(bool activeHigh, bool persist) {
  settings.activeHigh = activeHigh;
  m_relayOn = false;
  digitalWrite(PIN_RELAY_PUMP, offLevel());
  if (persist) saveSettings();
}

void PumpController::setEnabled(bool on) {
  m_enabled = on;
  settings.enabled = on;
  saveSettings();          // 持久化：上次关掉的，重启后依然是关的（安全）
  if (!on) {
    setRelay(false);
    m_state = ST_STANDBY;
  }
}

void PumpController::setMode(uint8_t m) {
  if (m > MODE_BENCH) return;
  settings.mode = m;
  if (m == MODE_BENCH) { m_benchStart = millis(); m_benchDone = 0; }
}

void PumpController::forcePump(int8_t v) {
  if (v < -1 || v > 1) return;
  m_force = v;
  if (v == FORCE_AUTO) {
    m_offSince = millis();   // 交回自动时重新计最短停机
  }
}

void PumpController::clearFault() {
  m_guardLatched = false;
  m_safetyLatched = false;
  inputs.clearLatches();      // 漏水 / 急停 都是锁存故障，必须显式复位
  m_warn &= ~(WARN_SKIN_LOW | WARN_WATER_LOW | WARN_SENSOR_FAULT | WARN_NO_SENSOR);
}

const char* PumpController::stateName() const {
  switch (m_state) {
    case ST_STANDBY:  return "STANDBY";
    case ST_MONITOR:  return "MONITOR";
    case ST_REST:     return "REST";
    case ST_PUMPING:  return "PUMPING";
    case ST_FAULT:    return "FAULT";
    default:          return "?";
  }
}

String PumpController::warnString(uint32_t w) {
  if (w == WARN_NONE) return String("OK");
  String s;
  if (w & WARN_SKIN_HIGH)       s += "SKIN_HIGH ";
  if (w & WARN_SKIN_LOW)        s += "SKIN_LOW ";
  if (w & WARN_WATER_LOW)       s += "WATER_LOW ";
  if (w & WARN_WATER_HIGH)      s += "WATER_HIGH ";
  if (w & WARN_NO_SKIN_SENSOR)  s += "NO_SKIN_SENSOR ";
  if (w & WARN_NO_WATER_SENSOR) s += "NO_WATER_SENSOR ";
  if (w & WARN_NO_SENSOR)       s += "NO_SENSOR ";
  if (w & WARN_DRY_RUN)         s += "DRY_RUN ";
  if (w & WARN_ICE_MELT)        s += "ICE_MELT ";
  if (w & WARN_SENSOR_FAULT)    s += "SENSOR_FAULT ";
  if (w & WARN_LEAK)            s += "LEAK ";
  if (w & WARN_ESTOP)           s += "ESTOP ";
  if (w & WARN_LEVEL_LOW)       s += "LEVEL_LOW ";
  if (w & WARN_BATT_LOW)        s += "BATT_LOW ";
  if (w & WARN_BATT_CRIT)       s += "BATT_CRIT ";
  if (w & WARN_NO_FLOW)         s += "NO_FLOW ";
  s.trim();
  return s;
}

float PumpController::duty10min() const {
  uint32_t run = 0;
  for (uint8_t i = 0; i < BUCKETS; i++) run += m_bucketRun[i];
  uint32_t total = (uint32_t)BUCKETS * BUCKET_MS;
  if (total == 0) return 0.0f;
  return (float)run / (float)total;
}

void PumpController::dutyWindow(uint32_t now) {
  uint8_t idx = (uint8_t)((now / BUCKET_MS) % BUCKETS);
  if (idx != m_bucketIdx) {
    m_bucketRun[m_bucketIdx] = m_bucketAcc;   // 归档旧桶
    m_bucketAcc = 0;
    m_bucketIdx = idx;
  }
  if (m_relayOn) m_bucketAcc += DEF_TICK_MS;
}

void PumpController::trackRuntime(uint32_t now) {
  if (m_relayOn && !m_prevOn) {
    m_onSince = now;
    m_startCount++;
    if (m_iceRunStart == 0) m_iceRunStart = now;
    m_statsDirty = true;
  } else if (!m_relayOn && m_prevOn) {
    m_totalRunMs += now - m_onSince;
    m_offSince = now;
    m_iceRunStart = 0;
    m_statsDirty = true;
  }
  // 不在切换瞬间写 flash：继电器动作 + flash 写入同时发生会拉大瞬时电流，
  // 表现就是「啪」的一下 ESP32 复位。改成最多每 60 秒落一次盘。
  if (m_statsDirty && (now - m_statsLastSave > 60000UL)) {
    m_statsLastSave = now;
    m_statsDirty = false;
    saveStats();
  }
  m_prevOn = m_relayOn;
  m_curOnMs = m_relayOn ? (now - m_onSince) : 0;
}

// ---------------------------------------------------------------------------
//  报警与安全联锁
// ---------------------------------------------------------------------------
void PumpController::evaluateWarnings(uint32_t now) {
  uint32_t w = WARN_NONE;

  const float skin = sensors.skinAvg();
  const float wOut = sensors.get(ROLE_WATER_OUT);
  const bool  haveSkin = !isnan(skin);
  const bool  haveWOut = !isnan(wOut);

  // ---- v2 输入层 ----
  if (inputs.leakSeen())     w |= WARN_LEAK;    // 锁存，需 clear
  if (inputs.estopLatched()) w |= WARN_ESTOP;   // 锁存，需 clear

#if ENABLE_LEVEL_SWITCH
  if (!inputs.levelOk()) w |= WARN_LEVEL_LOW;
#endif

#if ENABLE_BATT_SENSE
  if (inputs.batteryValid()) {
    if (inputs.batteryV() <= BATT_STOP_V)      w |= WARN_BATT_CRIT;
    else if (inputs.batteryV() <= BATT_WARN_V) w |= WARN_BATT_LOW;
  }
#endif

  if (sensors.count() == 0) {
    w |= WARN_NO_SENSOR;
  } else {
    if (sensors.skinValidCount() == 0) w |= WARN_NO_SKIN_SENSOR;
    if (!haveWOut) w |= WARN_NO_WATER_SENSOR;
    if (!sensors.anyValid()) w |= WARN_SENSOR_FAULT;
  }

  if (haveSkin) {
    if (skin >= settings.skinHighC) w |= WARN_SKIN_HIGH;
    if (skin <= settings.skinLowC)  w |= WARN_SKIN_LOW;
  }
  if (haveWOut) {
    if (wOut <= settings.waterMinC) w |= WARN_WATER_LOW;
    if (wOut >= settings.waterMaxC) w |= WARN_WATER_HIGH;
  }

  // 干转（有水流传感器 -- 最可靠）：泵在转，但管路里根本没有水在动
#if ENABLE_FLOW_SENSOR
  if (m_relayOn && m_curOnMs > FLOW_CHECK_MS && inputs.flowLpm() < FLOW_MIN_LPM) {
    w |= WARN_NO_FLOW;
  }
#endif

  // 干转（没有水流传感器时的兜底）：泵在转，但「最冷点」根本不冷
  if (m_relayOn && haveWOut && m_curOnMs > 60000UL) {
    if (wOut >= settings.waterMaxC - 2.0f) w |= WARN_DRY_RUN;
  }

  // 冰袋失效：连续运行超过评估窗口，回水与出水几乎没温差，体表还热着
  if (m_relayOn && m_iceRunStart != 0 && now - m_iceRunStart > settings.iceCheckMs) {
    float dt = sensors.waterDeltaT();
    if (!isnan(dt) && dt < 0.5f && haveSkin && skin > settings.targetC) {
      w |= WARN_ICE_MELT;
    }
  }

  m_warn = w;
}

void PumpController::updateSafetyLatch(uint32_t now) {
  const float skin = sensors.skinAvg();
  const float wOut = sensors.get(ROLE_WATER_OUT);
  const bool  haveSkin = !isnan(skin);
  const bool  haveWOut = !isnan(wOut);

  bool enter = false;
  const char* why = nullptr;

  // --- v2 输入层：这几条都是"硬"条件，任何一条成立都立刻停泵 ---
  if (inputs.leakSeen())     { enter = true; why = "漏水检测到水（需 clear 复位）"; }
  if (inputs.estopLatched()) { enter = true; why = "急停按钮已按下（需 clear 复位）"; }
#if ENABLE_LEVEL_SWITCH
  if (!inputs.levelOk())     { enter = true; why = "液位过低，防干转"; }
#endif
#if ENABLE_BATT_SENSE
  if (inputs.batteryValid() && inputs.batteryV() <= BATT_STOP_V) { enter = true; why = "电池电压过低"; }
#endif

  if (sensors.count() == 0) {
    enter = true; why = "总线上没有任何温度探头";
  } else {
    if (!sensors.anyValid()) { enter = true; why = "所有探头读数都无效"; }
    else if (!haveSkin && !haveWOut) { enter = true; why = "没有绑角色：体表/水温探头都没 map"; }
    else if (haveSkin && skin <= settings.skinLowC) { enter = true; why = "体表温度低于下限（过冷保护）"; }
    else if (haveWOut && wOut <= settings.waterMinC) { enter = true; why = "水温低于下限（防冷损伤）"; }
  }

  if (enter) {
    m_safetyLatched = true;
    if (why) snprintf(m_latchReason, sizeof(m_latchReason), "%s", why);
    return;
  }

  if (m_safetyLatched) {
    // 恢复要带 1C 回差，否则会在阈值上疯狂抖动
    bool ok = true;
    if (haveSkin && skin < settings.skinLowC + 1.0f) ok = false;
    if (haveWOut && wOut < settings.waterMinC + 1.0f) ok = false;
    if (!haveSkin && !haveWOut) ok = false;
#if ENABLE_BATT_SENSE
    // 电池恢复要带回差，否则会在阈值上反复启停
    if (inputs.batteryValid() && inputs.batteryV() < BATT_STOP_V + BATT_RECOVER_V) ok = false;
#endif
    if (ok) m_safetyLatched = false;
  }
  (void)now;
}

// ---------------------------------------------------------------------------
//  泵自我保护：软管被压瘪 / 堵住 / 没水 -> 隔膜泵憋压 -> 电机过热烧毁。
//  已经烧掉 2 台泵了，所以这里做两道判据，触发后强制休息一段时间再自动重试。
// ---------------------------------------------------------------------------
void PumpController::guardLatch(const char* why, uint32_t now) {
  if (m_guardLatched) return;
  const uint32_t rest = settings.guardRestMs ? settings.guardRestMs : DEF_GUARD_REST_MS;
  m_guardLatched = true;
  m_guardUntil = now + rest;
  snprintf(m_guardReason, sizeof(m_guardReason), "%s", why);
  Serial.printf("[泵保护] %s\n", why);
  Serial.printf("[泵保护] -> 立即停泵，休息 %lu 秒后自动重试\n", (unsigned long)(rest / 1000));
  Serial.println(F("[泵保护] 检查管路被压瘪/打死折、罐里还有没有水。clear 可立即解除。"));
}

void PumpController::updateRunGuard(uint32_t now) {
  // --- 休息够了就自动解除，允许再试一次 ---
  if (m_guardLatched && (int32_t)(now - m_guardUntil) >= 0) {
    m_guardLatched = false;
    m_offSince = now;              // 重新计最短停机，别一解除就猛开
    Serial.printf("[泵保护] 休息结束（上次原因: %s），恢复自动控温\n", m_guardReason);
  }
  if (m_guardLatched) return;

  // --- 判据①：水流传感器读不到水（最灵，能抓住「管子刚好被压瘪」那一瞬间）---
#if ENABLE_FLOW_SENSOR
  if (m_relayOn && m_curOnMs > FLOW_CHECK_MS && inputs.flowLpm() < FLOW_MIN_LPM) {
    guardLatch("泵在转但水流传感器读不到水（管瘪 / 堵塞 / 没水）", now);
    return;
  }
#endif

  // --- 判据②：连续运行硬上限（不用传感器，兜底）---
  if (settings.maxRunMs && m_relayOn && m_curOnMs > settings.maxRunMs) {
    guardLatch("连续运行超过上限（疑似憋压）", now);
    return;
  }
}

// ---------------------------------------------------------------------------
//  需求判定
// ---------------------------------------------------------------------------
bool PumpController::dutyMode(float skin, uint32_t now) {
  const float band = settings.bandC;
  float err = skin - settings.targetC;
  float duty;

  if (err <= -band) {
    duty = 0.0f;
  } else if (err >= band * 2.0f) {
    duty = DEF_DUTY_MAX;
  } else {
    float k = (err + band) / (3.0f * band);        // 0..1
    duty = DEF_DUTY_MIN + k * (DEF_DUTY_MAX - DEF_DUTY_MIN);
  }
  duty = constrain(duty, 0.0f, DEF_DUTY_MAX);
  m_lastDuty = duty;
  if (duty <= 0.001f) return false;

  uint32_t phase  = now % DEF_DUTY_CYCLE_MS;
  uint32_t onTime = (uint32_t)((float)DEF_DUTY_CYCLE_MS * duty);
  if (onTime < settings.minOnMs) onTime = settings.minOnMs;
  return phase < onTime;
}

bool PumpController::decide(uint32_t now) {
  float skin = sensors.skinAvg();
  bool haveWOut = sensors.valid(ROLE_WATER_OUT);

  if (isnan(skin)) {
    // 体表探头挂了：降级为「按水温保守循环」。出水温还低于目标就间歇跑
    if (!haveWOut) return false;
    float wOut = sensors.get(ROLE_WATER_OUT);
    if (wOut > settings.targetC) return false;
    bool on = (now % DEF_DUTY_CYCLE_MS) < (DEF_DUTY_CYCLE_MS / 4);  // 25% 占空比
    m_lastDuty = 0.25f;
    return on;
  }

  if (settings.mode == MODE_DUTY) return dutyMode(skin, now);
  (void)now;

  const float onTh  = settings.targetC + settings.bandC * 0.5f;
  const float offTh = settings.targetC - settings.bandC * 0.5f;
  m_lastDuty = (skin > settings.targetC) ? 1.0f : 0.0f;
  if (m_relayOn) return skin > offTh;    // 回差：靠当前状态做记忆
  return skin >= onTh;
}

// ---------------------------------------------------------------------------
//  主状态机
// ---------------------------------------------------------------------------
void PumpController::tick() {
  uint32_t now = millis();
  if (now - m_lastTick < DEF_TICK_MS) return;
  m_lastTick = now;

  // ---- 0) 继电器极性实测：无视状态机、无视联锁，只管翻 IN 电平 ----
  if (m_testLeft > 0) {
    if (now - m_testNext >= 5000UL) {
      m_testNext = now;
      m_testOn = !m_testOn;
      m_testLeft--;
      const int lvl = m_testOn ? onLevel() : offLevel();
      digitalWrite(PIN_RELAY_PUMP, lvl);
      m_relayOn = m_testOn;
      delayMicroseconds(50);
      const int back = digitalRead(PIN_RELAY_PUMP);   // 读回真实电平
      Serial.printf("[RELAY TEST] 指令 IN=%s  实测 IN=%s %s   现在应当%s   (还剩 %d 次)\n",
                    lvl ? "HIGH" : "LOW", back ? "HIGH" : "LOW",
                    (back == lvl) ? "" : "<<< 不符！引脚被短路/接错脚",
                    m_testOn ? "吸合/泵转" : "释放/泵停",
                    (int)m_testLeft);
      if (back != lvl) {
        Serial.println(F("[RELAY TEST] !! 读回电平和指令不一致 -> 先查 GPIO5 到 IN 这根线，"));
        Serial.println(F("[RELAY TEST] !! 以及 ESP32 的 GND 有没有和继电器模块的 GND 共地。"));
      }
    }
    m_state = ST_STANDBY;
    snprintf(m_reason, sizeof(m_reason), "继电器极性实测中（relay test）");
    return;
  }

  evaluateWarnings(now);
  updateSafetyLatch(now);
  updateRunGuard(now);

  // ---- 1) 手动强制优先（台架测试 / 排空气用）----
  if (m_force != FORCE_AUTO) {
    setRelay(m_force == FORCE_ON);
    snprintf(m_reason, sizeof(m_reason), "手动强制 %s（pump %s）",
             m_force == FORCE_ON ? "开" : "关", m_force == FORCE_ON ? "on" : "off");
    m_state = (m_force == FORCE_ON) ? ST_PUMPING : ST_STANDBY;
    trackRuntime(now);
    dutyWindow(now);
    return;
  }

  // ---- 2) 总开关关闭 ----
  if (!m_enabled) {
    setRelay(false);
    snprintf(m_reason, sizeof(m_reason), "控温总开关关闭（enable on 打开）");
    m_state = ST_STANDBY;
    trackRuntime(now);
    dutyWindow(now);
    return;
  }

  // ---- 2.5) 台架测试模式：固定节拍开/停，完全绕过安全联锁 ----
  //      只接了 继电器+水泵+电池 的时候用这个模式跑。
  //      注意它不看任何传感器，也不管水温 —— 是纯粹的电机启停测试。
  if (settings.mode == MODE_BENCH) {
    uint32_t onMs  = settings.benchOnMs  ? settings.benchOnMs  : DEF_BENCH_ON_MS;
    uint32_t offMs = settings.benchOffMs ? settings.benchOffMs : DEF_BENCH_OFF_MS;
    uint32_t period = onMs + offMs;

    if (DEF_BENCH_CYCLES > 0 && m_benchDone >= DEF_BENCH_CYCLES) {
      setRelay(false);
      if (m_state != ST_STANDBY) {
        Serial.printf("[BENCH] 已跑满 %u 个循环，自动停泵（安全上限）\n", (unsigned)DEF_BENCH_CYCLES);
        Serial.println(F("[BENCH] 继续跑请发: pump auto   （确认泵里有水）"));
      }
      m_state = ST_STANDBY;
      trackRuntime(now); dutyWindow(now);
      return;
    }

    uint32_t phase = (period ? (now - m_benchStart) % period : 0);
    bool on = (phase < onMs);
    if (on && !m_prevOn) m_benchDone++;   // 每次开启算一个循环
    setRelay(on);
    snprintf(m_reason, sizeof(m_reason), "台架模式：%lus开/%lus停，第%lu轮",
             (unsigned long)(onMs / 1000), (unsigned long)(offMs / 1000),
             (unsigned long)(m_benchDone + 1));
    m_state = on ? ST_PUMPING : ST_REST;
    trackRuntime(now);
    dutyWindow(now);
    return;
  }

  // ---- 2.7) 泵自我保护：管瘪 / 没水 / 连转超时。排在需求判定之前 ----
  if (m_guardLatched) {
    setRelay(false);
    m_state = ST_FAULT;
    uint32_t left = ((int32_t)(m_guardUntil - now) > 0) ? (m_guardUntil - now) : 0;
    snprintf(m_reason, sizeof(m_reason), "泵保护停机：%s（%lu 秒后自动重试）",
             m_guardReason, (unsigned long)(left / 1000));
    trackRuntime(now); dutyWindow(now);
    return;
  }

  // ---- 3) 安全联锁：先于最短运行时间，安全永远能打断 ----
  if (m_safetyLatched) {
    setRelay(false);
    snprintf(m_reason, sizeof(m_reason), "安全联锁已锁：%s（clear 可解除）", m_latchReason);
    m_state = ST_FAULT;
    trackRuntime(now);
    dutyWindow(now);
    return;
  }

  // ---- 4) 需求 ----
  const float skin = sensors.skinAvg();   // 只用于 status 里解释判决原因
  bool wantOn = decide(now);
  bool suppressedByOff = false;
  bool heldByMinOn = false;

  // ---- 5) 最短运行 / 最短停机约束（慢 PWM 的物理下限）----
  if (m_relayOn) {
    if (!wantOn && m_curOnMs < settings.minOnMs) { wantOn = true; heldByMinOn = true; }
  } else {
    uint32_t offDur = now - m_offSince;
    if (wantOn && offDur < settings.minOffMs) {
      wantOn = false;
      suppressedByOff = true;
    }
  }

  setRelay(wantOn);
  if (wantOn) {
    m_state = ST_PUMPING;
    if (heldByMinOn) {
      uint32_t left = (settings.minOnMs > m_curOnMs) ? (settings.minOnMs - m_curOnMs) : 0;
      snprintf(m_reason, sizeof(m_reason), "最短运行中：还差 %lu 秒", (unsigned long)(left / 1000));
    } else {
      snprintf(m_reason, sizeof(m_reason), "体表 %.2fC >= 开泵阈值 %.2fC", skin, settings.targetC + settings.bandC * 0.5f);
    }
  } else if (suppressedByOff) {
    uint32_t left = (settings.minOffMs > (now - m_offSince)) ? (settings.minOffMs - (now - m_offSince)) : 0;
    m_state = ST_REST;
    snprintf(m_reason, sizeof(m_reason), "等最短停机结束：还差 %lu 秒", (unsigned long)(left / 1000));
  } else {
    m_state = ST_MONITOR;
    snprintf(m_reason, sizeof(m_reason), "体表 %.2fC < 开泵阈值 %.2fC，不需要制冷",
             skin, settings.targetC + settings.bandC * 0.5f);
  }

  trackRuntime(now);
  dutyWindow(now);
}

// ---------------------------------------------------------------------------
//  NVS
// ---------------------------------------------------------------------------
bool PumpController::loadSettings() {
  Preferences p;
  if (!p.begin(NVS_CFG, false)) return false;   // 读写打开，自动创建命名空间
  bool ok = p.isKey("tgt");
  if (ok) {
    settings.targetC    = p.getFloat("tgt",  DEF_TARGET_C);
    settings.bandC      = p.getFloat("band", DEF_BAND_C);
    settings.skinLowC   = p.getFloat("slow", DEF_SKIN_LOW_C);
    settings.skinHighC  = p.getFloat("shigh", DEF_SKIN_HIGH_C);
    settings.waterMinC  = p.getFloat("wmin", DEF_WATER_MIN_C);
    settings.waterMaxC  = p.getFloat("wmax", DEF_WATER_MAX_C);
    settings.flowLpm    = p.getFloat("flow", DEF_FLOW_LPM);
    settings.minOnMs    = p.getULong("mon",  DEF_MIN_ON_MS);
    settings.minOffMs   = p.getULong("moff", DEF_MIN_OFF_MS);
    settings.iceCheckMs = p.getULong("ice",  DEF_ICE_CHECK_MS);
    settings.flowPpl    = p.getUShort("ppl", DEF_FLOW_PPL);
    if (settings.flowPpl == 0) settings.flowPpl = DEF_FLOW_PPL;
    settings.benchOnMs  = p.getULong("bOn",  DEF_BENCH_ON_MS);
    settings.benchOffMs = p.getULong("bOff", DEF_BENCH_OFF_MS);
    settings.maxRunMs    = p.getULong("mrun",  DEF_MAX_RUN_MS);
    settings.guardRestMs = p.getULong("grest", DEF_GUARD_REST_MS);
    settings.mode       = p.getUChar("mode", MODE_BENCH);
    if (settings.mode > MODE_BENCH) settings.mode = MODE_HYSTERESIS;
    settings.activeHigh = p.getBool("rah", (RELAY_ACTIVE_HIGH != 0));
    settings.openDrain  = p.getBool("rod", false);
    settings.enabled    = p.getBool("en",  true);
  }
  p.end();
  return ok;
}

bool PumpController::saveSettings() {
  Preferences p;
  if (!p.begin(NVS_CFG, false)) return false;
  p.putFloat("tgt",  settings.targetC);
  p.putFloat("band", settings.bandC);
  p.putFloat("slow", settings.skinLowC);
  p.putFloat("shigh", settings.skinHighC);
  p.putFloat("wmin", settings.waterMinC);
  p.putFloat("wmax", settings.waterMaxC);
  p.putFloat("flow", settings.flowLpm);
  p.putULong("mon",  settings.minOnMs);
  p.putULong("moff", settings.minOffMs);
  p.putULong("ice",  settings.iceCheckMs);
  p.putUShort("ppl", settings.flowPpl);
  p.putULong("bOn",  settings.benchOnMs);
  p.putULong("bOff", settings.benchOffMs);
  p.putULong("mrun",  settings.maxRunMs);
  p.putULong("grest", settings.guardRestMs);
  p.putUChar("mode", settings.mode);
  p.putBool("rah", settings.activeHigh);
  p.putBool("rod", settings.openDrain);
  p.putBool("en",  settings.enabled);
  p.end();
  return true;
}

bool PumpController::loadStats() {
  Preferences p;
  if (!p.begin(NVS_STATS, false)) return false;
  m_totalRunMs = p.getULong("runms", 0);
  m_startCount = p.getULong("starts", 0);
  p.end();
  return true;
}

bool PumpController::saveStats() {
  Preferences p;
  if (!p.begin(NVS_STATS, false)) return false;
  p.putULong("runms", m_totalRunMs);
  p.putULong("starts", m_startCount);
  p.end();
  return true;
}

void PumpController::resetSettings() {
  applyDefaults();
}
