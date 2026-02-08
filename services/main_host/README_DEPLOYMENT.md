# 🚨 INSTRUCTIONS FOR DEPLOYMENT 🚨

This directory contains TWO versions of the application:

## 1️⃣ Current Version (Legacy - HTTP only)
- **File**: `app.py`
- **Protocol**: Plain HTTP
- **Encryption**: ❌ None
- **Use**: Testing only, NOT production-ready

## 2️⃣ Secure Version (MQTT + Ascon)
- **File**: `app_encrypted.py`
- **Protocol**: MQTT over TLS
- **Encryption**: ✅ Ascon-128 authenticated encryption
- **Use**: Production-ready, follows security architecture

## 🔄 How to Switch to Encrypted Version

### Option A: Rename files (Recommended)
```powershell
# Backup original
mv app.py app_legacy.py

# Activate encrypted version
mv app_encrypted.py app.py

# Restart container
docker-compose restart main_host
```

### Option B: Update Dockerfile CMD
Edit `Dockerfile` to use:
```dockerfile
CMD ["python", "app_encrypted.py"]
```

## ⚠️ Important Notes
- The encrypted version requires MQTT broker running
- TLS certificates must be generated first
- Both versions expose the same Flask API endpoints
- Gradual migration supported (both can coexist)

## 🧪 Testing
Run both versions simultaneously on different ports to test before full migration.
