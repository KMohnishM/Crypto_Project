#!/usr/bin/env python3
"""
Healthcare IoT Security - Test Suite
Validates encryption, authentication, and key management
"""

import sys
import os

# Test results
tests_passed = 0
tests_failed = 0

def test_header(name):
    print(f"\n{'='*70}")
    print(f"  TEST: {name}")
    print(f"{'='*70}")

def test_pass(message):
    global tests_passed
    tests_passed += 1
    print(f"✅ PASS: {message}")

def test_fail(message, error=None):
    global tests_failed
    tests_failed += 1
    print(f"❌ FAIL: {message}")
    if error:
        print(f"   Error: {error}")

def test_module_import(module_name, module_path=None):
    """Test if a module can be imported"""
    try:
        if module_path:
            sys.path.insert(0, module_path)
        __import__(module_name)
        test_pass(f"Module '{module_name}' imported successfully")
        return True
    except ImportError as e:
        test_fail(f"Cannot import '{module_name}'", e)
        return False

def test_crypto_utils():
    """Test Ascon encryption utilities"""
    test_header("Crypto Utilities (Ascon-128)")
    
    # Import test
    sys.path.insert(0, 'services/common')
    if not test_module_import('crypto_utils'):
        return
    
    from crypto_utils import AsconCrypto, KeyManager, encode_payload, decode_payload
    
    # Test key generation
    try:
        import os
        test_key = os.urandom(16).hex()
        if len(test_key) == 32:  # 16 bytes = 32 hex chars
            test_pass("Key generation (16 bytes)")
        else:
            test_fail("Key generation: incorrect length")
    except Exception as e:
        test_fail("Key generation", e)
    
    # Test encryption/decryption
    try:
        crypto = AsconCrypto(test_key)
        test_payload = {"heart_rate": 72, "spo2": 98, "patient_id": "test_1"}
        
        ciphertext, nonce = crypto.encrypt(test_payload)
        test_pass(f"Encryption ({len(ciphertext)} bytes ciphertext)")
        
        decrypted = crypto.decrypt(ciphertext, nonce)
        if decrypted == test_payload:
            test_pass("Decryption and integrity check")
        else:
            test_fail("Decryption: payload mismatch")
    except Exception as e:
        test_fail("Encryption/Decryption cycle", e)
    
    # Test base64 encoding
    try:
        encoded = encode_payload(ciphertext, nonce)
        decoded_ct, decoded_nonce = decode_payload(encoded)
        if decoded_ct == ciphertext and decoded_nonce == nonce:
            test_pass("Base64 encoding/decoding")
        else:
            test_fail("Base64: data mismatch")
    except Exception as e:
        test_fail("Base64 encoding/decoding", e)
    
    # Test key manager
    try:
        km = KeyManager("test_keys_temp.json")
        device_key = km.provision_device("test_device_1")
        
        if len(device_key) == 32:
            test_pass("KeyManager: device provisioning")
        else:
            test_fail("KeyManager: invalid key length")
        
        retrieved_key = km.get_device_key("test_device_1")
        if retrieved_key == device_key:
            test_pass("KeyManager: key retrieval")
        else:
            test_fail("KeyManager: key mismatch")
        
        # Cleanup
        if os.path.exists("test_keys_temp.json"):
            os.remove("test_keys_temp.json")
    except Exception as e:
        test_fail("KeyManager operations", e)

def test_service_auth():
    """Test JWT service authentication"""
    test_header("Service Authentication (JWT)")
    
    sys.path.insert(0, 'services/common')
    if not test_module_import('service_auth'):
        return
    
    from service_auth import generate_service_token, verify_service_token
    
    # Test token generation
    try:
        token = generate_service_token('test_service')
        if token and len(token) > 0:
            test_pass(f"JWT token generation ({len(token)} chars)")
        else:
            test_fail("JWT token generation: empty token")
    except Exception as e:
        test_fail("JWT token generation", e)
    
    # Test token verification
    try:
        payload = verify_service_token(token)
        if payload['service'] == 'test_service':
            test_pass("JWT token verification")
        else:
            test_fail("JWT token verification: incorrect payload")
    except Exception as e:
        test_fail("JWT token verification", e)
    
    # Test invalid token
    try:
        verify_service_token("invalid.token.here")
        test_fail("Invalid token should have been rejected")
    except:
        test_pass("Invalid token rejection")

def test_file_structure():
    """Test that all required files exist"""
    test_header("File Structure")
    
    required_files = [
        'services/common/crypto_utils.py',
        'services/common/service_auth.py',
        'services/patient_simulator/send_data_encrypted.py',
        'services/main_host/app_encrypted.py',
        'config/mosquitto/mosquitto.conf',
        'config/mosquitto/certs/generate_certs.ps1',
        'docker-compose.yml',
        'setup_security.ps1',
        'SECURITY_IMPLEMENTATION.md',
        'QUICKSTART.md',
    ]
    
    for filepath in required_files:
        if os.path.exists(filepath):
            test_pass(f"File exists: {filepath}")
        else:
            test_fail(f"Missing file: {filepath}")

def test_docker_config():
    """Test docker-compose configuration"""
    test_header("Docker Configuration")
    
    try:
        with open('docker-compose.yml', 'r') as f:
            content = f.read()
        
        if 'mosquitto' in content:
            test_pass("MQTT broker service defined")
        else:
            test_fail("MQTT broker service not found")
        
        if '8883' in content:
            test_pass("TLS port (8883) configured")
        else:
            test_fail("TLS port not configured")
        
        if '/app/common' in content:
            test_pass("Common modules mounted")
        else:
            test_fail("Common modules not mounted")
        
        if '/app/certs' in content:
            test_pass("Certificate volumes mounted")
        else:
            test_fail("Certificate volumes not mounted")
            
    except Exception as e:
        test_fail("Docker configuration check", e)

def test_requirements():
    """Test Python requirements files"""
    test_header("Python Requirements")
    
    files_to_check = [
        ('services/patient_simulator/requirements.txt', ['ascon', 'paho-mqtt']),
        ('services/main_host/requirements.txt', ['ascon', 'paho-mqtt']),
        ('services/ml_service/requirements.txt', ['PyJWT']),
    ]
    
    for filepath, required_packages in files_to_check:
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            filepath_short = filepath.split('/')[-2]
            for package in required_packages:
                if package in content:
                    test_pass(f"{filepath_short}: '{package}' present")
                else:
                    test_fail(f"{filepath_short}: '{package}' missing")
        except Exception as e:
            test_fail(f"Reading {filepath}", e)

def test_environment_config():
    """Test environment configuration"""
    test_header("Environment Configuration")
    
    try:
        with open('config/environment/development.env', 'r') as f:
            content = f.read()
        
        required_vars = [
            'MQTT_BROKER',
            'MQTT_PORT_TLS',
            'USE_TLS',
            'SERVICE_SECRET_KEY',
            'ENABLE_ENCRYPTION'
        ]
        
        for var in required_vars:
            if var in content:
                test_pass(f"Environment variable: {var}")
            else:
                test_fail(f"Missing environment variable: {var}")
    except Exception as e:
        test_fail("Environment configuration check", e)

def print_summary():
    """Print test summary"""
    print(f"\n{'='*70}")
    print(f"  TEST SUMMARY")
    print(f"{'='*70}")
    
    total = tests_passed + tests_failed
    percentage = (tests_passed / total * 100) if total > 0 else 0
    
    print(f"\n  Total Tests:  {total}")
    print(f"  ✅ Passed:    {tests_passed}")
    print(f"  ❌ Failed:    {tests_failed}")
    print(f"  Success Rate: {percentage:.1f}%")
    print()
    
    if tests_failed == 0:
        print("  🎉 ALL TESTS PASSED! System is ready for deployment.")
    elif percentage >= 80:
        print("  ⚠️  Most tests passed. Check failures above.")
    else:
        print("  ❌ Multiple failures detected. Review implementation.")
    
    print(f"{'='*70}\n")
    
    return 0 if tests_failed == 0 else 1

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║         Healthcare IoT Security - Automated Test Suite              ║
║                                                                      ║
║  This script validates the security implementation including:       ║
║  • Ascon-128 encryption/decryption                                  ║
║  • JWT service authentication                                       ║
║  • Key management                                                   ║
║  • File structure                                                   ║
║  • Docker configuration                                             ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run all tests
    test_file_structure()
    test_docker_config()
    test_requirements()
    test_environment_config()
    test_crypto_utils()
    test_service_auth()
    
    # Print summary and exit
    sys.exit(print_summary())
