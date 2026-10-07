// =============================================================================
//  tempsensor.h  --  DS18B20 多探头异步采集 + ROM 角色映射（存 NVS）
//
//  为什么不用 DallasTemperature 的同步 requestTemperatures()：
//  12 位精度一次转换要 750ms，同步调用会把整个控制循环卡住。这里用异步模式
//  （setWaitForConversion(false)），采样放进状态机里跑，loop() 永不阻塞。
// =============================================================================
#pragma once
#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "config.h"

struct SensorSlot {
  DeviceAddress rom;
  bool          present;
  uint8_t       role;        // SensorRole 或 ROLE_NONE
  float         tempC;       // NAN = 本次读取无效
  uint8_t       badStreak;   // 连续坏值计数
  uint32_t      lastGoodMs;
};

class TempSensors {
 public:
  TempSensors();

  void begin();                       // 初始化总线
  int  scan();                        // 枚举总线，返回在线数量
  int  count() const { return m_count; }

  bool loadRoles();                   // 从 NVS 读取 ROM -> 角色 映射
  bool saveRoles();                   // 保存映射到 NVS
  void clearRoles();
  bool setRoleByIndex(int idx, uint8_t role);      // 按枚举序号分配
  bool setRoleByRom(const String& hex, uint8_t role);
  int  indexOfRom(const String& hex) const;
  bool autoMapByOrder();              // 按总线顺序粗暴映射（仅供台架试跑）

  void tick();                        // 状态机：请求 -> 等待 -> 读取
  float get(uint8_t role) const;      // 角色温度，无效返回 NAN
  bool  valid(uint8_t role) const;
  float rawOfIndex(int idx) const;
  const char* hexOfIndex(int idx) const;
  uint8_t roleOfIndex(int idx) const;

  // 聚合量
  float skinAvg() const;              // 有效体表探头均值
  int   skinValidCount() const;
  float waterDeltaT() const;          // 回水 - 出水
  float estCoolingW(float flowLpm) const;   // 估算制冷功率 P = m_dot*cp*dT
  bool  anyValid() const;

  uint32_t sampleCount() const { return m_samples; }

 private:
  enum Phase { PH_IDLE, PH_WAIT };

  void  readScratchpads();

  OneWire           m_wire;
  DallasTemperature m_dallas;
  SensorSlot        m_slots[ONEWIRE_MAX_DEVICES];
  int               m_count;
  Phase             m_phase;
  uint32_t          m_tPhaseStart;
  uint32_t          m_samples;
  char              m_hex[ONEWIRE_MAX_DEVICES][17];
};

extern TempSensors sensors;
