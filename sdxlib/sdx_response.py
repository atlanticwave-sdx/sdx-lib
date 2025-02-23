import json
import logging

from dacite import from_dict, Config
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from sdxlib.sdx_topology import Node, Port, Link, Location, State, Status

class SDXResponse:
    """
    Class representing a response object from the L2VPN creation API.

    Attributes:
        service_id (str): The service Universally Unique Identifier (UUID).
        ownership (str): The authenticated user or token that submitted the request.
        creation_date (str): The service creation time in ISO8601 format.
        archived_date (str): The datetime of the archive request (initially 0).
        status (str): The current operational status of the L2VPN (up, down, error, under provisioning, maintenance).
        state (str): The current administrative state of the L2VPN (enabled, disabled).
        counters_location (str): The link to the Grafana page with counters.
        last_modified (str): The datetime of the last modification (initially 0).
        current_path (str): The URI of the interdomain links in the path as a list.
        oxp_service_ids (Optional[List[Dict[str, str]]]): A list of dictionaries containing OXP service IDs.
    """

    ALLOWED_STATUS = {"up", "down", "error", "under provisioning", "maintenance"}
    ALLOWED_STATE = {"enabled", "disabled"}

    def __init__(self, response_json: dict):
        """
        Initializes the SDXResponse object and validates the response fields.

        Args:
            response_json (dict): The JSON response dictionary from the L2VPN API.

        Raises:
            ValueError: If required fields are missing or invalid.
        """

        if not isinstance(response_json, dict):
            raise TypeError("Expected a dictionary response_json.")

        self._logger = logging.getLogger(__name__)

        # Required fields - MUST have a value
        self.service_id: str = self._validate_required(
            response_json, "service_id", str, must_have_value=True
        )
        self.name: str = self._validate_required(
            response_json, "name", str, must_have_value=True
        )
        self.endpoints: List[Dict[str, str]] = self._validate_required(
            response_json, "endpoints", list, must_have_value=True
        )
        self.ownership: str = self._validate_required(
            response_json, "ownership", str, must_have_value=True
        )
        self.creation_date: str = self._validate_required(
            response_json, "creation_date", str, must_have_value=True
        )
        self.archived_date: str = self._validate_required(
            response_json, "archived_date", str, must_have_value=True, default="0"
        )
        # self.status: str = self._validate_required(
        #     response_json, "status", str, must_have_value=True
        # )
        # if self.status not in self.ALLOWED_STATUS:
        #     raise ValueError(f"Invalid status: {self.status}. Allowed values: {self.ALLOWED_STATUS}")

        # self.state: str = self._validate_required(
        #     response_json, "state", str, must_have_value=True
        # )
        # if self.state not in self.ALLOWED_STATE:
        #     raise ValueError(f"Invalid state: {self.state}. Allowed values: {self.ALLOWED_STATE}")
        
        self.status: str = self._validate_required(
            response_json, "status", str, must_have_value=True, allowed_values=self.ALLOWED_STATUS
        )

        self.state: str = self._validate_required(
            response_json, "state", str, must_have_value=True, allowed_values=self.ALLOWED_STATE
        )

        self.counters_location: str = self._validate_required(
            response_json, "counters_location", str, must_have_value=True
        )
        self.last_modified: str = self._validate_required(
            response_json, "last_modified", str, must_have_value=True, default="0"
        )
        self.current_path: List[str] = self._validate_required(
            response_json, "current_path", list, must_have_value=True
        )
        self.oxp_service_ids: Dict[str, List[str]] = self._validate_required(
            response_json, "oxp_service_ids", dict, must_have_value=True
        )
        # Optional fields - May be None
        self.description: Optional[str] = self._validate_optional(
            response_json, "description", str
        )
        self.notifications: Optional[List[Dict[str, str]]] = self._validate_optional(
            response_json, "notifications", list
        )
        self.scheduling: Optional[Dict[str, str]] = self._validate_optional(
            response_json, "scheduling", dict
        )
        self.qos_metrics: Optional[
            Dict[str, Dict[str, Union[int, bool]]]
        ] = self._validate_optional(response_json, "qos_metrics", dict)

        # Log successful validation
        self._logger.debug("SDXResponse successfully initialized.")

    # def _validate_required(
    #     self,
    #     data: dict,
    #     key: str,
    #     expected_type: type,
    #     must_have_value: bool = False,
    #     default=None,
    # ):
    #     """Ensures a required field exists and has a valid value."""
    #     if key not in data:
    #         self._logger.error(f"Missing required field: {key}")
    #         raise ValueError(f"Missing required field: {key}")

    #     value = data.get(key, default)

    #     if must_have_value and (value is None or value == ""):
    #         self._logger.error(
    #             f"Required field {key} must have a value, cannot be None or empty."
    #         )
    #         raise ValueError(
    #             f"Required field {key} must have a value, cannot be None or empty."
    #         )

    #     if value is not None and not isinstance(value, expected_type):
    #         self._logger.error(
    #             f"Invalid type for {key}: Expected {expected_type.__name__}, got {type(value).__name__}"
    #         )
    #         raise ValueError(
    #             f"Invalid type for {key}: Expected {expected_type.__name__}, got {type(value).__name__}"
    #         )

    #     return value
    def _validate_required(
        self,
        data: dict,
        key: str,
        expected_type: type,
        must_have_value: bool = False,
        default=None,
        allowed_values: Optional[set] = None,  # New optional argument
    ):
        """Ensures a required field exists and has a valid value."""
        if key not in data:
            self._logger.error(f"Missing required field: {key}")
            raise ValueError(f"Missing required field: {key}")

        value = data.get(key, default)

        if must_have_value and (value is None or value == ""):
            self._logger.error(f"Required field {key} must have a value, cannot be None or empty.")
            raise ValueError(f"Required field {key} must have a value, cannot be None or empty.")

        if value is not None and not isinstance(value, expected_type):
            self._logger.error(f"Invalid type for {key}: Expected {expected_type.__name__}, got {type(value).__name__}")
            raise ValueError(f"Invalid type for {key}: Expected {expected_type.__name__}, got {type(value).__name__}")

        if allowed_values and value not in allowed_values:
            self._logger.error(f"Invalid {key}: {value}. Allowed values: {allowed_values}")
            raise ValueError(f"Invalid {key}: {value}. Allowed values: {allowed_values}")

        return value
    
    def _validate_optional(self, data: dict, key: str, expected_type: type):
        """Validates optional fields and ensures correct type if present."""
        value = data.get(key)

        if value is not None and not isinstance(value, expected_type):
            self._logger.warning(
                f"Optional field {key} has incorrect type: Expected {expected_type.__name__}, got {type(value).__name__}"
            )
            return None

        return value

    def __eq__(self, other):
        if not isinstance(other, SDXResponse):
            return NotImplemented

        return all(
            getattr(self, attr) == getattr(other, attr)
            for attr in vars(self)
            if attr != "_logger"  # Exclude logger attribute
        )

    def __str__(self):
        """Formatted string representation for logging/debugging."""
        return json.dumps(
            {
                "service_id": self.service_id,
                "name": self.name,
                "endpoints": self.endpoints,
                "description": self.description,
                "qos_metrics": self.qos_metrics,
                "notifications": self.notifications,
                "ownership": self.ownership,
                "creation_date": self.creation_date,
                "archived_date": self.archived_date,
                "status": self.status,
                "state": self.state,
                "counters_location": self.counters_location,
                "last_modified": self.last_modified,
                "current_path": self.current_path,
                "oxp_service_ids": [oxp["id"] for oxp in self.oxp_service_ids]
                if isinstance(self.oxp_service_ids, list)
                else self.oxp_service_ids,
            },
            indent=4,
            ensure_ascii=False,
        )
    

@dataclass
class SDXTopologyResponse:
    """
    Parses and stores the topology response from the SDX controller.
    """
    # Stores list of all nodes in network
    nodes: List[Node] = field(default_factory=list)
    # Stores list of all links between nodes
    links: List[Link] = field(default_factory=list)
    # Dict that maps port.id to a Port object for fast lookups
    port_lookup: Dict[str, Port] = field(default_factory=dict)

    @classmethod
    def from_json(cls, response_json: dict) -> "SDXTopologyResponse":
        """
        Parses JSON response from SDX Controller and returns an instance of SDXTopologyResponse.
        """
        nodes = []
        port_lookup = {}

        # Extract nodes from response_json['nodes']
        for node_data in response_json.get("nodes", []):
            # Convert JSON into Node object
            node = from_dict(Node, node_data, config=Config(cast=[Status, State]))
            
            # Populate port lookup dictionary
            for port in node.ports:
                port_lookup[port.id] = port
            
            # Add parsed node to nodes list
            nodes.append(node)
        
        # Same thing for links as for nodes except no lookup table 
        links = [
            from_dict(Link, link_data, config=Config(cast=[Status, State]))
            for link_data in response_json.get("links", [])
        ]

        # Returns SDXTopologyResponse instance with nodes list, links list, and port lookup dict
        return cls(nodes=nodes, links=links, port_lookup=port_lookup)


    def get_available_ports(self) -> List[Port]:
        """Returns a list of available ports that are UP and not NNI."""
        return [port for port in self.port_lookup.values() if port.status == Status.UP and not port.nni]

    def search_ports(self, search_term: str) -> List[Port]:
        """Search for ports based on a substring in the port name."""
        return [port for port in self.port_lookup.values() if search_term.lower() in port.name.lower()]

    # Allows substring search of entities
    def search_entities(self, search_term: str) -> List[Port]:
        """Search for ports based on entities."""
        return [
            port for port in self.port_lookup.values()
            if any(search_term.lower() in entity.lower() for entity in port.entities)
        ]

