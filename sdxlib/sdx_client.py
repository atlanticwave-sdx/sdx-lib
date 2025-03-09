import logging
import pandas as pd
import requests
from typing import Optional, List, Dict, Union
from requests.exceptions import RequestException, HTTPError, Timeout
from sdxlib.sdx_token_auth import TokenAuthentication
from sdxlib.sdx_exception import SDXException
from sdxlib.sdx_response import SDXResponse
from sdxlib.sdx_validator import SDXValidator


class SDXClient:
    """Client for interacting with the AtlanticWave-SDX L2VPN API."""

    VERSION = "1.0"

    def __init__(
        self,
        base_url: str,
        name: Optional[str] = None,
        endpoints: Optional[List[Dict[str, str]]] = None,
        description: Optional[str] = None,
        notifications: Optional[List[Dict[str, str]]] = None,
        scheduling: Optional[Dict[str, str]] = None,
        qos_metrics: Optional[Dict[str, Dict[str, Union[int, bool]]]] = None,
        fabric_token: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize SDXClient instance."""
        self.base_url = SDXValidator.validate_non_empty_string(base_url, "Base URL")
        self.name = SDXValidator.validate_name(name)
        self.endpoints = SDXValidator.validate_endpoints(endpoints)
        self.description = SDXValidator.validate_description(description)
        self.notifications = (
            notifications if notifications is not None
            else [{"email": TokenAuthentication().load_token().token_eppn}]
        )
        self.notifications = SDXValidator.validate_notifications(self.notifications)
        self.scheduling = SDXValidator.validate_scheduling(scheduling)
        self.qos_metrics = SDXValidator.validate_qos_metrics(qos_metrics)
        self.fabric_token = fabric_token or TokenAuthentication().load_token().fabric_token
        self._logger = logger or logging.getLogger(__name__)
        self._request_cache = {}

    def create_l2vpn(self) -> dict:
        """Creates an L2VPN."""
        print(f"Base URL: {self.base_url}")
        print(f"Name: {self.name}")
        print(f"Endpoints: {self.endpoints}")

        # Perform validation using SDXValidator
        SDXValidator.validate_required_attributes(self.base_url, self.name, self.endpoints)
        SDXValidator.validate_notifications(self.notifications)
        SDXValidator.validate_scheduling(self.scheduling)
        SDXValidator.validate_qos_metrics(self.qos_metrics)

        url = f"{self.base_url}/l2vpn/{self.VERSION}"
        payload = self._build_payload()
        headers = self._get_headers()

        # Generate cache key safely
        cache_key = (
            self.name,
            tuple(endpoint.get("port_id", "") for endpoint in self.endpoints),
        )

        # Check cache for existing request
        if cache_key in self._request_cache:
            _, response_json = self._request_cache[cache_key]
            self._logger.info(f"Using cached response for L2VPN: {self.name}")
            return {"service_id": response_json.get("service_id")}

        try:
            self._logger.debug("Sending request to create L2VPN with payload: %s", payload)
            print("Sending request to create L2VPN with payload:", payload)
            print("Sending request to create L2VPN with cache_key:", cache_key)

            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()  # Ensure HTTP errors are caught early
            response_json = response.json()

            # Cache only successful responses
            self._request_cache[cache_key] = (payload, response_json)
            self._logger.info(f"L2VPN created successfully with service_id: {response_json.get('service_id', 'UNKNOWN')}")
        
            return {"service_id": response_json.get("service_id")}

        except HTTPError as e:
            SDXValidator.handle_http_error(self._logger, e, "create L2VPN")

        except Timeout:
            self._logger.error("The request to create the L2VPN timed out.")
            raise SDXException("The request to create the L2VPN timed out.")

        except RequestException as e:
            self._logger.error(f"Failed to create L2VPN: {e}")
            raise SDXException(f"Failed to create L2VPN: {e}")


    def update_l2vpn(self, service_id: str, **kwargs) -> dict:
        """ Updates an existing L2VPN."""
        url = f"{self.base_url}/l2vpn/{self.VERSION}/{service_id}"
        headers = self._get_headers()

        if "state" in kwargs:
            if kwargs["state"].lower() not in ["enabled", "disabled"]:
                raise ValueError("State must be 'enabled' or 'disabled'.")
            kwargs["state"] = kwargs["state"].lower()

        payload = {k: v for k, v in kwargs.items() if v is not None}
        payload["service_id"] = service_id

        self._logger.debug(f"Sending request to update L2VPN with payload: {payload}")
        return self._make_request("PATCH", url, headers, payload)

    def delete_l2vpn(self, service_id: str) -> Optional[Dict]:
        """
        Deletes an L2VPN using the provided L2VPN ID.
        Args:
        service_id (str): The ID of the L2VPN to delete.
        Returns:
        dict: Response from the SDX API.
        Raises:
        SDXException: If the API request fails.
        """
        url = f"{self.base_url}/l2vpn/{self.VERSION}/{service_id}"
        headers = self._get_headers()

        try:
            response = requests.delete(url, headers=headers, timeout=120)
            response.raise_for_status()
            self._logger.info(f"L2VPN deletion request sent to {url}.")
            return response.json() if response.content else None
        except HTTPError as e:
            SDXValidator.handle_http_error(self._logger, e, "delete L2VPN")
        except Timeout:
            self._logger.error("Request timed out.")
            raise SDXException("The request to delete the L2VPN timed out.")
        except RequestException as e:
            self._logger.error(f"Failed to delete L2VPN: {e}")
            raise SDXException(f"Failed to delete L2VPN: {e}")

    def get_available_ports(self, format: str = "dataframe") -> Union[pd.DataFrame, List[Dict[str, str]]]:
        """Fetches and returns a list of available ports from the SDX topology.
        Args:
        format (str): The output format, either "dataframe" (default) or "json".
        Returns:
        Union[pd.DataFrame, List[Dict[str, str]]]: The available ports in the specified format.
        Raises:
        SDXException: If the API request fails or returns an error.
        """
        url = f"{self.base_url}/topology"
        headers = self._get_headers()

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            self._logger.info(f"Topology retrieval request sent to {url}.")
            self._logger.debug(f"Full response: {data}")

            # Extract available ports with entities
            port_list = [
                {
                    "Port ID": port.get("id"),
                    "Status": port.get("status"),
                    "Entities": ", ".join(port.get("entities", []))  # Convert list to comma-separated string
                }
                for node in data.get("nodes", [])
                for port in node.get("ports", [])
                if port.get("status") == "up" and not port.get("nni")
            ]

            if format == "dataframe":
                df = pd.DataFrame(port_list)
                pd.set_option("display.max_rows", None)  # Show all rows
                pd.set_option("display.max_colwidth", None)  # Ensure full text is displayed
                return df

            if format == "json":
                return port_list

            raise ValueError("Invalid format specified. Use 'dataframe' or 'json'.")

        except HTTPError as e:
            SDXValidator.handle_http_error(self._logger, e, "retrieve available ports")
        except Timeout:
            self._logger.error("The request to retrieve available ports timed out.")
            raise SDXException("The request to retrieve available ports timed out.")
        except RequestException as e:
            self._logger.error(f"Failed to retrieve available ports: {e}")
            raise SDXException(f"Failed to retrieve available ports: {e}")
    
    def get_l2vpn(self, service_id: str, format: str = "dataframe") -> Union[pd.DataFrame, SDXResponse]:
        """Retrieves details of an existing L2VPN using the provided service ID.
        Args:
        service_id (str): The ID of the L2VPN to retrieve.
        format (str): The output format, either "dataframe" (default) or "json".
        Returns:
        Union[pd.DataFrame, SDXResponse]: Parsed response from the SDX API in 
        the form of a DataFrame or a JSON-formatted SDXResponse.
        Raises:
        SDXException: If the API request fails.
        """
        url = f"{self.base_url}/l2vpn/{self.VERSION}/{service_id}"
        headers = self._get_headers()

        try:
            response = requests.get(url, headers=headers, timeout=120)
            response.raise_for_status()
            response_json = response.json()
        
            self._logger.info(f"L2VPN retrieval request sent to {url}.")
            self._logger.info(f"Full response: {response_json}")

            l2vpn_data = response_json.get(service_id)

            if l2vpn_data is None:
                raise SDXException(f"L2VPN with ID {service_id} not found.")

            # Create SDXResponse object and store it
            sdx_response = SDXResponse(l2vpn_data)
            self.last_sdx_response = sdx_response

            # Format the response based on user preference
            if format == "dataframe":
                node_info_list = [
                    {
                        **vars(sdx_response),
                        "port_id": endpoint.get("port_id"),
                        "vlan": endpoint.get("vlan"),
                    }
                    for endpoint in sdx_response.endpoints
                ]

                ordered_columns = [
                    "service_id", "name", "port_id", "vlan", "description",
                    "qos_metrics", "notifications", "ownership", "creation_date",
                    "archived_date", "status", "state", "counters_location",
                    "last_modified", "current_path", "oxp_service_ids"
                ]

                df = pd.DataFrame(node_info_list)
                return df[ordered_columns] if not df.empty else df

            if format == "json":
                return vars(sdx_response)

            raise ValueError("Invalid format specified. Use 'dataframe' or 'json'.")

        except HTTPError as e:
            SDXValidator.handle_http_error(self._logger, e, "retrieve L2VPN")
        except Timeout:
            self._logger.error("Request timed out.")
            raise SDXException("The request to retrieve the L2VPN timed out.")
        except RequestException as e:
            self._logger.error(f"Failed to retrieve L2VPN: {e}")
            raise SDXException(f"Failed to retrieve L2VPN: {e}")

    def get_all_l2vpns(
        self, archived: bool = False, format: str = "dataframe"
        ) -> Union[pd.DataFrame, Dict[str, SDXResponse]]:
        """
        Retrieves all L2VPNs, either archived or active.
        Args:
        archived (bool): If True, retrieve only archived L2VPNs. Defaults to False.
        format (str): The output format, either "dataframe" (default) or "json".
        Returns:
        Union[pd.DataFrame, Dict[str, SDXResponse]]: The L2VPNs in the specified format.
        Raises:
        SDXException: If the API request fails with a known error.
        ValueError: If an invalid format is specified.
        """
        url = f"{self.base_url}/l2vpn/{self.VERSION}/archived" if archived else f"{self.base_url}/l2vpn/{self.VERSION}"
        headers = self._get_headers()

        self._logger.info("Retrieving %s L2VPNs from URL: %s", "archived" if archived else "active", url)

        try:
            response = requests.get(url, headers=headers, timeout=120)
            response.raise_for_status()
            l2vpns_json = response.json()

            self._logger.debug("L2VPNs retrieved successfully: %s", l2vpns_json)

            # Convert JSON response to SDXResponse objects
            l2vpns = {service_id: SDXResponse(l2vpn_data) for service_id, l2vpn_data in l2vpns_json.items()}

            if format == "dataframe":
                node_info_list = [
                    {"service_id": service_id, **vars(sdx_response)}
                    for service_id, sdx_response in l2vpns.items()
                ]
                df = pd.DataFrame(node_info_list)
                return df if not df.empty else pd.DataFrame(columns=["service_id"])  # Ensure proper DataFrame structure

            if format == "json":
                return {service_id: vars(sdx_response) for service_id, sdx_response in l2vpns.items()}

            raise ValueError("Invalid format specified. Use 'dataframe' or 'json'.")

        except HTTPError as e:
            SDXValidator.handle_http_error(self._logger, e, "retrieve all L2VPNs")
        except Timeout:
            self._logger.error("The request to retrieve L2VPN(s) timed out.")
            raise SDXException("The request to retrieve L2VPN(s) timed out.")
        except RequestException as e:
            self._logger.error("Failed to retrieve L2VPN(s): %s", e)
            raise SDXException(f"Failed to retrieve L2VPN(s): {e}")

    def _build_payload(self) -> dict:
        """ Constructs payload for API requests, excluding None values."""
        return {
            key: value for key, value in {
                "name": self.name,
                "endpoints": self.endpoints,
                "description": self.description,
                "notifications": self.notifications,
                "scheduling": self.scheduling,
                "qos_metrics": self.qos_metrics,
            }.items() if value is not None  # Exclude None values
    }

    def _get_headers(self) -> Dict[str, str]:
        """Returns headers for API requests."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.fabric_token}",
        }

    def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        payload: Optional[dict] = None,
        operation: str = "",
        cache_key: Optional[tuple] = None
    ) -> dict:
        """Handles API requests with error handling and logging."""
        try:
            response = requests.request(method, url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            response_json = response.json()

            if cache_key:
                self._request_cache[cache_key] = (payload, response_json)

            self._logger.info(f"{operation.capitalize()} request successful.")
            return response_json

        except HTTPError as e:
            # Pass self._logger explicitly
            SDXValidator.handle_http_error(self._logger, e, operation)

        except Timeout:
            self._logger.error(f"The request to {operation} timed out.")
            raise SDXException(message=f"The request to {operation} timed out.")

        except RequestException as e:
            self._logger.error(f"An error occurred during {operation}: {e}")
            raise SDXException(message=f"An error occurred during {operation}: {e}")
