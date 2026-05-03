import requests
import time

#add your fleet node URLs here
FLEET_NODES = ["http://127.0.0.1:8000"]

TARGET_CATEGORIES = ["cpu", "gpu", "ram", "disk", "network"]

def discover_agent(node_url):
    """Fetches and parses the agent card to understand available capabilities."""
    try:
        response = requests.get(f"{node_url}/.well-known/agent-card.json", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return None

def execute_capability(node_url, endpoint, method="GET"):
    """Makes a dynamic HTTP request to a discovered capability endpoint."""
    try:
        url = f"{node_url}{endpoint}"
        response = requests.request(method=method, url=url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException as e:
        print(f"Error executing {url}: {e}")
    return None

def print_payload(data, indent=4):
    """Recursively formats and prints arbitrary JSON dictionaries without hardcoding keys."""
    if not isinstance(data, dict):
        print(f"{' ' * indent}{data}")
        return

    for key, value in data.items():
        formatted_key = str(key).replace("_", " ").title()
        
        if isinstance(value, dict):
            if value:
                print(f"{' ' * indent}{formatted_key}:")
                print_payload(value, indent + 2)
        elif isinstance(value, list):
            if not value:
                print(f"{' ' * indent}{formatted_key}: []")
            elif isinstance(value[0], dict):
                print(f"{' ' * indent}{formatted_key}:")
                for item in value:
                    print_payload(item, indent + 2)
                    print(f"{' ' * (indent + 2)}---")
            else:
                print(f"{' ' * indent}{formatted_key}: {value}")
        else:
            print(f"{' ' * indent}{formatted_key}: {value}")

def run_master():
    """Main execution loop that orchestrates fleet discovery and data aggregation."""
    print("Initializing Fleet Master Agent...")
    
    while True:
        print("\n" + "="*80)
        print(f"FLEET TELEMETRY REPORT - {time.ctime()}")
        print("="*80)
        
        for node in FLEET_NODES:
            card = discover_agent(node)
            if not card:
                print(f"Node {node}: OFFLINE or AgentCard missing.")
                continue
            
            agent_name = card.get('name', 'Unknown Agent')
            print(f"\nNODE: {node} | AGENT: [{agent_name}]")
            print("-" * 40)
            
            capabilities = card.get("capabilities", [])
            
            for cap in capabilities:
                category = cap.get("category")
                if category in TARGET_CATEGORIES:
                    cap_name = cap.get("name", "Unnamed Capability")
                    endpoint = cap.get("endpoint")
                    method = cap.get("method", "GET")
                    
                    print(f"\n>>> Category: {category.upper()} | Capability: {cap_name}")
                    
                    data = execute_capability(node, endpoint, method)
                    
                    if data:
                        print_payload(data)
                    else:
                        print("    [!] Execution failed or returned empty payload.")
                        
        print("\n" + "="*80)
        time.sleep(10)

if __name__ == "__main__":
    run_master()