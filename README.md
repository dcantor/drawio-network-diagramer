# Network Diagram Generator

Generates Cisco network topology diagrams in [draw.io](https://app.diagrams.net) format. Supports leaf-spine fabrics with optional WAN, border, firewall, load balancer, and DNS layers.

## Quick Start

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Web App

```bash
uvicorn api:app --reload
```

Open **http://localhost:8000** in your browser. Fill in the form and click **Generate & Download** to get a `.drawio` file.

## CLI

```bash
python leaf_spine.py --spine <n> --leaf <n> [options]
```

Output is saved to `leaf_spine.drawio` in the current directory.

### Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `--spine` | Yes | — | Number of spine switches (Cisco Nexus 9336C-FX2) |
| `--leaf` | Yes | — | Number of leaf switches (Cisco Nexus 93180YC-FX) |
| `--border` | No | 0 | Number of border leaf switches (appear above spines) |
| `--wan` | No | 0 | Number of WAN routers (appear above borders, Cisco ISR 4321) |
| `--dns` | No | 0 | Number of DNS servers — minimum 2 if set |

### Examples

```bash
# Minimal fabric
python leaf_spine.py --spine 2 --leaf 4

# Full topology
python leaf_spine.py --spine 4 --leaf 10 --border 2 --wan 2 --dns 4
```

## Topology

Layers are stacked top to bottom in the diagram:

```
WAN Routers        (--wan)
     │
Border Switches    (--border)
     │
Spine Switches     (--spine)       ← every spine connects to every leaf
     │
Leaf Switches      (--leaf)
   │   │
  FW  LB  DNS      fixed 2 FWs, 2 LBs on first two leaves; DNS distributed across first two leaves
```

Each layer is fully meshed with the layer below it. The first two leaf switches also have firewalls and load balancers attached.

## Diagram Features

- **Cisco icons** — routers, switches, firewalls, servers, load balancers
- **Bounding boxes** — colour-coded groups for each layer:
  - WAN — yellow
  - Switches — blue
  - Firewalls — red
  - Load Balancers — green
  - DNS Servers — purple
- **Straight lines**, no arrowheads
- **Tooltips** — hover over any node in draw.io to see model, IP, and role

## API

`POST /generate` — returns a `.drawio` file download.

**Request body (JSON):**

```json
{
  "spines":  4,
  "leaves":  10,
  "borders": 2,
  "wan":     2,
  "dns":     4
}
```

Interactive API docs available at **http://localhost:8000/docs** when the server is running.

## Files

| File | Description |
|---|---|
| `network_diagram.py` | Core library — `NetworkDiagram` class, device types, layout engine |
| `leaf_spine.py` | Leaf-spine topology builder — CLI and `build_diagram()` function |
| `api.py` | FastAPI backend |
| `static/index.html` | Web frontend |
| `example.py` | Three-tier office network example |
