import pycountry
import re

from dacite import from_dict, Config
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

# Global Constants
MODEL_VERSION = "2.0.0"

# # Regex Patterns
# Matches name pattern
NAME_PATTERN = re.compile(r"^[\w.,\-/]{1,30}$")

# Matches topology URNs: urn:sdx:topology:<oxp_url>
URN_TOPOLOGY_PATTERN = re.compile(r"^urn:sdx:topology:[a-zA-Z0-9.-]+\.[a-zA-Z]{2,3}$")
# Matches node URNs: urn:sdx:node:<oxp_url>:<node_name>
URN_NODE_PATTERN = re.compile(
    r"^urn:sdx:node:[a-zA-Z0-9.-]+\.[a-zA-Z]{2,3}:[\w.,\-/]{1,30}$"
)
# Matches port URNs: urn:sdx:port:<oxp_url>:<node_name>:<port_name>
URN_PORT_PATTERN = re.compile(
    r"^urn:sdx:port:[a-zA-Z0-9.-]+\.[a-zA-Z]{2,3}:[\w.,\-/]{1,30}:[\w.,\-/]{1,30}$"
)
# Matches link URNs: urn:sdx:link:<oxp_url>:<link_name>
URN_LINK_PATTERN = re.compile(
    r"^urn:sdx:link:[a-zA-Z0-9.-]+\.[a-zA-Z]{2,3}:[\w.,\-/]{1,30}$"
)


# Matches timestamps (ISO 8601 format with 'Z' at the end)
TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class Status(Enum):
    UP = "up"
    DOWN = "down"
    ERROR = "error"
    MAINTENANCE = "maintenance" # in spec but not topology
    UNDER_PROVISIONING = "under provisioning" # in spec but not topology


class State(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    MAINTENANCE = "maintenance" # in topology but not spec


class PortType(str, Enum):
    FE_100 = "100FE"
    GE_1 = "1GE"
    GE_10 = "10GE"
    GE_25 = "25GE"
    GE_40 = "40GE"
    GE_50 = "50GE"
    GE_100 = "100GE"
    GE_400 = "400GE"
    OTHER = "Other"


class LinkType(Enum):
    INTRA = "intra"


@dataclass
class Location:
    address: str
    latitude: float
    longitude: float
    iso3166_2_lvl4: str

    def __post_init__(self):
        if len(self.address) > 255:
            raise ValueError("Address must be at most 255 characters.")
        if not (-90 <= self.latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90.")
        if not (-180 <= self.longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180.")
        if not (2 <= len(self.iso3166_2_lvl4) <= 6):
            raise ValueError(
                "ISO 3166-2 level 4 code must be between 2 and 6 characters."
            )

        # Validate ISO 3166-2 code
        parts = self.iso3166_2_lvl4.split("-")
        if len(parts) != 2:
            raise ValueError("Invalid ISO 3166-2 format. Expected format: 'XX-YYY'.")

        country_code, subdivision_code = parts

        # Validate country code
        if not pycountry.countries.get(alpha_2=country_code):
            raise ValueError(f"Invalid ISO 3166-1 country code: {country_code}")

        # Validate subdivision code
        valid_subdivisions = {
            sub.code.split("-")[1]
            for sub in pycountry.subdivisions
            if sub.country_code == country_code
        }
        if subdivision_code not in valid_subdivisions:
            raise ValueError(
                f"Invalid subdivision code '{subdivision_code}' for country '{country_code}'."
            )


@dataclass
class Port:
    name: str
    id: str
    node: str  # If I explicitly reference this as a Node.name, I create a circular dependency
    type: PortType
    status: Status
    state: State
    mtu: Optional[int] = 1500
    nni: Optional[str] = ""
    services: Optional[Dict[str, Dict[str, List[List[int]]]]] = field(
        default_factory=lambda: {"l2vpn-ptp": {"vlan_range": [[1, 4095]]}}
    )
    entities: Optional[List[str]] = field(default_factory=list)

    def __post_init__(self):
        if not NAME_PATTERN.match(self.name) or len(self.name) > 30:
            raise ValueError(f"Invalid port name: {self.name}")
        if not URN_PORT_PATTERN.match(self.id):
            raise ValueError(f"Invalid port ID format: {self.id}")
        if not URN_NODE_PATTERN.match(self.node):
            raise ValueError(f"Invalid node ID format in port: {self.node}")
        if self.mtu and not (1500 <= self.mtu <= 10000):
            raise ValueError("MTU must be between 1500 and 10000.")
        if self.nni:
            if not (
                URN_PORT_PATTERN.match(self.nni) or URN_LINK_PATTERN.match(self.nni)
            ):
                raise ValueError(f"Invalid NNI format: {self.nni}")

        if not self.services:
            self.services = {"l2vpn-ptp": {"vlan_range": [[1, 4095]]}}

        for service, attributes in self.services.items():
            if service not in {"l2vpn-ptp", "l2vpn-ptmp"}:
                raise ValueError(
                    f"Unsupported service: {service}. Must be 'l2vpn-ptp' or 'l2vpn-ptmp'"
                )

            vlan_ranges = attributes.get("vlan_range", [])
            for vlan_range in vlan_ranges:
                if len(vlan_range) != 2 or not (
                    1 <= vlan_range[0] < vlan_range[1] <= 4095
                ):
                    raise ValueError(
                        f"Invalid VLAN range: {vlan_range}. Must be between 1 and 4095, and first value must be smaller than the second."
                    )
    def __hash__(self):
        """Make Port hashable by using its unique ID."""
        return hash(self.id)

@dataclass
class Node:
    name: str
    id: str
    location: Location
    ports: List[Port]
    status: Status
    state: State

    def __post_init__(self):
        if not NAME_PATTERN.match(self.name) or len(self.name) > 30:
            raise ValueError(f"Invalid node name: {self.name}")
        if not URN_NODE_PATTERN.match(self.id):
            raise ValueError(f"Invalid node ID format: {self.id}")
        if not self.ports:
            raise ValueError("A node must have at least one port.")
        if not isinstance(self.ports, list) or not all(
            isinstance(port, Port) for port in self.ports
        ):
            raise TypeError("All elements in 'ports' must be Port objects.")


@dataclass
class Link:
    name: str
    id: str
    ports: List[str]
    bandwidth: float
    type: Optional[LinkType] = LinkType.INTRA
    residual_bandwidth: float = 100.0
    latency: float = 0.0
    packet_loss: float = 0.0
    availability: float = 100.0
    status: Status = Status.UP
    state: State = State.ENABLED
    private: Optional[List[str]] = field(default_factory=list)

    def __post_init__(self):
        if not NAME_PATTERN.match(self.name) or len(self.name) > 30:
            raise ValueError(f"Invalid link name: {self.name}")
        if not URN_LINK_PATTERN.match(self.id):
            raise ValueError(f"Invalid link ID format: {self.id}")
        if len(self.ports) != 2:
            raise ValueError("A link must have exactly two ports.")
        if not all(isinstance(port_id, str) for port_id in self.ports):
            raise TypeError(
                "All elements in 'ports' must be Port object IDs (strings)."
            )
        if self.bandwidth <= 0:
            raise ValueError("Bandwidth must be greater than 0.")
        if not (0 <= self.residual_bandwidth <= 100):
            raise ValueError("Residual bandwidth must be between 0 and 100.")
        if self.latency < 0:
            raise ValueError("Latency must be non-negative.")
        if not (0 <= self.packet_loss <= 100):
            raise ValueError("Packet loss must be between 0 and 100.")
        if not (0 <= self.availability <= 100):
            raise ValueError("Availability must be between 0 and 100.")

        # Validate type (optional but must be "intra" for now)
        if self.type not in LinkType:
            raise ValueError(
                f"Invalid link type: {self.type}. Must be one of {list(LinkType)}."
            )

        # Validate private attribute (must only contain valid values or be empty)
        valid_private_values = {"residual_bandwidth", "latency", "packet_loss"}
        if not isinstance(self.private, list):
            raise TypeError("The 'private' attribute must be a list of strings.")
        if not all(value in valid_private_values for value in self.private):
            raise ValueError(
                f"Invalid values in 'private'. Must be one of {valid_private_values}, or an empty list."
            )


@dataclass
class Topology:
    name: str
    id: str
    version: int
    timestamp: str
    model_version: str = MODEL_VERSION
    nodes: List[Node] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)
    services: Optional[List[str]] = field(default_factory=lambda: ["l2vpn-ptp"])

    def __post_init__(self):
        if not NAME_PATTERN.match(self.name) or len(self.name) > 30:
            raise ValueError(f"Invalid topology name: {self.name}")
        if not URN_TOPOLOGY_PATTERN.match(self.id):
            raise ValueError(f"Invalid topology ID format: {self.id}")
        if self.version < 1:
            raise ValueError("Version must be at least 1.")
        if not TIMESTAMP_PATTERN.match(self.timestamp):
            raise ValueError("Invalid timestamp format. Expected YYYY-MM-DDTHH:mm:SSZ.")

        # Make certain there is at least one node
        if not self.nodes:
            raise ValueError("Topology must have at least one node.")
        if not all(isinstance(node, Node) for node in self.nodes):
            raise TypeError("All elements in 'nodes' must be Node objects.")

        # Ensure links are a list of Link objects (can be empty)
        if self.links is None:
            self.links = []  # Default to an empty list
        if not isinstance(self.links, list):
            raise TypeError("'links' must be a list.")
        if not all(isinstance(link, Link) for link in self.links):
            raise TypeError("All elements in 'links' must be Link objects.")

        # Ensure services contain only valid values
        # Ensure services contain only valid values
        allowed_services = {"l2vpn-ptp", "l2vpn-ptmp"}
        if self.services is None:
            self.services = ["l2vpn-ptp"]  # Default if missing
        elif not all(service in allowed_services for service in self.services):
            raise ValueError(
                f"Invalid service type. Must be one of {allowed_services}."
            )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Topology":
        """Automatically converts a dictionary to a Topology object using dacite."""
        return from_dict(
            data_class=cls,
            data=data,
            config=Config(cast=[Status, State, PortType, LinkType, List[str]]),
        )
