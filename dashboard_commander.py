# dashboard_commander.py
import requests
import time
import json

# List of known DGX worker IPs (assuming running locally on port 8000 for this example)
FLEET_NODES = ["http://127.0.0.1:8000"]

# Alert Thresholds
TEMP_THRESHOLD = 80.0
DISK_THRESHOLD = 90.0
RAM_THRESHOLD = 95.0

def discover_capabilities(node_url):
    try:
        response = requests.get(f"{node_url}/.well-known/agent-card.json", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None

def fetch_telemetry(node_url, endpoint):
    try:
        response = requests.post(f"{node_url}{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None

def run_dashboard():
    print("Initializing Fleet Dashboard...")
    
    while True:
        print("\n" + "="*50)
        print(f"DGX FLEET STATUS - {time.ctime()}")
        print("="*50)
        
        for node in FLEET_NODES:
            card = discover_capabilities(node)
            if not card:
                print(f"Node {node}: OFFLINE or AgentCard not found.")
                continue
                
            # Find the telemetry capability
            telemetry_endpoint = None
            for cap in card.get("capabilities", []):
                if cap["name"] == "get_system_telemetry":
                    telemetry_endpoint = cap["endpoint"]
                    break
            
            if not telemetry_endpoint:
                print(f"Node {node}: Telemetry capability not exposed.")
                continue
                
            data = fetch_telemetry(node, telemetry_endpoint)
            if not data:
                print(f"Node {node}: Failed to fetch telemetry data.")
                continue

            # Display Data
            print(f"Node: {node}")
            print(f"  CPU: {data['cpu']['overall_utilization']:.1f}%")
            print(f"  RAM: {data['ram']['used_gb']}GB / {data['ram']['total_gb']}GB ({data['ram']['percent']}%)")
            print(f"  Disk: {data['disk']['used_tb']}TB / {data['disk']['total_tb']}TB ({data['disk']['percent']}%)")
            
            if data['gpu']:
                print(f"  GPU: {data['gpu']['utilization_percent']}% Util | {data['gpu']['temperature_c']}C | {data['gpu']['power_draw_w']}W")
                
                # Alerting Logic
                if data['gpu']['temperature_c'] > TEMP_THRESHOLD:
                    print(f"  [!] ALERT: GPU Temperature Critical ({data['gpu']['temperature_c']}C)")
            
            if data['ram']['percent'] > RAM_THRESHOLD:
                print(f"  [!] ALERT: Memory capacity near limit ({data['ram']['percent']}%)")
            if data['disk']['percent'] > DISK_THRESHOLD:
                print(f"  [!] ALERT: NVMe storage near limit ({data['disk']['percent']}%)")
                
        print("="*50)
        time.sleep(10)

if __name__ == "__main__":
    run_dashboard()