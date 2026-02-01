# Repository Structure - Clean & Organized

## ✅ Current Clean Structure

```
Iot_new/
├── .env                          # Local environment configuration
├── .env.example                  # Template for environment setup
├── docker-compose.yml            # Main orchestration file
├── README.md                     # Project overview
├── QUICKSTART.md                 # Quick start guide
├── LOCAL_DEPLOYMENT.md           # Local deployment details
├── HARDWARE_INTEGRATION.md       # Hardware sensor integration guide
├── LICENSE                       # MIT License
│
├── config/                       # ⭐ Single source of truth for configs
│   ├── alertmanager/
│   │   └── alertmanager.yml      # Alert routing configuration
│   ├── prometheus/
│   │   ├── prometheus.yml        # Prometheus scraping config
│   │   └── alert.rules.yml       # Alert rules definition
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   └── patient_vitals.json
│   │   └── provisioning/
│   │       ├── dashboards/
│   │       │   └── dashboards.yaml
│   │       └── datasources/
│   │           └── datasources.yaml
│   └── environment/
│       ├── development.env
│       └── production.env
│
├── services/                     # Application services
│   ├── main_host/               # Data collection API
│   ├── ml_service/              # Anomaly detection
│   ├── patient_simulator/       # Test data generator
│   └── web_dashboard/           # Web UI & database
│
├── data/                        # Data storage
│   └── patient_samples/
│
├── scripts/                     # Utility scripts
│   └── setup.sh
│
├── docs/                        # Documentation
│   ├── API.md
│   ├── DEPLOYMENT_DIAGRAM_GUIDE.md
│   ├── deployment/
│   └── Images/
│
├── AWS_Documentation_Archive/   # Archived AWS files
│   ├── AWS_DEPLOYMENT_GUIDE.md
│   ├── docker-compose-with-rds.yml
│   └── ... (12 files)
│
└── Documentation_Archive/       # Archived academic reports
    ├── DA2_Report.md
    ├── DA3_Comprehensive_Report.md
    └── ... (other reports)
```

---

## 🔧 Configuration Files Location

All configuration files are now centralized in the `config/` directory:

| Service | Configuration | Location |
|---------|--------------|----------|
| **Prometheus** | Main config | `config/prometheus/prometheus.yml` |
| | Alert rules | `config/prometheus/alert.rules.yml` |
| **AlertManager** | Routing | `config/alertmanager/alertmanager.yml` |
| **Grafana** | Dashboards | `config/grafana/dashboards/` |
| | Dashboard provisioning | `config/grafana/provisioning/dashboards/` |
| | Datasource provisioning | `config/grafana/provisioning/datasources/` |
| **Environment** | Development | `config/environment/development.env` |
| | Production | `config/environment/production.env` |

---

## 🗑️ What Was Removed

### Duplicate Files (Root → config/)
- ❌ `alertmanager/` → ✅ `config/alertmanager/`
- ❌ `dashboards.yaml` → ✅ `config/grafana/provisioning/dashboards/`
- ❌ `datasources.yaml` → ✅ `config/grafana/provisioning/datasources/`
- ❌ `grafana/` → ✅ `config/grafana/`

### Empty Folders
- ❌ `alert.rules.yml/` (empty folder, actual file in config/)
- ❌ `prometheus.yml/` (empty folder, actual file in config/)

### Unused Files
- ❌ `grafana_security.ini` (unused)
- ❌ `database_init.sql` (unused, using init_database.py instead)
- ❌ `alertmanager.ymlZone.Identifier` (download artifact)

### Archived Academic Files
Moved to `Documentation_Archive/`:
- DA2_Report.md
- DA3_Comprehensive_Report.md
- DA3_Deployment_Evidence.md
- DA3_PowerPoint_Outline.md
- DA3_Quick_Action_Plan.md
- DA3_Social_Media_Strategy.md
- DA3_Submission_Checklist.md
- SOLID_Principles_Report.md
- MANUAL_STEPS.md
- PATIENT_DATA_INTEGRATION.md
- ML_SERVICE_UPDATE_SUMMARY.md

---

## 📋 Docker Compose Volume Mounts

All volume mounts now correctly point to `config/`:

```yaml
prometheus:
  volumes:
    - ./config/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    - ./config/prometheus/alert.rules.yml:/etc/prometheus/alert.rules.yml

alertmanager:
  volumes:
    - ./config/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml

grafana:
  volumes:
    - ./config/grafana/dashboards:/etc/grafana/dashboards
    - ./config/grafana/provisioning:/etc/grafana/provisioning
```

---

## ✅ Benefits of Clean Structure

1. **Single Source of Truth**: All configs in `config/` folder
2. **No Duplicates**: Eliminated confusion from multiple versions
3. **Clear Organization**: Logical folder structure
4. **Easy Maintenance**: One place to update configurations
5. **Version Control**: Cleaner git history
6. **Reduced Clutter**: Removed unused files

---

## 🔍 How to Find Configurations

**Need to update Prometheus scraping?**
→ `config/prometheus/prometheus.yml`

**Need to change alert rules?**
→ `config/prometheus/alert.rules.yml`

**Need to configure alert emails?**
→ `config/alertmanager/alertmanager.yml`

**Need to add Grafana dashboards?**
→ `config/grafana/dashboards/`

**Need to configure Grafana datasources?**
→ `config/grafana/provisioning/datasources/datasources.yaml`

---

## 📝 Root Directory Files (Essential Only)

| File | Purpose |
|------|---------|
| `.env` | Local environment variables |
| `.env.example` | Template for new users |
| `docker-compose.yml` | Container orchestration |
| `README.md` | Project documentation |
| `QUICKSTART.md` | Quick start guide |
| `LOCAL_DEPLOYMENT.md` | Deployment details |
| `HARDWARE_INTEGRATION.md` | Hardware setup guide |
| `LICENSE` | MIT License |

---

## 🎯 Next Steps

1. **Start the system:**
   ```bash
   docker-compose up --build
   ```

2. **Modify configurations:**
   - All configs are in `config/` folder
   - Edit files there, restart affected containers

3. **Add new dashboards:**
   - Place JSON files in `config/grafana/dashboards/`
   - Grafana will auto-load them

4. **Update alert rules:**
   - Edit `config/prometheus/alert.rules.yml`
   - Restart Prometheus: `docker-compose restart prometheus`

---

## 🔄 Restoring Old Files (If Needed)

If you need to restore any archived files:

**AWS files:**
```bash
# In AWS_Documentation_Archive/
cp docker-compose-with-rds.yml ../
```

**Academic reports:**
```bash
# In Documentation_Archive/
cp DA3_Comprehensive_Report.md ../
```

---

## ✨ Clean, Organized, Ready!

Your repository is now clean, organized, and follows best practices:
- ✅ No duplicate configurations
- ✅ Clear folder structure
- ✅ Single source of truth
- ✅ Easy to maintain
- ✅ Ready for hardware integration
