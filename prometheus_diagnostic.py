import requests
import json
import time

def check_prometheus_connection():
    """Check if Prometheus is running and accessible."""
    print("\n=== Checking Prometheus Connection ===")
    try:
        response = requests.get("http://localhost:9090/-/healthy", timeout=5)
        if response.status_code == 200:
            print("✅ Prometheus is running and healthy")
            return True
        else:
            print(f"❌ Prometheus returned status code {response.status_code} when checking health")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to Prometheus: {e}")
        return False

def check_prometheus_targets():
    """Check if Prometheus has configured targets and their status."""
    print("\n=== Checking Prometheus Targets ===")
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
        print(f"Found {len(active_targets)} active targets in Prometheus:")
        
        for i, target in enumerate(active_targets, 1):
            job = target['labels'].get('job', 'unknown')
            instance = target['labels'].get('instance', 'unknown')
            health = target['health']
            last_error = target.get('lastError', '')
            
            print(f"  {i}. {job} ({instance}): {health}")
            if last_error:
                print(f"     Error: {last_error}")
        
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
        print(f"❌ Error connecting to Prometheus targets API: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing Prometheus API response: {e}")
        return False

def check_prometheus_metrics():
    """Check if Prometheus has metrics for patients."""
    print("\n=== Checking Prometheus Metrics ===")
    
    metrics_to_check = [
        "heart_rate_bpm",
        "bp_systolic", 
        "temperature_celsius"
    ]
    
    found_data = False
    
    for metric in metrics_to_check:
        try:
            print(f"\nChecking metric: {metric}")
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
            found_data = True
            
            # Show sample of the first result
            if results:
                sample = results[0]
                print(f"  Sample metric data: {json.dumps(sample, indent=2)}")
            
            # Get patient IDs from metric results
            patient_ids = set()
            for result in results:
                if "metric" in result and "patient" in result["metric"]:
                    patient_ids.add(result["metric"]["patient"])
            
            if patient_ids:
                print(f"  Patient IDs with {metric} data: {sorted(patient_ids)}")
            else:
                print("  No patient IDs found in the results")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to Prometheus for {metric} query: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing Prometheus API response for {metric} query: {e}")
    
    return found_data

def check_main_host_metrics():
    """Check if the main_host service has metrics and patient data."""
    print("\n=== Checking Main Host Metrics ===")
    
    try:
        response = requests.get("http://localhost:8000/metrics", timeout=5)
        if response.status_code != 200:
            print(f"❌ Error: main_host /metrics endpoint returned status code {response.status_code}")
            return False
        
        metrics_text = response.text
        metrics_lines = metrics_text.strip().split('\n')
        metrics_count = len(metrics_lines)
        
        print(f"✅ Successfully reached main_host /metrics endpoint")
        print(f"  Found {metrics_count} lines of metrics")
        
        # Print a sample of the metrics (first 5 lines)
        if metrics_count > 0:
            print("\nSample metrics (first 5 lines):")
            for i, line in enumerate(metrics_lines[:5]):
                print(f"  {line}")
        
        # Check if there are heart_rate metrics (indicates patient data)
        heart_rate_lines = [line for line in metrics_lines if "heart_rate" in line]
        if heart_rate_lines:
            print(f"\n✅ Found {len(heart_rate_lines)} heart_rate metrics in the response")
            print("\nSample heart rate metrics (first 2):")
            for i, line in enumerate(heart_rate_lines[:2]):
                print(f"  {line}")
            
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
            
            if patients:
                print(f"\n🔍 Found data for {len(patients)} distinct patients in the metrics")
                print(f"  Patient IDs: {sorted(patients)}")
            else:
                print("\n❌ No patient IDs found in the metrics")
            
            return True
        else:
            print("\n❌ No heart_rate metrics found. Patient data is not being collected.")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to main_host: {e}")
        return False

def check_patient_simulator_api():
    """Check the API endpoints on the main host."""
    print("\n=== Checking Patient API Endpoints ===")
    
    api_endpoints = [
        {"url": "http://localhost:8000/api/patients", "name": "List Patients"},
        {"url": "http://localhost:8000/api/dashboard-data", "name": "Dashboard Data"}
    ]
    
    for endpoint in api_endpoints:
        try:
            print(f"\nChecking {endpoint['name']} endpoint: {endpoint['url']}")
            response = requests.get(endpoint['url'], timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Status code: {response.status_code}")
                
                # Process specific endpoint data
                if "patients" in endpoint['url']:
                    if "patients" in data:
                        patients = data["patients"]
                        print(f"  Found {len(patients)} patients")
                        if patients:
                            print(f"  Patient IDs: {patients}")
                    else:
                        print("  No patients field in the response")
                
                elif "dashboard-data" in endpoint['url']:
                    if "data" in data:
                        dashboard_data = data["data"]
                        print(f"  Found dashboard data for {len(dashboard_data)} entries")
                        
                        # Sample of the first entry
                        if dashboard_data:
                            first_key = next(iter(dashboard_data))
                            print(f"  Sample data entry for {first_key}:")
                            print(f"    {json.dumps(dashboard_data[first_key], indent=2)[:200]}...")
                    else:
                        print("  No data field in the response")
                
            else:
                print(f"❌ Failed! Status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to endpoint: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing response as JSON: {e}")

def main():
    """Main function to check Prometheus data issues."""
    print("=" * 50)
    print("PROMETHEUS DATA DIAGNOSTIC TOOL")
    print("=" * 50)
    
    # Step 1: Check if Prometheus is running
    if not check_prometheus_connection():
        print("\n⚠️ Prometheus is not running or not accessible")
        print("Please make sure the Prometheus container is running.")
        return
    
    # Step 2: Check if main_host is exposing metrics
    main_host_has_metrics = check_main_host_metrics()
    
    # Step 3: Check Prometheus targets (scrape config)
    prometheus_targets_ok = check_prometheus_targets()
    
    # Step 4: Check Prometheus metrics for patient data
    prometheus_has_data = check_prometheus_metrics()
    
    # Step 5: Check the API endpoints
    check_patient_simulator_api()
    
    # Summary and diagnosis
    print("\n" + "=" * 50)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    if not main_host_has_metrics:
        print("\n🔴 ISSUE: The main_host service is not exposing patient metrics")
        print("This means no data is available for Prometheus to scrape.")
        print("\nPossible causes:")
        print("1. Patient simulator is not sending data to the main_host")
        print("2. The Excel data file is not being loaded properly")
        print("3. The main_host is not storing the metrics correctly")
        
    elif not prometheus_targets_ok:
        print("\n🔴 ISSUE: Prometheus cannot scrape data from the main_host")
        print("The main_host has metrics but Prometheus can't access them.")
        print("\nPossible causes:")
        print("1. Networking issue between Prometheus and main_host containers")
        print("2. Incorrect scrape configuration in prometheus.yml")
        print("3. Firewall or security settings blocking connections")
        
    elif not prometheus_has_data:
        print("\n🔴 ISSUE: Prometheus is not storing the scraped metrics")
        print("Prometheus can connect to main_host but no data is being stored.")
        print("\nPossible causes:")
        print("1. Storage issue in Prometheus")
        print("2. Main host metrics format is incorrect")
        print("3. Metrics are being dropped due to configuration issues")
        
    else:
        print("\n🟢 All systems appear to be working correctly")
        print("Prometheus is running, main_host has metrics, and Prometheus is storing the data")

if __name__ == "__main__":
    main()