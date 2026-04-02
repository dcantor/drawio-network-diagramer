# Network Diagram Generator

Generates Cisco and Arista network topology diagrams in [draw.io](https://app.diagrams.net) format. Supports leaf-spine fabrics with optional super spine, WAN, border, multiple fabric pods, and per-fabric services.

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
source .venv/bin/activate
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
| `--spine` | Yes | — | Spine switches per fabric |
| `--leaf` | Yes | — | Leaf switches per fabric |
| `--super-spine` | No | 0 | Super spine switches (between borders and fabric spines) |
| `--fabric` | No | 1 | Number of independent spine+leaf pods below the super spine layer. Requires `--super-spine` |
| `--border` | No | 0 | Border leaf switches (above super spines) |
| `--wan` | No | 0 | WAN routers (above borders) |
| `--vendor` | No | `cisco` | Switch vendor: `cisco` or `arista` |
| `--no-firewalls` | No | — | Omit firewalls |
| `--no-lb` | No | — | Omit load balancers |
| `--dns` | No | — | Add 2 DNS servers per fabric |
| `--ntp` | No | — | Add 2 NTP servers per fabric |
| `--mgmt-pool` | No | — | Subnet to allocate management IPs from (e.g. `10.0.0.0/24`) |
| `--output` | No | `leaf_spine` | Output filename without extension |

### Examples

```bash
# Minimal fabric
python leaf_spine.py --spine 2 --leaf 4

# Arista fabric with all services
python leaf_spine.py --spine 4 --leaf 10 --vendor arista --dns --ntp

# Multi-fabric topology
python leaf_spine.py --spine 4 --leaf 6 --super-spine 2 --fabric 3

# Full topology with management IPs, no load balancers
python leaf_spine.py --spine 4 --leaf 10 --super-spine 2 --fabric 2 \
  --border 2 --wan 2 --vendor cisco --dns --ntp --no-lb \
  --mgmt-pool 10.0.0.0/22 --output my_datacenter
```

## Topology

Layers are stacked top to bottom. Each layer is fully meshed with the layer directly below it.

```
WAN Routers          (--wan)
       │
Border Switches      (--border)
       │
Super Spine          (--super-spine)
     /   \
Fabric 1  Fabric 2 ...        (--fabric)
 Spines    Spines
   │         │
 Leaves    Leaves
 │ │ │ │   │ │ │ │
FW LB DNS NTP  (per fabric, all optional)
```

- **Firewalls** — 2 per fabric, connected to the first two leaf switches (default: on)
- **Load balancers** — 2 per fabric, connected to the first two leaf switches (default: on)
- **DNS servers** — 2 per fabric, connected to the first two leaf switches (default: off)
- **NTP servers** — 2 per fabric, connected to the first two leaf switches (default: off)

## Switch Models

| Role | Cisco | Arista |
|---|---|---|
| Super Spine | N9K-C9504 | DCS-7304X3 |
| Spine | N9K-9508 | DCS-7308X3 |
| Border | N9K-9504 | DCS-7304X3 |
| Leaf | N9K-C93180YC-FX3 | DCS-7050SX3-48YC |

## Diagram Features

- **Cisco icons** for all device types; Arista switches rendered in red to distinguish from Cisco blue
- **Colour-coded bounding boxes** per layer:

  | Box | Colour | Contents |
  |---|---|---|
  | WAN | Yellow | WAN routers |
  | Core | Light grey | Border switches + super spines (multi-fabric only) |
  | Switches | Blue | All switches (single-fabric) |
  | Fabric 1 / 2 / … | Blue, green, yellow, … | Per-fabric spine + leaf nodes (multi-fabric) |
  | Firewalls | Red | Firewall nodes |
  | Load Balancers | Green | Load balancer nodes |
  | DNS Servers | Purple | DNS server nodes |
  | NTP Servers | Orange | NTP server nodes |

- **Straight lines**, no arrowheads
- **Custom Properties** — each node stores model, role, rack, and management IP as draw.io Custom Properties, visible in the Edit Data dialog and on hover

## API

`POST /generate` — accepts JSON, returns a `.drawio` file download.

**Request body:**

```json
{
  "spines":            4,
  "leaves":            10,
  "super_spines":      2,
  "fabrics":           2,
  "borders":           2,
  "wan":               2,
  "vendor":            "cisco",
  "include_firewalls": true,
  "include_lbs":       true,
  "include_dns":       false,
  "include_ntp":       false,
  "mgmt_pool":         "10.0.0.0/22",
  "filename":          "my_datacenter"
}
```

Only `spines` and `leaves` are required. All other fields are optional.

## Files

| File | Description |
|---|---|
| `network_diagram.py` | Core library — `NetworkDiagram` class, device types, auto-layout engine, bounding boxes |
| `leaf_spine.py` | Leaf-spine topology builder — `build_diagram()` function and CLI |
| `api.py` | FastAPI backend |
| `static/index.html` | Web frontend |
| `example.py` | Three-tier office network example |
| `requirements.txt` | Python dependencies (`fastapi`, `uvicorn`) |
