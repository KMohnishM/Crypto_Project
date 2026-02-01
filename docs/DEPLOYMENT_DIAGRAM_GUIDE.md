# Deployment Diagram and Architecture Guide

This document explains the deployment architecture for the Healthcare Monitoring System and provides a PlantUML deployment diagram. It also includes step-by-step instructions to recreate the same diagram in StarUML.

## 📐 PlantUML Deployment Diagram

The deployment diagram is available at `docs/deployment/healthcare-deployment.puml`.
You can render it with any PlantUML tool or VS Code PlantUML extension.

Key elements in the diagram:
- AWS Account → VPC → Public Subnet (ALB + EC2 Docker Host)
- Private DB Subnet Group → RDS MySQL
- Docker containers on EC2: web_dashboard, main_host, ml_service, patient_simulator, Prometheus, Grafana, Alertmanager
- Data flows: user ↔ ALB ↔ web_dashboard; web_dashboard ↔ main_host / Grafana / RDS; patient_simulator ↔ main_host / ml_service; Prometheus ↔ main_host; Grafana ↔ Prometheus; Prometheus ↔ Alertmanager

## 🗺️ High-Level Architecture

- Users access the system via the **Application Load Balancer (ALB)** over HTTPS (443).
- The **web_dashboard (Flask)** runs on EC2 inside Docker, serving the UI and embedding Grafana dashboards.
- The **main_host (Flask)** receives live vitals from the patient simulator and exposes `/metrics` for Prometheus scraping and `/api/*` for the dashboard.
- The **ml_service** provides anomaly scores via `/predict`.
- **Prometheus** scrapes `main_host` for metrics. **Grafana** queries Prometheus and is embedded into the dashboard.
- **Alertmanager** receives alerts from Prometheus.
- **RDS MySQL** stores persistent data (patients, users). Access is restricted to the app's security group.

## 🔐 Security & Networking

- **TLS everywhere**: ALB terminates HTTPS; internal traffic restricted by Security Groups.
- **Least privilege** inbound rules:
  - ALB → web_dashboard: 443 → 5000
  - EC2 internal: 8000 (main_host), 6000 (ml_service), 9090 (prometheus), 9093 (alertmanager)
  - RDS 3306 only from EC2/ECS security group
- **Secrets** via environment variables (prefer AWS Secrets Manager in production).
- **Grafana embedding** enabled; restrict access and avoid anonymous access in production.

## 🔄 Data Flows

1. Patient simulator reads Excel, generates vitals → POSTs to main_host `/track`.
2. main_host exposes latest vitals via `/api/dashboard-data` for the web_dashboard and `/metrics` for Prometheus.
3. ml_service returns anomaly scores to patient_simulator.
4. Prometheus scrapes main_host `/metrics`; Grafana queries Prometheus.
5. web_dashboard embeds Grafana dashboards and calls main_host APIs.
6. web_dashboard persists users/patients to RDS via SQLAlchemy.

## 🧩 StarUML: Recreate the Deployment Diagram (Step-by-Step)

1. Create a new **Deployment Diagram**.
2. Add a **Node** named `AWS Account`.
3. Inside it, add a **Node** named `VPC (10.0.0.0/16)`.
4. Inside VPC, add:
   - **Node**: `Public Subnet (10.0.1.0/24)`
   - **Node**: `DB Subnet Group (Private)`
5. In `Public Subnet`, add:
   - **Node**: `ALB (HTTPS 443)`
   - **Node**: `EC2: Docker Host`
6. Inside `EC2: Docker Host`, add one **Node** per container with stereotype `«container»` and ports in names:
   - `web_dashboard — Flask (5000)`
   - `main_host — Flask (8000)`
   - `ml_service — Flask (6000)`
   - `patient_simulator — Python`
   - `Prometheus (9090)`
   - `Grafana (3000)`
   - `Alertmanager (9093)`
7. In `DB Subnet Group (Private)`, add a **Database** element named `RDS MySQL (3306)`.
8. Add an **Actor** outside the AWS nodes: `User (Clinician/Admin)`.
9. Connect with **Communication Paths** (or Dependencies) and label with protocols/ports:
   - User → ALB: `HTTPS 443`
   - ALB → web_dashboard: `HTTP 5000 (Target Group)`
   - web_dashboard → main_host: `HTTP 8000 (/api/*)`
   - web_dashboard → Grafana: `HTTP 3000 (Embed)`
   - web_dashboard → RDS: `MySQL 3306`
   - patient_simulator → main_host: `HTTP 8000 /track`
   - patient_simulator → ml_service: `HTTP 6000 /predict`
   - Prometheus → main_host: `HTTP 8000 /metrics`
   - Grafana → Prometheus: `HTTP 9090 API`
   - Prometheus → Alertmanager: `HTTP 9093`
10. Add **Notes** for environment variables and security groups:
    - Env: `MAIN_HOST_URL, GRAFANA_URL, PROMETHEUS_URL, ALERTMANAGER_URL, DATABASE_URL`
    - SGs: ALB→5000, internal ports, RDS from app SG only.

## 📦 Files Added
- `docs/deployment/healthcare-deployment.puml` — PlantUML deployment diagram
- `docs/DEPLOYMENT_DIAGRAM_GUIDE.md` — this guide with StarUML steps and explanations

## ✅ How to Render the Diagram (Locally)
- VS Code: install the "PlantUML" extension → open the `.puml` file → "Preview Current Diagram".
- CLI (if Java + Graphviz installed):
  ```bash
  plantuml docs/deployment/healthcare-deployment.puml
  ```

If you want, I can also export a PNG/SVG version and commit it to `docs/deployment/`.
