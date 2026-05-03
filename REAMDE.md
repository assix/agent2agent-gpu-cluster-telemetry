# GPU Cluster Telemetry via A2A Protocol

An advanced Agent-to-Agent (A2A) implementation for monitoring deep hardware telemetry across a fleet of compute nodes (e.g., NVIDIA DGX Spark). 

## Architecture

This project utilizes a decentralized, autonomous multi-agent architecture:
1. **GPU Node Agent (`gpu_node_agent.py`)**: A distributed worker daemon running on individual cluster nodes. It interacts directly with local hardware (NVML, psutil) and exposes capabilities via an A2A AgentCard.
2. **Fleet Master Agent (`master_agent.py`)**: The central orchestration node. It dynamically discovers fleet workers, parses their exposed capabilities, executes relevant endpoints, and dynamically renders the resulting payloads without hardcoded data structures.

---

## The Agent-to-Agent (A2A) Protocol: Deep Dive

This repository serves as a reference implementation for the A2A protocol, which abandons tightly-coupled client-server API contracts in favor of autonomous discovery and dynamic execution.

### 1. Core Philosophy: Absolute Decoupling
In traditional architectures, the Master node must know the exact API endpoints, HTTP methods, and response schemas of the Worker nodes. In A2A, the Master knows **nothing** about the Worker in advance. The Master only knows *how to read an AgentCard* and *how to execute categorized capabilities*.

### 2. The AgentCard (`/.well-known/agent-card.json`)
The foundation of A2A discovery. Every participating agent hosts a standardized JSON manifest at a globally recognized path. 
* It acts as the agent's digital identity.
* It explicitly defines the agent's **Capabilities** (skills).

### 3. Categorical Discovery vs. Hardcoded Endpoints
Instead of the Master asking, *"What is your CPU load endpoint?"* (which breaks if the endpoint name changes), the Master dynamically loops through the AgentCard and asks, *"Do you have any capabilities in the `cpu` category?"*

```json
{
  "name": "Processor Telemetry",
  "category": "cpu",
  "endpoint": "/a2a/cpu",
  "method": "GET"
}
```
If the Worker upgrades its API to `/v2/hardware/cpu_metrics`, it only updates its AgentCard. The Master immediately adapts without a single line of code changing.

### 4. Schema-Agnostic Execution
The A2A Master does not hardcode JSON key lookups (e.g., `print(data['cpu']['utilization'])`). Instead, it treats the returned payload as an arbitrary data structure and recursively parses it. This allows the Worker to return entirely new metrics (e.g., adding L2 cache stats or Infiniband throughput) and the Master will automatically display them.

### 5. The Standard A2A Interaction Flow
1. **Discovery:** Master queries `http://<node-ip>/.well-known/agent-card.json`.
2. **Parsing:** Master identifies capabilities matching its target categories (`cpu`, `gpu`, `ram`, `disk`, `network`).
3. **Execution:** Master dynamically constructs the request using the `endpoint` and `method` defined in the card.
4. **Ingestion:** Master receives the arbitrary JSON payload and dynamically renders it.

---

## Prerequisites

```bash
pip install fastapi uvicorn psutil requests nvidia-ml-py
```

## Usage

### 1. Start the GPU Node Agent
Deploy this to your cluster nodes (e.g., DGX Spark):
```bash
python3 gpu_node_agent.py &
```
*Hosts the AgentCard at `http://<node-ip>:8000/.well-known/agent-card.json`*

### 2. Start the Master Agent
Edit `FLEET_NODES` in `master_agent.py` to target your cluster IPs, then run:
```bash
python3 fmaster_agent.py
```