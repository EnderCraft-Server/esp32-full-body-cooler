// =============================================================================
//  console.h  --  非阻塞串口命令行
//  用法：串口 115200，输入 help 看命令表。
// =============================================================================
#pragma once
#include <Arduino.h>

class Console {
 public:
  void begin();
  void tick();
  void printStatus();
  void printHelp();
  void printScan();

  bool logEnabled() const { return m_log; }
  void setLog(bool on) { m_log = on; }
  uint32_t logIntervalMs() const { return m_logMs; }

 private:
  void handleLine(String line);
  void printRoles();
  void printCfg();

  String   m_buf;
  bool     m_log;
  uint32_t m_logMs;
  uint32_t m_lastLog;
};

extern Console console;
