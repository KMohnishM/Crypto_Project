# API Documentation

This document describes the API endpoints available in the Healthcare Monitoring System.

## Main Host API

### Track Patient Data

Sends patient vital signs data to be tracked by the monitoring system.

**Endpoint:** `POST /track`

**Request Body:**
```json
{
  "hospital": "string",
  "dept": "string",
  "ward": "string",
  "patient": "string",
  "heart_rate": number,
  "bp_systolic": number,
  "bp_diastolic": number,
  "respiratory_rate": number,
  "spo2": number,
  "etco2": number,
  "fio2": number,
  "temperature": number,
  "wbc_count": number,
  "lactate": number,
  "blood_glucose": number,
  "timestamp": "ISO-8601 string",
  "ecg_signal": "string"
}
```

**Response:**
```json
{
  "status": "success"
}
```

### Get Metrics

Retrieve Prometheus metrics for all tracked data.

**Endpoint:** `GET /metrics`

**Response:**
- Content-Type: `text/plain; version=0.0.4`
- Body: Prometheus-formatted metrics

## ML Service API

### Predict Anomaly

Analyzes patient vital signs to detect anomalies.

**Endpoint:** `POST /predict`

**Request Body:**
```json
{
  "heart_rate": number,
  "bp_systolic": number,
  "bp_diastolic": number,
  "respiratory_rate": number,
  "spo2": number,
  "etco2": number,
  "fio2": number,
  "temperature": number,
  "wbc_count": number,
  "lactate": number,
  "blood_glucose": number
}
```

**Response:**
```json
{
  "anomaly_score": number
}
```

## Prometheus API

Prometheus provides a robust API for querying metrics. The most commonly used endpoints are:

### Query

Evaluates an instant query at a single point in time.

**Endpoint:** `GET /api/v1/query`

**Parameters:**
- `query`: Prometheus expression query string
- `time`: Evaluation timestamp (optional)

### Query Range

Evaluates an expression query over a range of time.

**Endpoint:** `GET /api/v1/query_range`

**Parameters:**
- `query`: Prometheus expression query string
- `start`: Start timestamp
- `end`: End timestamp
- `step`: Query resolution step width in duration format or float seconds

## Alertmanager API

### Alerts

Get a list of all active alerts.

**Endpoint:** `GET /api/v2/alerts`

### Silences

Get a list of all silences.

**Endpoint:** `GET /api/v2/silences`

Create a new silence.

**Endpoint:** `POST /api/v2/silences`