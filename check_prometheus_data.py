import requests
import time
import json

def check_main_host_metrics():
    """Check if the main_host service has metrics and patient data."""
    print("Checking main_host metrics endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/metrics", timeout=5)
        if response.status_code != 200:
            print(f"❌ Error: main_host /metrics endpoint returned status code {response.status_code}")
            return False
        
        metrics_text = response.text
        print(f"✅ Successfully reached main_host /metrics endpoint. Response size: {len(metrics_text)} bytes")
        
        # Check if there are heart_rate metrics (indicates patient data)
        if "heart_rate" in metrics_text:
            print("✅ Found heart_rate metrics in the response. Patient data is being collected.")
            
            # Count distinct patients by looking for patient label patterns
            patients = set()
            for line in metrics_text.split('\n'):
                if 'patient="' in line:
                    # Extract patient id from the line
                    start = line.find('patient="') + 9
                    end = line.find('"', start)
                    if start > 0 and end > start:
                        patient_id = line[start:end]
                        patients.add(patient_id)
            
            print(f"🔍 Found data for {len(patients)} distinct patients in the metrics")
            print(f"Patient IDs: {sorted(patients)}")
            return True
        else:
            print("❌ No heart_rate metrics found. Patient data is not being collected.")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to main_host: {e}")
        return False

def check_patient_simulator():
    """Check if the patient simulator container is running and check its logs."""
    print("\nChecking patient_simulator status...")
    
    try:
        # First try the dashboard API to see if patients are registered
        response = requests.get("http://localhost:8000/api/patients")
        if response.status_code == 200:
            data = response.json()
            if "patients" in data and len(data["patients"]) > 0:
                print(f"✅ Found {len(data['patients'])} patients via the API")
                print(f"Patient IDs: {data['patients']}")
            else:
                print("❌ No patients found via the API")
        else:
            print(f"❌ Error accessing API: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to API: {e}")

def check_prometheus_targets():
    """Check if Prometheus has scraped the main_host target."""
    print("\nChecking Prometheus targets...")
    
    try:
        response = requests.get("http://localhost:9090/api/v1/targets")
        if response.status_code != 200:
            print(f"❌ Error: Prometheus targets API returned status code {response.status_code}")
            return False
        
        targets_data = response.json()
        
        if "data" not in targets_data or "activeTargets" not in targets_data["data"]:
            print("❌ Invalid response format from Prometheus targets API")
            return False
        
        active_targets = targets_data["data"]["activeTargets"]
        print(f"Found {len(active_targets)} active targets in Prometheus")
        
        for target in active_targets:
            print(f"Target: {target['labels'].get('job', 'unknown')} ({target['labels'].get('instance', 'unknown')})")
            print(f"  Status: {target['health']} (Last Scrape: {target['lastScrape']})")
            print(f"  Error: {target.get('lastError', 'None')}")
        
        # Check specifically for the hospital-metrics target
        hospital_targets = [t for t in active_targets if t['labels'].get('job') == 'hospital-metrics']
        if hospital_targets:
            target = hospital_targets[0]
            if target['health'] == 'up':
                print("✅ hospital-metrics target is UP in Prometheus")
                return True
            else:
                print(f"❌ hospital-metrics target is {target['health']} in Prometheus")
                print(f"Error: {target.get('lastError', 'None')}")
                return False
        else:
            print("❌ No hospital-metrics target found in Prometheus")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to Prometheus: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing Prometheus API response: {e}")
        return False

def check_prometheus_metrics():
    """Check if Prometheus has metrics for patients."""
    print("\nChecking Prometheus metrics for patient data...")
    
    metrics_to_check = [
        "heart_rate_bpm",
        "bp_systolic", 
        "temperature_celsius"
    ]
    
    for metric in metrics_to_check:
        try:
            response = requests.get(f"http://localhost:9090/api/v1/query?query={metric}")
            if response.status_code != 200:
                print(f"❌ Error: Prometheus query for {metric} returned status code {response.status_code}")
                continue
            
            data = response.json()
            if "data" not in data or "result" not in data["data"]:
                print(f"❌ Invalid response format from Prometheus query for {metric}")
                continue
            
            results = data["data"]["result"]
            if not results:
                print(f"❌ No data found for metric {metric}")
                continue
            
            print(f"✅ Found {len(results)} results for metric {metric}")
            
            # Get patient IDs from metric results
            patient_ids = set()
            for result in results:
                if "metric" in result and "patient" in result["metric"]:
                    patient_ids.add(result["metric"]["patient"])
            
            print(f"  Patient IDs with {metric} data: {sorted(patient_ids)}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to Prometheus for {metric} query: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing Prometheus API response for {metric} query: {e}")

def main():
    print("===== Hospital Dashboard Diagnosis =====")
    print("Checking why Prometheus is returning empty results...\n")
    
    # Check main host metrics endpoint
    has_metrics = check_main_host_metrics()
    
    # Check patient simulator
    check_patient_simulator()
    
    # Check Prometheus targets
    check_prometheus_targets()
    
    # Check Prometheus metrics
    check_prometheus_metrics()

if __name__ == "__main__":
    main()