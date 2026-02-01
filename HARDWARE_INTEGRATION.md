# Hardware Integration Guide

## Overview

This guide explains how to integrate real hardware sensors with the Healthcare IoT Monitoring System. The system is designed to work with various types of medical sensors and IoT devices.

## Supported Hardware Types

### 1. Microcontroller-Based Sensors
- **Arduino** (Uno, Mega, Nano)
- **ESP32/ESP8266** (WiFi-enabled)
- **Raspberry Pi** with sensor modules

### 2. Medical Sensors
- **Heart Rate Sensors**: MAX30102, Pulse Sensor
- **SpO2 Sensors**: MAX30102, MAX30100
- **Temperature Sensors**: DS18B20, MLX90614 (contactless)
- **Blood Pressure Sensors**: Omron-compatible modules
- **ECG Sensors**: AD8232 ECG module

### 3. Communication Protocols
- **Serial/USB**: Direct connection via COM ports
- **Bluetooth/BLE**: Wireless sensor connectivity
- **MQTT**: Network-based sensor communication
- **HTTP/REST**: Direct API integration

---

## Integration Methods

### Method 1: Replace Patient Simulator (Recommended)

Modify the patient simulator service to read from real hardware instead of generating random data.

**Steps:**
1. Connect your hardware sensors
2. Modify `services/patient_simulator/send_data.py`
3. Replace random data generation with sensor readings
4. Keep the same data format for main_host compatibility

**Example - Reading from Serial (Arduino):**
```python
import serial
import requests
import json
import time

# Configure serial port
SERIAL_PORT = 'COM3'  # Change to your port (e.g., /dev/ttyUSB0 on Linux)
BAUD_RATE = 9600
MAIN_HOST_URL = 'http://localhost:8000/track'

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

while True:
    try:
        # Read sensor data from Arduino
        line = ser.readline().decode('utf-8').strip()
        
        if line:
            # Parse sensor data (assuming JSON format from Arduino)
            sensor_data = json.loads(line)
            
            # Format for main_host
            payload = {
                "hospital": "hospital_1",
                "dept": "icu",
                "ward": "ward_1",
                "patient": "patient_1",
                "heart_rate": sensor_data.get("hr", 0),
                "spo2": sensor_data.get("spo2", 0),
                "temperature": sensor_data.get("temp", 0),
                "bp_systolic": sensor_data.get("bp_sys", 0),
                "bp_diastolic": sensor_data.get("bp_dia", 0),
                "respiratory_rate": sensor_data.get("rr", 0)
            }
            
            # Send to main_host
            response = requests.post(MAIN_HOST_URL, json=payload)
            print(f"Sent: {payload}")
            print(f"Response: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
        
    time.sleep(5)  # Send data every 5 seconds
```

**Arduino Example Code (for MAX30102 sensor):**
```cpp
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"

MAX30105 particleSensor;

void setup() {
  Serial.begin(9600);
  
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("MAX30105 not found");
    while (1);
  }
  
  particleSensor.setup();
}

void loop() {
  long irValue = particleSensor.getIR();
  
  if (checkForBeat(irValue)) {
    long delta = millis() - lastBeat;
    lastBeat = millis();
    
    float beatsPerMinute = 60 / (delta / 1000.0);
    int heartRate = (int)beatsPerMinute;
    int spo2 = particleSensor.getSPO2();
    
    // Send JSON to Python
    Serial.print("{\"hr\":");
    Serial.print(heartRate);
    Serial.print(",\"spo2\":");
    Serial.print(spo2);
    Serial.print(",\"temp\":");
    Serial.print(36.5);  // Add temperature sensor reading
    Serial.println("}");
  }
  
  delay(5000);
}
```

---

### Method 2: Create Dedicated Hardware Service

Create a new service that runs outside Docker to access hardware directly.

**Steps:**
1. Create `services/hardware_interface/` directory
2. Install Python and required libraries on host machine
3. Run the hardware interface script directly (not in Docker)
4. Send data to main_host running in Docker

**File Structure:**
```
services/hardware_interface/
├── hardware_reader.py
├── requirements.txt
├── config.yaml
└── README.md
```

**Example `hardware_reader.py`:**
```python
import serial
import requests
import time
import yaml

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Setup serial connection
ser = serial.Serial(
    port=config['serial']['port'],
    baudrate=config['serial']['baudrate'],
    timeout=1
)

MAIN_HOST_URL = config['api']['main_host_url']

def read_and_send():
    while True:
        try:
            data = ser.readline().decode('utf-8').strip()
            if data:
                # Process and send data
                send_to_main_host(data)
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(config['api']['interval'])

if __name__ == '__main__':
    read_and_send()
```

---

### Method 3: MQTT Integration

Use MQTT for wireless sensor communication.

**Setup Mosquitto MQTT Broker:**
```bash
docker run -d -p 1883:1883 -p 9001:9001 --name mqtt eclipse-mosquitto
```

**ESP32 Example (Publishing to MQTT):**
```cpp
#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "your_wifi";
const char* password = "your_password";
const char* mqtt_server = "192.168.1.100";

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  WiFi.begin(ssid, password);
  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  
  // Read sensor
  int heartRate = readHeartRate();
  int spo2 = readSpO2();
  
  // Publish to MQTT
  String payload = "{\"hr\":" + String(heartRate) + 
                   ",\"spo2\":" + String(spo2) + "}";
  client.publish("hospital/patient1/vitals", payload.c_str());
  
  delay(5000);
}
```

---

## Data Format

The main_host expects this JSON structure:

```json
{
  "hospital": "hospital_1",
  "dept": "department_1",
  "ward": "ward_1",
  "patient": "patient_1",
  "heart_rate": 75,
  "bp_systolic": 120,
  "bp_diastolic": 80,
  "respiratory_rate": 16,
  "spo2": 98,
  "etco2": 38,
  "fio2": 21,
  "temperature": 36.5,
  "wbc_count": 7500,
  "lactate": 1.2,
  "blood_glucose": 95
}
```

**Required Fields:** hospital, dept, ward, patient
**Optional Fields:** All vital sign metrics (use only the sensors you have)

---

## Wiring Examples

### MAX30102 (Heart Rate & SpO2)
```
MAX30102 -> Arduino
VIN      -> 3.3V
GND      -> GND
SDA      -> A4 (Uno) / SDA (Mega)
SCL      -> A5 (Uno) / SCL (Mega)
```

### DS18B20 (Temperature)
```
DS18B20 -> Arduino
VDD     -> 5V
GND     -> GND
DATA    -> D2 (with 4.7kΩ pull-up resistor to VCC)
```

### AD8232 (ECG)
```
AD8232  -> Arduino
GND     -> GND
3.3V    -> 3.3V
OUTPUT  -> A0
LO+     -> D10
LO-     -> D11
```

---

## Testing Hardware Integration

1. **Test sensor readings locally:**
   ```bash
   python services/hardware_interface/hardware_reader.py
   ```

2. **Verify data in Prometheus:**
   - Open http://localhost:9090
   - Query: `heart_rate_bpm`
   - Should show real sensor data

3. **Check Grafana dashboard:**
   - Open http://localhost:3001
   - View real-time sensor visualizations

4. **Monitor alerts:**
   - Check http://localhost:9093
   - Alerts should trigger based on real sensor thresholds

---

## Troubleshooting

### Serial Port Issues
- **Windows**: Check Device Manager for COM port number
- **Linux**: Use `ls /dev/tty*` and add user to dialout group
  ```bash
  sudo usermod -a -G dialout $USER
  ```
- **Permission denied**: Run with sudo or fix permissions

### Sensor Not Detected
- Check wiring connections
- Verify power supply (3.3V vs 5V)
- Test sensor with example code from manufacturer

### Data Not Appearing
- Verify main_host is running: `docker ps`
- Check logs: `docker logs main_host`
- Test API manually:
  ```bash
  curl -X POST http://localhost:8000/track \\
    -H "Content-Type: application/json" \\
    -d '{"hospital":"h1","dept":"d1","ward":"w1","patient":"p1","heart_rate":75}'
  ```

---

## Safety & Medical Device Compliance

⚠️ **Important**: This system is for educational and development purposes only.

- Do **NOT** use for actual patient care without proper medical device certification
- Follow local regulations for medical device development
- Consider: FDA (US), CE Mark (EU), PMDA (Japan), etc.
- Implement proper data encryption and HIPAA compliance for production use
- Always have human oversight and redundant monitoring systems

---

## Next Steps

1. **Start with simulated data** to understand the data flow
2. **Connect one sensor** (e.g., MAX30102 for heart rate)
3. **Verify data appears** in Prometheus and Grafana
4. **Add more sensors** incrementally
5. **Implement error handling** and sensor failure detection
6. **Add calibration** routines for accurate readings
7. **Consider multi-patient setups** with multiple hardware units

---

## Additional Resources

- **Arduino Libraries**: 
  - MAX30105: https://github.com/sparkfun/SparkFun_MAX3010x_Sensor_Library
  - OneWire (DS18B20): https://github.com/PaulStoffregen/OneWire
  
- **ESP32 Examples**:
  - WiFi: https://github.com/espressif/arduino-esp32
  - MQTT: https://github.com/knolleary/pubsubclient

- **Raspberry Pi**:
  - GPIO: https://gpiozero.readthedocs.io/
  - Serial: https://pyserial.readthedocs.io/

---

## Support

For hardware integration questions:
1. Check sensor datasheets
2. Review example code from sensor manufacturers
3. Test sensors independently before integration
4. Open an issue on GitHub with specific hardware details

Good luck with your hardware integration! 🚀🏥
