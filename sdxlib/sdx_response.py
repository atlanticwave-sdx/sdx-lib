import json
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
        return self.__dict__ == other.__dict__

    def __str__(self):

        # Format lists and dictionaries using json.dumps for indentation
        formatted_endpoints = (
            json.dumps(self.endpoints, indent=4) if self.endpoints else "None"
        )
        formatted_qos_metrics = (
            json.dumps(self.qos_metrics, indent=4) if self.qos_metrics else "None"
        )
        formatted_notifications = (
            json.dumps(self.notifications, indent=4) if self.notifications else "None"
        )
        formatted_oxp_service_ids = json.dumps(
            [oxp["id"] for oxp in self.oxp_service_ids]
            if isinstance(self.oxp_service_ids, list)
            else self.oxp_service_ids,
            indent=4,
        )

        return (
            "L2VPN Response:\n"
            f"        service_id: '{self.service_id}'\n"
            f"        name: '{self.name}'\n"
            f"        endpoints: {formatted_endpoints}\n"
            f"        description: '{self.description}'\n"
            f"        qos_metrics: {formatted_qos_metrics}\n"
            f"        notifications: {formatted_notifications}\n"
            f"        ownership: '{self.ownership}'\n"
            f"        creation_date: '{self.creation_date}'\n"
            f"        archived_date: '{self.archived_date}'\n"
            f"        status: '{self.status}'\n"
            f"        state: '{self.state}'\n"
            f"        counters_location: '{self.counters_location}'\n"
            f"        last_modified: '{self.last_modified}'\n"
            f"        current_path: {json.dumps(self.current_path, indent=4)}\n"
            f"        oxp_service_ids: {formatted_oxp_service_ids}"
        )
