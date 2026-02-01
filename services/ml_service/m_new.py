"""
Simple inference script to test anomaly detection on new data (adapted for ml_service)
"""

import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
import os
from sklearn.ensemble import IsolationForest

# Define vital columns
vital_columns = [
    "heart_rate", "bp_systolic", "bp_diastolic", "respiratory_rate",
    "spo2", "etco2", "fio2", "temperature", "wbc_count", 
    "lactate", "blood_glucose"
]

def train_anomaly_model(data):
    """Train a new anomaly model on the given data."""
    print("\n🧠 Training a new anomaly detection model...")
    
    # Make sure all columns exist
    for col in vital_columns:
        if col not in data.columns:
            data[col] = np.random.normal(0, 1, len(data))
    
    X = data[vital_columns].values
    
    # Train the model with appropriate contamination
    model = IsolationForest(n_estimators=100, contamination=0.2, random_state=42)
    model.fit(X)
    
    # Save the model
    joblib.dump(model, "anomaly_model.pkl")
    print("✅ Model trained and saved as anomaly_model.pkl")
    
    return model

def main():
    print("🔍 Patient Vitals Anomaly Detection - Inference (ml_service)")
    print("=" * 60)
    
    # Create some test data (simulating new patient data)
    print("\n📈 Creating test data...")
    np.random.seed(42)
    
    # Generate normal data
    normal_data = []
    for i in range(50):
        normal_data.append({
            "patient_id": "TEST_001",
            "timestamp": datetime.now() - timedelta(minutes=i),
            "heart_rate": np.random.normal(75, 8),
            "bp_systolic": np.random.normal(120, 10),
            "bp_diastolic": np.random.normal(80, 8),
            "respiratory_rate": np.random.normal(18, 2),
            "spo2": np.random.normal(97, 1.5),
            "etco2": np.random.normal(37, 3),
            "fio2": 21.0,
            "temperature": np.random.normal(36.6, 0.3),
            "wbc_count": np.random.normal(7, 1),
            "lactate": np.random.normal(1.2, 0.3),
            "blood_glucose": np.random.normal(95, 10)
        })
    
    # Add some anomalies
    anomaly_data = []
    for i in range(10):
        anomaly_data.append({
            "patient_id": "TEST_001",
            "timestamp": datetime.now() - timedelta(minutes=50+i),
            "heart_rate": np.random.choice([30, 150]),  # Very low or high
            "bp_systolic": np.random.choice([70, 180]),  # Very low or high
            "bp_diastolic": np.random.choice([40, 120]),  # Very low or high
            "respiratory_rate": np.random.choice([5, 35]),  # Very low or high
            "spo2": np.random.uniform(70, 85),  # Low oxygen
            "etco2": np.random.choice([10, 60]),  # Very low or high
            "fio2": 21.0,
            "temperature": np.random.choice([34, 40]),  # Very low or high
            "wbc_count": np.random.choice([2, 20]),  # Very low or high
            "lactate": np.random.choice([0.1, 5]),  # Very low or high
            "blood_glucose": np.random.choice([40, 200])  # Very low or high
        })
    
    # Combine test data
    test_df = pd.DataFrame(normal_data + anomaly_data)
    test_df = test_df.sort_values("timestamp").reset_index(drop=True)
    
    print(f"📈 Test data: {len(test_df)} samples")
    print(f"   - Normal samples: {len(normal_data)}")
    print(f"   - Anomaly samples: {len(anomaly_data)}")
    
    # Train a new model with this data
    model = train_anomaly_model(test_df)
    
    # Apply same normalization as training
    print("\n🔄 Applying normalization...")
    
    # For simplicity, use global normalization (in real scenario, you'd use per-patient)
    for col in vital_columns:
        mean_val = test_df[col].mean()
        std_val = test_df[col].std()
        if std_val > 0:
            test_df[f"{col}_normalized"] = (test_df[col] - mean_val) / std_val
        else:
            test_df[f"{col}_normalized"] = 0
    
    # Prepare features - use original features, not normalized
    X = test_df[vital_columns].values
    
    # Get predictions
    print("🤖 Running anomaly detection...")
    predictions = model.predict(X)
    scores = model.decision_function(X)
    
    # Convert scores to 0-1 range
    min_score = scores.min()
    max_score = scores.max()
    if max_score > min_score:
        anomaly_scores = (scores - min_score) / (max_score - min_score)
    else:
        anomaly_scores = np.zeros_like(scores)
    anomaly_scores = 1 - anomaly_scores  # Invert so higher = more anomalous
    
    # Results
    anomaly_count = np.sum(predictions == -1)
    anomaly_rate = anomaly_count / len(predictions)
    
    print("\n" + "=" * 60)
    print("📊 INFERENCE RESULTS")
    print("=" * 60)
    print(f"Total samples: {len(test_df)}")
    print(f"Anomalies detected: {anomaly_count}")
    print(f"Anomaly rate: {anomaly_rate:.3f}")
    print(f"Expected anomalies: {len(anomaly_data)}")
    print(f"Detection accuracy: {anomaly_count/len(anomaly_data):.3f}")
    
    # Show detected anomalies
    print("\n🚨 Detected Anomalies:")
    print("-" * 50)
    anomaly_indices = np.where(predictions == -1)[0]
    for i, idx in enumerate(anomaly_indices[:10]):  # Show first 10
        row = test_df.iloc[idx]
        score = anomaly_scores[idx]
        print(f"{i+1:2d}. Time: {row['timestamp'].strftime('%H:%M:%S')} | "
              f"HR: {row['heart_rate']:3.0f} | SpO2: {row['spo2']:4.1f} | "
              f"Score: {score:.3f}")
    
    # Show top scores
    print("\n📈 Top 10 Highest Anomaly Scores:")
    print("-" * 50)
    top_indices = np.argsort(anomaly_scores)[-10:][::-1]
    for i, idx in enumerate(top_indices):
        row = test_df.iloc[idx]
        score = anomaly_scores[idx]
        prediction = "ANOMALY" if predictions[idx] == -1 else "Normal"
        print(f"{i+1:2d}. {prediction:8s} | Score: {score:.3f} | "
              f"HR: {row['heart_rate']:3.0f} | SpO2: {row['spo2']:4.1f}")
    
    # Save results
    results_df = test_df.copy()
    results_df["anomaly_score"] = anomaly_scores
    results_df["prediction"] = predictions
    results_df["is_anomaly"] = (predictions == -1).astype(int)
    
    results_path = "inference_results.xlsx"
    results_df.to_excel(results_path, index=False)
    print(f"\n💾 Results saved to: {results_path}")
    
    print("\n✅ Inference completed successfully!")

if __name__ == "__main__":
    main()