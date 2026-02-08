# Healthcare IoT Monitoring System with Layered Security

A real-time patient monitoring system built with Docker, Prometheus, Grafana, and machine learning for anomaly detection in healthcare environments. Features **defense-in-depth security architecture** with TLS encryption, Ascon-128 authenticated encryption, per-device key management, JWT service authentication, and SQLCipher database encryption.

## 🔒 Security Features

This system implements a **5-phase layered security architecture** to protect sensitive patient health information:

- **Phase 1: TLS 1.2 Transport Encryption** - Secure MQTT communication with certificate-based authentication
- **Phase 2: Ascon-128 Payload Encryption** - Authenticated encryption for all patient vitals data
- **Phase 3: Per-Device Key Management** - Unique encryption keys for each patient device
- **Phase 4: JWT Service Authentication** - Token-based authentication between microservices
- **Phase 4: SQLCipher Database Encryption** - Encrypted SQLite database for patient records
- **Phase 5: Complete Docker Deployment** - Containerized architecture for production use

## 📋 What This Does

This system monitors patient vital signs (heart rate, SpO2, blood pressure, temperature, etc.) and provides:

- Real-time visualization through Grafana dashboards
- Automated alerting for abnormal vital signs
- Machine learning-based anomaly detection
- Secure web dashboard for patient management (encrypted database)
- End-to-end encryption for all patient data
- Ready for hardware sensor integration (Arduino, ESP32, Raspberry Pi)

## 🏗️ Architecture

The system consists of microservices running in Docker containers with integrated security:

- **MQTT Broker**: Secure message broker with TLS 1.2 encryption (port 8883)
- **Main Host**: Collects and decrypts patient data, exposes metrics to Prometheus
- **Web Dashboard**: Flask-based UI with SQLCipher encrypted database for patient management
- **ML Service**: Analyzes vitals and detects anomalies using machine learning (JWT authenticated)
- **Patient Simulator**: Generates encrypted patient data with Ascon-128 encryption
- **Prometheus**: Scrapes and stores metrics
- **Grafana**: Visualizes data in real-time dashboards
- **AlertManager**: Sends alerts when vital signs exceed thresholds

### Security Architecture

All patient data flows through multiple security layers:

1. **Device Layer**: Each patient device has a unique 128-bit encryption key
2. **Transport Layer**: TLS 1.2 encrypted MQTT communication with certificates
3. **Payload Layer**: Ascon-128 authenticated encryption for all vital signs data
4. **Service Layer**: JWT tokens authenticate inter-service communication
5. **Storage Layer**: SQLCipher encrypts the patient database at rest

### System Architecture Diagram

```mermaid
graph TB
    subgraph "External Users"
        User[👤 Clinician/Admin]
    end
    
    subgraph "Docker Environment"
        subgraph "Frontend Layer"
            WebDash[🌐 Web Dashboard<br/>Flask + SQLite<br/>:5000]
        end
        
        subgraph "Application Layer"
            MainHost[📊 Main Host<br/>Data Collection API<br/>:8000]
            MLService[🤖 ML Service<br/>Anomaly Detection<br/>:6000]
            PatientSim[👥 Patient Simulator<br/>Data Generator<br/>Python]
        end
        
        subgraph "Monitoring Layer"
            Prometheus[📈 Prometheus<br/>Metrics Storage<br/>:9090]
            Grafana[📉 Grafana<br/>Visualization<br/>:3000]
            AlertMgr[🔔 AlertManager<br/>Alert Routing<br/>:9093]
        end
    end
    
    User -->|HTTP :5000| WebDash
    WebDash -->|API Calls| MainHost
    WebDash -->|Embed Dashboards| Grafana
    PatientSim -->|POST /track| MainHost
    PatientSim -->|POST /predict| MLService
    MainHost -->|Anomaly Check| MLService
    Prometheus -->|Scrape /metrics| MainHost
    Grafana -->|Query Metrics| Prometheus
    Prometheus -->|Fire Alerts| AlertMgr
    
    style User fill:#e1f5ff
    style WebDash fill:#4CAF50,color:#fff
    style MainHost fill:#2196F3,color:#fff
    style MLService fill:#9C27B0,color:#fff
    style PatientSim fill:#FF9800,color:#fff
    style Prometheus fill:#E91E63,color:#fff
    style Grafana fill:#F44336,color:#fff
    style AlertMgr fill:#FF5722,color:#fff
```

### Architecture Images

For additional visual reference, see the following architecture diagrams:

- **System Architecture**: ![Architecture Diagram](docs/Images/architecture.jpg)
- **Deployment View**: ![Deployment Diagram](docs/Images/Picture1.jpg)
- **Component Overview**: ![Component Diagram](docs/Images/Picture2.jpg)
- **System Design**: ![Design Overview](docs/Images/image.png)

For detailed deployment architecture and PlantUML diagrams, refer to [DEPLOYMENT_DIAGRAM_GUIDE.md](docs/DEPLOYMENT_DIAGRAM_GUIDE.md).

### 📊 High-Level Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PATIENT IoT DEVICE (ESP32)                          │
│                    Simulated by: patient_simulator                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ Raw vitals: {heart_rate: 75, bp: 120/80...}
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: Per-Device Key Management                                         │
│  • Load unique key for patient 1_1 from device_keys.json                   │
│  • Key: 128-bit unique to this patient                                     │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: Ascon-128 Authenticated Encryption                                │
│  • Encrypt payload with Ascon-128                                           │
│  • Generate 128-bit nonce (random, unique per message)                     │
│  • Result: {ciphertext: "a4f3d2...", nonce: "8b7c...", tag: "9e2f..."}    │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: TLS 1.2 Transport Layer                                           │
│  • Wrap encrypted payload in TLS connection                                 │
│  • MQTT over TLS (port 8883)                                               │
│  • Topic: hospital/1/ward/1/patient/1                                      │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │   MQTT BROKER        │
                      │   (mosquitto:8883)   │
                      │   TLS Termination    │
                      └──────────┬───────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MAIN HOST                                         │
│                        (Decryption Server)                                   │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: Ascon-128 Decryption                                              │
│  • Receive encrypted message from MQTT                                      │
│  • Load patient 1_1's key from device_keys.json                            │
│  • Decrypt: Ascon.decrypt(ciphertext, key, nonce)                          │
│  • Verify authentication tag (ensures integrity)                            │
│  • Result: {heart_rate: 75, bp_sys: 120, bp_dia: 80...}                   │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ Decrypted vitals
                                 ▼
                    ┌────────────────────────────┐
                    │  ML Service Request        │
                    │  (Anomaly Detection)       │
                    └────────────┬───────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 4a: JWT Authentication                                               │
│  • patient_simulator generates JWT token                                    │
│  • Token payload: {service: "patient_simulator", exp: 24h}                 │
│  • Sign with HS256 using JWT_SECRET_KEY                                     │
│  • Add header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs...                │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ML SERVICE (port 6000)                               │
│                      @require_service_auth                                   │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  JWT Validation                                                              │
│  • Extract token from Authorization header                                  │
│  • Verify signature with JWT_SECRET_KEY                                     │
│  • Check expiration time                                                    │
│  • Set request.service_name = "patient_simulator"                          │
│  • Set request.authenticated = True                                         │
│  • If failed → Return 401 Unauthorized                                      │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ ✅ Authenticated
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Anomaly Detection (IsolationForest)                                        │
│  • Extract features: [75, 120, 80, 16, 98, 40, 21, 37.0, 7.5, 1.8, 95]    │
│  • Calculate anomaly score: 0.54 (normalized)                              │
│  • Return: {normalized_score: 0.54}                                        │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ Score: 0.54
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACK TO MAIN HOST                                    │
│  • Combine decrypted vitals + anomaly score                                 │
│  • Forward to web_dashboard API                                             │
│  • Store in database                                                        │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WEB DASHBOARD (port 5000)                               │
│                         Flask Application                                    │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 4b: SQLCipher Database Encryption                                    │
│  • Open connection to hospital.db                                           │
│  • Execute: PRAGMA key = 'DB_ENCRYPTION_KEY'                               │
│  • Execute: PRAGMA cipher_page_size = 4096                                  │
│  • SQLCipher transparently encrypts/decrypts with AES-256                  │
│  • INSERT patient vitals + anomaly score                                    │
│  • Data written to disk in encrypted format                                 │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────────┐
                    │   DASHBOARD UI             │
                    │   (Browser: localhost:5000)│
                    │   • Real-time vitals       │
                    │   • Anomaly scores         │
                    │   • Patient list           │
                    │   • Analytics charts       │
                    └────────────────────────────┘
```

### Data Flow Diagram

```mermaid
sequenceDiagram
    participant PS as Patient Simulator
    participant MH as Main Host
    participant ML as ML Service
    participant P as Prometheus
    participant G as Grafana
    participant WD as Web Dashboard
    participant AM as AlertManager
    
    Note over PS: Read Excel Data
    PS->>MH: POST /track (vitals data)
    MH->>ML: POST /predict (check anomaly)
    ML-->>MH: Anomaly score
    MH-->>PS: 200 OK
    
    loop Every 15s
        P->>MH: Scrape /metrics
        MH-->>P: Patient metrics
    end
    
    P->>P: Evaluate alert rules
    
    alt Threshold Exceeded
        P->>AM: Send Alert
        AM->>AM: Route notification
    end
    
    loop Dashboard Refresh
        WD->>MH: GET /api/dashboard-data
        MH-->>WD: Latest vitals
        WD->>G: Embed dashboard
        G->>P: Query metrics
        P-->>G: Time-series data
        G-->>WD: Rendered charts
    end
```

## 🚀 How to Run

### Prerequisites

- Docker Desktop installed and running
- Git (to clone the repository)

### Quick Start

1. **Clone and navigate to the project**

   ```bash
   git clone https://github.com/KMohnishM/CN_Project.git
   cd CN_Project
   ```

2. **Configure security settings** (Optional - defaults are provided)

   Edit `config/environment/development.env` to customize:
   
   ```bash
   # Encryption Settings
   ENABLE_ENCRYPTION=true
   ENABLE_SERVICE_AUTH=true
   ENABLE_DB_ENCRYPTION=true
   
   # Security Keys (CHANGE IN PRODUCTION!)
   JWT_SECRET_KEY=your-256-bit-secret-key
   DB_ENCRYPTION_KEY=your-database-encryption-key
   
   # TLS Configuration
   USE_TLS=true
   MQTT_BROKER_HOST=mqtt_broker
   MQTT_BROKER_PORT=8883
   ```

3. **Start the system**

   ```bash
   docker-compose up --build
   ```

   Wait 2-3 minutes for all services to start. You'll see:
   - 🔐 Encrypted messages being published by patient simulator
   - 🔓 Decryption logs in main_host
   - ✅ "Database encryption ENABLED" in web_dashboard logs

4. **Access the dashboards**

   - **Web Dashboard**: http://localhost:5000 (login: admin/admin)
   - **Grafana**: http://localhost:3001 (login: admin/admin)
   - **Prometheus**: http://localhost:9090
   - **AlertManager**: http://localhost:9093

5. **Verify security is active**

   ```bash
   # Check encryption status
   docker logs main_host | grep "Decrypted vitals"
   
   # Verify JWT authentication
   docker exec ml_service python -c "import sys; sys.path.insert(0, '/app/common'); from service_auth import generate_service_token; print(generate_service_token('test'))"
   
   # Confirm database encryption
   docker logs web_dashboard | grep "Database encryption ENABLED"
   ```

6. **Stop the system**

   ```bash
   docker-compose down
   ```

That's it! The system will start generating encrypted patient data automatically with all security layers active.

## 🖥️ Web UI Navigation Flow

The web dashboard provides an intuitive interface for monitoring and managing patient data:

```mermaid
graph TD
    Start([User Visits<br/>localhost:5000]) --> Login{Authenticated?}
    
    Login -->|No| LoginPage[🔐 Login Page<br/>/auth/login]
    LoginPage -->|Success| Dashboard
    Login -->|Yes| Dashboard[📊 Dashboard<br/>Real-time Overview]
    
    Dashboard --> Nav{Navigation Menu}
    
    Nav -->|View Charts| Monitoring[📈 Monitoring Page<br/>Real-time Grafana Charts<br/>Patient Vitals Graphs]
    Nav -->|Patient Data| PatientList[👥 Patient List<br/>View All Patients]
    Nav -->|Analytics| Analytics[📉 Analytics Page<br/>Trends & Statistics]
    Nav -->|Profile| Profile[👤 User Profile<br/>Account Settings]
    
    PatientList -->|Select| PatientView[🔍 Patient Details<br/>View Specific Patient<br/>Vital History]
    PatientList -->|Add New| AddPatient[➕ Add Patient Form<br/>Register New Patient]
    
    PatientView -->|Edit| EditPatient[✏️ Edit Patient<br/>Update Information]
    
    Monitoring -->|Live Data| GrafanaEmbed[📊 Embedded Grafana<br/>Heart Rate, SpO2, BP<br/>Temperature, Resp Rate]
    
    Analytics -->|View Stats| Charts[📈 Statistical Charts<br/>Patient Trends<br/>Anomaly Reports]
    
    Dashboard -->|Alerts| AlertView[🔔 Alert Notifications<br/>Threshold Violations<br/>Critical Conditions]
    
    Nav -->|Logout| Logout[🚪 Logout]
    Logout --> LoginPage
    
    style Start fill:#4CAF50,color:#fff
    style Dashboard fill:#2196F3,color:#fff
    style Monitoring fill:#FF9800,color:#fff
    style PatientList fill:#9C27B0,color:#fff
    style Analytics fill:#E91E63,color:#fff
    style LoginPage fill:#607D8B,color:#fff
    style GrafanaEmbed fill:#F44336,color:#fff
    style AlertView fill:#FF5722,color:#fff
```

### Key Features by Page:

- **Dashboard** (`/`): Real-time patient status overview, recent alerts, system health
- **Monitoring** (`/monitoring`): Live Grafana charts embedded showing vital signs trends
- **Patients** (`/patients`): 
  - List all patients with search/filter
  - Add new patients with medical information
  - View individual patient details and vital history
  - Edit patient information
- **Analytics** (`/analytics`): Statistical analysis, anomaly detection reports
- **User Profile** (`/profile`): Account management, password change, role information
- **Admin Features**: Threshold configuration, user management (admin role only)

## 📁 Project Structure

```
├── services/           # Application microservices
│   ├── main_host/     # Data collection API with decryption
│   ├── web_dashboard/ # Patient management UI (encrypted DB)
│   ├── ml_service/    # Anomaly detection (JWT auth)
│   ├── patient_simulator/  # Encrypted data generator
│   └── common/        # Shared utilities (crypto, auth)
├── config/            # Configuration files
│   ├── environment/   # Security settings (JWT, encryption keys)
│   ├── prometheus/    # Metrics & alerting rules
│   ├── grafana/       # Dashboards & datasources
│   ├── alertmanager/  # Alert routing
│   └── mosquitto/     # MQTT TLS certificates
├── data/
│   └── keys/          # Per-device encryption keys
└── docker-compose.yml # Container orchestration
```

## 🔐 Security Implementation Details

### Phase 1: TLS 1.2 Transport Layer
- MQTT broker configured with TLS certificates
- Client and server certificate authentication
- Secure port 8883 (vs unencrypted 1883)

### Phase 2: Ascon-128 Authenticated Encryption
- Lightweight authenticated encryption cipher
- 128-bit keys, 128-bit nonces for each message
- Protection against tampering and replay attacks
- Implementation in `services/common/crypto_utils.py`

### Phase 3: Per-Device Key Management
- Each patient device has unique encryption key
- Keys stored in `data/keys/` directory
- Automatic key provisioning for new devices
- Key rotation support

### Phase 4: JWT Service Authentication
- HS256 algorithm with 24-hour token expiry
- Service-to-service authentication
- Implementation in `services/common/service_auth.py`
- Environment-based secret key management

### Phase 4: SQLCipher Database Encryption
- Encrypted SQLite database using SQLCipher
- AES-256 encryption for patient records
- Transparent encryption/decryption
- Implementation in `services/web_dashboard/database_encrypted.py`

### Phase 5: Docker Deployment
- All 8 services containerized and orchestrated
- Volume mounts for certificates and keys
- Environment-based configuration
- Production-ready architecture
