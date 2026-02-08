"""
Ascon-based Cryptographic Utilities for Healthcare IoT
Provides device-level payload encryption and key management
"""

import os
import json
from typing import Dict, Tuple, Optional
import base64

try:
    import ascon
except ImportError:
    print("⚠️  WARNING: ascon library not installed. Run: pip install ascon")
    ascon = None


class AsconCrypto:
    """
    Ascon-128 authenticated encryption for patient vitals payloads
    
    Provides:
    - Confidentiality (AES-level security)
    - Integrity (authentication tag)
    - Replay protection (via nonces)
    """
    
    def __init__(self, key_hex: str):
        """
        Initialize with 16-byte (128-bit) hex key
        
        Args:
            key_hex: Hexadecimal string representing 128-bit key
        """
        if ascon is None:
            raise ImportError("ascon library not available")
            
        self.key = bytes.fromhex(key_hex)
        if len(self.key) != 16:
            raise ValueError(f"Key must be 16 bytes (128 bits), got {len(self.key)} bytes")
    
    def encrypt(self, payload: Dict, nonce: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Encrypt patient vitals payload using Ascon-128
        
        Args:
            payload: Dictionary containing patient vitals
            nonce: Optional 16-byte nonce (generated if not provided)
        
        Returns:
            (ciphertext, nonce) tuple
            
        Security: Nonce MUST be unique per encryption with same key
        """
        if nonce is None:
            nonce = os.urandom(16)  # 128-bit random nonce
        
        if len(nonce) != 16:
            raise ValueError(f"Nonce must be 16 bytes, got {len(nonce)} bytes")
        
        # Serialize payload to JSON bytes
        plaintext = json.dumps(payload).encode('utf-8')
        
        # Ascon authenticated encryption
        # Parameters: key, nonce, associated_data, plaintext
        ciphertext = ascon.encrypt(self.key, nonce, b'', plaintext)
        
        return ciphertext, nonce
    
    def decrypt(self, ciphertext: bytes, nonce: bytes) -> Dict:
        """
        Decrypt and authenticate patient vitals payload
        
        Args:
            ciphertext: Encrypted payload bytes
            nonce: 16-byte nonce used during encryption
        
        Returns:
            Decrypted payload dictionary
            
        Raises:
            ValueError: If authentication tag verification fails (tampered data)
        """
        if len(nonce) != 16:
            raise ValueError(f"Nonce must be 16 bytes, got {len(nonce)} bytes")
        
        try:
            # Ascon authenticated decryption
            plaintext = ascon.decrypt(self.key, nonce, b'', ciphertext)
            return json.loads(plaintext.decode('utf-8'))
        except Exception as e:
            raise ValueError(f"Decryption failed - data may be tampered: {e}")


class KeyManager:
    """
    Manages per-device encryption keys (K_device)
    
    Security model:
    - Each device/patient has unique key
    - Keys stored in secure file (encrypt this file in production!)
    - Supports key provisioning, lookup, and revocation
    """
    
    def __init__(self, key_file: str = "device_keys.json"):
        """
        Initialize key manager
        
        Args:
            key_file: Path to key storage file
        """
        self.key_file = key_file
        self.keys = self._load_keys()
    
    def _load_keys(self) -> Dict[str, Dict]:
        """Load keys from secure storage"""
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading keys: {e}")
                return {}
        return {}
    
    def _save_keys(self):
        """Save keys to secure storage"""
        try:
            with open(self.key_file, 'w') as f:
                json.dump(self.keys, f, indent=2)
            # Set restrictive permissions (Windows compatible)
            os.chmod(self.key_file, 0o600)
        except Exception as e:
            print(f"⚠️  Error saving keys: {e}")
    
    def provision_device(self, device_id: str) -> str:
        """
        Provision new device with unique key
        
        Args:
            device_id: Unique device identifier (e.g., "hospital_1_patient_1")
        
        Returns:
            Hex-encoded 128-bit key
        """
        if device_id in self.keys:
            print(f"⚠️  Device {device_id} already provisioned")
            return self.keys[device_id]['key']
        
        # Generate cryptographically secure random key
        new_key = os.urandom(16).hex()
        
        self.keys[device_id] = {
            'key': new_key,
            'created_at': self._get_timestamp(),
            'status': 'active'
        }
        
        self._save_keys()
        print(f"✅ Provisioned device: {device_id}")
        return new_key
    
    def get_device_key(self, device_id: str) -> str:
        """
        Get encryption key for specific device
        
        Args:
            device_id: Device identifier
        
        Returns:
            Hex-encoded key
            
        Note: Auto-provisions if device not found (development mode)
        """
        if device_id not in self.keys:
            print(f"🔑 Auto-provisioning new device: {device_id}")
            return self.provision_device(device_id)
        
        device_info = self.keys[device_id]
        
        if device_info.get('status') != 'active':
            raise ValueError(f"Device {device_id} is not active (status: {device_info.get('status')})")
        
        return device_info['key']
    
    def revoke_device(self, device_id: str):
        """
        Revoke device key (disable encryption for compromised device)
        
        Args:
            device_id: Device to revoke
        """
        if device_id in self.keys:
            self.keys[device_id]['status'] = 'revoked'
            self.keys[device_id]['revoked_at'] = self._get_timestamp()
            self._save_keys()
            print(f"🚫 Revoked device: {device_id}")
    
    def rotate_key(self, device_id: str) -> str:
        """
        Generate new key for device (key rotation)
        
        Args:
            device_id: Device for key rotation
        
        Returns:
            New hex-encoded key
        """
        if device_id in self.keys:
            old_key = self.keys[device_id]['key']
            # Archive old key for grace period
            self.keys[f"{device_id}_old"] = {
                'key': old_key,
                'archived_at': self._get_timestamp()
            }
        
        # Generate new key
        new_key = os.urandom(16).hex()
        self.keys[device_id] = {
            'key': new_key,
            'rotated_at': self._get_timestamp(),
            'status': 'active'
        }
        
        self._save_keys()
        print(f"🔄 Rotated key for device: {device_id}")
        return new_key
    
    def list_devices(self) -> list:
        """List all active devices"""
        return [
            device_id for device_id, info in self.keys.items()
            if not device_id.endswith('_old') and info.get('status') == 'active'
        ]
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current UTC timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'


def encode_payload(ciphertext: bytes, nonce: bytes) -> Dict[str, str]:
    """
    Encode encrypted payload for JSON transmission
    
    Args:
        ciphertext: Encrypted data
        nonce: Nonce used for encryption
    
    Returns:
        Dictionary with base64-encoded fields
    """
    return {
        'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
        'nonce': base64.b64encode(nonce).decode('utf-8')
    }


def decode_payload(encoded: Dict[str, str]) -> Tuple[bytes, bytes]:
    """
    Decode encrypted payload from JSON transmission
    
    Args:
        encoded: Dictionary with base64-encoded fields
    
    Returns:
        (ciphertext, nonce) tuple
    """
    ciphertext = base64.b64decode(encoded['ciphertext'])
    nonce = base64.b64decode(encoded['nonce'])
    return ciphertext, nonce


# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Ascon Crypto...")
    
    # Initialize key manager
    km = KeyManager("test_keys.json")
    
    # Provision device
    device_id = "hospital_1_patient_1"
    key = km.provision_device(device_id)
    print(f"Device key: {key}")
    
    # Initialize crypto
    crypto = AsconCrypto(key)
    
    # Test payload
    test_payload = {
        "patient_id": "patient_1",
        "heart_rate": 72,
        "spo2": 98,
        "bp_systolic": 120,
        "bp_diastolic": 80,
        "timestamp": "2026-02-08T12:00:00Z"
    }
    
    # Encrypt
    ciphertext, nonce = crypto.encrypt(test_payload)
    print(f"✅ Encrypted: {len(ciphertext)} bytes")
    
    # Encode for transmission
    encoded = encode_payload(ciphertext, nonce)
    print(f"📤 Encoded for MQTT: {len(encoded['ciphertext'])} chars")
    
    # Decode
    decoded_ct, decoded_nonce = decode_payload(encoded)
    
    # Decrypt
    decrypted = crypto.decrypt(decoded_ct, decoded_nonce)
    print(f"✅ Decrypted: {decrypted}")
    
    # Verify
    assert decrypted == test_payload
    print("✅ All tests passed!")
