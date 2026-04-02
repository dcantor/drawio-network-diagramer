# Network Diagram Generator

Generates Cisco network topology diagrams in [draw.io](https://app.diagrams.net) format. Supports leaf-spine fabrics with optional super spine, WAN, border, multiple fabric pods, firewalls, load balancers, and DNS servers.

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

Interactive API docs are available at **http://localhost:8000/docs**.

## CLI

```bash
python leaf_spine.py --spine <n> --leaf <n> [options]
```

Output is saved to `leaf_spine.drawio` by default. Use `--output` for a custom filename.

### Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `--spine` | Yes | — | Spine switches per fabric (Cisco Nexus 9336C-FX2) |
| `--leaf` | Yes | — | Leaf switches per fabric (Cisco Nexus 93180YC-FX) |
| `--super-spine` | No | 0 | Super spine switches — sit between borders and fabric spines (Cisco Nexus 9508) |
| `--fabric` | No | 1 | Number of independent spine+leaf pods below the super spine layer. Requires `--super-spine` |
| `--border` | No | 0 | Border leaf switches — sit above super spines (Cisco Nexus 93180YC-FX) |
| `--wan` | No | 0 | WAN routers — sit above borders (Cisco ISR 4321) |
| `--dns` | No | 0 | DNS servers per fabric — minimum 2 if set |
| `--output` | No | `leaf_spine` | Output filename without extension |

### Examples

```bash
# Minimal fabric
python leaf_spine.py --spine 2 --leaf 4

# Full single-fabric topology
python leaf_spine.py --spine 4 --leaf 10 --border 2 --wan 2 --dns 4

# Multi-fabric topology with super spine
python leaf_spine.py --spine 4 --leaf 6 --super-spine 2 --fabric 3

# Everything
python leaf_spine.py --spine 4 --leaf 10 --super-spine 2 --fabric 2 --border 2 --wan 2 --dns 4 --output my_datacenter
```

## Topology

Layers are stacked top to bottom. Each layer is fully meshed with the layer directly below it.

```
WAN Routers          (--wan)
       │
Border Switches      (--border)
       │
Super Spine          (--super-spine)
     / | \
    /  |  \──────────────────────┐
   │         Fabric 1            │         Fabric 2 ...   (--fabric)
   │   Spine Switches (--spine)  │   Spine Switches
   │         │                   │         │
   │   Leaf Switches  (--leaf)   │   Leaf Switches
   │   │    │    │               │   │    │    │
   │  FW   LB  DNS               │  FW   LB  DNS
   └───────────────────────────────────────────────────────
```

- **Firewalls** and **load balancers** are always created — 2 per fabric, attached to the first two leaf switches of each fabric
- **DNS servers** (`--dns`) are distributed across the first two leaf switches of each fabric
- When only one fabric is used (default), the `--super-spine` and `--fabric` arguments are optional

## Diagram Features

- **Cisco icons** — routers, switches (spine, super spine, border, leaf), firewalls, servers, load balancers
- **Colour-coded bounding boxes** per layer:

  | Box | Colour | Contents |
  |---|---|---|
  | WAN | Yellow | WAN routers |
  | Core | Light grey | Border switches + super spines (multi-fabric only) |
  | Switches | Blue | All switches (single-fabric) |
  | Fabric 1 / 2 / … | Blue, green, yellow, … | Per-fabric spine + leaf nodes (multi-fabric) |
  | Firewalls | Red | All firewall nodes |
  | Load Balancers | Green | All load balancer nodes |
  | DNS Servers | Purple | All DNS server nodes |

- **Straight lines**, no arrowheads
- **Tooltips** — hover any node in draw.io to see model, IP, role, and rack

## API

`POST /generate` — accepts JSON, returns a `.drawio` file download.

**Request body:**

```json
{
  "spines":       4,
  "leaves":       10,
  "super_spines": 2,
  "fabrics":      2,
  "borders":      2,
  "wan":          2,
  "dns":          4,
  "filename":     "my_datacenter"
}
```

All fields except `spines` and `leaves` are optional.

## Files

| File | Description |
|---|---|
| `network_diagram.py` | Core library — `NetworkDiagram` class, device types, auto-layout engine, bounding boxes |
| `leaf_spine.py` | Leaf-spine topology builder — `build_diagram()` function and CLI |
| `api.py` | FastAPI backend |
| `static/index.html` | Web frontend |
| `example.py` | Three-tier office network example |
| `requirements.txt` | Python dependencies (`fastapi`, `uvicorn`) |
