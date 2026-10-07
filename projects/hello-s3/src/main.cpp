/*
 * hello-s3 -- ESP32-S3-N16R8 bring-up / smoke test
 *
 * Proves, on real silicon, that the whole toolchain is correctly wired:
 *   - the image boots from the 16 MB QIO flash
 *   - the octal (OPI) PSRAM is detected and usable
 *   - the CH343 UART bridge carries a 115200 baud console
 *   - the onboard addressable LED toggles
 *
 * Build:   .\scripts\pio.ps1 run  -d .\projects\hello-s3
 * Upload:  .\scripts\pio.ps1 run  -d .\projects\hello-s3 -t upload
 * Monitor: .\scripts\pio.ps1 device monitor -d .\projects\hello-s3
 */

#include <Arduino.h>
#include <esp_system.h>
#include <esp_chip_info.h>
#include <esp_flash.h>
#include <esp_heap_caps.h>
#include <esp_mac.h>
#include <esp_arduino_version.h>

#ifndef LED_PIN
#define LED_PIN 48
#endif

static void printBanner() {
  Serial.println();
  Serial.println(F("+------------------------------------------+"));
  Serial.println(F("|  hello-s3  ESP32-S3-N16R8 smoke test     |"));
  Serial.println(F("+------------------------------------------+"));
}

static void printChipInfo() {
  esp_chip_info_t chip;
  esp_chip_info(&chip);

  Serial.printf("chip model      : %s (%d core%s)\n",
                chip.model == CHIP_ESP32S3 ? "ESP32-S3" : "other",
                chip.cores, chip.cores == 1 ? "" : "s");
  // esp_chip_info() leaves this at 0 on ESP32-S3 with IDF 4.4 -- it is NOT
  // the revision esptool prints.  esptool reads the eFuse directly and reports
  // the authoritative value ("Chip is ESP32-S3 (QFN56) (revision v0.2)") during
  // upload, so treat that line as the source of truth.
  Serial.printf("chip revision   : %u (esp_chip_info; see esptool upload log)\n",
                (unsigned)chip.revision);
  Serial.printf("cpu frequency   : %u MHz\n", (unsigned)(getCpuFrequencyMhz()));
  Serial.printf("xtal frequency  : %u MHz\n", (unsigned)(getXtalFrequencyMhz()));
  Serial.printf("sdk version     : %s\n", ESP.getSdkVersion());
  Serial.printf("arduino core    : %d.%d.%d\n",
                ESP_ARDUINO_VERSION_MAJOR, ESP_ARDUINO_VERSION_MINOR, ESP_ARDUINO_VERSION_PATCH);

  uint32_t flashSize = 0;
  if (esp_flash_get_size(NULL, &flashSize) == ESP_OK) {
    Serial.printf("flash size      : %u MB\n", (unsigned)(flashSize / (1024 * 1024)));
  }

  uint8_t mac[6] = {0};
  esp_read_mac(mac, ESP_MAC_WIFI_STA);
  Serial.printf("wifi mac        : %02X:%02X:%02X:%02X:%02X:%02X\n",
                mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

static void printPsramInfo() {
  size_t psram = ESP.getPsramSize();
  if (psram > 0) {
    Serial.printf("psram           : %u bytes total, %u bytes free\n",
                  (unsigned)psram, (unsigned)ESP.getFreePsram());
  } else {
    Serial.println(F("psram           : NOT DETECTED"));
    Serial.println(F("                  check board_build.arduino.memory_type = qio_opi"));
  }

  Serial.printf("heap (internal) : %u bytes free\n", (unsigned)ESP.getFreeHeap());
  Serial.printf("heap (largest)  : %u bytes\n",
                (unsigned)heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL));
}

static bool psramAllocationSelfTest() {
  if (ESP.getPsramSize() == 0) return false;

  const size_t kBytes = 1024 * 1024;  // 1 MB out of the 8 MB part
  uint8_t *buf = (uint8_t *)heap_caps_malloc(kBytes, MALLOC_CAP_SPIRAM);
  if (buf == nullptr) {
    Serial.println(F("[FAIL] could not allocate 1 MB from PSRAM"));
    return false;
  }

  // Walking-bit pattern: catches address-line faults that a plain memset misses.
  bool ok = true;
  for (size_t i = 0; i < kBytes; i += 4096) {
    buf[i] = (uint8_t)(i / 4096);
  }
  for (size_t i = 0; i < kBytes; i += 4096) {
    if (buf[i] != (uint8_t)(i / 4096)) { ok = false; break; }
  }
  heap_caps_free(buf);

  Serial.println(ok ? F("[ OK ] 1 MB PSRAM read/write test passed")
                    : F("[FAIL] PSRAM read/write test mismatch"));
  return ok;
}

void setup() {
  Serial.begin(115200);
  delay(1500);  // let the CH343 host-side port settle

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  printBanner();
  printChipInfo();
  printPsramInfo();
  psramAllocationSelfTest();

  Serial.printf("reset reason   : %d\n", (int)esp_reset_reason());
  Serial.println(F("------------------------------------------"));
  Serial.println(F("boot OK -- heartbeat follows"));
}

void loop() {
  static uint32_t tick = 0;
  static bool ledOn = false;

  ledOn = !ledOn;
  digitalWrite(LED_PIN, ledOn ? HIGH : LOW);

  Serial.printf("tick %lu  heap=%u  psram_free=%u  led=%s\n",
                (unsigned long)tick++,
                (unsigned)ESP.getFreeHeap(),
                (unsigned)ESP.getFreePsram(),
                ledOn ? "on" : "off");

  delay(1000);
}
