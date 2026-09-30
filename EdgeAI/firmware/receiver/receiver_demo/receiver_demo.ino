// RECEIVER - DEMO MODE FOR VIDEO RECORDING (with web page control)
// Standalone demo sketch - not the real live-inference receiver.
//
// Real sensor data still flows in live via ESP-NOW and is shown on the raw
// sensor page (Button 1) - that page is genuine, not hardcoded.
//
// The "current condition" on the status page (Button 2) can be changed
// THREE ways: physical Button 3 (next) / Button 4 (previous), OR by
// connecting to this board's own WiFi hotspot and clicking a status on
// the web page it hosts.
//
// WiFi hotspot: SSID "PredictiveMaintenance", password "maintenance123"
// After connecting, open a browser to: http://192.168.4.1

#include <WiFi.h>
#include <esp_now.h>
#include <WebServer.h>
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
#define BTN1 15
#define BTN2 16
#define BTN3 17
#define BTN4 18

// ---- Buzzer ----
#define BUZZER 21

// ---- RGB LED (common anode - LOW = on) ----
#define RGB_R 38
#define RGB_G 39
#define RGB_B 40

// ---- WiFi hotspot settings ----
const char* AP_SSID = "PredictiveMaintenance";
const char* AP_PASSWORD = "maintenance123";
const int WIFI_CHANNEL = 1;

WebServer server(80);

// ---- The 7 trained fault classes ----
const char* DEMO_LABELS[] = {
  "healthy",
  "bearing_fault_near",
  "bearing_fault_far",
  "bearing_fault_both",
  "rotor_imbalance",
  "shaft_misalignment",
  "mechanical_looseness"
};
const int NUM_DEMO_LABELS = 7;
int currentDemoIndex = 0;

// ---- Latest raw sensor values (real, live) ----
float latest_bearing_ax, latest_bearing_ay, latest_bearing_az;
float latest_motor_ax, latest_motor_ay, latest_motor_az;
float latest_current_mA, latest_temperature_C, latest_audio_rms;

// ---- Display / UI state ----
int displayPage = 1;
unsigned long lastOledUpdate = 0;
const unsigned long OLED_UPDATE_INTERVAL = 300;

// ---- Buzzer state ----
unsigned long lastBeepTime = 0;
bool beepState = false;

// ---- Button debounce ----
unsigned long lastButtonPress = 0;
const unsigned long BUTTON_DEBOUNCE_MS = 250;


void onDataRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  if (len != FRAME_SIZE) return;
  if (data[0] != SYNC_BYTE_1 || data[1] != SYNC_BYTE_2) return;

  uint8_t checksum = 0;
  for (int i = 0; i < PAYLOAD_SIZE; i++) checksum ^= data[2 + i];
  if (checksum != data[74]) return;

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

  latest_bearing_ax = bearing_ax; latest_bearing_ay = bearing_ay; latest_bearing_az = bearing_az;
  latest_motor_ax = motor_ax; latest_motor_ay = motor_ay; latest_motor_az = motor_az;
  latest_current_mA = current; latest_temperature_C = temperature; latest_audio_rms = audio_rms;
}

void setRgbColor(int r, int g, int b) {
  digitalWrite(RGB_R, r ? LOW : HIGH);
  digitalWrite(RGB_G, g ? LOW : HIGH);
  digitalWrite(RGB_B, b ? LOW : HIGH);
}

void updateRgbAndBuzzer() {
  bool isFault = (currentDemoIndex != 0);

  if (isFault) {
    setRgbColor(HIGH, LOW, LOW);
    unsigned long now = millis();
    if (now - lastBeepTime >= 400) {
      beepState = !beepState;
      digitalWrite(BUZZER, beepState ? HIGH : LOW);
      lastBeepTime = now;
    }
  } else {
    setRgbColor(LOW, HIGH, LOW);
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
    display.println("STATUS");
    display.println("-----------------");
    display.print("Cond: ");
    display.println(DEMO_LABELS[currentDemoIndex]);
  } else {
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
    currentDemoIndex = (currentDemoIndex + 1) % NUM_DEMO_LABELS;
    lastButtonPress = now;
  } else if (digitalRead(BTN4) == LOW) {
    currentDemoIndex = (currentDemoIndex - 1 + NUM_DEMO_LABELS) % NUM_DEMO_LABELS;
    lastButtonPress = now;
  }
}

// ---- Web server handlers ----

String buildWebPage() {
  String html = "<!DOCTYPE html><html><head><title>Predictive Maintenance Demo</title>";
  html += "<meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<style>";
  html += "body{font-family:sans-serif;background:#1e1e2f;color:#fff;text-align:center;padding:20px;}";
  html += "h1{font-size:20px;color:#8ab4f8;}";
  html += "p.current{font-size:16px;color:#9be29b;margin-bottom:20px;}";
  html += "a.btn{display:block;margin:10px auto;padding:16px;width:80%;max-width:320px;";
  html += "background:#2f5496;color:#fff;text-decoration:none;border-radius:8px;font-size:16px;}";
  html += "a.btn.active{background:#c0392b;}";
  html += "</style></head><body>";
  html += "<h1>Receiver Status Control</h1>";
  html += "<p class='current'>Current: " + String(DEMO_LABELS[currentDemoIndex]) + "</p>";

  for (int i = 0; i < NUM_DEMO_LABELS; i++) {
    String activeClass = (i == currentDemoIndex) ? " active" : "";
    html += "<a class='btn" + activeClass + "' href='/set?state=" + String(i) + "'>" + String(DEMO_LABELS[i]) + "</a>";
  }

  html += "</body></html>";
  return html;
}

void handleRoot() {
  server.send(200, "text/html", buildWebPage());
}

void handleSetState() {
  if (server.hasArg("state")) {
    int newState = server.arg("state").toInt();
    if (newState >= 0 && newState < NUM_DEMO_LABELS) {
      currentDemoIndex = newState;
    }
  }
  server.sendHeader("Location", "/");
  server.send(303);
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
    display.println("Demo mode starting...");
    display.display();
  }

  WiFi.mode(WIFI_AP_STA);   // FIXED: was WIFI_AP - AP-only mode disabled the
                             // STA interface that ESP-NOW needs to receive
                             // incoming packets from the transmitter
  WiFi.softAP(AP_SSID, AP_PASSWORD, WIFI_CHANNEL);
  Serial.print("AP started. Connect to WiFi '");
  Serial.print(AP_SSID);
  Serial.println("' then browse to http://192.168.4.1");

  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW init FAILED");
    return;
  }
  esp_now_register_recv_cb(onDataRecv);

  server.on("/", handleRoot);
  server.on("/set", handleSetState);
  server.begin();
  Serial.println("Web server started. Receiver DEMO MODE ready.");
}

void loop() {
  server.handleClient();
  checkButtons();
  updateRgbAndBuzzer();
  updateOledDisplay();
}