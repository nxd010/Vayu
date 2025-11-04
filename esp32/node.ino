#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <ArduinoJson.h>

// --- Wi-Fi Configuration ---
const char* ssid = "YOUR_WIFI_SSID";        // Change this to your WiFi name
const char* password = "YOUR_WIFI_PASSWORD"; // Change this to your WiFi password

// --- Backend Server Configuration ---
// IMPORTANT: Replace with your laptop's local IP address
// Find it using: ifconfig (Linux/Mac) or ipconfig (Windows)
const char* serverUrl = "http://192.168.1.100:8000/api/sensor-data";  // CHANGE THIS IP!

// --- Pin Definitions ---
#define DHTPIN 4
#define DHTTYPE DHT11
#define MQ135_PIN 34
#define GREEN_LED 12
#define RED_LED 14
#define BUZZER 27

// --- LCD Setup ---
LiquidCrystal_I2C lcd(0x27, 16, 2);

// --- DHT Sensor ---
DHT dht(DHTPIN, DHTTYPE);

// --- Sensor Data Variables ---
float temperature = 0.0;
float humidity = 0.0;
int airQualityRaw = 0;
float airQualityVoltage = 0.0;
String airQualityLevel = "Unknown";

// --- Timing ---
unsigned long lastSensorTime = 0;
const long sensorDelay = 2000;  // Read and send every 2 seconds
unsigned long lastBeepTime = 0;
const long beepInterval = 2000;

// LCD alternating display
bool showTempHum = true;
unsigned long lcdLastSwitch = 0;
const long lcdSwitchInterval = 4000;

// Connection status
bool wifiConnected = false;
bool backendReachable = false;
int failedRequests = 0;
const int maxFailedRequests = 5;

// --- ADC Calibration ---
const float ADC_VREF = 3.3;

// --- Thresholds ---
const float AQ_GOOD_MAX = 1.0;
const float AQ_MODERATE_MAX = 2.0;

void setup() {
  Serial.begin(115200);
  
  // Initialize LCD
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Vayu Monitor");
  lcd.setCursor(0, 1);
  lcd.print("Starting...");
  
  // Initialize sensors
  dht.begin();
  analogReadResolution(12);
  analogSetPinAttenuation(MQ135_PIN, ADC_11db);
  
  // Initialize outputs
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);
  digitalWrite(BUZZER, LOW);
  
  // Connect to WiFi
  connectToWiFi();
  
  delay(2000);
}

void connectToWiFi() {
  Serial.println("\n Connecting to WiFi...");
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi");
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    lcd.setCursor(attempts % 16, 1);
    lcd.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("\n WiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Server: ");
    Serial.println(serverUrl);
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("WiFi Connected!");
    lcd.setCursor(0, 1);
    lcd.print(WiFi.localIP());
    delay(2000);
    
    // Test backend connection
    testBackendConnection();
  } else {
    wifiConnected = false;
    Serial.println("\n WiFi connection failed!");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("WiFi Failed!");
    lcd.setCursor(0, 1);
    lcd.print("Check Settings");
    delay(3000);
  }
}

void testBackendConnection() {
  Serial.println("🧪 Testing backend connection...");
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Testing Backend");
  
  HTTPClient http;
  http.begin(String(serverUrl).substring(0, String(serverUrl).lastIndexOf('/')) + "/../health");
  http.setTimeout(5000);
  
  int httpCode = http.GET();
  
  if (httpCode > 0) {
    backendReachable = true;
    Serial.println("Backend is reachable!");
    lcd.setCursor(0, 1);
    lcd.print("Backend OK!");
  } else {
    backendReachable = false;
    Serial.println("Backend not reachable!");
    Serial.println("Check if server is running");
    lcd.setCursor(0, 1);
    lcd.print("Backend Error!");
  }
  
  http.end();
  delay(2000);
}

bool sendDataToBackend() {
  if (!wifiConnected) {
    Serial.println("WiFi not connected, attempting reconnect...");
    connectToWiFi();
    return false;
  }
  
  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);
  
  // Create JSON payload matching backend schema
  StaticJsonDocument<256> doc;
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["airQualityVoltage"] = airQualityVoltage;
  doc["airQualityLevel"] = airQualityLevel;
  
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  // Send POST request
  int httpCode = http.POST(jsonPayload);
  
  bool success = false;
  if (httpCode > 0) {
    if (httpCode == 200) {
      success = true;
      failedRequests = 0;
      backendReachable = true;
      
      String response = http.getString();
      Serial.println("Data sent successfully!");
      Serial.println("Response: " + response);
    } else {
      Serial.printf("HTTP Error: %d\n", httpCode);
      failedRequests++;
    }
  } else {
    Serial.printf("Connection failed: %s\n", http.errorToString(httpCode).c_str());
    failedRequests++;
    
    if (failedRequests >= maxFailedRequests) {
      backendReachable = false;
      Serial.println("⚠️  Too many failures, backend may be down");
    }
  }
  
  http.end();
  return success;
}

void readSensors() {
  // Read temperature and humidity
  temperature = dht.readTemperature();
  humidity = dht.readHumidity();
  
  // Check for valid readings
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("⚠️  Failed to read from DHT sensor!");
    temperature = 0.0;
    humidity = 0.0;
  }
  
  // Read air quality
  airQualityRaw = analogRead(MQ135_PIN);
  airQualityVoltage = airQualityRaw * (ADC_VREF / 4095.0);
  
  // Classify air quality
  if (airQualityVoltage <= AQ_GOOD_MAX) {
    airQualityLevel = "Good";
  } else if (airQualityVoltage <= AQ_MODERATE_MAX) {
    airQualityLevel = "Moderate";
  } else {
    airQualityLevel = "Poor";
  }
}

void updateIndicators() {
  // Update LEDs based on air quality
  if (airQualityLevel == "Good") {
    digitalWrite(GREEN_LED, HIGH);
    digitalWrite(RED_LED, LOW);
  } else if (airQualityLevel == "Moderate") {
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(RED_LED, LOW);
  } else {  // Poor
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(RED_LED, HIGH);
  }
}

void updateLCD() {
  unsigned long now = millis();
  
  // Switch display every 4 seconds
  if (now - lcdLastSwitch >= lcdSwitchInterval) {
    showTempHum = !showTempHum;
    lcdLastSwitch = now;
  }
  
  lcd.clear();
  
  if (showTempHum) {
    // Show temperature and humidity
    lcd.setCursor(0, 0);
    lcd.printf("Temp: %.1fC", temperature);
    lcd.setCursor(0, 1);
    lcd.printf("Humidity: %.0f%%", humidity);
  } else {
    // Show air quality
    lcd.setCursor(0, 0);
    lcd.printf("AQ: %.2fV", airQualityVoltage);
    lcd.setCursor(0, 1);
    lcd.print("Status: " + airQualityLevel);
  }
  
  // Show connection status indicator in corner
  if (!backendReachable) {
    lcd.setCursor(15, 0);
    lcd.print("X");  // Connection error indicator
  } else if (failedRequests > 0) {
    lcd.setCursor(15, 0);
    lcd.print("!");  // Warning indicator
  }
}

void handleBuzzer() {
  unsigned long now = millis();
  
  if (airQualityLevel == "Poor") {
    if (now - lastBeepTime >= beepInterval) {
      tone(BUZZER, 1000, 400);  // 400ms beep
      lastBeepTime = now;
    }
  } else {
    noTone(BUZZER);
  }
}

void printDebugInfo() {
  Serial.println("\n Current Readings:");
  Serial.printf("   Temperature: %.1f°C\n", temperature);
  Serial.printf("   Humidity: %.0f%%\n", humidity);
  Serial.printf("   Air Quality: %.2fV (%s)\n", airQualityVoltage, airQualityLevel.c_str());
  Serial.printf("   WiFi: %s | Backend: %s | Failed: %d\n", 
                wifiConnected ? "✓" : "✗",
                backendReachable ? "✓" : "✗",
                failedRequests);
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Read sensors and send data every 2 seconds
  if (currentMillis - lastSensorTime >= sensorDelay) {
    // Read sensor data
    readSensors();
    
    // Update indicators
    updateIndicators();
    
    // Update LCD
    updateLCD();
    
    // Print debug info to Serial
    printDebugInfo();
    
    // Send data to backend
    if (wifiConnected) {
      bool sent = sendDataToBackend();
      if (!sent && !backendReachable) {
        Serial.println("Backend unreachable - data not sent");
        Serial.println("Make sure backend server is running:");
        Serial.println("cd backend && uvicorn app.main:app --reload --host 0.0.0.0");
      }
    }
    
    lastSensorTime = currentMillis;
  }
  
  // Handle buzzer alerts
  handleBuzzer();
  
  // Auto-reconnect WiFi if disconnected
  if (WiFi.status() != WL_CONNECTED) {
    wifiConnected = false;
    Serial.println("WiFi disconnected! Reconnecting...");
    connectToWiFi();
  }
}