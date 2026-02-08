#!/usr/bin/env python3
"""
Debug tool: Capture MQTT message and test decryption
"""
import sys
sys.path.insert(0, '/app/common')

from crypto_utils import AsconCrypto, KeyManager, decode_payload
import json
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("hospital/#")

def on_message(client,userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        device_id = payload['device_id']
        print(f"\n📥 Received from {device_id}")
        print(f"Encrypted: {payload['encrypted']}")
        
        if payload['encrypted']:
            # Decode
            ct_b64 = payload['ciphertext']
            nonce_b64 = payload['nonce']
            print(f"Ciphertext (b64): {ct_b64[:50]}...")
            print(f"Nonce (b64): {nonce_b64}")
            
            ciphertext, nonce = decode_payload({'ciphertext': ct_b64, 'nonce': nonce_b64})
            print(f"Ciphertext length: {len(ciphertext)}")
            print(f"Nonce hex: {nonce.hex()}")
            
            # Get key
            km = KeyManager('/app/keys/device_keys.json')
            device_key = km.get_device_key(device_id)
            print(f"Device key: {device_key}")
            
            # Try decrypt
            crypto = AsconCrypto(device_key)
            print("Attempting decryption...")
            vitals = crypto.decrypt(ciphertext, nonce)
            print(f"✅ SUCCESS: {vitals}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Connecting to MQTT broker...")
client.connect("mosquitto", 1883, 60)
client.loop_forever()
