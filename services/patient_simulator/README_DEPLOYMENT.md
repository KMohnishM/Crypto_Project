# 🚨 INSTRUCTIONS FOR DEPLOYMENT 🚨

This directory contains TWO versions of the simulator:

## 1️⃣ Current Version (Legacy - HTTP only)
- **File**: `send_data.py`
- **Protocol**: Plain HTTP POST
- **Encryption**: ❌ None
- **Use**: Testing only

## 2️⃣ Secure Version (MQTT + Ascon)
- **File**: `send_data_encrypted.py`
- **Protocol**: MQTT over TLS
- **Encryption**: ✅ Ascon-128 authenticated encryption
- **Use**: Production-ready, simulates ESP32 behavior

## 🔄 How to Switch to Encrypted Version

### Option A: Rename files (Recommended)
```powershell
# Backup original
mv send_data.py send_data_legacy.py

# Activate encrypted version
mv send_data_encrypted.py send_data.py

# Restart container
docker-compose restart patient_simulator
```

### Option B: Update Dockerfile CMD
Edit `Dockerfile` to use:
```dockerfile
CMD ["python", "send_data_encrypted.py"]
```

## ⚠️ Important Notes
- The encrypted version requires MQTT broker running
- TLS certificates must be generated first
- Keys are auto-provisioned on first run
- Backward compatible with plain mode (fallback)

## 🧪 Testing
You can run both versions simultaneously to compare encrypted vs plain transmission.
