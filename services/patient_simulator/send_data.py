"""
Patient Simulator with Ascon Encryption & MQTT Publishing
Simulates ESP32/IoT devices sending encrypted patient vitals
"""

import requests
import time
import pandas as pd
from datetime import datetime, timedelta
import os
import random
import numpy as np
import json
import sys
import paho.mqtt.client as mqtt
import ssl

# Add common directory to path for crypto utilities
sys.path.insert(0, '/app/common')

try:
    from crypto_utils import AsconCrypto, KeyManager, encode_payload
    CRYPTO_AVAILABLE = True
except ImportError:
    print("⚠️  WARNING: Crypto utilities not available - running in plain mode")
    CRYPTO_AVAILABLE = False

# Try to import service authentication (lightweight client without Flask deps)
try:
    from auth_client import ServiceAuthClient
    AUTH_AVAILABLE = True
    print("🔐 Service authentication available")
except ImportError:
    print("⚠️  Service authentication not available")
    AUTH_AVAILABLE = False
    ServiceAuthClient = None

# Configuration
ML_MODEL_URL = 'http://ml_service:6000/predict'
MQTT_BROKER = os.getenv('MQTT_BROKER', 'mosquitto')
MQTT_PORT = int(os.getenv('MQTT_PORT_TLS', '8883'))  # TLS port
MQTT_PORT_PLAIN = int(os.getenv('MQTT_PORT_PLAIN', '1883'))  # Fallback
USE_TLS = os.getenv('USE_TLS', 'true').lower() == 'true'
MQTT_TOPIC_TEMPLATE = "hospital/{hospital}/ward/{ward}/patient/{patient_id}"
ENABLE_SERVICE_AUTH = os.getenv('ENABLE_SERVICE_AUTH', 'false').lower() == 'true'

# Initialize authenticated client for ML service
ml_client = None
if AUTH_AVAILABLE and ENABLE_SERVICE_AUTH:
    ml_client = ServiceAuthClient('patient_simulator')
    print("🔐 ML service authentication enabled")

# Initialize key manager
key_manager = None
if CRYPTO_AVAILABLE:
    try:
        key_manager = KeyManager("/app/keys/device_keys.json")
        print("🔑 Key manager initialized")
    except Exception as e:
        print(f"⚠️  Key manager initialization failed: {e}")

# MQTT Client
mqtt_client = None
mqtt_connected = False


def on_mqtt_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        tls_status = "with TLS" if USE_TLS else "plain"
        print(f"✅ Connected to MQTT broker ({tls_status})")
    else:
        mqtt_connected = False
        print(f"❌ MQTT connection failed with code {rc}")


def on_mqtt_disconnect(client, userdata, rc):
    """MQTT disconnect callback"""
    global mqtt_connected
    mqtt_connected = False
    if rc != 0:
        print(f"⚠️  Unexpected MQTT disconnection")


def on_mqtt_publish(client, userdata, mid):
    """MQTT publish confirmation"""
    pass  # Uncomment for debug: print(f"📤 Message {mid} published")


def init_mqtt():
    """Initialize MQTT client with TLS support"""
    global mqtt_client
    
    mqtt_client = mqtt.Client(client_id=f"patient_simulator_{random.randint(1000, 9999)}")
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_disconnect = on_mqtt_disconnect
    mqtt_client.on_publish = on_mqtt_publish
    
    if USE_TLS:
        try:
            # Configure TLS
            mqtt_client.tls_set(
                ca_certs="/app/certs/ca.crt",
                certfile=None,  # Optional client cert
                keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )
            mqtt_client.tls_insecure_set(False)
            print(f"🔐 TLS configured - connecting to {MQTT_BROKER}:{MQTT_PORT}")
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        except Exception as e:
            print(f"❌ TLS connection failed: {e}")
            print(f"⚠️  Falling back to plain MQTT on port {MQTT_PORT_PLAIN}")
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT_PLAIN, 60)
    else:
        print(f"⚠️  Connecting to plain MQTT on port {MQTT_PORT_PLAIN}")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT_PLAIN, 60)
    
    mqtt_client.loop_start()
    
    # Wait for connection
    for i in range(10):
        if mqtt_connected:
            break
        time.sleep(0.5)
    
    if not mqtt_connected:
        print("⚠️  MQTT connection timeout - messages will be queued")


# Read Excel file with multiple sheets
def read_patient_data_from_excel(file_path):
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return []
    
    try:
        df_sheets = pd.read_excel(file_path, sheet_name=None)
    except Exception as e:
        print(f"Error reading the Excel file: {e}")
        return []
    
    return df_sheets


# Generate slightly updated vitals
def generate_updated_patient_data(meta, time_diff_minutes=1):
    heart_rate = meta['heart_rate'] + random.randint(-5, 5)
    bp_systolic = meta['bp_systolic'] + random.randint(-2, 2)
    bp_diastolic = meta['bp_diastolic'] + random.randint(-2, 2)
    respiratory_rate = meta['respiratory_rate'] + random.randint(-1, 1)
    spo2 = meta['spo2'] + random.randint(-1, 1)
    etco2 = meta['etco2'] + random.randint(-1, 1)
    temperature = round(meta['temperature'] + random.uniform(-0.1, 0.1), 1)
    wbc_count = round(meta['wbc_count'] + random.uniform(-0.2, 0.2), 1)
    lactate = round(meta['lactate'] + random.uniform(-0.1, 0.1), 1)
    blood_glucose = meta['blood_glucose'] + random.randint(-5, 5)

    timestamp = (datetime.utcnow() + timedelta(minutes=time_diff_minutes)).isoformat()

    return {
        "hospital": meta['hospital'],
        "dept": meta['dept'],
        "ward": meta['ward'],
        "patient": meta['patient'],
        "heart_rate": heart_rate,
        "bp_systolic": bp_systolic,
        "bp_diastolic": bp_diastolic,
        "respiratory_rate": respiratory_rate,
        "spo2": spo2,
        "etco2": etco2,
        "fio2": meta['fio2'],
        "temperature": temperature,
        "wbc_count": wbc_count,
        "lactate": lactate,
        "blood_glucose": blood_glucose,
        "timestamp": timestamp,
        "ecg_signal": "dummy_waveform_data"
    }


# Get anomaly score from ML service
def get_anomaly_score(data):
    """Get anomaly score from ML service with optional authentication"""
    try:
        # Use authenticated client if available
        if ml_client:
            response = ml_client.post(ML_MODEL_URL, json=data, timeout=3)
        else:
            response = requests.post(ML_MODEL_URL, json=data, timeout=3)
            
        if response.status_code == 200:
            response_data = response.json()
            
            if "normalized_score" in response_data:
                anomaly_score = float(response_data.get("normalized_score", 0.0))
            elif "anomaly_score" in response_data:
                anomaly_score = float(response_data.get("anomaly_score", 0.0))
            else:
                anomaly_score = 0.0
                
            return anomaly_score
        else:
            print(f"ML service failed with code {response.status_code}")
            return 0.0
    except Exception as e:
        print(f"Error contacting ML service: {e}")
        return 0.0


def publish_encrypted_vitals(patient_data, anomaly_score):
    """
    Encrypt patient vitals and publish via MQTT
    This simulates ESP32 device behavior
    """
    if not mqtt_connected:
        print("⚠️  MQTT not connected - skipping publish")
        return False
    
    # Generate device ID (unique per patient)
    device_id = f"{patient_data['hospital']}_{patient_data['patient']}"
    
    # Prepare vitals payload
    vitals_payload = {
        "patient_id": patient_data['patient'],
        "heart_rate": patient_data['heart_rate'],
        "spo2": patient_data['spo2'],
        "bp_systolic": patient_data['bp_systolic'],
        "bp_diastolic": patient_data['bp_diastolic'],
        "respiratory_rate": patient_data['respiratory_rate'],
        "etco2": patient_data['etco2'],
        "fio2": patient_data['fio2'],
        "temperature": patient_data['temperature'],
        "wbc_count": patient_data['wbc_count'],
        "lactate": patient_data['lactate'],
        "blood_glucose": patient_data['blood_glucose'],
        "timestamp": patient_data['timestamp'],
        "anomaly_score": anomaly_score
    }
    
    # Encrypt if crypto available
    if CRYPTO_AVAILABLE and key_manager:
        try:
            # Get device-specific key
            device_key = key_manager.get_device_key(device_id)
            crypto = AsconCrypto(device_key)
            
            # Encrypt payload
            ciphertext, nonce, encrypt_time_ms = crypto.encrypt(vitals_payload)
            
            # Encode for transmission
            encoded = encode_payload(ciphertext, nonce)
            
            # Package metadata
            mqtt_payload = {
                "device_id": device_id,
                "hospital": patient_data['hospital'],
                "ward": patient_data['ward'],
                "encrypted": True,
                "ciphertext": encoded['ciphertext'],
                "nonce": encoded['nonce'],
                "timestamp": patient_data['timestamp']
            }
            
            encryption_status = "🔐 encrypted"
        except Exception as e:
            print(f"⚠️  Encryption failed: {e} - sending plain")
            mqtt_payload = {
                "device_id": device_id,
                "hospital": patient_data['hospital'],
                "ward": patient_data['ward'],
                "encrypted": False,
                "vitals": vitals_payload
            }
            encryption_status = "⚠️  plain"
    else:
        # Fallback to plain transmission
        mqtt_payload = {
            "device_id": device_id,
            "hospital": patient_data['hospital'],
            "ward": patient_data['ward'],
            "encrypted": False,
            "vitals": vitals_payload
        }
        encryption_status = "⚠️  plain"
    
    # Construct MQTT topic
    topic = MQTT_TOPIC_TEMPLATE.format(
        hospital=patient_data['hospital'],
        ward=patient_data['ward'],
        patient_id=patient_data['patient']
    )
    
    # Publish to MQTT
    try:
        result = mqtt_client.publish(topic, json.dumps(mqtt_payload), qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"📤 {encryption_status} | {device_id} | Score: {anomaly_score:.2f} | Topic: {topic}")
            return True
        else:
            print(f"❌ Publish failed: {result.rc}")
            return False
    except Exception as e:
        print(f"❌ MQTT publish error: {e}")
        return False


# Simulate traffic
def simulate_traffic(file_path):
    sheets = read_patient_data_from_excel(file_path)
    if not sheets:
        return

    sheet_names = list(sheets.keys())
    sheet_data = {name: sheets[name].to_dict(orient='records') for name in sheet_names}

    row_index = 0
    time_diff_minutes = 1

    print(f"\n{'='*80}")
    print(f"🚀 Starting Patient Simulator")
    print(f"{'='*80}")
    print(f"Sheets loaded: {len(sheet_names)}")
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Encryption: {'✅ Enabled' if CRYPTO_AVAILABLE else '❌ Disabled'}")
    print(f"TLS: {'✅ Enabled' if USE_TLS else '❌ Disabled'}")
    print(f"{'='*80}\n")

    # Initialize MQTT
    init_mqtt()
    
    # Give MQTT time to stabilize
    time.sleep(2)

    while True:
        active = False

        for sheet_name in sheet_names:
            rows = sheet_data[sheet_name]
            if row_index < len(rows):
                active = True
                patient_meta = rows[row_index]

                # Generate updated vitals
                data = generate_updated_patient_data(patient_meta, time_diff_minutes)

                # Get anomaly score from ML service
                anomaly_score = get_anomaly_score(data)

                # Publish encrypted data via MQTT
                publish_encrypted_vitals(data, anomaly_score)

                time.sleep(1)
                time_diff_minutes += 1

        if not active:
            print("\n✅ All rows processed.")
            break

        row_index += 1

    # Cleanup
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("🔌 Disconnected from MQTT broker")


# Main
if __name__ == '__main__':
    file_path = "/app/data/patients_data.xlsx"
    
    # Startup delay to let other services initialize
    startup_delay = int(os.getenv('STARTUP_DELAY', '5'))
    if startup_delay > 0:
        print(f"⏳ Waiting {startup_delay} seconds for services to start...")
        time.sleep(startup_delay)
    
    try:
        simulate_traffic(file_path)
    except KeyboardInterrupt:
        print("\n⚠️  Simulator stopped by user")
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
