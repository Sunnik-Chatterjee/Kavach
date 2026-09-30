// FINAL RECEIVER CODE (v4) - real live-inference receiver
// ESP-NOW receive -> validate -> parse -> relay CSV to laptop over serial,
// AND listen on that same serial connection for "PRED,<label>,<confidence>"
// messages sent back by ml/live_inference.py, driving the OLED (2 pages),
// RGB LED health color, and buzzer alert from the model's real prediction.
//
// This is NOT the demo/video sketch - see firmware/receiver/receiver_demo
// for the button/webpage-controlled walkthrough used for filming. That one
// never runs live inference; this one does.
//
// RGB LED is common-anode: LOW = on, HIGH = off (handled in setRgbColor()).

#include <WiFi.h>
#include <esp_now.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define FRAME_SIZE 75
#define PAYLOAD_SIZE 72
#define SYNC_BYTE_1 0xAA
#define SYNC_BYTE_2 0x55

// ---- OLED pins (SPI) ----
#define OLED_CS   8
#define OLED_DC   9
#define OLED_RST  10
#define OLED_MOSI 11
#define OLED_SCK  12
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &SPI, OLED_DC, OLED_RST, OLED_CS);

// ---- Buttons ----
#define BTN1 15   // show raw sensor readings
#define BTN2 16   // show fault status (default page)
#define BTN3 17   // silence buzzer
#define BTN4 18   // unmute / re-arm buzzer

// ---- Buzzer ----
#define BUZZER 21

// ---- RGB LED ----
#define RGB_R 38
#define RGB_G 39
#define RGB_B 40

// ---- Packet loss tracking ----
uint32_t lastPacketCounter = 0;
uint32_t totalReceived = 0;
uint32_t totalExpected = 0;
bool firstPacket = true;
unsigned long lastStatsTime = 0;

// ---- Latest raw sensor values (for button 1 display) ----
float latest_bearing_ax, latest_bearing_ay, latest_bearing_az;
float latest_motor_ax, latest_motor_ay, latest_motor_az;
float latest_current_mA, latest_temperature_C, latest_audio_rms;

// ---- Latest prediction (received from laptop over Serial) ----
String currentLabel = "waiting...";
float currentConfidence = 0.0;
unsigned long lastPredictionTime = 0;

// ---- Display / UI state ----
int displayPage = 1;   // 1 = status (default), 0 = raw sensors
unsigned long lastOledUpdate = 0;
const unsigned long OLED_UPDATE_INTERVAL = 300;

// ---- Buzzer state ----
bool buzzerMuted = false;
unsigned long lastBeepTime = 0;
bool beepState = false;

// ---- Button debounce ----
unsigned long lastButtonPress = 0;
const unsigned long BUTTON_DEBOUNCE_MS = 200;

void trackPacketLoss(uint32_t packetCounter) {
  totalReceived++;
  if (!firstPacket) {
    uint32_t expectedGap = packetCounter - lastPacketCounter;
    totalExpected += expectedGap;
  } else {
    firstPacket = false;
    totalExpected = 1;
  }
  lastPacketCounter = packetCounter;
}

void printLossStatsIfDue() {
  unsigned long now = millis();
  if (now - lastStatsTime >= 1000) {
    lastStatsTime = now;
    if (totalExpected > 0) {
      float deliveryRate = (float)totalReceived / (float)totalExpected * 100.0;
      Serial.print("[STATS] Delivery rate: ");
      Serial.print(deliveryRate, 1);
      Serial.print("% (");
      Serial.print(totalReceived);
      Serial.print("/");
      Serial.print(totalExpected);
      Serial.println(")");
    }
  }
}

void onDataRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  if (len != FRAME_SIZE) {
    Serial.print("REJECTED - wrong length: ");
    Serial.println(len);
    return;
  }

  if (data[0] != SYNC_BYTE_1 || data[1] != SYNC_BYTE_2) {
    Serial.println("REJECTED - bad sync bytes");
    return;
  }

  uint8_t checksum = 0;
  for (int i = 0; i < PAYLOAD_SIZE; i++) {
    checksum ^= data[2 + i];
  }
  if (checksum != data[74]) {
    Serial.println("REJECTED - checksum mismatch");
    return;
  }

  const uint8_t *payload = &data[2];

  float bearing_ax, bearing_ay, bearing_az, bearing_gx, bearing_gy, bearing_gz;
  float motor_ax, motor_ay, motor_az, motor_gx, motor_gy, motor_gz;
  float bus_voltage, current, power, temperature, audio_rms;
  uint32_t packet_counter;

  memcpy(&bearing_ax, payload + 0,  4);
  memcpy(&bearing_ay, payload + 4,  4);
  memcpy(&bearing_az, payload + 8,  4);
  memcpy(&bearing_gx, payload + 12, 4);
  memcpy(&bearing_gy, payload + 16, 4);
  memcpy(&bearing_gz, payload + 20, 4);
  memcpy(&motor_ax,   payload + 24, 4);
  memcpy(&motor_ay,   payload + 28, 4);
  memcpy(&motor_az,   payload + 32, 4);
  memcpy(&motor_gx,   payload + 36, 4);
  memcpy(&motor_gy,   payload + 40, 4);
  memcpy(&motor_gz,   payload + 44, 4);
  memcpy(&bus_voltage,payload + 48, 4);
  memcpy(&current,    payload + 52, 4);
  memcpy(&power,       payload + 56, 4);
  memcpy(&temperature,payload + 60, 4);
  memcpy(&audio_rms,  payload + 64, 4);
  memcpy(&packet_counter, payload + 68, 4);

  trackPacketLoss(packet_counter);

  // Save for button-1 raw display
  latest_bearing_ax = bearing_ax; latest_bearing_ay = bearing_ay; latest_bearing_az = bearing_az;
  latest_motor_ax = motor_ax; latest_motor_ay = motor_ay; latest_motor_az = motor_az;
  latest_current_mA = current; latest_temperature_C = temperature; latest_audio_rms = audio_rms;

  // CSV relay - this is what ml/live_inference.py parses
  Serial.print(bearing_ax, 4); Serial.print(",");
  Serial.print(bearing_ay, 4); Serial.print(",");
  Serial.print(bearing_az, 4); Serial.print(",");
  Serial.print(bearing_gx, 4); Serial.print(",");
  Serial.print(bearing_gy, 4); Serial.print(",");
  Serial.print(bearing_gz, 4); Serial.print(",");
  Serial.print(motor_ax, 4); Serial.print(",");
  Serial.print(motor_ay, 4); Serial.print(",");
  Serial.print(motor_az, 4); Serial.print(",");
  Serial.print(motor_gx, 4); Serial.print(",");
  Serial.print(motor_gy, 4); Serial.print(",");
  Serial.print(motor_gz, 4); Serial.print(",");
  Serial.print(bus_voltage, 4); Serial.print(",");
  Serial.print(current, 4); Serial.print(",");
  Serial.print(power, 4); Serial.print(",");
  Serial.print(temperature, 4); Serial.print(",");
  Serial.print(audio_rms, 4); Serial.print(",");
  Serial.println(packet_counter);
}

// Reads any incoming prediction messages from the laptop.
// Expected format: "PRED,<label>,<confidence>\n"  e.g. "PRED,healthy,0.94"
void checkForPredictionFromLaptop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    if (line.startsWith("PRED,")) {
      int firstComma = line.indexOf(',');
      int secondComma = line.indexOf(',', firstComma + 1);
      if (secondComma > 0) {
        String label = line.substring(firstComma + 1, secondComma);
        String confStr = line.substring(secondComma + 1);

        if (label != currentLabel) {
          // New/different prediction - reset mute so a NEW fault still alerts
          buzzerMuted = false;
        }
        currentLabel = label;
        currentConfidence = confStr.toFloat();
        lastPredictionTime = millis();
      }
    }
  }
}

void setRgbColor(int r, int g, int b) {
  // Common-anode LED - pin driven LOW turns that color ON, HIGH turns it OFF.
  digitalWrite(RGB_R, r ? LOW : HIGH);
  digitalWrite(RGB_G, g ? LOW : HIGH);
  digitalWrite(RGB_B, b ? LOW : HIGH);
}

void updateRgbAndBuzzer() {
  bool isFault = (currentLabel != "healthy" && currentLabel != "waiting...");
  bool lowConfidence = (currentConfidence < 0.40);

  if (currentLabel == "waiting...") {
    setRgbColor(LOW, LOW, LOW);   // off - no prediction yet
  } else if (lowConfidence) {
    setRgbColor(HIGH, HIGH, LOW); // yellow - uncertain
  } else if (isFault) {
    setRgbColor(HIGH, LOW, LOW);  // red - fault detected
  } else {
    setRgbColor(LOW, HIGH, LOW);  // green - healthy
  }

  // Buzzer: beep pattern while a real fault is active, confident, and not muted
  if (isFault && !lowConfidence && !buzzerMuted) {
    unsigned long now = millis();
    if (now - lastBeepTime >= 400) {
      beepState = !beepState;
      digitalWrite(BUZZER, beepState ? HIGH : LOW);
      lastBeepTime = now;
    }
  } else {
    digitalWrite(BUZZER, LOW);
  }
}

void updateOledDisplay() {
  unsigned long now = millis();
  if (now - lastOledUpdate < OLED_UPDATE_INTERVAL) return;
  lastOledUpdate = now;

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);

  if (displayPage == 1) {
    // Status page
    display.println("STATUS");
    display.println("-----------------");
    display.print("Cond: ");
    display.println(currentLabel);
    display.print("Conf: ");
    display.print(currentConfidence * 100, 1);
    display.println("%");
    if (buzzerMuted) display.println("[Alarm muted]");
  } else {
    // Raw sensor page
    display.println("RAW SENSORS");
    display.println("-----------------");
    display.print("BrAx:"); display.print(latest_bearing_ax, 1);
    display.print(" MoAx:"); display.println(latest_motor_ax, 1);
    display.print("Cur:"); display.print(latest_current_mA, 0); display.println("mA");
    display.print("Tmp:"); display.print(latest_temperature_C, 1); display.println("C");
    display.print("Aud:"); display.println(latest_audio_rms, 0);
  }

  display.display();
}

void checkButtons() {
  unsigned long now = millis();
  if (now - lastButtonPress < BUTTON_DEBOUNCE_MS) return;

  if (digitalRead(BTN1) == LOW) {
    displayPage = 0;
    lastButtonPress = now;
  } else if (digitalRead(BTN2) == LOW) {
    displayPage = 1;
    lastButtonPress = now;
  } else if (digitalRead(BTN3) == LOW) {
    buzzerMuted = true;
    lastButtonPress = now;
  } else if (digitalRead(BTN4) == LOW) {
    buzzerMuted = false;
    lastButtonPress = now;
  }
}

void setup() {
  Serial.begin(460800);
  delay(500);

  pinMode(BTN1, INPUT_PULLUP);
  pinMode(BTN2, INPUT_PULLUP);
  pinMode(BTN3, INPUT_PULLUP);
  pinMode(BTN4, INPUT_PULLUP);
  pinMode(BUZZER, OUTPUT);
  pinMode(RGB_R, OUTPUT);
  pinMode(RGB_G, OUTPUT);
  pinMode(RGB_B, OUTPUT);
  digitalWrite(BUZZER, LOW);

  if (!display.begin(SSD1306_SWITCHCAPVCC)) {
    Serial.println("OLED init FAILED");
  } else {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 0);
    display.println("Receiver starting...");
    display.display();
  }

  WiFi.mode(WIFI_STA);
  delay(100);

  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW init FAILED");
    return;
  }

  esp_now_register_recv_cb(onDataRecv);
  Serial.println("ESP-NOW receiver ready, relaying valid frames as CSV...");
}

void loop() {
  printLossStatsIfDue();
  checkForPredictionFromLaptop();
  checkButtons();
  updateRgbAndBuzzer();
  updateOledDisplay();
}
