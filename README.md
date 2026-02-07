# Healthcare IoT Monitoring System

A real-time patient monitoring system built with Docker, Prometheus, Grafana, and machine learning for anomaly detection in healthcare environments.

## 📋 What This Does

This system monitors patient vital signs (heart rate, SpO2, blood pressure, temperature, etc.) and provides:

- Real-time visualization through Grafana dashboards
- Automated alerting for abnormal vital signs
- Machine learning-based anomaly detection
- Web dashboard for patient management
- Ready for hardware sensor integration (Arduino, ESP32, Raspberry Pi)

## 🏗️ Architecture

The system consists of microservices running in Docker containers:

- **Main Host**: Collects patient data and exposes metrics to Prometheus
- **Web Dashboard**: Flask-based UI for patient management (SQLite database)
- **ML Service**: Analyzes vitals and detects anomalies using machine learning
- **Patient Simulator**: Generates realistic patient data for testing
- **Prometheus**: Scrapes and stores metrics
- **Grafana**: Visualizes data in real-time dashboards
- **AlertManager**: Sends alerts when vital signs exceed thresholds

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
2. **Start the system**

   ```bash
   docker-compose up --build
   ```

   Wait 2-3 minutes for all services to start.
3. **Access the dashboards**

   - **Web Dashboard**: http://localhost:5000 (login: admin/admin)
   - **Grafana**: http://localhost:3001 (login: admin/admin)
   - **Prometheus**: http://localhost:9090
   - **AlertManager**: http://localhost:9093
4. **Stop the system**

   ```bash
   docker-compose down
   ```

That's it! The system will start generating simulated patient data automatically.

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
│   ├── main_host/     # Data collection API
│   ├── web_dashboard/ # Patient management UI
│   ├── ml_service/    # Anomaly detection
│   └── patient_simulator/
├── config/            # Configuration files
│   ├── prometheus/    # Metrics & alerting rules
│   ├── grafana/       # Dashboards & datasources
│   └── alertmanager/  # Alert routing
└── docker-compose.yml # Container orchestration
```
