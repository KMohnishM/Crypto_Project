ESP32 Firmware Demo

This folder contains a runnable Arduino sketch (`esp32_aead_mqtt.ino`) that demonstrates:
- Connecting an ESP32 to Wi‑Fi
- Establishing MQTT over TLS to a broker (port 8883)
- Encrypting a small sensor payload using AES‑128‑GCM (AEAD)
- Publishing a JSON message with `device_id`, `nonce`, `ciphertext`, and `tag` (all base64)

Notes:
- This demo uses AES‑GCM because the ESP32 toolchain provides `mbedtls` out of the box for a runnable example. For production replace AES‑GCM calls with an Ascon‑128 AEAD implementation (drop-in functions `aead_encrypt()` / `aead_decrypt()` are recommended).
- For secure key storage in production, use a secure element (ATECC608A) or ESP32 secure flash + secure boot. Do NOT hardcode keys in firmware.

Build / flash steps (Arduino IDE / PlatformIO)
1. Install "ESP32 by Espressif Systems" board in Arduino IDE.
2. Open `esp32_aead_mqtt.ino`.
3. Edit Wi‑Fi and MQTT broker settings at the top of the file.
4. Provide CA certificate (and client cert/key if using mTLS) in PEM format and update file paths.
5. Compile & upload to ESP32.

Replace AEAD implementation with Ascon for compliance with the server if required. See the project docs for provisioning and secure-element integration.