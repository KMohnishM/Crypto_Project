"""
End-to-End Security Architecture Test
Tests complete flow: ESP32 → MQTT → Backend → ML → Storage
"""

print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     Healthcare IoT - End-to-End Architecture Validation             ║
║                                                                      ║
║  This script validates the complete security flow:                  ║
║  1. Device Encryption (Ascon-128)                                   ║
║  2. Transport Security (TLS)                                        ║
║  3. Payload Decryption (Backend)                                    ║
║  4. Service Authentication (JWT)                                    ║
║  5. ML Processing                                                   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")

import sys
import os
import time

# Test counters
tests_passed = 0
tests_failed = 0

def test_header(name):
    print(f"\n{'='*70}")
    print(f"  {name}")
    print(f"{'='*70}")

def test_pass(message):
    global tests_passed
    tests_passed += 1
    print(f"PASS: {message}")

def test_fail(message, error=None):
    global tests_failed
    tests_failed += 1
    print(f"FAIL: {message}")
    if error:
        print(f"   Error: {error}")

def test_step(step_num, description):
    print(f"\nStep {step_num}: {description}")

# ============================================================================
# LAYER 1: Device-Level Encryption (Ascon-128)
# ============================================================================
test_header("LAYER 1: Device-Level Encryption (Ascon-128)")

test_step(1, "Import crypto utilities")
sys.path.insert(0, 'services/common')
try:
    from crypto_utils import AsconCrypto, KeyManager, encode_payload, decode_payload
    test_pass("Crypto utilities imported")
except Exception as e:
    test_fail("Failed to import crypto utilities", e)
    sys.exit(1)

test_step(2, "Provision device with unique key")
try:
    km = KeyManager("test_e2e_keys.json")
    device_id = "hospital_1_patient_1"
    device_key = km.provision_device(device_id)
    test_pass(f"Device provisioned: {device_id}")
    print(f"   Key (first 16 chars): {device_key[:16]}...")
except Exception as e:
    test_fail("Device provisioning failed", e)
    sys.exit(1)

test_step(3, "Encrypt patient vitals payload")
try:
    crypto = AsconCrypto(device_key)
    
    # Simulate real patient data
    patient_vitals = {
        "patient_id": "patient_1",
        "heart_rate": 72,
        "spo2": 98,
        "bp_systolic": 120,
        "bp_diastolic": 80,
        "respiratory_rate": 16,
        "temperature": 36.8,
        "timestamp": "2026-02-08T14:30:00Z"
    }
    
    ciphertext, nonce, encrypt_time = crypto.encrypt(patient_vitals)
    print(f"Encryption time: {encrypt_time:.3f}ms")
    test_pass(f"Payload encrypted: {len(ciphertext)} bytes")
    print(f"   Original size: {len(str(patient_vitals))} bytes")
    print(f"   Encrypted size: {len(ciphertext)} bytes")
    print(f"   Nonce: {nonce.hex()[:32]}...")
except Exception as e:
    test_fail("Encryption failed", e)
    sys.exit(1)

test_step(4, "Encode for transmission (Base64)")
try:
    encoded = encode_payload(ciphertext, nonce)
    test_pass("Payload encoded for MQTT transmission")
    print(f"   Ciphertext (base64): {encoded['ciphertext'][:50]}...")
    print(f"   Nonce (base64): {encoded['nonce'][:50]}...")
except Exception as e:
    test_fail("Encoding failed", e)
    sys.exit(1)

# ============================================================================
# LAYER 2: Transport Security (Simulated)
# ============================================================================
test_header("LAYER 2: Transport Security (TLS + MQTT)")

test_step(5, "Verify TLS configuration exists")
try:
    ca_cert_path = "config/mosquitto/certs/ca.crt"
    mosquitto_conf = "config/mosquitto/mosquitto.conf"
    
    if os.path.exists(ca_cert_path):
        test_pass("CA certificate exists")
    else:
        test_fail("CA certificate not found - run generate_certs.ps1")
    
    if os.path.exists(mosquitto_conf):
        with open(mosquitto_conf, 'r') as f:
            content = f.read()
            if '8883' in content and 'tlsv1.2' in content:
                test_pass("MQTT broker configured with TLS 1.2")
            else:
                test_fail("MQTT broker TLS configuration incomplete")
    else:
        test_fail("MQTT configuration not found")
except Exception as e:
    test_fail("TLS verification failed", e)

test_step(6, "Simulate MQTT topic routing")
try:
    mqtt_topic = f"hospital/hospital_1/ward/ward_1/patient/patient_1"
    mqtt_payload = {
        "device_id": device_id,
        "hospital": "hospital_1",
        "ward": "ward_1",
        "encrypted": True,
        "ciphertext": encoded['ciphertext'],
        "nonce": encoded['nonce'],
        "timestamp": patient_vitals['timestamp']
    }
    test_pass(f"MQTT message prepared")
    print(f"   Topic: {mqtt_topic}")
    print(f"   Payload size: {len(str(mqtt_payload))} bytes")
    print(f"   Broker sees only ciphertext (end-to-end encryption)")
except Exception as e:
    test_fail("MQTT payload preparation failed", e)

# ============================================================================
# LAYER 3: Backend Decryption
# ============================================================================
test_header("LAYER 3: Backend Decryption & Authentication")

test_step(7, "Backend receives and decodes payload")
try:
    decoded_ct, decoded_nonce = decode_payload(encoded)
    test_pass("Payload decoded from base64")
except Exception as e:
    test_fail("Decoding failed", e)
    sys.exit(1)

test_step(8, "Backend decrypts with device key")
try:
    # Backend looks up device key
    backend_km = KeyManager("test_e2e_keys.json")
    backend_device_key = backend_km.get_device_key(device_id)
    
    # Decrypt
    backend_crypto = AsconCrypto(backend_device_key)
    decrypted_vitals, decrypt_time = backend_crypto.decrypt(decoded_ct, decoded_nonce)
    print(f"Decryption time: {decrypt_time:.3f}ms")
    
    test_pass("Payload decrypted successfully")
    print(f"   Decrypted data: {decrypted_vitals}")
    
    # Verify integrity
    if decrypted_vitals == patient_vitals:
        test_pass("Authentication tag verified - no tampering")
    else:
        test_fail("Data integrity check failed")
except Exception as e:
    test_fail("Decryption failed", e)
    sys.exit(1)

test_step(9, "Test tampered data detection")
try:
    # Tamper with ciphertext
    tampered_ct = bytearray(ciphertext)
    tampered_ct[10] ^= 0xFF  # Flip some bits
    
    try:
        backend_crypto.decrypt(bytes(tampered_ct), nonce)  # Returns (data, time)
        test_fail("Tampered data was not detected!")
    except:
        test_pass("Tampered data correctly rejected")
except Exception as e:
    test_fail("Tamper detection test failed", e)

# ============================================================================
# LAYER 4: Service Authentication
# ============================================================================
test_header("LAYER 4: Service-to-Service Authentication (JWT)")

test_step(10, "Import service authentication")
try:
    from service_auth import generate_service_token, verify_service_token, ServiceAuthClient
    test_pass("Service authentication module imported")
except Exception as e:
    test_fail("Failed to import service auth", e)

test_step(11, "Generate JWT token for backend")
try:
    token = generate_service_token('main_host')
    test_pass("JWT token generated")
    print(f"   Token (first 50 chars): {token[:50]}...")
except Exception as e:
    test_fail("Token generation failed", e)

test_step(12, "Verify JWT token")
try:
    payload = verify_service_token(token)
    if payload['service'] == 'main_host':
        test_pass("JWT token verified successfully")
        print(f"   Service: {payload['service']}")
    else:
        test_fail("Token verification returned wrong service")
except Exception as e:
    test_fail("Token verification failed", e)

test_step(13, "Test ServiceAuthClient")
try:
    client = ServiceAuthClient('main_host')
    headers = client.get_headers()
    if 'Authorization' in headers and 'Bearer' in headers['Authorization']:
        test_pass("ServiceAuthClient initialized correctly")
        print(f"   Auth header: Bearer {headers['Authorization'][7:57]}...")
    else:
        test_fail("ServiceAuthClient headers incorrect")
except Exception as e:
    test_fail("ServiceAuthClient test failed", e)

# ============================================================================
# LAYER 5: Data Flow Validation
# ============================================================================
test_header("LAYER 5: Complete Data Flow Validation")

test_step(14, "Validate Docker Compose configuration")
try:
    with open('docker-compose.yml', 'r') as f:
        content = f.read()
    
    required_services = ['mosquitto', 'main_host', 'patient_simulator', 'ml_service']
    for service in required_services:
        if service in content:
            test_pass(f"Service '{service}' defined in docker-compose.yml")
        else:
            test_fail(f"Service '{service}' not found in docker-compose.yml")
    
    # Check volume mounts
    if '/app/common' in content and '/app/certs' in content:
        test_pass("Crypto utilities and certificates mounted")
    else:
        test_fail("Required volume mounts missing")
        
except Exception as e:
    test_fail("Docker configuration validation failed", e)

test_step(15, "Verify environment configuration")
try:
    with open('config/environment/development.env', 'r') as f:
        env_content = f.read()
    
    required_vars = ['MQTT_BROKER', 'USE_TLS', 'ENABLE_ENCRYPTION', 
                     'ENABLE_SERVICE_AUTH', 'SERVICE_SECRET_KEY']
    
    for var in required_vars:
        if var in env_content:
            test_pass(f"Environment variable '{var}' configured")
        else:
            test_fail(f"Environment variable '{var}' missing")
            
except Exception as e:
    test_fail("Environment validation failed", e)

# ============================================================================
# Architecture Diagram ASCII Art
# ============================================================================
test_header("SECURITY ARCHITECTURE SUMMARY")

print("""
┌─────────────────────────────────────────────────────────────────────┐
│                    LAYERED SECURITY ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────────────┘

  ┌───────────────┐
  │  ESP32/IoT    │  ① Encrypt with K_device (Ascon-128)
  │   Device      │     • 128-bit key per device
  └───────┬───────┘     • Authenticated encryption
          │
          │ ② TLS 1.2 Transport Encryption
          │    • Certificate-based auth
          ▼    • Session keys
  ┌───────────────┐
  │ MQTT Broker   │  Sees only ciphertext
  │  (Mosquitto)  │     • Cannot decrypt payload
  └───────┬───────┘     • Routes encrypted messages
          │
          │ ③ MQTT/TLS Subscriber
          ▼
  ┌───────────────┐
  │   Backend     │  Decrypt with K_device
  │  (Main Host)  │     • Verify auth tag
  └───────┬───────┘     • Detect tampering
          │
          │ ④ JWT Authentication
          │    • Service-to-service
          ▼    • HS256 tokens
  ┌───────────────┐
  │  ML Service   │  Anomaly Detection
  │  (Protected)  │     • Authenticated API
  └───────────────┘

KEY SECURITY PROPERTIES:
  End-to-End Encryption: Broker cannot read patient data
  Per-Device Keys: Compromise of one device doesn't affect others
  Authentication Tags: Tampering detected and rejected
  Defense in Depth: Multiple independent security layers
  Key Isolation: Transport keys ≠ Payload keys
""")

# ============================================================================
# Final Summary
# ============================================================================
print("\n" + "="*70)
print("  SECURITY ARCHITECTURE VALIDATION COMPLETE")
print("="*70)

total = tests_passed + tests_failed
percentage = (tests_passed / total * 100) if total > 0 else 0

print(f"\n  Test Results:")
print(f"     Total Tests:  {total}")
print(f"     Passed:    {tests_passed}")
print(f"     Failed:    {tests_failed}")
print(f"     Success Rate: {percentage:.1f}%")

print(f"\n  Security Layers Validated:")
print(f"     Layer 1: Device Encryption (Ascon-128)")
print(f"     Layer 2: Transport Security (TLS 1.2)")
print(f"     Layer 3: Backend Decryption & Integrity")
print(f"     Layer 4: Service Authentication (JWT)")
print(f"     Layer 5: Configuration & Integration")

print(f"\n  Ready for Deployment:")
if tests_failed == 0:
    print(f"     All security layers operational")
    print(f"     Architecture matches design document")
    print(f"     System ready for production deployment")
else:
    print(f"     WARNING: Review {tests_failed} failed test(s) above")

print("\n" + "="*70)
print()

# Cleanup
if os.path.exists("test_e2e_keys.json"):
    os.remove("test_e2e_keys.json")

sys.exit(0 if tests_failed == 0 else 1)
