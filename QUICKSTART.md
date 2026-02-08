# 🎯 Healthcare IoT Security - Quick Start Guide

## ⚡ **3-Step Deployment (Windows)**

### Step 1: Generate TLS Certificates
```powershell
cd config\mosquitto\certs
.\generate_certs.ps1
cd ..\..\..
```

### Step 2: Run Automated Setup
```powershell
.\setup_security.ps1
```
Select **Option 1** (🔐 Secure Mode) when prompted.

### Step 3: Verify Deployment
```powershell
# Check container status
docker-compose ps

# Watch encrypted data transmission
docker-compose logs -f patient_simulator

# Watch decryption in backend
docker-compose logs -f main_host
```

---

## ✅ **What to Look For**

### Patient Simulator Logs
```
✅ Connected to MQTT broker (with TLS)
📤 🔐 encrypted | hospital_1_patient_1 | Score: 0.42 | Topic: hospital/...
```

### Main Host Logs
```
✅ Backend connected to MQTT broker (with TLS)
📬 Subscribed to topic: hospital/#
🔓 Decrypted vitals from hospital_1_patient_1 | Patient: patient_1
```

### If You See This - SUCCESS! 🎉
- ✅ TLS connection established
- ✅ Payload encrypted with Ascon-128
- ✅ Data decrypted and authenticated
- ✅ Per-device keys working

---

## 🔧 **Troubleshooting**

### Issue: "TLS connection failed"
**Solution:** Check if certificates exist
```powershell
dir config\mosquitto\certs\*.crt
```
If missing, run `generate_certs.ps1`

### Issue: "Crypto utilities not available"
**Solution:** Rebuild containers
```powershell
docker-compose down
docker-compose up --build
```

### Issue: "MQTT not connected"
**Solution:** Check MQTT broker
```powershell
docker-compose logs mosquitto
```

### Issue: "Decryption failed"
**Solution:** Check if keys match
```powershell
# Device keys
Get-Content data\keys\device_keys.json

# Backend keys (should have same devices)
Get-Content data\keys\backend_keys.json
```

---

## 📊 **Access Services**

- **Web Dashboard:** http://localhost:5000
- **Grafana:** http://localhost:3001 (admin/admin)
- **Prometheus:** http://localhost:9090
- **AlertManager:** http://localhost:9093
- **Main Host API:** http://localhost:8000
- **Main Host Health:** http://localhost:8000/health

---

## 🧪 **Test Commands**

### View Encryption Keys
```powershell
Get-Content data\keys\device_keys.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Test Crypto Module
```powershell
docker-compose exec patient_simulator python /app/common/crypto_utils.py
```

### Monitor MQTT Traffic
```powershell
# Install mosquitto clients if needed: choco install mosquitto
mosquitto_sub -h localhost -p 8883 --cafile config/mosquitto/certs/ca.crt -t "hospital/#" -v
```

### Check Security Metrics
```powershell
curl http://localhost:8000/metrics | Select-String "decryption"
```

---

## 🔄 **Switch Between Modes**

### To Secure Mode (MQTT + Encryption)
```powershell
Copy-Item services\patient_simulator\send_data_encrypted.py services\patient_simulator\send_data.py -Force
Copy-Item services\main_host\app_encrypted.py services\main_host\app.py -Force
docker-compose restart patient_simulator main_host
```

### To Legacy Mode (HTTP Only)
```powershell
Copy-Item services\patient_simulator\send_data_legacy.py services\patient_simulator\send_data.py -Force
Copy-Item services\main_host\app_legacy.py services\main_host\app.py -Force
docker-compose restart patient_simulator main_host
```

---

## 📚 **Documentation**

- **Full Implementation:** [SECURITY_IMPLEMENTATION.md](SECURITY_IMPLEMENTATION.md)
- **Deployment Instructions:** Check README_DEPLOYMENT.md in each service folder
- **Crypto Details:** `services/common/crypto_utils.py`
- **Auth Details:** `services/common/service_auth.py`

---

## 🎓 **For Your Defense/Viva**

### Show This Flow
1. "Data encrypted at device level with Ascon-128"
2. "Transmitted via MQTT over TLS"
3. "Broker cannot read plaintext (end-to-end encryption)"
4. "Backend decrypts and verifies integrity"
5. "Per-device unique keys prevent cross-device attacks"

### Key Architecture Point
> "We use **layered security**: TLS for transport, Ascon for payload. Even if TLS is compromised, payload remains encrypted."

---

**Ready to deploy!** 🚀
