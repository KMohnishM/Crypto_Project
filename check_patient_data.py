import pandas as pd
import sys
import os

# Get the path to the patient data Excel file
excel_file_path = r"c:\Users\kmohn\New folder\AWS_Cloud\data\patient_samples\patients_data.xlsx"

def check_excel_file():
    try:
        # Check if the file exists
        if not os.path.exists(excel_file_path):
            print(f"Error: The file '{excel_file_path}' does not exist.")
            return
        
        # Try to read the Excel file
        print(f"Reading Excel file: {excel_file_path}")
        df_sheets = pd.read_excel(excel_file_path, sheet_name=None)
        
        # Print information about each sheet
        print(f"\nFound {len(df_sheets)} sheets in the Excel file:")
        for sheet_name, df in df_sheets.items():
            print(f"\n-- Sheet: {sheet_name} --")
            print(f"Shape: {df.shape} (rows × columns)")
            print(f"Columns: {list(df.columns)}")
            print(f"Sample rows (first 2):")
            print(df.head(2))
        
        # Check if the file has the expected structure for the patient simulator
        expected_columns = ['hospital', 'dept', 'ward', 'patient', 'heart_rate', 
                           'bp_systolic', 'bp_diastolic', 'respiratory_rate', 
                           'spo2', 'etco2', 'fio2', 'temperature', 'wbc_count', 
                           'lactate', 'blood_glucose']
        
        missing_cols = {}
        for sheet_name, df in df_sheets.items():
            missing = [col for col in expected_columns if col not in df.columns]
            if missing:
                missing_cols[sheet_name] = missing
        
        if missing_cols:
            print("\n⚠️ WARNING: Missing expected columns in some sheets:")
            for sheet, cols in missing_cols.items():
                print(f"Sheet '{sheet}' is missing columns: {cols}")
        else:
            print("\n✅ All sheets have the expected columns for the patient simulator.")
        
        # Count total unique patients
        all_patients = set()
        for sheet_name, df in df_sheets.items():
            if 'patient' in df.columns:
                all_patients.update(df['patient'].unique())
        
        print(f"\nTotal unique patients across all sheets: {len(all_patients)}")
        print(f"Patient IDs: {sorted(all_patients)}")
        
    except Exception as e:
        print(f"Error checking Excel file: {e}")

if __name__ == "__main__":
    check_excel_file()