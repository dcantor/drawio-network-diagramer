"""
example.py — Demonstrates building a typical three-tier network diagram.

Topology:
    Internet (cloud)
        |
    Firewall
        |
    Core Router
      /     \\
  SW-1      SW-2
  / \\        / \\
SRV1 SRV2  PC1  PC2
"""

from network_diagram import NetworkDiagram, DeviceType


def main():
    diagram = NetworkDiagram("Three-Tier Office Network")

    # Tier 0 — Internet
    internet = diagram.add_node("internet", "Internet", DeviceType.CLOUD)

    # Tier 1 — Edge
    fw = diagram.add_node(
        "fw1", "Firewall",
        DeviceType.FIREWALL,
        ip="203.0.113.1",
        model="Cisco ASA 5506",
    )

    # Tier 2 — Core
    router = diagram.add_node(
        "router1", "Core Router",
        DeviceType.ROUTER,
        ip="10.0.0.1",
        model="Cisco ISR 4321",
    )

    # Tier 3 — Distribution
    sw1 = diagram.add_node(
        "sw1", "SW-1 (Servers)",
        DeviceType.SWITCH,
        ip="10.0.1.1",
        vlan="VLAN 10",
    )
    sw2 = diagram.add_node(
        "sw2", "SW-2 (Users)",
        DeviceType.SWITCH,
        ip="10.0.2.1",
        vlan="VLAN 20",
    )

    # Tier 4 — End devices
    srv1 = diagram.add_node("srv1", "Web Server",  DeviceType.SERVER, ip="10.0.1.10")
    srv2 = diagram.add_node("srv2", "DB Server",   DeviceType.SERVER, ip="10.0.1.11")
    pc1  = diagram.add_node("pc1",  "Workstation 1", DeviceType.WORKSTATION, ip="10.0.2.10")
    pc2  = diagram.add_node("pc2",  "Workstation 2", DeviceType.WORKSTATION, ip="10.0.2.11")

    # Connections
    diagram.add_connection(internet, fw,     label="WAN")
    diagram.add_connection(fw,       router, label="10.0.0.0/30")
    diagram.add_connection(router,   sw1,    label="Gi0/0 — 10.0.1.0/24")
    diagram.add_connection(router,   sw2,    label="Gi0/1 — 10.0.2.0/24")
    diagram.add_connection(sw1,      srv1,   label="Fa0/1")
    diagram.add_connection(sw1,      srv2,   label="Fa0/2")
    diagram.add_connection(sw2,      pc1,    label="Fa0/1")
    diagram.add_connection(sw2,      pc2,    label="Fa0/2")

    diagram.save("three_tier_network.drawio")


if __name__ == "__main__":
    main()
