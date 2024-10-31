from typing import Dict, List, Optional, Union


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

    def __init__(self, response_json: dict):
        """
        Initializes the L2VPNResponse object from a JSON response dictionary.

        Args:
            response_json (dict): The JSON response dictionary from the L2VPN creation API.
        """
        if not isinstance(response_json, dict):
            raise TypeError("Expected a dictionary response_json.")

        self.service_id: str = response_json.get("service_id")
        self.name: str = response_json.get("name")
        self.endpoints: List[Dict[str, str]] = response_json.get("endpoints")
        self.description: Optional[str] = response_json.get("description")
        self.notifications: Optional[List[Dict[str, str]]] = response_json.get(
            "notifications"
        )
        self.scheduling: Optional[Dict[str, str]] = response_json.get("scheduling")
        self.qos_metrics: Optional[
            Dict[str, Dict[str, Union[int, bool]]]
        ] = response_json.get("qos_metrics")
        self.ownership: str = response_json.get("ownership")
        self.creation_date: str = response_json.get("creation_date")
        self.archived_date: str = response_json.get("archived_date")
        self.status: str = response_json.get("status")
        self.state: str = response_json.get("state")
        self.counters_location: str = response_json.get("counters_location")
        self.last_modified: str = response_json.get("last_modified")
        self.current_path: List[str] = response_json.get("current_path")
        self.oxp_service_ids: List[Dict[str, str]] = response_json.get(
            "oxp_service_ids"
        )

    def __eq__(self, other):
        if not isinstance(other, SDXResponse):
            return NotImplemented
        return (
            self.service_id == other.service_id
            and self.ownership == other.ownership
            and self.creation_date == other.creation_date
            and self.archived_date == other.archived_date
            and self.status == other.status
            and self.state == other.state
            and self.counters_location == other.counters_location
            and self.last_modified == other.last_modified
            and self.current_path == other.current_path
            and self.oxp_service_ids == other.oxp_service_ids
        )

    def __str__(self):
        current_path_str = (
            self.current_path[0]
            if isinstance(self.current_path, list) and len(self.current_path) == 1
            else str(self.current_path)
        )

        oxp_service_ids_str = (
            [oxp["id"] for oxp in self.oxp_service_ids]
            if isinstance(self.oxp_service_ids, list)
            else str(self.oxp_service_ids)
        )

        return (
            "L2VPN Response:\n"
            f"        service_id: {self.service_id}\n"
            f"        name: {self.name}\n"
            f"        endpoints: {self.endpoints}\n"
            f"        description: {self.description}\n"
            f"        scheduling: {self.scheduling}\n"
            f"        qos_metrics: {self.qos_metrics}\n"
            f"        notifications: {self.notifications}\n"
            f"        ownership: {self.ownership}\n"
            f"        creation_date: {self.creation_date}\n"
            f"        archived_date: {self.archived_date}\n"
            f"        status: {self.status}\n"
            f"        state: {self.state}\n"
            f"        counters_location: {self.counters_location}\n"
            f"        last_modified: {self.last_modified}\n"
            f"        current_path: {current_path_str}\n"
            f"        oxp_service_ids: {oxp_service_ids_str}"
        )
