"""
leaf_spine.py — Generates a leaf/spine network diagram.

Topology (top to bottom):
  - Optional WAN routers
  - Optional border leaf switches
  - Optional super spine switches
  - One or more fabrics, each containing spine + leaf switches
  - Firewalls, load balancers, and DNS servers on first two leaves of fabric 1
"""

import argparse
from network_diagram import NetworkDiagram, DeviceType


def build_diagram(
    spines:       int,
    leaves:       int,
    borders:      int = 0,
    wan:          int = 0,
    dns:          int = 0,
    super_spines: int = 0,
    fabrics:      int = 1,
) -> NetworkDiagram:
    """Build and return a configured NetworkDiagram (not yet saved)."""
    diagram = NetworkDiagram(f"Leaf-Spine Fabric ({spines} spines, {leaves} leaves)")

    # --- WAN layer ---
    wan_routers = []
    for i in range(1, wan + 1):
        node = diagram.add_node(
            f"wan{i}", f"WAN-{i:02d}\nISR 4321", DeviceType.ROUTER,
            model="Cisco ISR 4321", role="WAN Router", loopback=f"10.3.0.{i}",
        )
        wan_routers.append(node)

    # --- Border layer ---
    border_nodes = []
    for i in range(1, borders + 1):
        node = diagram.add_node(
            f"border{i}", f"Border-{i:02d}\nNexus 93180", DeviceType.SWITCH,
            model="Cisco Nexus 93180YC-FX", role="Border Leaf", loopback=f"10.2.0.{i}",
        )
        border_nodes.append(node)

    # --- Super spine layer ---
    super_spine_nodes = []
    for i in range(1, super_spines + 1):
        node = diagram.add_node(
            f"sspine{i}", f"SS-{i:02d}\nNexus 9508", DeviceType.SUPER_SPINE,
            model="Cisco Nexus 9508", role="Super Spine", loopback=f"10.4.0.{i}",
        )
        super_spine_nodes.append(node)

    # --- Fabric layers (one or more spine+leaf pods) ---
    # Each fabric has its own spine and leaf nodes.
    # Node IDs include the fabric index when fabrics > 1.
    all_fabric_data = []   # list of (spine_nodes, leaf_nodes) per fabric
    all_spine_nodes = []
    all_leaf_nodes  = []

    for f in range(1, fabrics + 1):
        prefix = f"f{f}_" if fabrics > 1 else ""
        label_prefix = f"F{f}-" if fabrics > 1 else ""

        fabric_spines = []
        for i in range(1, spines + 1):
            node = diagram.add_node(
                f"{prefix}spine{i}",
                f"{label_prefix}Spine-{i:02d}\nNexus 9336C",
                DeviceType.SPINE,
                model="Cisco Nexus 9336C-FX2", role="Spine",
                fabric=f if fabrics > 1 else None,
                loopback=f"10.0.{f}.{i}",
            )
            fabric_spines.append(node)

        fabric_leaves = []
        for i in range(1, leaves + 1):
            node = diagram.add_node(
                f"{prefix}leaf{i}",
                f"{label_prefix}Leaf-{i:02d}\nNexus 93180",
                DeviceType.SWITCH,
                model="Cisco Nexus 93180YC-FX", role="Leaf",
                fabric=f if fabrics > 1 else None,
                loopback=f"10.1.{f}.{i}",
                rack=f"Rack-{((i - 1) // 2) + 1}",
            )
            fabric_leaves.append(node)

        all_fabric_data.append((fabric_spines, fabric_leaves))
        all_spine_nodes.extend(fabric_spines)
        all_leaf_nodes.extend(fabric_leaves)

    # --- Connections ---
    for w in wan_routers:
        for b in border_nodes:
            diagram.add_connection(w, b)

    if super_spine_nodes:
        for b in border_nodes:
            for ss in super_spine_nodes:
                diagram.add_connection(b, ss)
        # Super spines connect down to every spine in every fabric
        for ss in super_spine_nodes:
            for s in all_spine_nodes:
                diagram.add_connection(ss, s)
    else:
        for b in border_nodes:
            for s in all_spine_nodes:
                diagram.add_connection(b, s)

    # Within each fabric: every spine → every leaf
    for fabric_spines, fabric_leaves in all_fabric_data:
        for s in fabric_spines:
            for l in fabric_leaves:
                diagram.add_connection(s, l)

    # --- Services — created per fabric ---
    # Node IDs include fabric index when fabrics > 1 to keep them unique.
    firewalls     = []
    load_balancers = []
    dns_servers   = []

    for f, (_, fabric_leaves) in enumerate(all_fabric_data, start=1):
        fp = f"f{f}_" if fabrics > 1 else ""   # fabric prefix for IDs
        fl = f"F{f}-" if fabrics > 1 else ""   # fabric prefix for labels

        # Firewalls
        fab_fws = []
        for i, leaf in enumerate(fabric_leaves[:2], start=1):
            fw = diagram.add_node(f"{fp}fw{i}", f"{fl}FW-{i:02d}\nASA 5516", DeviceType.FIREWALL,
                                  model="Cisco ASA 5516-X", attached_to=leaf.label.split("\n")[0])
            diagram.add_connection(leaf, fw)
            fab_fws.append(fw)
        if len(fab_fws) == 2:
            diagram.add_connection(fab_fws[0], fab_fws[1])
        firewalls.extend(fab_fws)

        # Load balancers
        for i, leaf in enumerate(fabric_leaves[:2], start=1):
            lb = diagram.add_node(f"{fp}lb{i}", f"{fl}LB-{i:02d}\nF5 BIG-IP", DeviceType.LOAD_BALANCER,
                                  model="F5 BIG-IP", attached_to=leaf.label.split("\n")[0])
            diagram.add_connection(leaf, lb)
            load_balancers.append(lb)

        # DNS servers — distributed across first two leaves of each fabric
        for i in range(dns):
            leaf = fabric_leaves[i % 2]
            srv  = diagram.add_node(f"{fp}dns{i + 1}", f"{fl}DNS-{i + 1:02d}", DeviceType.DNS_SERVER,
                                    role="DNS Server", attached_to=leaf.label.split("\n")[0])
            diagram.add_connection(leaf, srv)
            dns_servers.append(srv)

    # --- Bounding boxes ---
    if wan_routers:
        diagram.add_group("WAN", wan_routers, padding=40,
                          fill_color="#fff2cc", stroke_color="#d6b656")

    if fabrics > 1:
        # Per-fabric boxes for spine+leaf pods; nudged apart so they don't overlap
        fabric_colors = [
            ("#dae8fc", "#6c8ebf"),  # blue
            ("#d5e8d4", "#82b366"),  # green
            ("#fff2cc", "#d6b656"),  # yellow
            ("#f8cecc", "#b85450"),  # red
            ("#e1d5e7", "#9673a6"),  # purple
        ]
        nudge_step = 80
        for f, (fabric_spines, fabric_leaves) in enumerate(all_fabric_data):
            nudge = round((-(fabrics - 1) / 2 + f) * nudge_step)
            fill, stroke = fabric_colors[f % len(fabric_colors)]
            diagram.add_group(
                f"Fabric {f + 1}", fabric_spines + fabric_leaves, padding=35,
                fill_color=fill, stroke_color=stroke, h_nudge=nudge,
            )
        # Shared infrastructure box (borders + super spines only)
        shared = border_nodes + super_spine_nodes
        if shared:
            diagram.add_group("Core", shared, padding=40,
                              fill_color="#f5f5f5", stroke_color="#666666")
    else:
        diagram.add_group(
            "Switches", border_nodes + super_spine_nodes + all_spine_nodes + all_leaf_nodes,
            padding=40, fill_color="#dae8fc", stroke_color="#6c8ebf",
        )

    # Service groups — spread evenly so boxes never overlap
    service_groups = []
    if firewalls:
        service_groups.append(("Firewalls",     firewalls,      "#f8cecc", "#b85450"))
    if load_balancers:
        service_groups.append(("Load Balancers", load_balancers, "#d5e8d4", "#82b366"))
    if dns_servers:
        service_groups.append(("DNS Servers",   dns_servers,    "#e9d8fd", "#6a3d9a"))

    n = len(service_groups)
    for i, (label, nodes, fill, stroke) in enumerate(service_groups):
        nudge = round((-(n - 1) / 2 + i) * 220)
        diagram.add_group(label, nodes, padding=40,
                          fill_color=fill, stroke_color=stroke, h_nudge=nudge)

    diagram.H_SPACING = 150
    diagram.V_SPACING = 220

    return diagram


def main():
    parser = argparse.ArgumentParser(description="Generate a leaf-spine network diagram.")
    parser.add_argument("--spine",        type=int, required=True, help="Spine switches per fabric")
    parser.add_argument("--leaf",         type=int, required=True, help="Leaf switches per fabric")
    parser.add_argument("--border",       type=int, default=0, help="Number of border leaf switches")
    parser.add_argument("--wan",          type=int, default=0, help="Number of WAN routers")
    parser.add_argument("--super-spine",  type=int, default=0, help="Number of super spine switches")
    parser.add_argument("--fabric",       type=int, default=1, help="Number of fabrics below the super spine layer")
    parser.add_argument("--dns",          type=int, default=0, help="Number of DNS servers (minimum 2 if set)")
    parser.add_argument("--output",       type=str, default="leaf_spine", help="Output filename without extension")
    args = parser.parse_args()

    if args.dns == 1:
        parser.error("--dns requires a minimum of 2")
    if args.fabric > 1 and args.super_spine == 0:
        parser.error("--fabric requires --super-spine to be set")

    output = args.output.removesuffix(".drawio") + ".drawio"
    diagram = build_diagram(
        args.spine, args.leaf, args.border, args.wan, args.dns,
        args.super_spine, args.fabric,
    )
    diagram.save(output)


if __name__ == "__main__":
    main()
