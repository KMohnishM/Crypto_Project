"""
ML Service with JWT Authentication
Provides anomaly detection with secure service-to-service authentication
"""

from flask import Flask, request, jsonify
from sklearn.ensemble import IsolationForest
import numpy as np
import pandas as pd
import joblib
import os
import sys

# Add common directory for authentication
sys.path.insert(0, '/app/common')

try:
    from service_auth import require_service_auth, optional_service_auth
    AUTH_AVAILABLE = True
except ImportError:
    print("⚠️  WARNING: Service authentication not available - running in open mode")
    AUTH_AVAILABLE = False
    # Dummy decorator for when auth module is not available
    def require_service_auth(f):
        return f
    def optional_service_auth(f):
        return f

app = Flask(__name__)

# Configuration
ENABLE_SERVICE_AUTH = os.getenv('ENABLE_SERVICE_AUTH', 'false').lower() == 'true'

MODEL_FILENAME = "anomaly_model.pkl"  # Updated to match the model name in m.py

# Feature columns - matching those used in m.py
feature_names = [
    "heart_rate", "bp_systolic", "bp_diastolic", "respiratory_rate",
    "spo2", "etco2", "fio2", "temperature", "wbc_count", "lactate", "blood_glucose"
]

# Function to train and save the model
def train_model():
    print("Training a new anomaly detection model...")
    np.random.seed(42)
    data = pd.DataFrame({
        "heart_rate": np.random.normal(75, 10, 300),
        "bp_systolic": np.random.normal(120, 15, 300),
        "bp_diastolic": np.random.normal(80, 10, 300),
        "respiratory_rate": np.random.normal(18, 3, 300),
        "spo2": np.random.normal(97, 2, 300),
        "etco2": np.random.normal(37, 4, 300),
        "fio2": np.random.normal(21, 2, 300),  # Normal room air is ~21%
        "temperature": np.random.normal(36.6, 0.5, 300),
        "wbc_count": np.random.normal(7, 1.5, 300),
        "lactate": np.random.normal(1.2, 0.4, 300),
        "blood_glucose": np.random.normal(95, 15, 300),
    })
    # Use contamination=0.2 to match m.py settings
    model = IsolationForest(n_estimators=100, contamination=0.2, random_state=42)
    model.fit(data)
    joblib.dump(model, MODEL_FILENAME)
    print(f"Model trained and saved as {MODEL_FILENAME}")
    return model

# Load or train model
if __name__ == "__main__":  # Only load the model if running as the main module
    if not os.path.exists(MODEL_FILENAME):
        model = train_model()
    else:
        model = joblib.load(MODEL_FILENAME)
        print(f"Model loaded from {MODEL_FILENAME}")

# Predict route with required authentication
@app.route("/predict", methods=["POST"])
@require_service_auth
def predict():
    # Load model if not already loaded
    if 'model' not in globals():
        global model
        if os.path.exists(MODEL_FILENAME):
            model = joblib.load(MODEL_FILENAME)
        else:
            model = train_model()
    
    # Log authentication status (should always be authenticated now)
    if AUTH_AVAILABLE and hasattr(request, 'authenticated') and request.authenticated:
        service_name = getattr(request, 'service_name', 'unknown')
        print(f"🔐 Authenticated request from: {service_name}")
    else:
        # This shouldn't happen with @require_service_auth
        print(f"⚠️  Authentication bypass detected!")
    
    input_data = request.json
    print(f"DEBUG: Received input data: {input_data}")

    try:
        features = [input_data[feat] for feat in feature_names]
    except KeyError as e:
        return jsonify({"error": f"Missing feature in input: {str(e)}"}), 400

    X = pd.DataFrame([features], columns=feature_names)
    print(f"DEBUG: Features extracted: {features}")

    # Get the raw decision function score
    score = model.decision_function(X)[0]
    print(f"DEBUG: Raw decision score: {score}")
    
    # Original calculation
    original_score = 1 - score
    print(f"DEBUG: Original calculation (1 - raw): {original_score}")
    
    # Normalize score to 0-1 range - consistent with m.py
    # Since we have only one sample, we need to set reasonable min/max bounds
    # A reasonable range for decision_function is typically -0.5 to 0.5
    min_score = -0.5
    max_score = 0.5
    
    if max_score > min_score:
        normalized_score = (score - min_score) / (max_score - min_score)
        # Clip to ensure it's in 0-1 range even if outside expected bounds
        normalized_score = max(0, min(1, normalized_score))
    else:
        normalized_score = 0.5  # Default if min=max (unlikely)
    
    print(f"DEBUG: After normalization: {normalized_score}")
    
    # Invert so higher = more anomalous
    anomaly_score = 1 - normalized_score
    print(f"DEBUG: Final normalized score: {anomaly_score}")
    
    # Return both original and normalized scores for comparison
    response = {
        "original_score": round(original_score, 4),
        "normalized_score": round(anomaly_score, 4)
    }
    print(f"DEBUG: Returning response: {response}")
    
    return jsonify(response)

if __name__ == "__main__":
    print("DEBUG: Starting server with normalized scoring...")
    app.run(host="0.0.0.0", port=6000)