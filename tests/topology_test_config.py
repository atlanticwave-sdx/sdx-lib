from sdxlib.sdx_topology import *

# Sample Location
sample_location = Location(
    address="123 Main St", latitude=37.7749, longitude=-122.4194, iso3166_2_lvl4="US-FL"
)

# **Valid Ports**
sample_port1 = Port(
    name="Port1",
    id="urn:sdx:port:amlight.net:Node1:Port1",
    node="urn:sdx:node:amlight.net:Node1",
    type=PortType.GE_10,
    status=Status.UP,
    state=State.ENABLED,
)

sample_port2 = Port(
    name="Port2",
    id="urn:sdx:port:amlight.net:Node2:Port2",
    node="urn:sdx:node:amlight.net:Node2",
    type=PortType.GE_10,
    status=Status.UP,
    state=State.ENABLED,
    entities=["Sprace", "UNESP", "LHC Tier 2 Brazil"],
)

# **Invalid Ports for Testing**
invalid_port_long_name = {
    "name": "A" * 31,  # Exceeds max length
    "id": "urn:sdx:port:amlight.net:Node1:Port1",
    "node": "urn:sdx:node:amlight.net:Node1",
    "type": PortType.GE_10,
    "status": Status.UP,
    "state": State.ENABLED,
}

invalid_port_special_chars = {
    "name": "Invalid@Port!",
    "id": "urn:sdx:port:amlight.net:Node1:Port1",
    "node": "urn:sdx:node:amlight.net:Node1",
    "type": PortType.GE_10,
    "status": Status.UP,
    "state": State.ENABLED,
}

invalid_port_bad_id = {
    "name": "Port1",
    "id": "bad_id_format",  # Invalid format
    "node": "urn:sdx:node:amlight.net:Node1",
    "type": PortType.GE_10,
    "status": Status.UP,
    "state": State.ENABLED,
}

invalid_port_mtu_low = {
    "name": "Port1",
    "id": "urn:sdx:port:amlight.net:Node1:Port1",
    "node": "urn:sdx:node:amlight.net:Node1",
    "type": PortType.GE_10,
    "status": Status.UP,
    "state": State.ENABLED,
    "mtu": 1400,  # Too low
}

invalid_port_mtu_high = {
    "name": "Port1",
    "id": "urn:sdx:port:amlight.net:Node1:Port1",
    "node": "urn:sdx:node:amlight.net:Node1",
    "type": PortType.GE_10,
    "status": Status.UP,
    "state": State.ENABLED,
    "mtu": 12000,  # Too high
}

# **Sample Nodes (Now using predefined sample ports)**
sample_node1 = Node(
    name="switch01",
    id="urn:sdx:node:amlight.net:switch01",
    location=sample_location,
    ports=[sample_port1],
    status=Status.UP,
    state=State.ENABLED,
)

sample_node2 = Node(
    name="switch02",
    id="urn:sdx:node:amlight.net:switch02",
    location=sample_location,
    ports=[sample_port2],
    status=Status.UP,
    state=State.ENABLED,
)

# **Sample Link**
sample_link = Link(
    name="100G_Sao_Paulo_to_Miami",
    id="urn:sdx:link:amlight.net:saopaulo_miami",
    ports=[sample_port1.id, sample_port2.id],
    bandwidth=100.0,
    residual_bandwidth=50.0,
    latency=10.5,
    packet_loss=0.5,
    availability=99.9,
    status=Status.UP,
    state=State.ENABLED,
    private=["residual_bandwidth"],
)

# **Valid Nodes and Links**
valid_nodes = [sample_node1, sample_node2]
valid_links = [sample_link]

# **Use Dictionaries in Topology**
valid_topology = {
    "name": "Test-Topology",
    "id": "urn:sdx:topology:amlight.net",
    "version": 1,
    "timestamp": "2024-02-20T12:00:00Z",
    "nodes": valid_nodes,
    "links": valid_links,
}

# **Invalid Topology (Empty Nodes)**
invalid_topology_empty_nodes = {
    "name": "Invalid Topology",
    "id": "urn:sdx:topology:amlight.net",
    "version": 1,
    "timestamp": "2024-02-20T12:34:56Z",
    "nodes": [],  # Should raise error
    "links": valid_links,
}

# **Invalid Topology (Bad ID)**
invalid_topology_bad_id = {
    "name": "Invalid ID",
    "id": "bad_id_format",  # Invalid ID format
    "version": 1,
    "timestamp": "2024-02-20T12:34:56Z",
    "nodes": valid_nodes,
    "links": valid_links,
}
