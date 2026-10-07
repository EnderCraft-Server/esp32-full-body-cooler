#include "tempsensor.h"
#include <Preferences.h>

TempSensors sensors;

static const char* NVS_NS = "bodycool";

TempSensors::TempSensors()
    : m_wire(PIN_ONEWIRE), m_dallas(&m_wire), m_count(0),
      m_phase(PH_IDLE), m_tPhaseStart(0), m_samples(0) {
  for (int i = 0; i < ONEWIRE_MAX_DEVICES; i++) {
    m_slots[i].present = false;
    m_slots[i].role = ROLE_NONE;
    m_slots[i].tempC = NAN;
    m_slots[i].badStreak = 0;
    m_slots[i].lastGoodMs = 0;
    memset(m_slots[i].rom, 0, sizeof(DeviceAddress));
    m_hex[i][0] = 0;
  }
}

void TempSensors::begin() {
  m_dallas.begin();
  m_dallas.setWaitForConversion(false);   // 关键：异步，不阻塞 loop()
  m_dallas.setResolution(DS18B20_RESOLUTION);
  scan();
  loadRoles();
}

int TempSensors::scan() {
  m_dallas.begin();
  int n = m_dallas.getDeviceCount();
  if (n > ONEWIRE_MAX_DEVICES) n = ONEWIRE_MAX_DEVICES;

  // 重扫会重排序号，但角色是绑在 ROM 上的。先把旧表的 ROM->角色 抄下来，
  // 重扫完再按 ROM 贴回去，这样 scan 不会把用户刚 map 好的角色清掉。
  DeviceAddress oldRom[ONEWIRE_MAX_DEVICES];
  uint8_t oldRole[ONEWIRE_MAX_DEVICES];
  int oldCount = m_count;
  for (int i = 0; i < ONEWIRE_MAX_DEVICES; i++) {
    memcpy(oldRom[i], m_slots[i].rom, sizeof(DeviceAddress));
    oldRole[i] = m_slots[i].role;
  }

  for (int i = 0; i < ONEWIRE_MAX_DEVICES; i++) {
    m_slots[i].present = false;
    m_hex[i][0] = 0;
  }
  m_count = 0;
  for (int i = 0; i < n; i++) {
    DeviceAddress a;
    if (!m_dallas.getAddress(a, i)) continue;
    memcpy(m_slots[m_count].rom, a, sizeof(DeviceAddress));
    m_slots[m_count].present = true;
    for (int b = 0; b < 8; b++) {
      sprintf(&m_hex[m_count][b * 2], "%02X", a[b]);
    }
    m_hex[m_count][16] = 0;
    m_count++;
  }

  // 按 ROM 把角色贴回去
  for (int i = 0; i < m_count; i++) {
    for (int j = 0; j < oldCount; j++) {
      if (oldRole[j] == ROLE_NONE) continue;
      if (memcmp(oldRom[j], m_slots[i].rom, sizeof(DeviceAddress)) == 0) {
        m_slots[i].role = oldRole[j];
        break;
      }
    }
  }
  return m_count;
}

int TempSensors::indexOfRom(const String& hexIn) const {
  String want = hexIn;
  want.trim();
  want.toUpperCase();
  for (int i = 0; i < m_count; i++) {
    if (want == m_hex[i]) return i;
  }
  return -1;
}

const char* TempSensors::hexOfIndex(int idx) const {
  if (idx < 0 || idx >= m_count) return "----------------";
  return m_hex[idx];
}

uint8_t TempSensors::roleOfIndex(int idx) const {
  if (idx < 0 || idx >= m_count) return ROLE_NONE;
  return m_slots[idx].role;
}

bool TempSensors::setRoleByIndex(int idx, uint8_t role) {
  if (idx < 0 || idx >= m_count) return false;
  if (role >= ROLE_COUNT && role != ROLE_NONE) return false;
  // 一个角色只能绑一个探头：先把旧绑定清掉
  for (int i = 0; i < ONEWIRE_MAX_DEVICES; i++) {
    if (m_slots[i].role == role && role != ROLE_NONE) m_slots[i].role = ROLE_NONE;
  }
  m_slots[idx].role = role;
  return true;
}

bool TempSensors::setRoleByRom(const String& hex, uint8_t role) {
  int idx = indexOfRom(hex);
  if (idx < 0) return false;
  return setRoleByIndex(idx, role);
}

void TempSensors::clearRoles() {
  for (int i = 0; i < ONEWIRE_MAX_DEVICES; i++) m_slots[i].role = ROLE_NONE;
}

bool TempSensors::autoMapByOrder() {
  if (m_count < 1) return false;
  clearRoles();
  for (int i = 0; i < m_count && i < ROLE_COUNT; i++) {
    m_slots[i].role = (uint8_t)i;
  }
  return true;
}

// NVS 里存两份：r<i> = 枚举序号 -> ROM（快照），role_<ROM> = ROM -> 角色。
// 真正生效的是 role_<ROM>，因为枚举序号会随上电顺序变化。
// NVS 键名最长 15 字符！不能把 16 位 ROM 拼进键名（role_加ROM = 21 字符，会静默写入失败）。
// 改用短键 m<序号> 存角色：r<i> 存 序号->ROM，m<i> 存 序号->角色。
// 读回来时用 ROM 反查探头，所以即使上电枚举顺序变了也不会串角色。
bool TempSensors::loadRoles() {
  Preferences p;
  // 用读写方式打开：命名空间不存在时 NVS 会自动创建，不会刷 NOT_FOUND 错误日志
  if (!p.begin(NVS_NS, false)) return false;
  clearRoles();
  bool any = false;
  for (int i = 0; i < m_count; i++) {
    String key = String("r") + String(i);
    String hex = p.getString(key.c_str(), "");
    if (hex.length() != 16) continue;
    int idx = indexOfRom(hex);
    if (idx < 0) continue;                    // 这个探头现在不在线上
    String mk = String("m") + String(i);
    uint8_t role = (uint8_t)p.getUChar(mk.c_str(), ROLE_NONE);
    if (role < ROLE_COUNT) {
      m_slots[idx].role = role;
      any = true;
    }
  }
  p.end();
  return any;
}

bool TempSensors::saveRoles() {
  Preferences p;
  if (!p.begin(NVS_NS, false)) return false;
  p.clear();
  for (int i = 0; i < m_count; i++) {
    p.putString((String("r") + String(i)).c_str(), m_hex[i]);
    p.putUChar((String("m") + String(i)).c_str(), m_slots[i].role);
  }
  p.end();
  return true;
}

void TempSensors::tick() {
  uint32_t now = millis();
  if (m_count <= 0) return;

  if (m_phase == PH_IDLE) {
    m_dallas.requestTemperatures();   // 非阻塞：只发 0x44 转换命令
    m_phase = PH_WAIT;
    m_tPhaseStart = now;
  } else if (now - m_tPhaseStart >= SENSOR_SETTLE_MS) {
    readScratchpads();
    m_phase = PH_IDLE;
    m_tPhaseStart = now;
    m_samples++;
  }
}

void TempSensors::readScratchpads() {
  for (int i = 0; i < m_count; i++) {
    if (!m_slots[i].present) continue;
    bool ok = true;
    float t = m_dallas.getTempC(m_slots[i].rom);

    if (t == DEVICE_DISCONNECTED_C)                              ok = false;
    else if (t != t)                                             ok = false;  // NaN
    else if (t >= SENSOR_FAULT_LIMIT_NORMAL)                     ok = false;  // 85C 上电默认值
    else if (t <= SENSOR_FAULT_LIMIT_LOW)                        ok = false;  // -127C 断线

    if (ok) {
      m_slots[i].tempC = t;
      m_slots[i].badStreak = 0;
      m_slots[i].lastGoodMs = millis();
    } else {
      if (m_slots[i].badStreak < 255) m_slots[i].badStreak++;
      // 连续坏值才判定失效；偶发一个坏值沿用上一次有效值
      if (m_slots[i].badStreak >= SENSOR_BAD_STREAK) {
        m_slots[i].tempC = NAN;
      }
    }
  }
}

float TempSensors::get(uint8_t role) const {
  for (int i = 0; i < m_count; i++) {
    if (m_slots[i].role == role) return m_slots[i].tempC;
  }
  return NAN;
}

bool TempSensors::valid(uint8_t role) const {
  float t = get(role);
  return !isnan(t);
}

float TempSensors::rawOfIndex(int idx) const {
  if (idx < 0 || idx >= m_count) return NAN;
  return m_slots[idx].tempC;
}

int TempSensors::skinValidCount() const {
  int n = 0;
  if (valid(ROLE_SKIN_CHEST)) n++;
  if (valid(ROLE_SKIN_BACK)) n++;
  return n;
}

float TempSensors::skinAvg() const {
  float sum = 0; int n = 0;
  float a = get(ROLE_SKIN_CHEST);
  float b = get(ROLE_SKIN_BACK);
  if (!isnan(a)) { sum += a; n++; }
  if (!isnan(b)) { sum += b; n++; }
  if (n == 0) return NAN;
  return sum / (float)n;
}

float TempSensors::waterDeltaT() const {
  float o = get(ROLE_WATER_OUT);
  float r = get(ROLE_WATER_RET);
  if (isnan(o) || isnan(r)) return NAN;
  return r - o;
}

float TempSensors::estCoolingW(float flowLpm) const {
  float dt = waterDeltaT();
  if (isnan(dt) || dt <= 0) return 0.0f;
  // P = m_dot * c_p * dT ;  1 L/min = 16.667 g/s（水 cp = 4.186 J/(g*K)）
  float mDot = flowLpm * 16.667f;
  return mDot * 4.186f * dt;
}

bool TempSensors::anyValid() const {
  for (int i = 0; i < m_count; i++) {
    if (!isnan(m_slots[i].tempC)) return true;
  }
  return false;
}
