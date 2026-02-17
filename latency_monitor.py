#!/usr/bin/env python3
"""
Latency Monitoring Tool
Query and display real-time latency metrics from the healthcare IoT system
"""

import requests
import time
import sys
from datetime import datetime
from typing import Dict, List

# Configuration
BACKEND_URL = "http://localhost:8000"
PROMETHEUS_URL = "http://localhost:9090"


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def get_current_latencies() -> Dict:
    """Get current latency metrics from backend API"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/latency", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Error fetching latency data: {e}")
        return {"status": "error", "latency_metrics": {}}


def get_prometheus_metric(query: str) -> float:
    """Query Prometheus for a specific metric"""
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        if data["status"] == "success" and data["data"]["result"]:
            return float(data["data"]["result"][0]["value"][1])
        return 0.0
    except Exception as e:
        print(f"WARNING: Prometheus query failed: {e}")
        return 0.0


def display_latency_table(latency_data: Dict):
    """Display latency metrics in a formatted table"""
    if not latency_data.get("latency_metrics"):
        print("WARNING: No latency data available\n")
        return
    
    print(f"{'Device ID':<15} {'Decrypt (ms)':<15} {'Process (ms)':<15} {'Network (ms)':<15} {'E2E (ms)':<15}")
    print("-" * 80)
    
    for device_id, metrics in latency_data["latency_metrics"].items():
        decrypt = metrics.get("decryption_ms", 0)
        process = metrics.get("processing_ms", 0)
        network = metrics.get("network_ms", 0)
        e2e = metrics.get("end_to_end_ms", 0)
        
        # Color coding based on thresholds
        e2e_str = f"{e2e:>6.1f}"
        if e2e > 1000:
            e2e_str = f"HIGH: {e2e_str}"
        elif e2e > 500:
            e2e_str = f"WARN: {e2e_str}"
        else:
            e2e_str = f"OK: {e2e_str}"
        
        print(f"{device_id:<15} {decrypt:>6.2f}        {process:>6.2f}        {network:>6.1f}        {e2e_str}")
    
    print()


def display_latency_breakdown(device_id: str = None):
    """Display detailed latency breakdown for a device or all devices"""
    print_header(f"Latency Breakdown - {device_id if device_id else 'All Devices'}")
    
    latency_data = get_current_latencies()
    
    if device_id:
        # Show specific device
        try:
            response = requests.get(f"{BACKEND_URL}/api/latency/{device_id}", timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "success":
                metrics = data["latency"]
                print(f"Device: {device_id}")
                print(f"  Decryption:    {metrics['decryption_ms']:>8.3f} ms")
                print(f"  Processing:    {metrics['processing_ms']:>8.3f} ms")
                print(f"  Network:       {metrics['network_ms']:>8.1f} ms")
                print(f"  End-to-End:    {metrics['end_to_end_ms']:>8.1f} ms")
                print()
            else:
                print(f"ERROR: Device {device_id} not found\n")
        except Exception as e:
            print(f"ERROR: Error: {e}\n")
    else:
        # Show all devices
        display_latency_table(latency_data)


def display_prometheus_stats():
    """Display Prometheus percentile statistics"""
    print_header("Prometheus Statistics (Last 5 minutes)")
    
    queries = {
        "Decryption P95": 'histogram_quantile(0.95, rate(decryption_latency_ms_bucket[5m]))',
        "Decryption P99": 'histogram_quantile(0.99, rate(decryption_latency_ms_bucket[5m]))',
        "Network P95": 'histogram_quantile(0.95, rate(mqtt_receive_latency_ms_bucket[5m]))',
        "Network P99": 'histogram_quantile(0.99, rate(mqtt_receive_latency_ms_bucket[5m]))',
        "E2E P95": 'histogram_quantile(0.95, rate(end_to_end_latency_ms_bucket[5m]))',
        "E2E P99": 'histogram_quantile(0.99, rate(end_to_end_latency_ms_bucket[5m]))',
    }
    
    print(f"{'Metric':<25} {'Value (ms)':<15} {'Status'}")
    print("-" * 50)
    
    for name, query in queries.items():
        value = get_prometheus_metric(query)
        
        # Status indicators
        if "E2E" in name:
            threshold = 1000
            warning = 500
        elif "Network" in name:
            threshold = 500
            warning = 250
        else:
            threshold = 50
            warning = 10
        
        if value > threshold:
            status = "HIGH"
        elif value > warning:
            status = "WARN"
        else:
            status = "OK"
        
        print(f"{name:<25} {value:>6.2f}         {status}")
    
    print()


def monitor_realtime(interval: int = 5):
    """Monitor latencies in real-time"""
    print_header("Real-Time Latency Monitor")
    print(f"Refreshing every {interval} seconds... (Press Ctrl+C to stop)\n")
    
    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{timestamp}]")
            
            latency_data = get_current_latencies()
            display_latency_table(latency_data)
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped\n")


def display_latency_budget():
    """Display latency budget vs actual performance"""
    print_header("Latency Budget Analysis")
    
    budget = [
        ("Sensor Read", 1, 0.2, "Device-side"),
        ("Device Encryption", 10, 2, "Device-side"),
        ("MQTT Transmission", 100, 50, "Network"),
        ("Backend Receive", 5, 5, "Backend"),
        ("Decryption", 10, 2, "Backend"),
        ("Processing", 10, 1, "Backend"),
        ("ML Inference", 50, 10, "ML Service"),
        ("Alert Trigger", 10, 1, "Backend"),
    ]
    
    print(f"{'Component':<25} {'Budget (ms)':<15} {'Actual (ms)':<15} {'Utilization':<15} {'Location'}")
    print("-" * 95)
    
    total_budget = 0
    total_actual = 0
    
    for component, budget_ms, actual_ms, location in budget:
        total_budget += budget_ms
        total_actual += actual_ms
        utilization = (actual_ms / budget_ms) * 100
        
        util_str = f"{utilization:>5.1f}%"
        if utilization > 100:
            util_str = f"HIGH: {util_str}"
        elif utilization > 75:
            util_str = f"WARN: {util_str}"
        else:
            util_str = f"OK: {util_str}"
        
        print(f"{component:<25} {budget_ms:>6.1f}         {actual_ms:>6.1f}         {util_str}         {location}")
    
    print("-" * 95)
    print(f"{'TOTAL':<25} {total_budget:>6.1f}         {total_actual:>6.1f}         {(total_actual/total_budget)*100:>5.1f}%")
    
    margin = 1000 - total_actual
    print(f"\nMargin for critical alerts (< 1s target): {margin:.1f}ms")
    
    if total_actual < 1000:
        print("System is within latency budget for critical alerts!")
    else:
        print("ERROR: System exceeds latency budget - optimization needed!")
    
    print()


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("""
Latency Monitoring Tool
=======================

Usage:
    python latency_monitor.py [command] [options]

Commands:
    current              - Display current latency metrics
    device <device_id>   - Display latency for specific device
    stats                - Display Prometheus percentile statistics
    budget               - Display latency budget analysis
    monitor [interval]   - Real-time monitoring (default: 5s)

Examples:
    python latency_monitor.py current
    python latency_monitor.py device 1_1
    python latency_monitor.py stats
    python latency_monitor.py budget
    python latency_monitor.py monitor 3
        """)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "current":
        display_latency_breakdown()
    
    elif command == "device":
        if len(sys.argv) < 3:
            print("ERROR: Device ID required")
            print("Usage: python latency_monitor.py device <device_id>")
            sys.exit(1)
        device_id = sys.argv[2]
        display_latency_breakdown(device_id)
    
    elif command == "stats":
        display_prometheus_stats()
    
    elif command == "budget":
        display_latency_budget()
    
    elif command == "monitor":
        interval = 5
        if len(sys.argv) >= 3:
            try:
                interval = int(sys.argv[2])
            except ValueError:
                print("ERROR: Interval must be an integer")
                sys.exit(1)
        monitor_realtime(interval)
    
    else:
        print(f"ERROR: Unknown command '{command}'")
        print("Run without arguments for usage information")
        sys.exit(1)


if __name__ == "__main__":
    main()
