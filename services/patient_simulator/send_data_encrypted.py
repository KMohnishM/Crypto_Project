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
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add common directory to path for crypto utilities
sys.path.insert(0, '/app/common')

try:
    from crypto_utils import AsconCrypto, KeyManager, encode_payload
    CRYPTO_AVAILABLE = True
except ImportError:
    print("WARNING: Crypto utilities not available - running in plain mode")
    CRYPTO_AVAILABLE = False

# Try to import service authentication
try:
    from service_auth import ServiceAuthClient
    AUTH_AVAILABLE = True
    print("Service authentication available")
except ImportError:
    print("WARNING: Service authentication not available")
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
    print("ML service authentication enabled")

# Initialize key manager
key_manager = None
if CRYPTO_AVAILABLE:
    try:
        key_manager = KeyManager("/app/keys/device_keys.json")
        print("Key manager initialized")
    except Exception as e:
        print(f"WARNING: Key manager initialization failed: {e}")

# MQTT Client
mqtt_client = None
mqtt_connected = False


def on_mqtt_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        tls_status = "with TLS" if USE_TLS else "plain"
        print(f"Connected to MQTT broker ({tls_status})")
    else:
        mqtt_connected = False
        print(f"ERROR: MQTT connection failed with code {rc}")


def on_mqtt_disconnect(client, userdata, rc):
    """MQTT disconnect callback"""
    global mqtt_connected
    mqtt_connected = False
    if rc != 0:
        print(f"WARNING: Unexpected MQTT disconnection")


def on_mqtt_publish(client, userdata, mid):
    """MQTT publish confirmation"""
    pass  # Uncomment for debug: print(f"Message {mid} published")


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
            print(f"TLS configured - connecting to {MQTT_BROKER}:{MQTT_PORT}")
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        except Exception as e:
            print(f"ERROR: TLS connection failed: {e}")
            print(f"WARNING: Falling back to plain MQTT on port {MQTT_PORT_PLAIN}")
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT_PLAIN, 60)
    else:
        print(f"WARNING: Connecting to plain MQTT on port {MQTT_PORT_PLAIN}")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT_PLAIN, 60)
    
    mqtt_client.loop_start()
    
    # Wait for connection
    for i in range(10):
        if mqtt_connected:
            break
        time.sleep(0.5)
    
    if not mqtt_connected:
        print("WARNING: MQTT connection timeout - messages will be queued")


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


# DEPRECATED: ML service is now called by backend
# This function is kept for backward compatibility but not used
def get_anomaly_score(data):
    """
    DEPRECATED: Backend now calls ML service after decryption
    Keeping this function for backward compatibility
    """
    print("WARNING: ML call skipped - Backend will handle ML inference")
    return 0.0, 0.0


def publish_encrypted_vitals(patient_data):
    """
    Encrypt patient vitals and publish via MQTT
    This simulates ESP32 device behavior with latency tracking
    Backend will call ML service to compute anomaly score
    """
    if not mqtt_connected:
        print("WARNING: MQTT not connected - skipping publish")
        return False
    
    total_start = time.time()
    
    # Generate device ID (unique per patient)
    device_id = f"{patient_data['hospital']}_{patient_data['patient']}"
    
    # Prepare vitals payload (NO anomaly_score - backend will compute)
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
        "timestamp": patient_data['timestamp']
    }
    
    encryption_time_ms = 0
    
    # Encrypt if crypto available
    if CRYPTO_AVAILABLE and key_manager:
        try:
            # Get device-specific key
            device_key = key_manager.get_device_key(device_id)
            crypto = AsconCrypto(device_key)
            
            # Encrypt payload - NOW RETURNS TIMING
            encrypt_start = time.time()
            ciphertext, nonce, encryption_time_ms = crypto.encrypt(vitals_payload)
            
            # Encode for transmission
            encoded = encode_payload(ciphertext, nonce)
            
            # Package metadata with latency info
            mqtt_payload = {
                "device_id": device_id,
                "hospital": patient_data['hospital'],
                "ward": patient_data['ward'],
                "encrypted": True,
                "ciphertext": encoded['ciphertext'],
                "nonce": encoded['nonce'],
                "timestamp": patient_data['timestamp'],
                "timestamp_us": int(time.time() * 1_000_000),  # For end-to-end latency
                "latency_encrypt_ms": round(encryption_time_ms, 3)
            }
            
            encryption_status = "encrypted"
        except Exception as e:
            print(f"WARNING: Encryption failed: {e} - sending plain")
            mqtt_payload = {
                "device_id": device_id,
                "hospital": patient_data['hospital'],
                "ward": patient_data['ward'],
                "encrypted": False,
                "vitals": vitals_payload
            }
            encryption_status = "WARNING: plain"
    else:
        # Fallback to plain transmission
        mqtt_payload = {
            "device_id": device_id,
            "hospital": patient_data['hospital'],
            "ward": patient_data['ward'],
            "encrypted": False,
            "vitals": vitals_payload
        }
        encryption_status = "WARNING: plain"
    
    # Construct MQTT topic
    topic = MQTT_TOPIC_TEMPLATE.format(
        hospital=patient_data['hospital'],
        ward=patient_data['ward'],
        patient_id=patient_data['patient']
    )
    
    # Publish to MQTT - MEASURE PUBLISH TIME
    publish_start = time.time()
    try:
        result = mqtt_client.publish(topic, json.dumps(mqtt_payload), qos=1)
        publish_time_ms = (time.time() - publish_start) * 1000
        
        total_time_ms = (time.time() - total_start) * 1000
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"{encryption_status} | {device_id}")
            print(f"TIME: Encrypt: {encryption_time_ms:.2f}ms | "
                  f"Publish: {publish_time_ms:.2f}ms | Total: {total_time_ms:.2f}ms")
            return True
        else:
            print(f"ERROR: Publish failed: {result.rc}")
            return False
    except Exception as e:
        publish_time_ms = (time.time() - publish_start) * 1000
        print(f"ERROR: MQTT publish error: {e} (took {publish_time_ms:.2f}ms)")
        return False


# Simulate traffic with parallel processing
def simulate_traffic(file_path):
    sheets = read_patient_data_from_excel(file_path)
    if not sheets:
        return

    sheet_names = list(sheets.keys())
    sheet_data = {name: sheets[name].to_dict(orient='records') for name in sheet_names}

    row_index = 0
    time_diff_minutes = 1

    print(f"\n{'='*80}")
    print(f"Starting Patient Simulator (Parallel Mode)")
    print(f"{'='*80}")
    print(f"Sheets loaded: {len(sheet_names)}")
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Encryption: {'Enabled' if CRYPTO_AVAILABLE else 'Disabled'}")
    print(f"TLS: {'Enabled' if USE_TLS else 'Disabled'}")
    print(f"Parallel Processing: Enabled (up to {len(sheet_names)} concurrent patients)")
    print(f"{'='*80}\n")

    # Initialize MQTT
    init_mqtt()
    
    # Give MQTT time to stabilize
    time.sleep(2)

    # Helper function to process one patient
    def process_patient(sheet_name, patient_meta, time_diff):
        """Process a single patient in parallel"""
        try:
            # Generate updated vitals
            data = generate_updated_patient_data(patient_meta, time_diff)
            
            # Publish encrypted data via MQTT
            # Backend will call ML service after decryption
            success = publish_encrypted_vitals(data)
            return (sheet_name, success)
        except Exception as e:
            print(f"ERROR: Error processing patient {sheet_name}: {e}")
            return (sheet_name, False)

    while True:
        active = False
        batch_start = time.time()
        
        # Collect all patients for this row_index
        patient_tasks = []
        for sheet_name in sheet_names:
            rows = sheet_data[sheet_name]
            if row_index < len(rows):
                active = True
                patient_meta = rows[row_index]
                patient_tasks.append((sheet_name, patient_meta, time_diff_minutes))
        
        if not active:
            print("\nAll rows processed.")
            break
        
        # Process all patients in parallel using ThreadPoolExecutor
        max_workers = min(len(patient_tasks), 15)  # Max 15 concurrent threads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(process_patient, sheet, meta, tdiff): sheet 
                for sheet, meta, tdiff in patient_tasks
            }
            
            # Wait for all to complete
            success_count = 0
            for future in as_completed(futures):
                sheet_name = futures[future]
                try:
                    sheet, success = future.result()
                    if success:
                        success_count += 1
                except Exception as e:
                    print(f"ERROR: Exception for {sheet_name}: {e}")
        
        batch_time_ms = (time.time() - batch_start) * 1000
        print(f"Batch complete: {success_count}/{len(patient_tasks)} patients | "
              f"Total time: {batch_time_ms:.2f}ms | "
              f"Avg per patient: {batch_time_ms/len(patient_tasks):.2f}ms")
        
        # Wait before next batch (simulate 1-second intervals)
        time.sleep(1)
        time_diff_minutes += 1
        row_index += 1

    # Cleanup
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("Disconnected from MQTT broker")


# Main
if __name__ == '__main__':
    file_path = "/app/data/patients_data.xlsx"
    
    # Startup delay to let other services initialize
    startup_delay = int(os.getenv('STARTUP_DELAY', '5'))
    if startup_delay > 0:
        print(f"Waiting {startup_delay} seconds for services to start...")
        time.sleep(startup_delay)
    
    try:
        simulate_traffic(file_path)
    except KeyboardInterrupt:
        print("\nWARNING: Simulator stopped by user")
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
    except Exception as e:
        print(f"\nERROR: Fatal error: {e}")
        import traceback
        traceback.print_exc()
