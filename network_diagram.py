"""
network_diagram.py — Generate draw.io (.drawio) network diagrams from Python.
"""

import xml.etree.ElementTree as ET
from collections import deque
from enum import Enum


class DeviceType(Enum):
    ROUTER = "router"
    SWITCH = "switch"
    SPINE = "spine"
    SUPER_SPINE = "super_spine"
    ARISTA_SWITCH = "arista_switch"
    ARISTA_SPINE = "arista_spine"
    ARISTA_SUPER_SPINE = "arista_super_spine"
    FIREWALL = "firewall"
    SERVER = "server"
    WORKSTATION = "workstation"
    CLOUD = "cloud"
    LOAD_BALANCER = "load_balancer"
    DNS_SERVER = "dns_server"
    NTP_SERVER = "ntp_server"
    GENERIC = "generic"


# draw.io styles for each device type
_STYLES = {
    DeviceType.ROUTER: (
        "shape=mxgraph.cisco.routers.router;html=1;pointerEvents=1;dashed=0;"
        "fillColor=#036897;strokeColor=#ffffff;strokeWidth=2;"
        "verticalLabelPosition=bottom;verticalAlign=top;align=center;outlineConnect=0;"
    ),
    DeviceType.SWITCH: (
        "shape=mxgraph.cisco.switches.workgroup_switch;html=1;pointerEvents=1;dashed=0;"
        "fillColor=#036897;strokeColor=#ffffff;strokeWidth=2;"
        "verticalLabelPosition=bottom;verticalAlign=top;align=center;outlineConnect=0;"
    ),
    DeviceType.SPINE: (
        "shape=mxgraph.cisco.switches.workgroup_switch;html=1;pointerEvents=1;dashed=0;"
        "fillColor=#036897;strokeColor=#ffffff;strokeWidth=2;"
        "verticalLabelPosition=top;verticalAlign=bottom;align=center;outlineConnect=0;"
    ),
    DeviceType.SUPER_SPINE: (
        "shape=mxgraph.cisco.switches.workgroup_switch;html=1;pointerEvents=1;dashed=0;"
        "fillColor=#023d5a;strokeColor=#ffffff;strokeWidth=2;"
        "verticalLabelPosition=top;verticalAlign=bottom;align=center;outlineConnect=0;"
    ),
    DeviceType.ARISTA_SWITCH: (
        "shape=mxgraph.cisco.switches.workgroup_switch;html=1;pointerEvents=1;dashed=0;"
        "fillColor=#cc2030;strokeColor=#ffffff;strokeWidth=2;"
        "verticalLabelPosition=bottom;verticalAlign=top;align=center;outlineConnect=0;"
    ),
    DeviceType.ARISTA_SPINE: (
        "shape=mxgraph.cisco.switches.workgroup_switch;html=1;pointerEvents=1;dashed=0;"
        "fillColor=#cc2030;strokeColor=#ffffff;strokeWidth=2;"
        "verticalLabelPosition=top;verticalAlign=bottom;align=center;outlineConnect=0;"
    ),
    DeviceType.ARISTA_SUPER_SPINE: (
        "shape=mxgraph.cisco.switches.workgroup_switch;html=1;pointerEvents=1;dashed=0;"
        "fillColor=#8b0000;strokeColor=#ffffff;strokeWidth=2;"
        "verticalLabelPosition=top;verticalAlign=bottom;align=center;outlineConnect=0;"
    ),
    DeviceType.FIREWALL: (
        "shape=mxgraph.cisco.firewalls.firewall;html=1;pointerEvents=1;dashed=0;"
        "fillColor=#AE4132;strokeColor=#ffffff;strokeWidth=2;"
        "verticalLabelPosition=bottom;verticalAlign=top;align=center;outlineConnect=0;"
    ),
    DeviceType.SERVER: (
        "shape=mxgraph.cisco.servers.standard_server;html=1;pointerEvents=1;dashed=0;"
        "fillColor=#036897;strokeColor=#ffffff;strokeWidth=2;"
        "verticalLabelPosition=bottom;verticalAlign=top;align=center;outlineConnect=0;"
    ),
    DeviceType.WORKSTATION: (
        "shape=mxgraph.cisco.computers_and_peripherals.pc;html=1;pointerEvents=1;dashed=0;"
        "fillColor=#036897;strokeColor=#ffffff;strokeWidth=2;"
        "verticalLabelPosition=bottom;verticalAlign=top;align=center;outlineConnect=0;"
    ),
    DeviceType.LOAD_BALANCER: (
        "shape=mxgraph.cisco.switches.content_switch;html=1;pointerEvents=1;dashed=0;"
        "fillColor=#036897;strokeColor=#ffffff;strokeWidth=2;"
        "verticalLabelPosition=bottom;verticalAlign=top;align=center;outlineConnect=0;"
    ),
    DeviceType.DNS_SERVER: (
        "shape=mxgraph.cisco.servers.standard_server;html=1;pointerEvents=1;dashed=0;"
        "fillColor=#6a3d9a;strokeColor=#ffffff;strokeWidth=2;"
        "verticalLabelPosition=bottom;verticalAlign=top;align=center;outlineConnect=0;"
    ),
    DeviceType.NTP_SERVER: (
        "shape=mxgraph.cisco.servers.standard_server;html=1;pointerEvents=1;dashed=0;"
        "fillColor=#d79b00;strokeColor=#ffffff;strokeWidth=2;"
        "verticalLabelPosition=bottom;verticalAlign=top;align=center;outlineConnect=0;"
    ),
    DeviceType.CLOUD: (
        "ellipse;whiteSpace=wrap;html=1;aspect=fixed;shape=cloud;"
        "fillColor=#dae8fc;strokeColor=#6c8ebf;"
    ),
    DeviceType.GENERIC: (
        "rounded=1;whiteSpace=wrap;html=1;"
        "fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;"
    ),
}

_SIZE = {
    DeviceType.ROUTER:      (50, 50),
    DeviceType.SWITCH:      (50, 50),
    DeviceType.SPINE:       (50, 50),
    DeviceType.SUPER_SPINE:       (50, 50),
    DeviceType.ARISTA_SWITCH:     (50, 50),
    DeviceType.ARISTA_SPINE:      (50, 50),
    DeviceType.ARISTA_SUPER_SPINE:(50, 50),
    DeviceType.FIREWALL:    (50, 50),
    DeviceType.SERVER:      (30, 50),
    DeviceType.WORKSTATION: (50, 50),
    DeviceType.LOAD_BALANCER: (50, 50),
    DeviceType.DNS_SERVER:   (30, 50),
    DeviceType.NTP_SERVER:   (30, 50),
    DeviceType.CLOUD:       (120, 80),
    DeviceType.GENERIC:     (120, 60),
}

_EDGE_STYLE = "html=1;rounded=0;edgeStyle=none;endArrow=none;startArrow=none;"


class Node:
    def __init__(self, node_id: str, label: str, device_type: DeviceType, **attrs):
        self.node_id = node_id
        self.label = label
        self.device_type = device_type
        self.attrs = attrs          # e.g. ip, vlan, description
        self.x: float = 0
        self.y: float = 0


class Connection:
    def __init__(self, conn_id: str, source: Node, target: Node, label: str = ""):
        self.conn_id = conn_id
        self.source = source
        self.target = target
        self.label = label


class NetworkDiagram:
    """
    Build a network diagram and export it as a .drawio file.

    Usage:
        diagram = NetworkDiagram("My Network")
        fw  = diagram.add_node("fw1",  "Firewall",  DeviceType.FIREWALL)
        sw  = diagram.add_node("sw1",  "Core SW",   DeviceType.SWITCH)
        srv = diagram.add_node("srv1", "Web Server", DeviceType.SERVER)
        diagram.add_connection(fw, sw,  label="Gi0/0 — 10.0.0.0/30")
        diagram.add_connection(sw, srv, label="Fa0/1")
        diagram.save("my_network.drawio")
    """

    # Layout tuning
    H_SPACING = 160   # horizontal gap between nodes on the same level
    V_SPACING = 140   # vertical gap between levels

    def __init__(self, name: str = "Network Diagram"):
        self.name = name
        self._nodes: dict[str, Node] = {}
        self._connections: list[Connection] = []
        self._groups: list[tuple[str, list[Node], int]] = []
        self._cell_counter = 2          # 0 and 1 are reserved by draw.io

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_node(
        self,
        node_id: str,
        label: str,
        device_type: DeviceType = DeviceType.GENERIC,
        **attrs,
    ) -> Node:
        """Add a device node.  Returns the Node so it can be used in add_connection()."""
        if node_id in self._nodes:
            raise ValueError(f"Node '{node_id}' already exists.")
        node = Node(node_id, label, device_type, **attrs)
        self._nodes[node_id] = node
        return node

    def add_group(
        self,
        label: str,
        nodes: list[Node],
        padding: int = 30,
        fill_color: str = "none",
        stroke_color: str = "#666666",
        h_nudge: int = 0,
    ) -> None:
        """Draw a labeled bounding box around a set of nodes.
        h_nudge shifts the group's nodes left (negative) or right (positive) after layout.
        """
        self._groups.append((label, nodes, padding, fill_color, stroke_color, h_nudge))

    def add_connection(
        self,
        source: Node,
        target: Node,
        label: str = "",
    ) -> Connection:
        """Connect two nodes with an optional label."""
        conn_id = f"e{len(self._connections)}"
        conn = Connection(conn_id, source, target, label)
        self._connections.append(conn)
        return conn

    def to_xml(self) -> str:
        """Auto-layout nodes and return the .drawio XML as a string."""
        self._auto_layout()
        self._apply_nudges()
        return self._build_xml()

    def save(self, path: str) -> None:
        """Auto-layout nodes and write the .drawio XML file."""
        xml_str = self.to_xml()
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        print(f"Saved: {path}  ({len(self._nodes)} nodes, {len(self._connections)} connections)")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _apply_nudges(self) -> None:
        for _label, nodes, _padding, _fill, _stroke, h_nudge in self._groups:
            if h_nudge:
                for node in nodes:
                    node.x += h_nudge

    def _auto_layout(self) -> None:
        """BFS hierarchical layout.  Root = nodes with no incoming edges."""
        if not self._nodes:
            return

        # Build adjacency
        children: dict[str, list[str]] = {nid: [] for nid in self._nodes}
        parents: dict[str, list[str]] = {nid: [] for nid in self._nodes}
        for conn in self._connections:
            children[conn.source.node_id].append(conn.target.node_id)
            parents[conn.target.node_id].append(conn.source.node_id)

        roots = [nid for nid, plist in parents.items() if not plist]
        if not roots:
            roots = [next(iter(self._nodes))]   # cycle fallback

        # BFS to assign levels
        level_of: dict[str, int] = {}
        queue: deque[str] = deque()
        for r in roots:
            level_of[r] = 0
            queue.append(r)

        while queue:
            nid = queue.popleft()
            for child in children[nid]:
                if child not in level_of:
                    level_of[child] = level_of[nid] + 1
                    queue.append(child)

        # Catch any nodes not reached (disconnected)
        max_level = max(level_of.values(), default=0)
        for nid in self._nodes:
            if nid not in level_of:
                max_level += 1
                level_of[nid] = max_level

        # Group nodes by level
        levels: dict[int, list[str]] = {}
        for nid, lvl in level_of.items():
            levels.setdefault(lvl, []).append(nid)

        # Sort within each level by group membership so same-group nodes are
        # adjacent (prevents interleaving when nudges are applied later).
        group_sort: dict[str, int] = {}
        for gi, (_, gnodes, *_) in enumerate(self._groups):
            for node in gnodes:
                group_sort.setdefault(node.node_id, gi)
        insertion_order = {nid: i for i, nid in enumerate(self._nodes)}

        # Assign x, y
        for lvl, nids in sorted(levels.items()):
            nids.sort(key=lambda nid: (
                group_sort.get(nid, len(self._groups)),
                insertion_order[nid],
            ))
            total_width = (len(nids) - 1) * self.H_SPACING
            start_x = -total_width / 2
            for i, nid in enumerate(nids):
                node = self._nodes[nid]
                w, h = _SIZE[node.device_type]
                node.x = start_x + i * self.H_SPACING - w / 2
                node.y = lvl * self.V_SPACING

    # ------------------------------------------------------------------
    # XML generation
    # ------------------------------------------------------------------

    def _next_id(self) -> str:
        cid = str(self._cell_counter)
        self._cell_counter += 1
        return cid

    def _build_xml(self) -> str:
        mxfile = ET.Element("mxfile", host="app.diagrams.net")
        diagram = ET.SubElement(mxfile, "diagram", name=self.name)
        model = ET.SubElement(
            diagram,
            "mxGraphModel",
            dx="1422", dy="762", grid="1", gridSize="10",
            guides="1", tooltips="1", connect="1", arrows="1",
            fold="1", page="1", pageScale="1",
            pageWidth="1169", pageHeight="827",
            math="0", shadow="0",
        )
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")

        # Bounding-box groups (rendered first so they sit behind nodes)
        _GROUP_STYLE_BASE = (
            "rounded=1;whiteSpace=wrap;html=1;dashed=1;strokeWidth=2;"
            "verticalAlign=top;fontSize=13;fontStyle=1;align=left;spacingLeft=10;"
        )
        for label, nodes, padding, fill_color, stroke_color, _nudge in self._groups:
            xs = [n.x for n in nodes]
            ys = [n.y for n in nodes]
            x2s = [n.x + _SIZE[n.device_type][0] for n in nodes]
            y2s = [n.y + _SIZE[n.device_type][1] for n in nodes]
            bx = min(xs) - padding
            by = min(ys) - padding
            bw = max(x2s) - min(xs) + padding * 2
            bh = max(y2s) - min(ys) + padding * 2
            style = (
                _GROUP_STYLE_BASE
                + f"fillColor={fill_color};strokeColor={stroke_color};"
            )
            cell = ET.SubElement(
                root, "mxCell",
                id=self._next_id(),
                value=label,
                style=style,
                vertex="1",
                parent="1",
            )
            ET.SubElement(
                cell, "mxGeometry",
                x=str(round(bx)),
                y=str(round(by)),
                width=str(round(bw)),
                height=str(round(bh)),
                **{"as": "geometry"},
            )

        # Assign stable XML IDs to nodes
        id_map: dict[str, str] = {}
        for nid, node in self._nodes.items():
            xml_id = self._next_id()
            id_map[nid] = xml_id
            w, h = _SIZE[node.device_type]
            style = _STYLES[node.device_type]

            # Build tooltip string from non-None attrs (shown on hover in draw.io)
            tooltip = "  ".join(
                f"{k}: {v}" for k, v in node.attrs.items() if v is not None
            )

            # UserObject wraps mxCell so each attr becomes a draw.io Custom Property
            user_obj_attrs = {"label": node.label, "id": xml_id, "tooltip": tooltip}
            for k, v in node.attrs.items():
                if v is not None:
                    user_obj_attrs[k] = str(v)
            user_obj = ET.SubElement(root, "UserObject", **user_obj_attrs)

            cell = ET.SubElement(
                user_obj, "mxCell",
                style=style,
                vertex="1",
                parent="1",
            )
            ET.SubElement(
                cell, "mxGeometry",
                x=str(round(node.x)),
                y=str(round(node.y)),
                width=str(w),
                height=str(h),
                **{"as": "geometry"},
            )

        # Edges
        for conn in self._connections:
            xml_id = self._next_id()
            cell = ET.SubElement(
                root, "mxCell",
                id=xml_id,
                value=conn.label,
                style=_EDGE_STYLE,
                edge="1",
                source=id_map[conn.source.node_id],
                target=id_map[conn.target.node_id],
                parent="1",
            )
            ET.SubElement(cell, "mxGeometry", relative="1", **{"as": "geometry"})

        ET.indent(mxfile, space="  ")
        return ET.tostring(mxfile, encoding="unicode", xml_declaration=True)
