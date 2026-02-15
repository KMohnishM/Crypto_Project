# 🔍 Complete Data Flow Analysis

## **ACTUAL DATA FLOW (Step-by-Step)**

### **Step 1: Patient Simulator Generates Vitals**
**File**: `services/patient_simulator/send_data_encrypted.py`

```python
# Lines 335-380: Simulation loop
def simulate_traffic(file_path):
    for sheet_name in sheet_names:
        patient_meta = rows[row_index]  # Read from Excel
        
        # 1. Generate NEW vitals (PLAIN)
        data = generate_updated_patient_data(patient_meta, time_diff_minutes)
        # data = {heart_rate: 78, spo2: 96, bp_systolic: 120, ...} - PLAIN TEXT
```

**Data State**: ❌ PLAIN TEXT (not encrypted yet)

---

### **Step 2: Simulator Sends PLAIN Data to ML Service**
**File**: `services/patient_simulator/send_data_encrypted.py` (Lines 186-213)

```python
# 2. Send PLAIN vitals to ML service (HTTP POST)
def get_anomaly_score(data):
    # Sends UNENCRYPTED JSON to http://ml_service:6000/predict
    response = requests.post(ML_MODEL_URL, json=data, timeout=3)
    
    # ML returns: {"normalized_score": 0.23, "inference_time_ms": 2.5}
    anomaly_score = float(response_data.get("normalized_score", 0.0))
    return anomaly_score, ml_latency_ms
```

**Important**: 
- ✅ **ML receives PLAIN (unencrypted) data** via HTTP
- ✅ ML returns PLAIN anomaly score
- ❌ **This HTTP communication is NOT encrypted** (only within Docker network)

---

### **Step 3: Simulator Encrypts Payload (Including Anomaly Score)**
**File**: `services/patient_simulator/send_data_encrypted.py` (Lines 218-270)

```python
def publish_encrypted_vitals(patient_data, anomaly_score, ml_latency_ms=0):
    # 3. Package vitals + anomaly score
    vitals_payload = {
        "heart_rate": patient_data['heart_rate'],
        "spo2": patient_data['spo2'],
        # ... other vitals ...
        "anomaly_score": anomaly_score  # ← ML score included
    }
    
    # 4. ENCRYPT with Ascon-128
    device_key = key_manager.get_device_key(device_id)
    crypto = AsconCrypto(device_key)
    ciphertext, nonce, encryption_time_ms = crypto.encrypt(vitals_payload)
    
    # 5. Package for MQTT
    mqtt_payload = {
        "device_id": device_id,
        "hospital": patient_data['hospital'],
        "encrypted": True,
        "ciphertext": encoded['ciphertext'],  # ← ENCRYPTED
        "nonce": encoded['nonce']
    }
```

**Data State**: ✅ **ENCRYPTED** (Ascon-128)

---

### **Step 4: Simulator Publishes to MQTT Broker**
**File**: `services/patient_simulator/send_data_encrypted.py` (Lines 312-325)

```python
    # 6. Publish ENCRYPTED payload via MQTT
    mqtt_client.publish(topic, json.dumps(mqtt_payload), qos=1)
    # Topic: "hospital/1/ward/1/patient/1"
```

**Transport**: MQTT over TLS (port 8883) - double encryption (TLS + Ascon)

---

### **Step 5: Main Host Receives & Decrypts**
**File**: `services/main_host/app_encrypted.py` (Lines 136-230)

```python
def on_mqtt_message(client, userdata, msg):
    # 7. Receive MQTT message
    mqtt_payload = json.loads(msg.payload)
    
    if mqtt_payload.get('encrypted'):
        # 8. DECRYPT with Ascon-128
        device_key = key_manager.get_device_key(device_id)
        crypto = AsconCrypto(device_key)
        vitals, decryption_time_ms = crypto.decrypt(ciphertext, nonce)
        
        # vitals = {heart_rate: 78, spo2: 96, anomaly_score: 0.23, ...}
        # ← NOW PLAIN TEXT AGAIN ✅
    
    # 9. Process vitals (store in RAM, update metrics)
    process_patient_data(vitals, hospital, dept, ward, patient_id)
```

**Data State**: ❌ **DECRYPTED (back to plain text)** - stored in RAM

**CRITICAL**: Main Host does **NOT** call ML service - anomaly score already included!

---

### **Step 6: Main Host Stores in RAM (NOT Database)**
**File**: `services/main_host/app_encrypted.py` (Lines 102-127)

```python
def process_patient_data(vitals, hospital, dept, ward, patient_id):
    # 10. Update Prometheus metrics (in-memory)
    metrics['heart_rate'].labels(...).set(vitals['heart_rate'])
    metrics['anomaly_score'].labels(...).set(vitals['anomaly_score'])
    
    # 11. Store in RAM dictionary (NOT database ❌)
    patient_key = f"{hospital}|{dept}|{ward}|{patient_id}"
    patient_data_store[patient_key].append(vitals)
    
    # Keep only latest 100 readings
    if len(patient_data_store[patient_key]) > 100:
        patient_data_store[patient_key] = patient_data_store[patient_key][-100:]
```

**Storage**: 
- ✅ RAM (Python dictionary)
- ✅ Prometheus metrics
- ❌ **NO database storage!**

---

### **Step 7: Data Displayed on Frontend**
**File**: `services/web_dashboard/static/js/dashboard.js`

```javascript
// 12. Frontend polls Main Host API
setInterval(fetchDashboardData, 10000);  // Every 10 seconds

function fetchDashboardData() {
    fetch('/api/metrics')  // Calls web_dashboard
        .then(response => response.json())
        .then(data => updateDashboardWidgets(data));
}
```

**File**: `services/web_dashboard/app.py` (Lines 85-97)

```python
@app.route('/api/metrics')
def get_metrics():
    # 13. Web dashboard queries Main Host
    response = requests.get(f"{MAIN_HOST_URL}/api/dashboard-data")
    return response.json()
```

**File**: `services/main_host/app_encrypted.py` (Lines 428-435)

```python
@app.route('/api/dashboard-data')
def get_dashboard_data():
    # 14. Return data from RAM (NOT database)
    result = {}
    for key, data_list in patient_data_store.items():
        result[key] = data_list[-1]  # Latest reading
    return jsonify({"data": result})
```

**Data State**: ❌ Plain text (served over HTTP within Docker network)

---

## **🚨 CRITICAL FINDINGS**

### **1. NO Automatic Database Storage**

```
❌ Real-time vitals are NEVER stored in the database!
✅ They only exist in:
   - Main Host RAM (lost on restart)
   - Prometheus time-series (for metrics/alerts)
   - Grafana dashboards (queries Prometheus)
```

**Evidence**: `services/main_host/app_encrypted.py` has:
- ❌ NO SQLAlchemy imports
- ❌ NO database connection
- ❌ NO `db.session.add()` calls
- ❌ NO PatientVitalSign inserts

---

### **2. Database Table Exists But Unused**

**File**: `services/web_dashboard/models/patient.py`

```python
class PatientVitalSign(db.Model):
    __tablename__ = 'patient_vital_signs'
    # Fields: heart_rate, spo2, bp_systolic, etc.
```

**Usage**: Only for **MANUAL entry** via web UI:

**File**: `services/web_dashboard/routes/patients.py` (Lines 122-150)

```python
@patients.route('/<int:patient_id>/vitals/add', methods=['POST'])
@login_required
def add_vitals(patient_id):
    # User manually enters vitals in web form
    new_vitals = PatientVitalSign(
        heart_rate=request.form.get('heart_rate'),
        spo2=request.form.get('spo2'),
        # ... manual input
    )
    db.session.add(new_vitals)  # ← Only manual saves
    db.session.commit()
```

---

### **3. ML Service Communication is Unencrypted**

```
Patient Simulator → ML Service: ❌ Plain HTTP (within Docker)
   POST http://ml_service:6000/predict
   Body: {"heart_rate": 78, "spo2": 96, ...}  # Plain JSON
```

**Why it's "safe"**: Communication happens inside Docker network, not over internet

---

## **📊 COMPLETE DATA FLOW DIAGRAM**

```
┌────────────────────────────────────────────────────────────────┐
│ 1. Patient Simulator                                           │
│    ↓ Reads Excel (baseline vitals)                            │
│    ↓ Generates new values (baseline + random)                 │
└────────────────────┬───────────────────────────────────────────┘
                     │ ❌ PLAIN HTTP
                     ↓
┌────────────────────────────────────────────────────────────────┐
│ 2. ML Service                                                  │
│    ↓ Receives PLAIN vitals                                    │
│    ↓ Returns anomaly_score: 0.23                              │
└────────────────────┬───────────────────────────────────────────┘
                     │ ❌ PLAIN (returned to simulator)
                     ↓
┌────────────────────────────────────────────────────────────────┐
│ 3. Patient Simulator (continued)                               │
│    ↓ Adds anomaly_score to vitals                             │
│    ↓ ENCRYPTS with Ascon-128 ✅                               │
│    ↓ Publishes to MQTT Broker                                 │
└────────────────────┬───────────────────────────────────────────┘
                     │ ✅ ENCRYPTED (TLS + Ascon)
                     ↓ MQTT Topic: hospital/1/ward/1/patient/1
┌────────────────────────────────────────────────────────────────┐
│ 4. MQTT Broker (Mosquitto)                                    │
│    ↓ Port 8883 (TLS)                                          │
└────────────────────┬───────────────────────────────────────────┘
                     │ ✅ ENCRYPTED
                     ↓ Subscribed to: hospital/#
┌────────────────────────────────────────────────────────────────┐
│ 5. Main Host Backend                                          │
│    ↓ DECRYPTS with Ascon-128 ✅                               │
│    ↓ Vitals now PLAIN in memory                               │
│    ↓ Stores in RAM dict (patient_data_store)                  │
│    ↓ Updates Prometheus Gauges                                │
│    ↓ ❌ DOES NOT call ML service                              │
│    ↓ ❌ DOES NOT save to database                             │
└────────┬─────────────────┬─────────────────────────────────────┘
         │                 │
         ↓                 ↓
    /metrics          /api/dashboard-data
         │                 │
         ↓                 ↓
    Prometheus       Web Dashboard API
         │                 │
         ↓                 ↓
      Grafana        Frontend (JavaScript)


SEPARATE SYSTEM (Not connected to real-time flow):
┌────────────────────────────────────────────────────────────────┐
│ SQLite Database (web_dashboard/instance/healthcare.db)        │
│   - patients (demographics)                                    │
│   - patient_vital_signs (❌ EMPTY - only manual entry)        │
│   - users (staff accounts)                                     │
└────────────────────────────────────────────────────────────────┘
```

---

## **🔐 ENCRYPTION STATE AT EACH STEP**

| Step | Location | Data State | Why? |
|------|----------|------------|------|
| 1 | Simulator generates | ❌ Plain | Fresh data creation |
| 2 | Simulator → ML | ❌ Plain HTTP | Within Docker network |
| 3 | ML → Simulator | ❌ Plain HTTP | Within Docker network |
| 4 | Simulator encrypts | ✅ Encrypted (Ascon) | Before leaving simulator |
| 5 | MQTT transport | ✅ Double encrypted (TLS + Ascon) | Over network |
| 6 | Main Host receives | ✅ Encrypted | Not yet processed |
| 7 | Main Host decrypts | ❌ Plain (in RAM) | For processing |
| 8 | Prometheus metrics | ❌ Plain | Monitoring system |
| 9 | Grafana dashboard | ❌ Plain | Visualization |
| 10 | Web frontend | ❌ Plain HTTP | Within Docker network |

---

## **❌ PROBLEMS IDENTIFIED**

### **Problem 1: No Persistent Storage of Real-Time Vitals**
- Real-time vitals stored ONLY in RAM
- Lost on container restart
- Cannot query historical data beyond Prometheus retention

### **Problem 2: Database Table Unused**
- `PatientVitalSign` table exists but never populated automatically
- Only manual web form entry works

### **Problem 3: Internal HTTP Communication Unencrypted**
- Simulator ↔ ML Service: Plain HTTP
- Web Dashboard ↔ Main Host: Plain HTTP
- **Acceptable** if Docker network is isolated
- **Risk** if containers compromised

---

## **✅ RECOMMENDATIONS**

### **1. Auto-Save Real-Time Vitals to Database**

Add to `services/main_host/app_encrypted.py`:

```python
# Import database dependencies
from database_client import DatabaseClient

db_client = DatabaseClient('http://web_dashboard:5000')

def process_patient_data(vitals, hospital, dept, ward, patient_id):
    # Existing code...
    metrics['heart_rate'].labels(...).set(vitals['heart_rate'])
    
    # NEW: Save to database via API
    db_client.save_vitals({
        'patient_id': patient_id,
        'heart_rate': vitals['heart_rate'],
        'spo2': vitals['spo2'],
        # ... all vitals
        'recorded_at': datetime.utcnow()
    })
```

### **2. Add API Endpoint in Web Dashboard**

Add to `services/web_dashboard/routes/patients.py`:

```python
@patients.route('/api/vitals/save', methods=['POST'])
def save_vitals_api():
    """API endpoint for automated vital sign storage"""
    data = request.get_json()
    
    new_vitals = PatientVitalSign(
        patient_id=data['patient_id'],
        heart_rate=data['heart_rate'],
        spo2=data['spo2'],
        # ... 
        recorded_at=datetime.utcnow()
    )
    
    db.session.add(new_vitals)
    db.session.commit()
    
    return jsonify({"status": "success"})
```

### **3. Encrypt Internal HTTP Communications**

Add JWT tokens or API keys for service-to-service auth:

```python
# services/main_host/app_encrypted.py
headers = {
    'Authorization': f'Bearer {SERVICE_API_KEY}',
    'Content-Type': 'application/json'
}
response = requests.post(url, json=data, headers=headers)
```

---

## **SUMMARY**

| Component | Current State | Should Store? |
|-----------|--------------|---------------|
| Main Host RAM | ✅ Stores latest 100 | Temporary only |
| Prometheus | ✅ Time-series metrics | ✅ Already doing |
| SQLite Database | ❌ NOT storing vitals | ✅ **SHOULD ADD** |
| Grafana | ✅ Visualizing | Read-only |

**Bottom Line**: Real-time vitals are NOT persisted to database - they should be!
