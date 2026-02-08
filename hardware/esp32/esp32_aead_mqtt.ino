/*
ESP32 AEAD + MQTT Demo
- Connects to WiFi
- Publishes encrypted sensor payload to MQTT broker over TLS (port 8883)
- Uses AES-128-GCM via mbedtls for AEAD (replace with Ascon-128 for production)

Notes:
- Edit WIFI_SSID, WIFI_PASS, MQTT_HOST, and CA_CERT below.
- For production: store keys in secure element and use mTLS client certs.
*/

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

extern "C" {
#include "mbedtls/gcm.h"
#include "mbedtls/aes.h"
}

#include <ArduinoJson.h>
#include <base64.h>

// --- Configuration (EDIT) ---
#define WIFI_SSID "your-ssid"
#define WIFI_PASS "your-password"

#define MQTT_HOST "mqtt-broker-host" // e.g., mosquitto
#define MQTT_PORT 8883

#define DEVICE_ID "1_1"

// Demo symmetric key (128-bit) - for production, put in secure element
const uint8_t DEVICE_KEY[16] = { 0x3a,0x7f,0x1b,0x2c,0x99,0xa1,0xb2,0xc3,0xd4,0xe5,0xf6,0x07,0x18,0x29,0x3a,0x4b };

// CA certificate (PEM) for broker verification - replace with your CA
const char CA_CERT[] = "-----BEGIN CERTIFICATE-----\n...your CA PEM...\n-----END CERTIFICATE-----\n";

// Optional: client cert/key for mTLS (recommended in production)
// const char CLIENT_CERT[] = "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n";
// const char CLIENT_KEY[] = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n";

// MQTT topic
String topicPrefix = "hospital/1/ward/1/patient/";

// Globals
WiFiClientSecure wifiClient;
PubSubClient mqttClient(wifiClient);

// Helper: random nonce generation (12 bytes for GCM)
void generate_nonce(uint8_t *nonce, size_t len) {
  for (size_t i = 0; i < len; ++i) nonce[i] = esp_random() & 0xFF;
}

// AEAD Encrypt using AES-128-GCM (mbedTLS)
// Inputs: key(16), plaintext, plaintext_len
// Outputs: ciphertext (allocated by caller), tag(16), nonce(12)
bool aead_encrypt_gcm(const uint8_t *key, const uint8_t *plaintext, size_t plaintext_len,
                      const uint8_t *ad, size_t ad_len,
                      uint8_t *nonce, size_t nonce_len,
                      uint8_t *ciphertext, uint8_t *tag) {
    mbedtls_gcm_context gcm;
    mbedtls_gcm_init(&gcm);
    if (mbedtls_gcm_setkey(&gcm, MBEDTLS_CIPHER_ID_AES, key, 128) != 0) {
        mbedtls_gcm_free(&gcm);
        return false;
    }
    int ret = mbedtls_gcm_crypt_and_tag(&gcm,
        MBEDTLS_GCM_ENCRYPT,
        plaintext_len,
        nonce, nonce_len,
        ad, ad_len,
        plaintext, ciphertext,
        16, tag);
    mbedtls_gcm_free(&gcm);
    return ret == 0;
}

// Base64 helpers (using Arduino base64 library)
String b64enc(const uint8_t *data, size_t len) {
  String out = base64::encode(data, len);
  return out;
}

// Simulated sensor read (replace with real sensor reads)
void read_sensors(JsonDocument &doc) {
  // For demo, random values
  doc["hospital"] = 1;
  doc["dept"] = "A";
  doc["ward"] = 1;
  doc["patient"] = 1;
  doc["heart_rate"] = random(50, 110);
  doc["bp_systolic"] = random(100, 140);
  doc["bp_diastolic"] = random(60, 95);
  doc["respiratory_rate"] = random(10, 20);
  doc["spo2"] = random(90, 100);
  doc["temperature"] = 36.0 + (random(0,100)/100.0);
  doc["timestamp"] = millis();
}

void connectWiFi() {
  Serial.print("Connecting to WiFi ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');
  }
  Serial.println("\nWiFi connected");
}

void connectMQTT() {
  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  while (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT...");
    if (mqttClient.connect(DEVICE_ID)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" retrying in 2s");
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(100);

  connectWiFi();

  // configure TLS
  wifiClient.setCACert(CA_CERT);
  // For mTLS, uncomment and set client cert/key
  // wifiClient.setCertificate(CLIENT_CERT);
  // wifiClient.setPrivateKey(CLIENT_KEY);

  mqttClient.setBufferSize(1024);
  connectMQTT();

  randomSeed(esp_random());
}

void loop() {
  if (!mqttClient.connected()) connectMQTT();
  mqttClient.loop();

  // 1. Read sensors
  StaticJsonDocument<512> doc;
  read_sensors(doc);
  char plaintextBuf[512];
  size_t plen = serializeJson(doc, plaintextBuf);

  // 2. Generate nonce
  uint8_t nonce[12];
  generate_nonce(nonce, sizeof(nonce));

  // 3. AEAD encrypt (AES-128-GCM here)
  uint8_t ciphertext[512];
  uint8_t tag[16];
  bool ok = aead_encrypt_gcm(DEVICE_KEY, (uint8_t*)plaintextBuf, plen,
                             NULL, 0, nonce, sizeof(nonce), ciphertext, tag);
  if (!ok) {
    Serial.println("Encryption failed");
    delay(2000);
    return;
  }

  // 4. Build JSON message: device_id, nonce, ciphertext, tag
  StaticJsonDocument<768> out;
  out["device_id"] = DEVICE_ID;
  out["nonce"] = b64enc(nonce, sizeof(nonce));
  out["ciphertext"] = b64enc(ciphertext, plen);
  out["tag"] = b64enc(tag, sizeof(tag));

  char outBuf[1024];
  size_t olen = serializeJson(out, outBuf);

  // 5. Publish
  String topic = topicPrefix + String(DEVICE_ID);
  boolean res = mqttClient.publish(topic.c_str(), outBuf, olen);
  if (res) Serial.println("Published encrypted payload");
  else Serial.println("Publish failed");

  delay(1000); // publish rate
}
