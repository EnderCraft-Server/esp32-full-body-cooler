// =============================================================================
//  inputs.h  --  v2 新增的输入层
//
//  电池电压 / 水流传感器 / 液位开关 / 急停按钮 / 漏水检测
//
//  设计原则：**每个输入都可能"没接线"**。所以每一项都做了"未接线"和"真故障"
//  的区分，避免没接线就误报：
//    * 电池分压没接 -> 读数接近 0V -> 判定为"未接线"，不报低电
//    * 水流传感器没接 -> 永远 0 脉冲 -> 由 ENABLE_FLOW_SENSOR 显式开关控制
//    * 液位/急停     -> 都有内部上拉，未接线时读到一个确定的"安全"电平
// =============================================================================
#pragma once
#include <Arduino.h>
#include "config.h"

class Inputs {
 public:
  Inputs();

  void begin();
  void tick(uint32_t now);      // 每 DEF_TICK_MS 调一次

  // --- 电池 ---
  float batteryV() const { return m_battV; }
  bool  batteryValid() const;   // 分压接了并且读数合理

  // --- 水流 ---
  float flowLpm() const { return m_flowLpm; }       // 瞬时流量，1 秒窗口
  float flowTotalL() const { return m_flowTotalL; } // 累计过水量
  uint32_t flowPulses() const { return m_pulseTotal; }
  uint16_t flowCal() const { return m_ppl; }
  void  setFlowCal(uint16_t ppl);
  void  resetFlowTotal();

  // --- 开关量 ---
  bool levelOk() const { return m_levelOk; }        // true = 罐里有水
  bool estopLatched() const { return m_estopLatched; }
  bool leakSeen() const { return m_leakSeen; }
  bool estopRaw() const { return m_estopRaw; }
  bool levelRaw() const { return m_levelRaw; }

  void clearLatches();          // clear 命令调用

  // 供串口打印用
  uint32_t battLastReadMs() const { return m_battLastMs; }

 private:
  float    m_battV;
  uint32_t m_battLastMs;
  uint32_t m_battAccum;
  uint8_t  m_battSamples;

  float    m_flowLpm;
  float    m_flowTotalL;
  uint32_t m_pulseTotal;
  uint32_t m_lastPulseTotal;
  uint32_t m_lastFlowMs;
  uint16_t m_ppl;

  bool     m_levelOk;
  bool     m_levelRaw;
  uint8_t  m_levelStable;

  bool     m_estopLatched;
  bool     m_estopRaw;
  bool     m_estopStable;

  bool     m_leakSeen;
};

extern Inputs inputs;
