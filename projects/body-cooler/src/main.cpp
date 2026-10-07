// =============================================================================
//  body-cooler  --  ESP32-S3 全身降温器主循环
//
//  任务分工（全部非阻塞）：
//    sensors.tick()   DS18B20 异步采样状态机（每 ~2s 一轮）
//    pump.tick()      控温状态机（每 500ms 一次判决）
//    console.tick()   串口命令解析
//    blinkTick()      状态灯
//    buzzerTick()     蜂鸣器报警
//
//  loop() 里没有任何 delay()，所以串口随时有响应，采样也不会互相打架。
// =============================================================================
#include <Arduino.h>
#include "config.h"
#include "tempsensor.h"
#include "controller.h"
#include "console.h"
#include "inputs.h"

// ---------------------------------------------------------------------------
//  备用继电器
// ---------------------------------------------------------------------------
static const int AUX_PINS[4] = {PIN_RELAY_AUX1, PIN_RELAY_AUX2, PIN_RELAY_AUX3, PIN_RELAY_AUX4};

void auxWrite(int idx, bool on) {
  if (idx < 0 || idx > 3) return;
  const bool level = RELAY_ACTIVE_HIGH ? on : !on;
  digitalWrite(AUX_PINS[idx], level ? HIGH : LOW);
}

// ---------------------------------------------------------------------------
//  状态灯
//  图案格式：{亮ms, 灭ms, 亮ms, 灭ms, ...} 循环播放
// ---------------------------------------------------------------------------
// 上电自检图案：绿色 3 短闪 = 正常上电；红色狂闪 = 检测到欠压复位(BROWNOUT)
static const uint16_t PAT_BOOT_OK[]  = {70, 130, 70, 130, 70, 1100};
static const uint16_t PAT_BOOT_BAD[] = {60, 60};
// 继电器状态变化瞬间：绿色常亮一小会儿
static const uint16_t PAT_EDGE[]     = {400, 400};

static uint32_t g_bootUntil = 0;
static bool     g_bootBad   = false;
static uint32_t g_edgeUntil = 0;
static bool     g_lastRelay = false;

static const uint16_t PAT_STANDBY[] = {20, 2980};
static const uint16_t PAT_MONITOR[] = {60, 940};
static const uint16_t PAT_REST[]    = {60, 200, 60, 680};
static const uint16_t PAT_PUMPING[] = {250, 250};
static const uint16_t PAT_FAULT[]   = {80, 120, 80, 120, 80, 840};

struct Blinker {
  const uint16_t* pat;
  uint8_t  n;
  uint8_t  i;
  uint32_t t;
  bool     level;
};

static Blinker  g_blink;
static uint8_t  g_r, g_g, g_b;

static void ledApply(bool on) {
#if LED_IS_WS2812
  if (on) neopixelWrite(PIN_STATUS_LED, g_r, g_g, g_b);
  else    neopixelWrite(PIN_STATUS_LED, 0, 0, 0);
#else
  digitalWrite(PIN_STATUS_LED, on ? HIGH : LOW);
#endif
}

// 强制切换图案（即使图案相同也重新开始）—— 用于继电器切换瞬间的绿闪
static void blinkForce(const uint16_t* p, uint8_t n, uint8_t r, uint8_t g, uint8_t b) {
  g_blink.pat = p; g_blink.n = n; g_blink.i = 0;
  g_blink.t = millis(); g_blink.level = true;
  g_r = r; g_g = g; g_b = b;
  ledApply(true);
}

static void blinkUse(const uint16_t* p, uint8_t n, uint8_t r, uint8_t g, uint8_t b) {
  if (g_blink.pat == p && g_blink.n == n) return;   // 同图案不重启，避免闪断
  g_blink.pat = p;
  g_blink.n = n;
  g_blink.i = 0;
  g_blink.t = millis();
  g_blink.level = true;
  g_r = r; g_g = g; g_b = b;
  ledApply(true);
}

static void blinkTick() {
  if (!g_blink.pat) return;
  uint32_t now = millis();
  if (now - g_blink.t >= g_blink.pat[g_blink.i]) {
    g_blink.t = now;
    g_blink.level = !g_blink.level;
    g_blink.i = (uint8_t)((g_blink.i + 1) % g_blink.n);
    ledApply(g_blink.level);
  }
}

static void ledUpdateForState() {
  // 1) 上电自检阶段：绿 3 闪 = 正常；红狂闪 = 上次是欠压复位（BROWNOUT）
  if (millis() < g_bootUntil) {
    if (g_bootBad) blinkUse(PAT_BOOT_BAD, sizeof(PAT_BOOT_BAD)/sizeof(PAT_BOOT_BAD[0]), 70, 0, 0);
    else           blinkUse(PAT_BOOT_OK,  sizeof(PAT_BOOT_OK) /sizeof(PAT_BOOT_OK [0]), 0, 70, 0);
    return;
  }
  // 2) 继电器刚切换：绿色常亮一下，方便和「听到的咔哒声」对齐
  if (millis() < g_edgeUntil) {
    blinkUse(PAT_EDGE, sizeof(PAT_EDGE)/sizeof(PAT_EDGE[0]), 0, 70, 0);
    return;
  }
  const uint32_t w = pump.warnings();
  if (pump.state() == ST_FAULT || (w & (WARN_SKIN_LOW | WARN_WATER_LOW | WARN_SENSOR_FAULT | WARN_NO_SENSOR))) {
    blinkUse(PAT_FAULT, sizeof(PAT_FAULT) / sizeof(PAT_FAULT[0]), 60, 0, 0);        // 红：故障
    return;
  }
  if (w & (WARN_SKIN_HIGH | WARN_WATER_HIGH | WARN_DRY_RUN | WARN_ICE_MELT)) {
    blinkUse(PAT_REST, sizeof(PAT_REST) / sizeof(PAT_REST[0]), 60, 30, 0);         // 橙：报警
    return;
  }
  switch (pump.state()) {
    case ST_PUMPING:
      blinkUse(PAT_PUMPING, sizeof(PAT_PUMPING) / sizeof(PAT_PUMPING[0]), 0, 40, 40);  // 青：泵转
      break;
    case ST_REST:
      blinkUse(PAT_REST, sizeof(PAT_REST) / sizeof(PAT_REST[0]), 40, 40, 0);           // 黄：等最短停机
      break;
    case ST_MONITOR:
      blinkUse(PAT_MONITOR, sizeof(PAT_MONITOR) / sizeof(PAT_MONITOR[0]), 0, 30, 0);   // 绿：待命
      break;
    case ST_STANDBY:
    default:
      blinkUse(PAT_STANDBY, sizeof(PAT_STANDBY) / sizeof(PAT_STANDBY[0]), 0, 0, 25);   // 蓝：待机
      break;
  }
}

// ---------------------------------------------------------------------------
//  蜂鸣器（可选硬件；没接也不影响）
// ---------------------------------------------------------------------------
static uint32_t g_buzzUntil = 0;
static uint32_t g_buzzNext  = 0;

static void buzzerTick() {
  const uint32_t now = millis();
  if (g_buzzUntil && now >= g_buzzUntil) {
    digitalWrite(PIN_BUZZER, LOW);
    g_buzzUntil = 0;
  }
  const uint32_t w = pump.warnings();
  const bool urgent = (pump.state() == ST_FAULT) ||
                      (w & (WARN_SKIN_HIGH | WARN_SKIN_LOW | WARN_WATER_LOW | WARN_WATER_HIGH | WARN_DRY_RUN));
  if (!urgent || g_buzzUntil != 0 || now < g_buzzNext) return;
  digitalWrite(PIN_BUZZER, HIGH);
  g_buzzUntil = now + 80;
  g_buzzNext  = now + 4000;
}

// ---------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
#if ARDUINO_USB_CDC_ON_BOOT
  // 走原生 USB 时，等主机打开串口再打印，否则启动横幅会丢
  { uint32_t t0 = millis(); while (!Serial && (millis() - t0 < 2500)) delay(10); }
#endif
  delay(300);

  // 先把所有输出脚置成「关」，再配置 LED / 蜂鸣器
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);

#if !LED_IS_WS2812
  digitalWrite(PIN_STATUS_LED, LOW);
  pinMode(PIN_STATUS_LED, OUTPUT);
  digitalWrite(PIN_STATUS_LED, LOW);
#endif
  ledApply(false);

  esp_reset_reason_t rr = esp_reset_reason();
  g_bootBad   = (rr == ESP_RST_BROWNOUT);
  g_bootUntil = millis() + 2600;
  const char* rrName =
      (rr == ESP_RST_POWERON)  ? "POWERON 正常上电" :
      (rr == ESP_RST_BROWNOUT) ? "BROWNOUT 掉电/欠压复位 <<< 电源有问题" :
      (rr == ESP_RST_PANIC)    ? "PANIC 程序崩溃" :
      (rr == ESP_RST_INT_WDT)  ? "INT_WDT 中断看门狗" :
      (rr == ESP_RST_TASK_WDT) ? "TASK_WDT 任务看门狗" :
      (rr == ESP_RST_WDT)      ? "WDT 看门狗" :
      (rr == ESP_RST_SW)       ? "SW 软件重启" :
      (rr == ESP_RST_DEEPSLEEP)? "DEEPSLEEP 唤醒" :
      (rr == ESP_RST_EXT)      ? "EXT 外部复位脚" : "其他";

  Serial.println();
  Serial.println(F("============================================================="));
  Serial.printf ("  上次复位原因: %s (code %d)\n", rrName, (int)rr);
  Serial.println(F("  LED: 绿3闪=正常上电   红狂闪=上次欠压复位"));
  Serial.println(F("============================================================="));
  Serial.println(F("  body-cooler  --  ESP32-S3 全身降温器固件"));
  Serial.printf ("  build %s %s\n", __DATE__, __TIME__);
  Serial.println(F("============================================================="));
  Serial.printf("chip       : %s rev%d, %d cores @ %u MHz\n",
                ESP.getChipModel(), ESP.getChipRevision(), ESP.getChipCores(),
                (unsigned)getCpuFrequencyMhz());
  Serial.printf("flash      : %u MB    psram: %u bytes\n",
                (unsigned)(ESP.getFlashChipSize() / (1024 * 1024)),
                (unsigned)ESP.getPsramSize());
  inputs.begin();          // 输入层要在控制器之前初始化
  sensors.begin();
  pump.begin();            // 先 begin，才能拿到 NVS 里持久化的触发电平

  const bool ah = pump.relayActiveHigh();
  Serial.println(F("--- pin map ---"));
  Serial.printf("  DS18B20 bus : GPIO%-2d (4.7k 上拉到 3V3)\n", PIN_ONEWIRE);
  Serial.printf("  relay pump  : GPIO%-2d (%s触发，输出 %s = 泵开)\n", PIN_RELAY_PUMP,
                ah ? "高电平" : "低电平", ah ? "HIGH" : "LOW");
  Serial.printf("  relay aux   : GPIO%d %d %d %d\n", PIN_RELAY_AUX1, PIN_RELAY_AUX2, PIN_RELAY_AUX3, PIN_RELAY_AUX4);
  Serial.printf("  buzzer      : GPIO%-2d   status LED: GPIO%d\n", PIN_BUZZER, PIN_STATUS_LED);
  Serial.printf("  继电器 IN   : 实测 %s     控温总开关 %s（持久化）\n",
                digitalRead(PIN_RELAY_PUMP) ? "HIGH" : "LOW",
                pump.enabled() ? "ON" : "OFF");
  if (!pump.enabled()) {
    Serial.println(F("  !! 上次是 enable off 关掉的，重启后依然是关的。要控温请发: enable on"));
  }
  Serial.println(F("  极性接反的症状：说 pump=ON 却不吸合 / 说 pump=OFF 反而一直转。"));
  Serial.println(F("  现场改极性: relay high | relay low     实测极性: relay test"));
  Serial.println(F("-------------------------------------------------------------"));
  inputs.setFlowCal(pump.cfg().flowPpl);   // 用持久化的标定值覆盖默认值
  console.begin();

  Serial.printf("DS18B20     : 总线发现 %d 个探头\n", sensors.count());
  if (sensors.count() == 0) {
    Serial.println(F("  !! 没找到温度探头 —— 自动控温会被安全联锁锁住（state=FAULT）。"));
    Serial.println(F("  !! 台架测试可用: pump on / pump auto 手动驱动继电器。"));
  }
  Serial.println(F("  --- 可选输入状态 ---"));
#if ENABLE_BATT_SENSE
  Serial.printf("  电池采样    : 启用  当前 %.2f V %s\n", inputs.batteryV(),
                inputs.batteryValid() ? "" : "(未接线？)");
#else
  Serial.println(F("  电池采样    : 关闭"));
#endif
#if ENABLE_FLOW_SENSOR
  Serial.printf("  水流传感器  : 启用  标定 %u 脉冲/升\n", (unsigned)inputs.flowCal());
#else
  Serial.println(F("  水流传感器  : 关闭"));
#endif
#if ENABLE_LEVEL_SWITCH
  Serial.printf("  液位开关    : 启用  当前 %s\n", inputs.levelOk() ? "有水" : "缺水");
#else
  Serial.println(F("  液位开关    : 关闭"));
#endif
#if ENABLE_ESTOP
  Serial.printf("  急停按钮    : 启用  当前 %s\n", inputs.estopLatched() ? "已按下" : "正常");
#else
  Serial.println(F("  急停按钮    : 关闭"));
#endif
#if ENABLE_LEAK_SENSOR
  Serial.println(F("  漏水检测    : 启用"));
#else
  Serial.println(F("  漏水检测    : 关闭"));
#endif
  if (pump.mode() == MODE_BENCH) {
    Serial.println(F(""));
    Serial.println(F("  ========================================================"));
    Serial.printf ("  ==  台架测试模式 BENCH  ==  每 %lu 秒开泵 / %lu 秒停泵\n",
                   (unsigned long)(pump.cfg().benchOnMs / 1000),
                   (unsigned long)(pump.cfg().benchOffMs / 1000));
    Serial.println(F("  ==  已绕过安全联锁：不看探头、不看水温、不管缺水"));
    Serial.println(F("  ==  >> 泵必须有水可抽，绝不允许长时间干转 <<"));
    Serial.println(F("  ==  停：enable off / pump off / 断电池"));
    Serial.println(F("  ==  退出：mode 0  （回到正常控温）"));
    Serial.println(F("  ========================================================"));
    Serial.println(F(""));
  }
  Serial.println(F("  输入 help 看命令表；status 看状态。"));
  Serial.printf("settings    : target=%.2fC band=%.2fC mode=%s  minOn=%lus minOff=%lus  relay=%s\n",
                pump.cfg().targetC, pump.cfg().bandC,
                pump.mode() == MODE_BENCH ? "BENCH" : (pump.mode() == MODE_DUTY ? "DUTY" : "HYSTERESIS"),
                (unsigned long)(pump.cfg().minOnMs / 1000),
                (unsigned long)(pump.cfg().minOffMs / 1000),
                pump.relayActiveHigh() ? "HIGH-on" : "LOW-on");
  Serial.println(F("============================================================="));
}

// ---------------------------------------------------------------------------
//  循环耗时探针：主循环被谁拖慢了，用 diag 命令一看便知
// ---------------------------------------------------------------------------
uint32_t g_loopCount  = 0;
uint32_t g_stageUs[6] = {0, 0, 0, 0, 0, 0};
uint32_t g_lastLoopUs = 0;
uint32_t g_maxLoopUs  = 0;

void loop() {
  const uint32_t t0 = micros();
  uint32_t tPrev = t0;

  // 检测继电器状态变化 -> 绿闪 + 强制重画图案
  {
    bool r = pump.pumpOn();
    if (r != g_lastRelay) {
      g_lastRelay = r;
      g_edgeUntil = millis() + 260;
      if (millis() >= g_bootUntil) blinkForce(PAT_EDGE, sizeof(PAT_EDGE)/sizeof(PAT_EDGE[0]), 0, 70, 0);
    }
  }
  uint32_t tNow = micros(); g_stageUs[0] += tNow - tPrev; tPrev = tNow;
  inputs.tick(millis());
  tNow = micros(); g_stageUs[1] += tNow - tPrev; tPrev = tNow;
  sensors.tick();
  tNow = micros(); g_stageUs[2] += tNow - tPrev; tPrev = tNow;
  pump.tick();
  tNow = micros(); g_stageUs[3] += tNow - tPrev; tPrev = tNow;
  console.tick();
  tNow = micros(); g_stageUs[4] += tNow - tPrev; tPrev = tNow;
  ledUpdateForState();
  blinkTick();
  buzzerTick();
  tNow = micros(); g_stageUs[5] += tNow - tPrev;

  g_lastLoopUs = micros() - t0;
  if (g_lastLoopUs > g_maxLoopUs) g_maxLoopUs = g_lastLoopUs;
  g_loopCount++;
}
