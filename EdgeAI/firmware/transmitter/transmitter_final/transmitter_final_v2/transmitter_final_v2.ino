// FINAL TRANSMITTER CODE (v2 - new sensor layout)
// 5 sensors -> ~90Hz sampling -> 72-byte payload -> 75-byte frame -> ESP-NOW
// POWER: barrel jack -> buck converter -> ESP32 5V pin ONLY. Do NOT connect USB
// while running on this power path (risk of backfeeding two power sources into
// the board at once). USB is only for flashing; unplug it before running the rig.

#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_INA219.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <driver/i2s.h>
#include <math.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

// ---- Pin definitions ----
#define SDA_PIN 8
#define SCL_PIN 9
#define BEARING_MPU_ADDR 0x68
#define MOTOR_MPU_ADDR   0x69
#define ONE_WIRE_PIN 4
#define I2S_SCK_PIN 5
#define I2S_WS_PIN  6
#define I2S_SD_PIN  7
#define I2S_SAMPLE_RATE 16000
#define I2S_SAMPLE_COUNT 64

// ---- Frame format ----
#define PAYLOAD_SIZE 72
#define FRAME_SIZE 75
#define SYNC_BYTE_1 0xAA
#define SYNC_BYTE_2 0x55

// ---- Timing ----
#define SAMPLE_INTERVAL_MS 11          // confirmed real-world rate ~90Hz
#define TEMP_REQUEST_INTERVAL_MS 200

// ---- Receiver MAC address ----
uint8_t receiverMac[] = {0x98, 0xA3, 0x16, 0xE6, 0x4A, 0xB4};

Adafruit_MPU6050 bearingMpu;
Adafruit_MPU6050 motorMpu;
Adafruit_INA219 ina219;
OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature ds18b20(&oneWire);

int32_t i2sBuffer[I2S_SAMPLE_COUNT];
uint8_t frame[FRAME_SIZE];
uint32_t packetCounter = 0;

unsigned long lastSampleTime = 0;

// ---- DS18B20 async state machine ----
unsigned long lastTempRequestTime = 0;
bool tempConversionInProgress = false;
float cachedTempC = 25.0;

void onDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
  // Intentionally empty - status callback unreliable at this rate,
  // real confirmation is receiver's packet counter continuity
}

void setupI2S() {
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = I2S_SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = 0,
    .dma_buf_count = 4,
    .dma_buf_len = 256,
    .use_apll = false
  };
  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK_PIN,
    .ws_io_num = I2S_WS_PIN,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD_PIN
  };
  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);
}

float readAudioRMS() {
  size_t bytesRead = 0;
  i2s_read(I2S_NUM_0, i2sBuffer, sizeof(i2sBuffer), &bytesRead, pdMS_TO_TICKS(5));

  int samplesRead = bytesRead / sizeof(int32_t);
  if (samplesRead == 0) return 0.0;

  double sumSquares = 0;
  for (int i = 0; i < samplesRead; i++) {
    int32_t sample = i2sBuffer[i] >> 8;
    sumSquares += (double)sample * (double)sample;
  }
  return sqrt(sumSquares / samplesRead);
}

void updateTemperatureAsync() {
  unsigned long now = millis();

  if (!tempConversionInProgress && (now - lastTempRequestTime >= TEMP_REQUEST_INTERVAL_MS)) {
    ds18b20.requestTemperatures();
    tempConversionInProgress = true;
    lastTempRequestTime = now;
  }

  if (tempConversionInProgress && ds18b20.isConversionComplete()) {
    cachedTempC = ds18b20.getTempCByIndex(0);
    tempConversionInProgress = false;
  }
}

void buildFrame() {
  sensors_event_t a1, g1, t1;
  sensors_event_t a2, g2, t2;
  bearingMpu.getEvent(&a1, &g1, &t1);
  motorMpu.getEvent(&a2, &g2, &t2);

  float busVoltage = ina219.getBusVoltage_V();
  float current_mA = ina219.getCurrent_mA();
  float power_mW = ina219.getPower_mW();

  float audioRMS = readAudioRMS();

  frame[0] = SYNC_BYTE_1;
  frame[1] = SYNC_BYTE_2;

  uint8_t *p = &frame[2];
  memcpy(p + 0,  &a1.acceleration.x, 4);
  memcpy(p + 4,  &a1.acceleration.y, 4);
  memcpy(p + 8,  &a1.acceleration.z, 4);
  memcpy(p + 12, &g1.gyro.x, 4);
  memcpy(p + 16, &g1.gyro.y, 4);
  memcpy(p + 20, &g1.gyro.z, 4);
  memcpy(p + 24, &a2.acceleration.x, 4);
  memcpy(p + 28, &a2.acceleration.y, 4);
  memcpy(p + 32, &a2.acceleration.z, 4);
  memcpy(p + 36, &g2.gyro.x, 4);
  memcpy(p + 40, &g2.gyro.y, 4);
  memcpy(p + 44, &g2.gyro.z, 4);
  memcpy(p + 48, &busVoltage, 4);
  memcpy(p + 52, &current_mA, 4);
  memcpy(p + 56, &power_mW, 4);
  memcpy(p + 60, &cachedTempC, 4);
  memcpy(p + 64, &audioRMS, 4);
  memcpy(p + 68, &packetCounter, 4);

  uint8_t checksum = 0;
  for (int i = 0; i < PAYLOAD_SIZE; i++) checksum ^= frame[2 + i];
  frame[74] = checksum;

  packetCounter++;
}

void setup() {
  Serial.begin(115200);   // local debug only, unrelated to receiver's 460800
  delay(500);

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);

  if (!bearingMpu.begin(BEARING_MPU_ADDR)) { Serial.println("FAILED - bearing MPU6050"); while (1) delay(1000); }
  if (!motorMpu.begin(MOTOR_MPU_ADDR))     { Serial.println("FAILED - motor MPU6050");   while (1) delay(1000); }
  if (!ina219.begin())                      { Serial.println("FAILED - INA219");          while (1) delay(1000); }

  ds18b20.begin();
  if (ds18b20.getDeviceCount() == 0)        { Serial.println("FAILED - DS18B20");         while (1) delay(1000); }
  ds18b20.setWaitForConversion(false);
  ds18b20.setResolution(9);

  bearingMpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  bearingMpu.setGyroRange(MPU6050_RANGE_500_DEG);
  bearingMpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  motorMpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  motorMpu.setGyroRange(MPU6050_RANGE_500_DEG);
  motorMpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  setupI2S();

  WiFi.mode(WIFI_STA);
  delay(100);
  esp_wifi_set_ps(WIFI_PS_NONE);

  if (esp_now_init() != ESP_OK) { Serial.println("ESP-NOW init FAILED"); while (1) delay(1000); }
  esp_now_register_send_cb(onDataSent);

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, receiverMac, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  if (esp_now_add_peer(&peerInfo) != ESP_OK) { Serial.println("Failed to add peer"); while (1) delay(1000); }

  Serial.println("Transmitter ready.");
  lastSampleTime = millis();
}

void loop() {
  updateTemperatureAsync();

  unsigned long now = millis();
  if (now - lastSampleTime >= SAMPLE_INTERVAL_MS) {
    lastSampleTime = now;
    buildFrame();
    esp_now_send(receiverMac, frame, FRAME_SIZE);
  }
}
