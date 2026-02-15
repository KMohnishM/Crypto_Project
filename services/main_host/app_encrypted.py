"""
Main Host Backend with MQTT Subscriber & Ascon Decryption
Receives encrypted patient vitals, decrypts, and exposes metrics
"""

from flask import Flask, request, jsonify
from prometheus_client import Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
import logging
import json
from collections import defaultdict
import sys
import os
import paho.mqtt.client as mqtt
import ssl
import threading
import time
import requests
from cryptography.fernet import Fernet
import base64
import hashlib

# Add common directory to path for crypto utilities
sys.path.insert(0, '/app/common')

try:
    from crypto_utils import AsconCrypto, KeyManager, decode_payload
    CRYPTO_AVAILABLE = True
except ImportError:
    print("⚠️  WARNING: Crypto utilities not available")
    CRYPTO_AVAILABLE = False

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', 'mosquitto')
MQTT_PORT = int(os.getenv('MQTT_PORT_TLS', '8883'))
MQTT_PORT_PLAIN = int(os.getenv('MQTT_PORT_PLAIN', '1883'))
USE_TLS = os.getenv('USE_TLS', 'true').lower() == 'true'

# ML Service Configuration
ML_SERVICE_URL = os.getenv('ML_SERVICE_URL', 'http://ml_service:6000/predict')

# Database API Configuration
WEB_DASHBOARD_URL = os.getenv('WEB_DASHBOARD_URL', 'http://web_dashboard:5000')
DB_ENCRYPTION_KEY = os.getenv('DB_ENCRYPTION_KEY', 'dev-db-key-change-in-production')

# Initialize key manager
key_manager = None
if CRYPTO_AVAILABLE:
    try:
        key_manager = KeyManager("/app/keys/backend_keys.json")
        print("🔑 Backend key manager initialized")
    except Exception as e:
        print(f"⚠️  Key manager initialization failed: {e}")

# Define Gauges (current value metrics)
metrics = {
    'heart_rate': Gauge('heart_rate_bpm', 'Heart Rate (BPM)', ['hospital', 'department', 'ward', 'patient']),
    'bp_systolic': Gauge('bp_systolic', 'BP Systolic', ['hospital', 'department', 'ward', 'patient']),
    'bp_diastolic': Gauge('bp_diastolic', 'BP Diastolic', ['hospital', 'department', 'ward', 'patient']),
    'respiratory_rate': Gauge('respiratory_rate', 'Respiratory Rate', ['hospital', 'department', 'ward', 'patient']),
    'spo2': Gauge('spo2_percent', 'SpO2 (%)', ['hospital', 'department', 'ward', 'patient']),
    'etco2': Gauge('etco2', 'EtCO2', ['hospital', 'department', 'ward', 'patient']),
    'fio2': Gauge('fio2_percent', 'FiO2 (%)', ['hospital', 'department', 'ward', 'patient']),
    'temperature': Gauge('temperature_celsius', 'Temperature (°C)', ['hospital', 'department', 'ward', 'patient']),
    'wbc_count': Gauge('wbc_count', 'WBC Count', ['hospital', 'department', 'ward', 'patient']),
    'lactate': Gauge('lactate', 'Lactate (mmol/L)', ['hospital', 'department', 'ward', 'patient']),
    'blood_glucose': Gauge('blood_glucose', 'Blood Glucose (mg/dL)', ['hospital', 'department', 'ward', 'patient']),
    'anomaly_score': Gauge('anomaly_score', 'Anomaly Score', ['hospital', 'department', 'ward', 'patient']),
}

# Additional security metrics
security_metrics = {
    'decryption_success': Gauge('decryption_success_total', 'Successful decryptions', ['device_id']),
    'decryption_failure': Gauge('decryption_failure_total', 'Failed decryptions', ['device_id', 'reason']),
    'encrypted_messages': Gauge('encrypted_messages_total', 'Total encrypted messages received'),
    'plain_messages': Gauge('plain_messages_total', 'Total plain messages received'),
}

# Latency metrics (Histograms for distribution tracking)
latency_metrics = {
    'mqtt_receive': Histogram('mqtt_receive_latency_ms', 'MQTT message receive latency (ms)', ['device_id'],
                              buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000]),
    'decryption': Histogram('decryption_latency_ms', 'Decryption latency (ms)', ['device_id'],
                           buckets=[0.1, 0.5, 1, 2, 5, 10, 25, 50, 100]),
    'processing': Histogram('processing_latency_ms', 'Data processing latency (ms)', ['device_id'],
                           buckets=[0.1, 0.5, 1, 2, 5, 10, 25, 50]),
    'end_to_end': Histogram('end_to_end_latency_ms', 'End-to-end latency from device to backend (ms)', ['device_id'],
                           buckets=[10, 50, 100, 250, 500, 1000, 2500, 5000, 10000]),
}

# Track current latency values for dashboard
current_latency = defaultdict(lambda: {'decryption': 0, 'processing': 0, 'end_to_end': 0})

# In-memory data store for the dashboard
patient_data_store = defaultdict(list)

# MQTT connection status
mqtt_connected = False

# Initialize AES encryption for database
def get_aes_cipher():
    """Generate AES cipher from encryption key"""
    # Use SHA-256 hash of key to get 32-byte key for AES
    key = hashlib.sha256(DB_ENCRYPTION_KEY.encode()).digest()
    # Base64 encode for Fernet (requires URL-safe base64)
    key_b64 = base64.urlsafe_b64encode(key)
    return Fernet(key_b64)


def call_ml_service(vitals_data):
    """
    Call ML service to get anomaly score
    This is now done by backend (not simulator)
    """
    ml_start_time = time.time()
    
    try:
        # Prepare payload for ML service
        ml_payload = {
            'heart_rate': vitals_data.get('heart_rate', 75),
            'bp_systolic': vitals_data.get('bp_systolic', 120),
            'bp_diastolic': vitals_data.get('bp_diastolic', 80),
            'respiratory_rate': vitals_data.get('respiratory_rate', 16),
            'spo2': vitals_data.get('spo2', 95),
            'etco2': vitals_data.get('etco2', 35),
            'fio2': vitals_data.get('fio2', 21),
            'temperature': vitals_data.get('temperature', 37.0),
            'wbc_count': vitals_data.get('wbc_count', 7.0),
            'lactate': vitals_data.get('lactate', 1.2),
            'blood_glucose': vitals_data.get('blood_glucose', 95)
        }
        
        response = requests.post(ML_SERVICE_URL, json=ml_payload, timeout=3)
        ml_latency_ms = (time.time() - ml_start_time) * 1000
        
        if response.status_code == 200:
            result = response.json()
            anomaly_score = result.get('normalized_score', 0.0)
            logging.info(f"🧠 ML inference: {ml_latency_ms:.2f}ms, Score: {anomaly_score:.3f}")
            return anomaly_score, ml_latency_ms
        else:
            logging.warning(f"⚠️ ML service returned {response.status_code}")
            return 0.0, ml_latency_ms
            
    except Exception as e:
        ml_latency_ms = (time.time() - ml_start_time) * 1000
        logging.error(f"❌ ML service error: {e}")
        return 0.0, ml_latency_ms


def save_vitals_to_database(vitals, hospital, dept, ward, patient_id):
    """
    Save encrypted vitals to database via Web Dashboard API
    Uses AES-256 encryption for data at rest
    """
    try:
        # Initialize cipher
        cipher = get_aes_cipher()
        
        # Prepare complete vitals record
        vitals_record = {
            'patient_id': patient_id,
            'hospital': hospital,
            'department': dept,
            'ward': ward,
            'heart_rate': vitals.get('heart_rate'),
            'spo2': vitals.get('spo2'),
            'bp_systolic': vitals.get('bp_systolic'),
            'bp_diastolic': vitals.get('bp_diastolic'),
            'respiratory_rate': vitals.get('respiratory_rate'),
            'temperature': vitals.get('temperature'),
            'etco2': vitals.get('etco2'),
            'fio2': vitals.get('fio2', 21),
            'wbc_count': vitals.get('wbc_count'),
            'lactate': vitals.get('lactate'),
            'blood_glucose': vitals.get('blood_glucose'),
            'anomaly_score': vitals.get('anomaly_score', 0.0),
            'timestamp': vitals.get('timestamp', time.time())
        }
        
        # Encrypt the vitals data
        vitals_json = json.dumps(vitals_record).encode()
        encrypted_vitals = cipher.encrypt(vitals_json)
        encrypted_b64 = base64.b64encode(encrypted_vitals).decode()
        
        # Send to Web Dashboard API
        api_url = f"{WEB_DASHBOARD_URL}/api/vitals/save"
        payload = {
            'encrypted_data': encrypted_b64,
            'patient_id': patient_id
        }
        
        response = requests.post(api_url, json=payload, timeout=2)
        
        if response.status_code == 200:
            logging.debug(f"💾 Saved encrypted vitals to DB: Patient {patient_id}")
            return True
        else:
            logging.warning(f"⚠️ DB save failed: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Database save error: {e}")
        return False


def process_patient_data(vitals, hospital, dept, ward, patient_id):
    """
    Process decrypted patient vitals and update metrics
    
    Args:
        vitals: Dictionary of patient vital signs
        hospital: Hospital identifier
        dept: Department identifier
        ward: Ward identifier
        patient_id: Patient identifier
    """
    labels = dict(hospital=hospital, department=dept, ward=ward, patient=patient_id)

    # Update Prometheus metrics
    for key, gauge in metrics.items():
        if key in vitals:
            try:
                gauge.labels(**labels).set(vitals[key])
            except Exception as e:
                logging.warning(f"Failed to set metric {key}: {e}")
    
    # Store the data for the dashboard
    patient_key = f"{hospital}|{dept}|{ward}|{patient_id}"
    
    # Add metadata
    vitals['hospital'] = hospital
    vitals['dept'] = dept
    vitals['ward'] = ward
    vitals['patient'] = patient_id
    
    patient_data_store[patient_key].append(vitals)
    
    # Keep only the latest 100 data points per patient
    if len(patient_data_store[patient_key]) > 100:
        patient_data_store[patient_key] = patient_data_store[patient_key][-100:]


def on_mqtt_message(client, userdata, msg):
    """
    Handle incoming MQTT messages
    Decrypt if encrypted, process vitals
    """
    mqtt_receive_time = time.time()
    
    try:
        # Parse MQTT payload
        mqtt_payload = json.loads(msg.payload.decode('utf-8'))
        device_id = mqtt_payload.get('device_id', 'unknown')
        hospital = mqtt_payload.get('hospital', 'unknown')
        ward = mqtt_payload.get('ward', 'unknown')
        is_encrypted = mqtt_payload.get('encrypted', False)
        
        # Calculate network latency if timestamp is available
        device_timestamp_us = mqtt_payload.get('timestamp_us', 0)
        network_latency_ms = 0
        if device_timestamp_us > 0:
            # Convert device timestamp from microseconds to seconds
            device_time = device_timestamp_us / 1_000_000
            network_latency_ms = (mqtt_receive_time - device_time) * 1000
            if network_latency_ms > 0:  # Only record positive latencies
                latency_metrics['mqtt_receive'].labels(device_id=device_id).observe(network_latency_ms)
        
        # Extract patient ID from topic
        # Topic format: hospital/{hospital}/ward/{ward}/patient/{patient_id}
        topic_parts = msg.topic.split('/')
        if len(topic_parts) >= 6:
            patient_id = topic_parts[5]
        else:
            patient_id = device_id.split('_')[-1] if '_' in device_id else 'unknown'
        
        # Infer department from ward (simplified)
        dept = ward.replace('ward_', 'dept_')
        
        decryption_time_ms = 0
        
        if is_encrypted:
            # Handle encrypted payload
            security_metrics['encrypted_messages'].inc()
            
            if not CRYPTO_AVAILABLE or not key_manager:
                logging.error("🔴 Received encrypted data but crypto not available")
                security_metrics['decryption_failure'].labels(
                    device_id=device_id, 
                    reason='crypto_unavailable'
                ).inc()
                return
            
            try:
                # Decode base64-encoded ciphertext and nonce
                decode_start = time.time()
                ciphertext, nonce = decode_payload({
                    'ciphertext': mqtt_payload['ciphertext'],
                    'nonce': mqtt_payload['nonce']
                })
                
                # Get device key
                device_key = key_manager.get_device_key(device_id)
                crypto = AsconCrypto(device_key)
                
                # Decrypt payload - NOW RETURNS TIMING
                decrypt_start = time.time()
                vitals, decryption_time_ms = crypto.decrypt(ciphertext, nonce)
                
                # Record decryption latency
                latency_metrics['decryption'].labels(device_id=device_id).observe(decryption_time_ms)
                
                logging.info(f"🔓 Decrypted vitals from {device_id} | Patient: {patient_id} | "
                           f"Decrypt: {decryption_time_ms:.2f}ms | Network: {network_latency_ms:.1f}ms")
                security_metrics['decryption_success'].labels(device_id=device_id).inc()
                
                # Store latency info
                current_latency[device_id]['decryption'] = decryption_time_ms
                current_latency[device_id]['network'] = network_latency_ms
                
            except ValueError as e:
                logging.error(f"🔴 Authentication failed for {device_id}: {e}")
                security_metrics['decryption_failure'].labels(
                    device_id=device_id, 
                    reason='auth_failed'
                ).inc()
                return  # Drop tampered/invalid data
            except Exception as e:
                logging.error(f"🔴 Decryption error for {device_id}: {e}")
                security_metrics['decryption_failure'].labels(
                    device_id=device_id, 
                    reason='decryption_error'
                ).inc()
                return
        else:
            # Handle plain payload (development/fallback mode)
            security_metrics['plain_messages'].inc()
            vitals = mqtt_payload.get('vitals', {})
            logging.warning(f"⚠️  Received PLAIN data from {device_id} (security risk!)")
        
        # NEW: Call ML service if anomaly_score not present
        if 'anomaly_score' not in vitals or vitals.get('anomaly_score') == 0:
            anomaly_score, ml_latency = call_ml_service(vitals)
            vitals['anomaly_score'] = anomaly_score
            logging.info(f"🧠 Backend ML call: {ml_latency:.2f}ms, Score: {anomaly_score:.3f}")
        
        # NEW: Save encrypted vitals to database (PATH 2)
        save_vitals_to_database(vitals, hospital, dept, ward, patient_id)
        
        # Process the vitals - MEASURE PROCESSING TIME (PATH 1: RAM + Prometheus)
        processing_start = time.time()
        process_patient_data(vitals, hospital, dept, ward, patient_id)
        processing_time_ms = (time.time() - processing_start) * 1000
        
        # Record processing latency
        latency_metrics['processing'].labels(device_id=device_id).observe(processing_time_ms)
        
        # Calculate end-to-end latency
        total_time_ms = (time.time() - mqtt_receive_time) * 1000
        end_to_end_ms = network_latency_ms + total_time_ms
        
        if end_to_end_ms > 0 and device_timestamp_us > 0:
            latency_metrics['end_to_end'].labels(device_id=device_id).observe(end_to_end_ms)
            current_latency[device_id]['end_to_end'] = end_to_end_ms
        
        current_latency[device_id]['processing'] = processing_time_ms
        
    except json.JSONDecodeError as e:
        logging.error(f"🔴 Invalid JSON from MQTT: {e}")
    except Exception as e:
        logging.error(f"🔴 Error processing MQTT message: {e}")
        import traceback
        traceback.print_exc()


def on_mqtt_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        tls_status = "with TLS" if USE_TLS else "plain"
        logging.info(f"✅ Backend connected to MQTT broker ({tls_status})")
        
        # Subscribe to all hospital topics
        client.subscribe("hospital/#")
        logging.info("📬 Subscribed to topic: hospital/#")
    else:
        mqtt_connected = False
        logging.error(f"❌ MQTT connection failed with code {rc}")


def on_mqtt_disconnect(client, userdata, rc):
    """MQTT disconnect callback"""
    global mqtt_connected
    mqtt_connected = False
    if rc != 0:
        logging.warning(f"⚠️  Unexpected MQTT disconnection (code: {rc})")


def init_mqtt_subscriber():
    """Initialize MQTT subscriber in background thread"""
    try:
        mqtt_client = mqtt.Client(client_id="main_host_backend")
        mqtt_client.on_connect = on_mqtt_connect
        mqtt_client.on_message = on_mqtt_message
        mqtt_client.on_disconnect = on_mqtt_disconnect
        
        if USE_TLS:
            try:
                mqtt_client.tls_set(
                    ca_certs="/app/certs/ca.crt",
                    certfile=None,
                    keyfile=None,
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLSv1_2
                )
                logging.info(f"🔐 TLS configured - connecting to {MQTT_BROKER}:{MQTT_PORT}")
                mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            except Exception as e:
                logging.error(f"❌ TLS connection failed: {e}")
                logging.info(f"⚠️  Falling back to plain MQTT on port {MQTT_PORT_PLAIN}")
                mqtt_client.connect(MQTT_BROKER, MQTT_PORT_PLAIN, 60)
        else:
            logging.warning(f"⚠️  Connecting to plain MQTT on port {MQTT_PORT_PLAIN}")
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT_PLAIN, 60)
        
        mqtt_client.loop_forever()
        
    except Exception as e:
        logging.error(f"❌ MQTT subscriber initialization failed: {e}")


# Flask Routes

@app.route('/track', methods=['POST'])
def track_traffic():
    """
    Legacy HTTP endpoint (kept for backward compatibility)
    New devices should use MQTT instead
    """
    data = request.get_json()
    logging.info("💡 Received HTTP payload (legacy mode)")
    
    hospital = data.get('hospital', 'unknown')
    dept = data.get('dept', 'unknown')
    ward = data.get('ward', 'unknown')
    patient = data.get('patient', 'unknown')

    process_patient_data(data, hospital, dept, ward, patient)

    return jsonify({'status': 'success'}), 200


@app.route('/metrics')
def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


@app.route('/')
def root():
    status = "🔐 Secure" if CRYPTO_AVAILABLE else "⚠️  Plain"
    mqtt_status = "✅ Connected" if mqtt_connected else "❌ Disconnected"
    return f"""
    <h1>Hospital Monitoring Service</h1>
    <p><strong>Status:</strong> {status}</p>
    <p><strong>MQTT:</strong> {mqtt_status}</p>
    <p><strong>Encryption:</strong> {'Enabled' if CRYPTO_AVAILABLE else 'Disabled'}</p>
    <hr>
    <ul>
        <li><a href="/metrics">/metrics</a> - Prometheus metrics</li>
        <li><a href="/api/patients">/api/patients</a> - List patients</li>
        <li><a href="/health">/health</a> - Health check</li>
    </ul>
    """


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'mqtt_connected': mqtt_connected,
        'crypto_available': CRYPTO_AVAILABLE,
        'active_patients': len(patient_data_store)
    })


@app.route('/api/latency', methods=['GET'])
def get_latency():
    """Get current latency metrics for all devices"""
    try:
        latency_data = {}
        for device_id, metrics in current_latency.items():
            latency_data[device_id] = {
                'decryption_ms': round(metrics.get('decryption', 0), 3),
                'processing_ms': round(metrics.get('processing', 0), 3),
                'network_ms': round(metrics.get('network', 0), 3),
                'end_to_end_ms': round(metrics.get('end_to_end', 0), 3)
            }
        
        return jsonify({
            "status": "success",
            "latency_metrics": latency_data
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/latency/<device_id>', methods=['GET'])
def get_device_latency(device_id):
    """Get latency metrics for a specific device"""
    try:
        if device_id not in current_latency:
            return jsonify({"status": "error", "message": "Device not found"}), 404
        
        metrics = current_latency[device_id]
        return jsonify({
            "status": "success",
            "device_id": device_id,
            "latency": {
                'decryption_ms': round(metrics.get('decryption', 0), 3),
                'processing_ms': round(metrics.get('processing', 0), 3),
                'network_ms': round(metrics.get('network', 0), 3),
                'end_to_end_ms': round(metrics.get('end_to_end', 0), 3)
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/patients', methods=['GET'])
def get_patients():
    """Get list of all patients"""
    try:
        patients = []
        for key in patient_data_store.keys():
            hospital, dept, ward, patient = key.split('|')
            if patient not in patients:
                patients.append(patient)
        
        return jsonify({
            "status": "success",
            "patients": patients
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/patient/<patient_id>', methods=['GET'])
def get_patient_data(patient_id):
    """Get data for a specific patient"""
    try:
        result = {}
        
        for key, data_list in patient_data_store.items():
            hospital, dept, ward, patient = key.split('|')
            
            if patient == patient_id:
                for idx, data_point in enumerate(data_list):
                    point_key = f"{key}|{idx}"
                    result[point_key] = data_point
        
        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/dashboard-data', methods=['GET'])
def get_dashboard_data():
    """Get all data for the dashboard"""
    try:
        result = {}
        for key, data_list in patient_data_store.items():
            result[key] = data_list[-1] if data_list else {}
        
        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    # Start MQTT subscriber in background thread
    mqtt_thread = threading.Thread(target=init_mqtt_subscriber, daemon=True)
    mqtt_thread.start()
    
    logging.info("🚀 Starting Main Host Backend")
    logging.info(f"   Encryption: {'✅ Enabled' if CRYPTO_AVAILABLE else '❌ Disabled'}")
    logging.info(f"   TLS: {'✅ Enabled' if USE_TLS else '❌ Disabled'}")
    
    # Start Flask app
    app.run(host='0.0.0.0', port=8000)
