#include "console.h"
#include "config.h"
#include "tempsensor.h"
#include "controller.h"
#include "inputs.h"

Console console;

extern void auxWrite(int idx, bool on);

// 主循环探针（定义在 main.cpp）
extern uint32_t g_loopCount;
extern uint32_t g_stageUs[6];
extern uint32_t g_lastLoopUs;
extern uint32_t g_maxLoopUs;

void Console::begin() {
  m_buf.reserve(96);
  m_log = false;
  m_logMs = 2000;
  m_lastLog = 0;
}

static uint8_t roleFromName(const String& n) {
  if (n == "water_out"  || n == "wo" || n == "0") return ROLE_WATER_OUT;
  if (n == "water_ret"  || n == "wr" || n == "1") return ROLE_WATER_RET;
  if (n == "skin_chest" || n == "sc" || n == "2") return ROLE_SKIN_CHEST;
  if (n == "skin_back"  || n == "sb" || n == "3") return ROLE_SKIN_BACK;
  if (n == "ambient"    || n == "am" || n == "4") return ROLE_AMBIENT;
  if (n == "none"       || n == "-")              return ROLE_NONE;
  return 0xFE;   // 非法
}

static const char* modeName(uint8_t m) {
  return (m == MODE_BENCH) ? "BENCH" : ((m == MODE_DUTY) ? "DUTY" : "HYSTERESIS");
}

static bool isOn(const String& s) { return (s == "on" || s == "1"); }

void Console::tick() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      String line = m_buf;
      m_buf = "";
      handleLine(line);
    } else if (c == 8 || c == 127) {          // 退格
      if (m_buf.length()) m_buf.remove(m_buf.length() - 1);
    } else if (m_buf.length() < 90) {
      m_buf += c;
    }
  }

  if (m_log) {
    uint32_t now = millis();
    if (now - m_lastLog >= m_logMs) {
      m_lastLog = now;
      printStatus();
    }
  }
}

void Console::printStatus() {
  float skin = sensors.skinAvg();
  float wOut = sensors.get(ROLE_WATER_OUT);
  float wRet = sensors.get(ROLE_WATER_RET);
  float amb  = sensors.get(ROLE_AMBIENT);
  float dt   = sensors.waterDeltaT();

  // 接了水流传感器并且读到了流量，就用实测值算制冷功率，否则退回设定值
  float flowUsed = pump.cfg().flowLpm;
  const char* flowSrc = "assumed";
#if ENABLE_FLOW_SENSOR
  if (inputs.flowLpm() > FLOW_MIN_LPM) { flowUsed = inputs.flowLpm(); flowSrc = "measured"; }
#endif
  float pW = sensors.estCoolingW(flowUsed);

  Serial.println(F("-------------------------------------------------------------"));
  Serial.printf("state   : %-9s pump=%s  force=%-4s enabled=%-3s mode=%s\n",
                pump.stateName(),
                pump.pumpOn() ? "ON " : "OFF",
                pump.forceState() == FORCE_AUTO ? "auto" : (pump.forceState() == FORCE_ON ? "ON" : "OFF"),
                pump.enabled() ? "yes" : "no",
                modeName(pump.mode()));
  Serial.printf("temps   : skin=%-6s wOut=%-6s wRet=%-6s amb=%s\n",
                isnan(skin) ? "--" : String(skin, 2).c_str(),
                isnan(wOut) ? "--" : String(wOut, 2).c_str(),
                isnan(wRet) ? "--" : String(wRet, 2).c_str(),
                isnan(amb)  ? "--" : String(amb, 2).c_str());
  Serial.printf("cooling : dT=%-6s C   P ~= %s W   (%.2f L/min, %s)\n",
                isnan(dt) ? "--" : String(dt, 2).c_str(),
                String(pW, 1).c_str(), flowUsed, flowSrc);
  Serial.printf("setpoint: target=%.2fC band=%.2fC  (ON >= %.2f / OFF <= %.2f)\n",
                pump.cfg().targetC, pump.cfg().bandC,
                pump.cfg().targetC + pump.cfg().bandC * 0.5f,
                pump.cfg().targetC - pump.cfg().bandC * 0.5f);
  Serial.printf("limits  : skin %.1f..%.1f C   water >= %.1f C   minOn=%lus minOff=%lus\n",
                pump.cfg().skinLowC, pump.cfg().skinHighC, pump.cfg().waterMinC,
                (unsigned long)(pump.cfg().minOnMs / 1000),
                (unsigned long)(pump.cfg().minOffMs / 1000));
  Serial.printf("run     : seg=%lus  total=%lus  starts=%lu  duty10m=%.0f%%\n",
                (unsigned long)(pump.currentOnMs() / 1000),
                (unsigned long)pump.totalRunSec(),
                (unsigned long)pump.startCount(),
                pump.duty10min() * 100.0f);
  // digitalRead 读的是引脚真实电平：如果外面把 IN 短路/强上拉，这里会读到和指令不符的值
  const int inLvl = digitalRead(PIN_RELAY_PUMP);
  const bool odRelease = pump.openDrain() && !pump.relayActiveHigh() && !pump.pumpOn();
  const int wantLvl = pump.pumpOn() ? pump.onLevel() : pump.offLevel();
  Serial.printf("relay   : IN实测=%s  指令=%s  驱动=%s  极性=%s  线圈=%s\n",
                inLvl ? "HIGH" : "LOW",
                odRelease ? "高阻(靠10k上拉)" : (wantLvl ? "HIGH" : "LOW"),
                pump.openDrain() ? "开漏" : "推挽",
                pump.relayActiveHigh() ? "高电平触发" : "低电平触发",
                pump.pumpOn() ? "吸合(泵开)" : "释放(泵停)");
  if (!odRelease && inLvl != wantLvl) {
    Serial.println(F("   !! IN 实测电平和指令不符 —— 引脚被外部短路/强上拉，或 IN 接在了别的脚上"));
  }
  Serial.printf("reason  : %s\n", pump.reason());
  Serial.printf("warn    : %s\n", PumpController::warnString(pump.warnings()).c_str());
  Serial.printf("sensors : %d online, %lu samples, safetyLatch=%s\n",
                sensors.count(), (unsigned long)sensors.sampleCount(),
                pump.safetyLatched() ? "YES" : "no");

  char battStr[20];
#if ENABLE_BATT_SENSE
  if (inputs.batteryValid()) snprintf(battStr, sizeof(battStr), "%.2fV", inputs.batteryV());
  else                       snprintf(battStr, sizeof(battStr), "notwired");
#else
  snprintf(battStr, sizeof(battStr), "off");
#endif

  String flowStr = "off";
#if ENABLE_FLOW_SENSOR
  flowStr = String(inputs.flowLpm(), 2) + " L/min";
#endif
  String lvlStr = "off";
#if ENABLE_LEVEL_SWITCH
  lvlStr = inputs.levelOk() ? "OK" : "LOW";
#endif
  String estStr = "off";
#if ENABLE_ESTOP
  estStr = inputs.estopLatched() ? "HIT" : "OK";
#endif
  String leakStr = "off";
#if ENABLE_LEAK_SENSOR
  leakStr = inputs.leakSeen() ? "WET" : "OK";
#endif

  Serial.printf("inputs  : batt=%-9s flow=%-12s level=%-4s estop=%-4s leak=%s\n",
                battStr, flowStr.c_str(), lvlStr.c_str(), estStr.c_str(), leakStr.c_str());
  Serial.println(F("-------------------------------------------------------------"));
}

void Console::printCfg() {
  Serial.printf("target=%.2f band=%.2f slow=%.2f shigh=%.2f wmin=%.2f wmax=%.2f\n",
                pump.cfg().targetC, pump.cfg().bandC, pump.cfg().skinLowC,
                pump.cfg().skinHighC, pump.cfg().waterMinC, pump.cfg().waterMaxC);
  Serial.printf("maxrun=%lumin rest=%lus\n",
                (unsigned long)(pump.cfg().maxRunMs / 60000),
                (unsigned long)(pump.cfg().guardRestMs / 1000));
  Serial.printf("flow=%.2f L/min  minOn=%lus minOff=%lus ice=%lumin mode=%s\n",
                pump.cfg().flowLpm,
                (unsigned long)(pump.cfg().minOnMs / 1000),
                (unsigned long)(pump.cfg().minOffMs / 1000),
                (unsigned long)(pump.cfg().iceCheckMs / 60000),
                modeName(pump.mode()));
  if (pump.mode() == MODE_BENCH)
    Serial.printf("台架测试: 每 %lu 秒开泵 / %lu 秒停泵  (mode 0 退出)\n",
                  (unsigned long)(pump.cfg().benchOnMs / 1000),
                  (unsigned long)(pump.cfg().benchOffMs / 1000));
}

void Console::printScan() {
  Serial.println(F("idx  ROM               role        temp"));
  for (int i = 0; i < sensors.count(); i++) {
    float t = sensors.rawOfIndex(i);
    Serial.printf("%-4d %s  %-11s %s\n", i, sensors.hexOfIndex(i),
                  roleName(sensors.roleOfIndex(i)),
                  isnan(t) ? "--" : String(t, 3).c_str());
  }
  if (sensors.count() == 0) {
    Serial.println(F("(总线上一颗 DS18B20 都没有 —— 查 4.7k 上拉、3V3/GND、数据线)"));
  }
}

void Console::printRoles() {
  Serial.println(F("role        -> ROM"));
  for (uint8_t r = 0; r < ROLE_COUNT; r++) {
    int found = -1;
    for (int i = 0; i < sensors.count(); i++) {
      if (sensors.roleOfIndex(i) == r) { found = i; break; }
    }
    Serial.printf("  %-11s -> %s\n", roleName(r),
                  found < 0 ? "(未分配)" : sensors.hexOfIndex(found));
  }
}

void Console::printHelp() {
  Serial.println(F(
    "\n===== body-cooler CLI =====\n"
    "  help                     显示本帮助\n"
    "  status | s               打印一次完整状态\n"
    "  scan                     重新扫描总线并列出 ROM / 角色 / 当前温度\n"
    "  roles                    显示角色分配表\n"
    "  map <role> <idx|ROM>     绑定探头角色\n"
    "                           role: water_out water_ret skin_chest skin_back ambient none\n"
    "  automap                  按总线顺序自动分配（台架试跑用）\n"
    "  clearroles               清空全部角色\n"
    "  save                     把角色映射写入 NVS\n"
    "\n"
    "  enable on|off            控温总开关（持久化，重启后保持）\n"
    "  relay                    看继电器极性 / IN 引脚实测电平\n"
    "  relay high|low           切换触发电平并保存（极性选错会「反着来」）\n"
    "  relay test               每 5 秒翻一次 IN，用耳朵实测模块极性\n"
    "  relay od|pp              开漏驱动 / 推挽驱动（3.3V 放不掉 5V 模块时用 od）\n"
    "  pump on|off|auto         手动强制水泵（台架排空气 / 测密封用）\n"
    "  clear                    清除安全联锁 / 漏水 / 急停\n"
    "  aux <1-4> on|off         备用继电器手动开关\n"
    "  inputs                   查看所有可选输入的引脚状态\n"
    "  batt                     电池电压（需 ENABLE_BATT_SENSE）\n"
    "  flow                     实测流量 / 累计水量（需 ENABLE_FLOW_SENSOR）\n"
    "  flowcal <脉冲/升>        水流传感器标定  YF-S401=5880  YF-S201=450\n"
    "  flowtotal                累计过水量清零\n"
    "\n"
    "  target <C>               体表目标温度\n"
    "  band <C>                 回差\n"
    "  slow <C> / shigh <C>     体表下限 / 上限\n"
    "  wmin <C> / wmax <C>      水温下限 / 上限\n"
    "  flow <L/min>             标称流量（仅用于估算制冷功率）\n"
    "  mon <s> / moff <s>       最短运行 / 最短停机（秒）\n"
    "  ice <min>                冰袋有效性评估窗口（分钟）\n"
    "  maxrun <min>             防烧泵：连续运行上限（0=关闭，默认10分钟）\n"
    "  grest <sec>              触发保护后强制休息多久再自动重试（默认60秒）\n"
    "  mode 0|1|2               0=回差启停  1=时间比例  2=台架测试\n"
    "  bench <秒>               ★台架测试节拍，例: bench 30 = 开30秒/停30秒\n"
    "  showcfg                  显示当前设定\n"
    "  savecfg                  保存设定到 NVS\n"
    "  defaults                 恢复出厂设定\n"
    "\n"
    "  log on|off               周期性状态输出\n"
    "  rate <ms>                周期输出间隔\n"
    "  stats                    运行统计\n"
    "  diag                     主循环各段耗时（排查卡顿）\n"
    "  reboot                   重启\n"));
}

void Console::handleLine(String line) {
  line.trim();
  if (line.length() == 0) return;

  int sp = line.indexOf(' ');
  String cmd = (sp < 0) ? line : line.substring(0, sp);
  String arg = (sp < 0) ? String("") : line.substring(sp + 1);
  cmd.toLowerCase();
  cmd.trim();
  arg.trim();

  int sp2 = arg.indexOf(' ');
  String a1 = (sp2 < 0) ? arg : arg.substring(0, sp2);
  String a2 = (sp2 < 0) ? String("") : arg.substring(sp2 + 1);
  a1.toLowerCase();
  a1.trim();
  a2.trim();

  if (cmd == "help" || cmd == "?")   { printHelp(); return; }
  if (cmd == "status" || cmd == "s") { printStatus(); return; }
  // 注意：这里只重扫，不能调 loadRoles()——它会先清空内存里的角色，
  // 把用户刚 map 完还没 save 的映射抹掉。角色只在开机 begin() 时从 NVS 载入一次。
  if (cmd == "scan")  { sensors.scan(); printScan(); return; }
  if (cmd == "roles") { printRoles(); return; }
  if (cmd == "diag") {
    const char* names[6] = {"relay/edge", "inputs", "sensors", "pump", "console", "led/buzz"};
    uint32_t up = millis() / 1000UL;
    Serial.printf("uptime   : %lu s   loops: %lu   (%.1f loop/s)\n",
                  (unsigned long)up, (unsigned long)g_loopCount,
                  up ? (float)g_loopCount / (float)up : 0.0f);
    Serial.printf("last loop: %lu us   max: %lu us\n",
                  (unsigned long)g_lastLoopUs, (unsigned long)g_maxLoopUs);
    for (int i = 0; i < 6; i++) {
      Serial.printf("  %-11s avg %6lu us/loop\n", names[i],
                    (unsigned long)(g_loopCount ? g_stageUs[i] / g_loopCount : 0));
    }
    return;
  }
  if (cmd == "showcfg") { printCfg(); return; }

  if (cmd == "stats") {
    Serial.printf("total run %lu s (%.1f h), starts %lu, duty10m %.0f%%\n",
                  (unsigned long)pump.totalRunSec(),
                  pump.totalRunSec() / 3600.0f,
                  (unsigned long)pump.startCount(),
                  pump.duty10min() * 100.0f);
    return;
  }

  if (cmd == "map") {
    uint8_t r = roleFromName(a1);
    if (r == 0xFE) { Serial.println(F("未知角色名，见 help")); return; }
    int idx = -1;
    if (a2.length() == 16)    idx = sensors.indexOfRom(a2);
    else if (a2.length() > 0) idx = a2.toInt();
    else { Serial.println(F("用法: map <role> <idx|ROM>")); return; }
    if (idx < 0 || idx >= sensors.count()) { Serial.println(F("序号/ROM 不存在，先 scan")); return; }
    sensors.setRoleByIndex(idx, r);
    bool okSave = sensors.saveRoles();   // 立刻落盘，避免 map 完忘了 save / 被 scan 清掉
    Serial.printf("OK: %s -> %s    (%s)\n", sensors.hexOfIndex(idx), roleName(r),
                  okSave ? "已写入 NVS" : "写入 NVS 失败");
    return;
  }
  if (cmd == "automap") {
    if (sensors.autoMapByOrder()) { printRoles(); Serial.println(F("(临时映射，save 才持久)")); }
    else Serial.println(F("总线上没有探头"));
    return;
  }
  if (cmd == "clearroles") { sensors.clearRoles(); Serial.println(F("已清空")); return; }
  if (cmd == "save") {
    Serial.println(sensors.saveRoles() ? F("角色映射已保存") : F("保存失败"));
    return;
  }

  if (cmd == "maxrun") {
    long v = a1.toInt();
    if (a1.length() == 0 || v < 0) { Serial.println(F("用法: maxrun <分钟>  (0 = 关闭)")); return; }
    pump.cfg().maxRunMs = (uint32_t)v * 60000UL;
    pump.saveSettings();
    Serial.printf("连续运行上限 = %ld 分钟%s\n", v, v == 0 ? "（已关闭！不建议）" : "");
    return;
  }
  if (cmd == "grest") {
    long v = a1.toInt();
    if (a1.length() == 0 || v < 5) { Serial.println(F("用法: grest <秒>  (至少 5 秒)")); return; }
    pump.cfg().guardRestMs = (uint32_t)v * 1000UL;
    pump.saveSettings();
    Serial.printf("保护后休息时长 = %ld 秒\n", v);
    return;
  }

  if (cmd == "relay") {
    if (a1 == "high" || a1 == "h" || a1 == "1") {
      pump.setRelayPolarity(true);
      Serial.printf("极性已改为【高电平触发】(IN=HIGH 吸合)，已保存。IN 现在 = %s（不吸合）\n",
                    digitalRead(PIN_RELAY_PUMP) ? "HIGH" : "LOW");
      return;
    }
    if (a1 == "low" || a1 == "l" || a1 == "0") {
      pump.setRelayPolarity(false);
      Serial.printf("极性已改为【低电平触发】(IN=LOW 吸合)，已保存。IN 现在 = %s（不吸合）\n",
                    digitalRead(PIN_RELAY_PUMP) ? "HIGH" : "LOW");
      return;
    }
    if (a1 == "od" || a1 == "opendrain") {
      pump.setOpenDrain(true);
      Serial.println(F("已切到【开漏驱动】并保存：吸合=推低 0V，释放=引脚高阻"));
      Serial.println(F("★ 必须配一只 10k 电阻：模块 IN ──[10k]── 模块 VCC(5V)，否则悬空不可靠"));
      Serial.printf("  现在 IN 实测 = %s\n", digitalRead(PIN_RELAY_PUMP) ? "HIGH" : "LOW");
      return;
    }
    if (a1 == "pp" || a1 == "pushpull") {
      pump.setOpenDrain(false);
      Serial.printf("已切回【推挽驱动】并保存，IN 现在 = %s\n",
                    digitalRead(PIN_RELAY_PUMP) ? "HIGH" : "LOW");
      return;
    }
    if (a1 == "test") { pump.startRelayTest(4); return; }
    Serial.printf("极性 = %s   驱动 = %s\n",
                  pump.relayActiveHigh() ? "高电平触发(IN=HIGH 吸合)" : "低电平触发(IN=LOW 吸合)",
                  pump.openDrain() ? "开漏(释放=高阻,靠10k拉到5V)" : "推挽(释放=3.3V)");
    Serial.printf("IN 引脚实测 = %s    线圈 = %s\n",
                  digitalRead(PIN_RELAY_PUMP) ? "HIGH" : "LOW",
                  pump.pumpOn() ? "吸合" : "释放");
    Serial.println(F("用法: relay high | relay low | relay od | relay pp | relay test"));
    return;
  }

  if (cmd == "enable") {
    pump.setEnabled(isOn(a1));
    Serial.printf("enabled=%s  (已保存，重启后保持)\n", pump.enabled() ? "on" : "off");
    return;
  }
  if (cmd == "pump") {
    if (a1 == "on")       pump.forcePump(FORCE_ON);
    else if (a1 == "off") pump.forcePump(FORCE_OFF);
    else                  pump.forcePump(FORCE_AUTO);
    Serial.printf("force=%s\n", pump.forceState() == FORCE_AUTO ? "auto" :
                                (pump.forceState() == FORCE_ON ? "ON" : "OFF"));
    return;
  }
  if (cmd == "clear") {
    pump.clearFault();
    inputs.clearLatches();
    Serial.println(F("安全联锁 / 漏水 / 急停 已全部复位"));
    return;
  }

  if (cmd == "batt") {
#if ENABLE_BATT_SENSE
    Serial.printf("battery : %.2f V   %s   warn <= %.2f   stop <= %.2f\n",
                  inputs.batteryV(),
                  inputs.batteryValid() ? "valid" : "NOT WIRED / 分压断了",
                  BATT_WARN_V, BATT_STOP_V);
    Serial.printf("          分压比 %.3f  (R1=%.0fk, R2=%.0fk)\n",
                  BATT_DIV_FACTOR, BATT_DIV_R1_KOHM, BATT_DIV_R2_KOHM);
#else
    Serial.println(F("电池采样未启用：include/config.h 里把 ENABLE_BATT_SENSE 改成 1"));
#endif
    return;
  }

  if (cmd == "flow") {
#if ENABLE_FLOW_SENSOR
    Serial.printf("flow    : %.2f L/min   累计 %.3f L   脉冲 %lu   标定 %u 脉冲/升\n",
                  inputs.flowLpm(), inputs.flowTotalL(),
                  (unsigned long)inputs.flowPulses(), (unsigned)inputs.flowCal());
#else
    Serial.println(F("水流传感器未启用：include/config.h 里把 ENABLE_FLOW_SENSOR 改成 1"));
#endif
    return;
  }

  if (cmd == "flowcal") {
    int v = arg.toInt();
    if (v <= 0) { Serial.println(F("用法: flowcal <每升脉冲数>   YF-S401=5880  YF-S201=450")); return; }
    pump.cfg().flowPpl = (uint16_t)v;
    inputs.setFlowCal((uint16_t)v);
    Serial.printf("标定 = %u 脉冲/升   (savecfg 才持久)\n", (unsigned)pump.cfg().flowPpl);
    return;
  }

  if (cmd == "flowtotal") {
    inputs.resetFlowTotal();
    Serial.println(F("累计过水量已清零"));
    return;
  }

  if (cmd == "inputs") {
    Serial.println(F("--- 可选输入 ---"));
    Serial.printf("  水位   : %s (引脚读 %s)\n",
                  inputs.levelOk() ? "有水" : "缺水",
                  inputs.levelRaw() ? "高" : "低");
    Serial.printf("  急停   : %s (引脚读 %s)\n",
                  inputs.estopLatched() ? "已触发" : "正常",
                  inputs.estopRaw() ? "高" : "低");
    Serial.printf("  漏水   : %s\n", inputs.leakSeen() ? "检测到水" : "正常");
#if ENABLE_BATT_SENSE
    Serial.printf("  电池   : %.2f V %s\n", inputs.batteryV(),
                  inputs.batteryValid() ? "" : "(未接线)");
#else
    Serial.println(F("  电池   : 未启用"));
#endif
#if ENABLE_FLOW_SENSOR
    Serial.printf("  水流   : %.2f L/min\n", inputs.flowLpm());
#else
    Serial.println(F("  水流   : 未启用"));
#endif
    return;
  }
  if (cmd == "aux") {
    int n = a1.toInt();
    if (n < 1 || n > 4) { Serial.println(F("用法: aux <1-4> on|off")); return; }
    auxWrite(n - 1, isOn(a2));
    Serial.printf("aux%d = %s\n", n, a2.c_str());
    return;
  }

  // ---- 设定值 ----
  bool cfgChanged = true;
  if      (cmd == "target") pump.cfg().targetC   = arg.toFloat();
  else if (cmd == "band")   pump.cfg().bandC     = arg.toFloat();
  else if (cmd == "slow")   pump.cfg().skinLowC  = arg.toFloat();
  else if (cmd == "shigh")  pump.cfg().skinHighC = arg.toFloat();
  else if (cmd == "wmin")   pump.cfg().waterMinC = arg.toFloat();
  else if (cmd == "wmax")   pump.cfg().waterMaxC = arg.toFloat();
  else if (cmd == "flow")   pump.cfg().flowLpm   = arg.toFloat();
  else if (cmd == "mon")    pump.cfg().minOnMs   = (uint32_t)(arg.toFloat() * 1000.0f);
  else if (cmd == "moff")   pump.cfg().minOffMs  = (uint32_t)(arg.toFloat() * 1000.0f);
  else if (cmd == "ice")    pump.cfg().iceCheckMs = (uint32_t)(arg.toFloat() * 60000.0f);
  else if (cmd == "mode")   pump.setMode((uint8_t)constrain(arg.toInt(), 0, 2));
  else if (cmd == "bench")  { uint32_t v = (uint32_t)arg.toInt();
                              if (v >= 1) { pump.cfg().benchOnMs = v * 1000UL; pump.cfg().benchOffMs = v * 1000UL; }
                              printCfg(); Serial.println(F("(savecfg 才持久)")); }
  else                      cfgChanged = false;

  if (cfgChanged) { printCfg(); Serial.println(F("(savecfg 才持久)")); return; }

  if (cmd == "savecfg") { Serial.println(pump.saveSettings() ? F("设定已保存") : F("保存失败")); return; }
  if (cmd == "defaults") { pump.resetSettings(); printCfg(); Serial.println(F("(savecfg 才持久)")); return; }

  if (cmd == "log")  { m_log = isOn(a1); Serial.printf("log=%s\n", m_log ? "on" : "off"); return; }
  if (cmd == "rate") {
    uint32_t v = (uint32_t)arg.toInt();
    if (v >= 200) m_logMs = v;
    Serial.printf("rate=%lums\n", (unsigned long)m_logMs);
    return;
  }
  if (cmd == "reboot") { Serial.println(F("rebooting...")); delay(100); ESP.restart(); return; }

  Serial.printf("未知命令: %s  (输入 help)\n", cmd.c_str());
}
