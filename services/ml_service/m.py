import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

# Thresholds for vital signs
thresholds = {
    "heart_rate": {"normal": (60, 100), "anomalous": [30, 120]},
    "bp_systolic": {"normal": (100, 130), "anomalous": [90, 140]},
    "bp_diastolic": {"normal": (60, 90), "anomalous": [55, 95]},
    "respiratory_rate": {"normal": (12, 20), "anomalous": [5, 25]},
    "spo2": {"normal": (70, 100), "anomalous": [50, 70]},
    "etco2": {"normal": (30, 45), "anomalous": [10, 25, 46, 60]},
    "fio2": {"normal": (21, 21), "anomalous": [15, 25]},  # Normal air as 21%
    "temperature": {"normal": (36.0, 37.0), "anomalous": [34, 38]},
    "wbc_count": {"normal": (4, 11), "anomalous": [2, 15]},
    "lactate": {"normal": (0.5, 2), "anomalous": [0, 3]},
    "blood_glucose": {"normal": (70, 120), "anomalous": [50, 180]},
}

# Function to generate labeled data based on thresholds
def generate_labeled_data(excel_path):
    all_data = pd.concat(
        pd.read_excel(excel_path, sheet_name=None),
        ignore_index=True
    )
    
    # Select only feature columns
    feature_columns = [
        "heart_rate", "bp_systolic", "bp_diastolic", "respiratory_rate", "spo2",
        "etco2", "fio2", "temperature", "wbc_count", "lactate", "blood_glucose"
    ]
    data = all_data[feature_columns].dropna()

    labeled_data = []
    
    for _, row in data.iterrows():
        label = 1  # Assume normal
        for feature, limits in thresholds.items():
            if row[feature] < limits["normal"][0] or row[feature] > limits["normal"][1]:
                label = -1  # Anomalous
                break
        labeled_data.append(row.tolist() + [label])  # Add the label at the end
    
    labeled_df = pd.DataFrame(labeled_data, columns=feature_columns + ["label"])
    return labeled_df

# 1. Load and label data based on thresholds
excel_path = "patients_data.xlsx"  # 👈 change this
labeled_data = generate_labeled_data(excel_path)

# 2. Split features (X) and labels (y)
X = labeled_data.drop(columns=["label"])  # Features
y = labeled_data["label"]  # Labels (1 for normal, -1 for anomalous)

# 3. Train Isolation Forest
model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
model.fit(X)

# 4. Save the model
joblib.dump(model, "iforest_model.pkl")
print("✅ Model trained and saved as iforest_model.pkl")

# Optional: Check the first few rows of labeled data
print(labeled_data.head())

