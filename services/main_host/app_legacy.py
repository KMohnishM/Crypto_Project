from flask import Flask, request, jsonify
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging
import json
from collections import defaultdict

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Define Gauges (current value metrics)
metrics = {
    'heart_rate': Gauge('heart_rate_bpm', 'Heart Rate (BPM)', ['hospital', 'department', 'ward', 'patient']),
    'bp_systolic': Gauge('bp_systolic', 'BP Systolic', ['hospital', 'department', 'ward', 'patient']),
    'bp_diastolic': Gauge('bp_diastolic', 'BP Diastolic', ['hospital', 'department', 'ward', 'patient']),
    'respiratory_rate': Gauge('respiratory_rate', 'Respiratory Rate', ['hospital', 'department', 'ward', 'patient']),
    'spo2': Gauge('spo2_percent', 'SpO2 (%)', ['hospital', 'department', 'ward', 'patient']),
    'etco2': Gauge('etco2', 'EtCO2', ['hospital', 'department', 'ward', 'patient']),
    'fio2': Gauge('fio2_percent', 'FiO2 (%)', ['hospital', 'department', 'ward', 'patient']),
    'temperature': Gauge('temperature_celsius', 'Temperature (°C)', ['hospital', 'department', 'ward', 'patient']),
    'wbc_count': Gauge('wbc_count', 'WBC Count', ['hospital', 'department', 'ward', 'patient']),
    'lactate': Gauge('lactate', 'Lactate (mmol/L)', ['hospital', 'department', 'ward', 'patient']),
    'blood_glucose': Gauge('blood_glucose', 'Blood Glucose (mg/dL)', ['hospital', 'department', 'ward', 'patient']),
    # ECG skipped for now
    'anomaly_score': Gauge('anomaly_score', 'Anomaly Score', ['hospital', 'department', 'ward', 'patient']),  # New anomaly score metric
}

# In-memory data store for the dashboard
patient_data_store = defaultdict(list)

@app.route('/track', methods=['POST'])
def track_traffic():
    data = request.get_json()
    print("Received Payload:", data)  # Add this
    
    hospital = data.get('hospital', 'unknown')
    dept = data.get('dept', 'unknown')
    ward = data.get('ward', 'unknown')
    patient = data.get('patient', 'unknown')

    labels = dict(hospital=hospital, department=dept, ward=ward, patient=patient)

    for key, gauge in metrics.items():
        if key in data:
            print(f"Setting {key} = {data[key]} for labels {labels}")  # Add this
            gauge.labels(**labels).set(data[key])
        else:
            print(f"WARNING: {key} missing in payload")
    
    # Store the data for the dashboard
    patient_key = f"{hospital}|{dept}|{ward}|{patient}"
    patient_data_store[patient_key].append(data)
    
    # Keep only the latest 100 data points per patient to prevent memory bloat
    if len(patient_data_store[patient_key]) > 100:
        patient_data_store[patient_key] = patient_data_store[patient_key][-100:]

    return jsonify({'status': 'success'}), 200


@app.route('/metrics')
def metrics_endpoint():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/')
def root():
    return "Hospital Monitoring Service is Running. Use /track (POST JSON) or /metrics."

@app.route('/api/patients', methods=['GET'])
def get_patients():
    """Get list of all patients"""
    try:
        patients = []
        for key in patient_data_store.keys():
            hospital, dept, ward, patient = key.split('|')
            if patient not in patients:
                patients.append(patient)
        
        return jsonify({
            "status": "success",
            "patients": patients
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/patient/<patient_id>', methods=['GET'])
def get_patient_data(patient_id):
    """Get data for a specific patient"""
    try:
        result = {}
        
        for key, data_list in patient_data_store.items():
            hospital, dept, ward, patient = key.split('|')
            
            if patient == patient_id:
                for idx, data_point in enumerate(data_list):
                    # Create a unique key for each data point
                    point_key = f"{key}|{idx}"
                    result[point_key] = data_point
        
        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/dashboard-data', methods=['GET'])
def get_dashboard_data():
    """Get all data for the dashboard"""
    try:
        # Convert defaultdict to regular dict for JSON serialization
        result = {}
        for key, data_list in patient_data_store.items():
            result[key] = data_list[-1]  # Get the latest data point for each patient
        
        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)