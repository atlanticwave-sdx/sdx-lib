import logging
import pandas as pd
import re
import requests
from typing import Optional, List, Dict, Union
from requests.exceptions import RequestException, HTTPError, Timeout

# Import the TokenAuthentication class from sdxlib.sdx_token_auth
from sdxlib.sdx_token_auth import TokenAuthentication

from sdxlib.sdx_exception import SDXException
from sdxlib.sdx_response import SDXResponse

# Basic configuration for logging to stdout
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

"""sdxlib

A Python client library for interacting with the AtlanticWave-SDX L2VPN API.
"""


class SDXClient:
    """A client class for managing interactions
        with the AtlanticWave-SDX L2VPN API.

    Attributes:
    - base_url (str): The base URL of the SDX API.
    - _name (str): Private attribute for storing the name of the L2VPN.
    - _endpoints (list): Private attribute for storing the list of endpoints.

    Raises:
    - ValueError: If provided parameters do not meet requirements.
    - SDXException: If an API request fails.
    """

    PORT_ID_PATTERN = (
        r"^urn:sdx:port:[a-zA-Z0-9.,-_\/]+:[a-zA-Z0-9.,-_\/]+:[a-zA-Z0-9.,-_\/]+$"
    )

    VERSION = "1.0"

    def __init__(
        self,
        base_url: Optional[str] = None,
        name: Optional[str] = None,
        endpoints: Optional[List[Dict[str, str]]] = None,
        description: Optional[str] = None,
        notifications: Optional[List[Dict[str, str]]] = None,
        scheduling: Optional[Dict[str, str]] = None,
        qos_metrics: Optional[Dict[str, Dict[str, Union[int, bool]]]] = None,
        fabric_token = Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initializes an instance of SDXClient.

        Args:
        - base_url (Optional[str]): The base URL of the SDX API.
        - name (Optional[str]): The name of the SDX client.
        - endpoints (Optional[List[Dict[str, str]]]): List  of dictionaries with 'port_id' and 'vlan' keys for each endpoint.
        - description (Optional[str]): Description of the client (default: None).
        - notifications (Optional[List[Dict[str, str]]]): List of dictionaries, each with a single 'email' key (default: None).
        - scheduling (Optional[Dict[str, str]]): Scheduling configuration (default: None).
        - qos_metrics (Optional[Dict[str, str]]): Quality of service metrics (default: None).
        """

        self.base_url = base_url
        self.name = name
        self.endpoints = endpoints
        self.description = description
        self.notifications = [{"email":TokenAuthentication().load_token().eppn}]
        self.scheduling = scheduling
        self.qos_metrics = qos_metrics
        self.fabric_token = TokenAuthentication().load_token().fabric_token
        self._logger = logger or logging.getLogger(__name__)
        self._request_cache = {}

    @property
    def base_url(self) -> str:
        """Getter for base_url attribute."""
        return self._base_url

    @base_url.setter
    def base_url(self, value: str):
        """Setter for base_url attribute."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Base URL must be a non-empty string.")
        self._base_url = value

    @property
    def name(self) -> Optional[str]:
        """Getter for name attribute."""
        return self._name

    @name.setter
    def name(self, value: Optional[str]):
        """Setter for name attribute."""
        if value is not None and (
            not isinstance(value, str) or not value.strip() or len(value) > 50
        ):
            raise ValueError(
                "Name must be a non-empty string with maximum 50 characters."
            )
        self._name = value

    @property
    def endpoints(self) -> Optional[List[Dict[str, str]]]:
        """Getter for endpoint attribute."""
        return self._endpoints

    @endpoints.setter
    def endpoints(self, value: Optional[List[Dict[str, str]]]):
        """Setter for endpoint attribute."""
        self._endpoints = self._validate_endpoints(value) if value else None

    @property
    def description(self) -> Optional[str]:
        """Getter for description attribute."""
        return self._description

    @description.setter
    def description(self, value: Optional[str]):
        """Setter for description attribute."""
        if value is None or not value:
            self._description = None
        elif value is not None and len(value) > 255:
            raise ValueError("Description attribute must be less than 256 characters.")
        else:
            self._description = value

    @property
    def notifications(self) -> Optional[List[Dict[str, str]]]:
        """Getter for notifications attribute."""
        return self._notifications

    @notifications.setter
    def notifications(self, value: Optional[List[Dict[str, str]]]):
        """Setter for notifications attribute."""
        if value is None or not value:
            self._notifications = None
        else:
            self._notifications = self._validate_notifications(value)

    @property
    def scheduling(self) -> Optional[Dict[str, str]]:
        """Getter for scheduling attribute."""
        return self._scheduling

    @scheduling.setter
    def scheduling(self, value: Optional[Dict[str, str]]):
        """Setter for scheduling attribute."""
        if value is None or not value:
            self._scheduling = None
            return

        if not isinstance(value, dict):
            raise TypeError("Scheduling attribute must be a dictionary.")

        self._validate_scheduling(value)
        self._scheduling = value

    @property
    def qos_metrics(self) -> Optional[Dict[str, Dict[str, Union[int, bool]]]]:
        """Getter for qos_metrics attribute."""
        return self._qos_metrics

    @qos_metrics.setter
    def qos_metrics(self, value: Optional[Dict[str, Dict[str, Union[int, bool]]]]):
        """Setter for qos_metrics attribute."""
        if value is None or not value:
            self._qos_metrics = None
            return

        self._validate_qos_metric(value)
        self._qos_metrics = value

    # Endpoints Methods
    def _validate_endpoints(
        self, endpoints: Optional[List[Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        """Validates the provided list of endpoints.

        Args:
            endpoints (Optional[List[Dict[str, str]]]): List of endpoint dictionaries.

        Returns:
            List[Dict[str, str]]: Validated list of endpoint dictionaries.

        Raises:
            TypeError: If endpoints is not a list.
            ValueError: If endpoints list is empty or does not contain at least 2 entries,
                or if VLAN configuration is invalid.
        """
        if endpoints is None:
            return []
        if not isinstance(endpoints, list):
            raise TypeError("Endpoints must be a list.")
        if len(endpoints) < 2:
            raise ValueError("Endpoints must contain at least 2 entries.")

        vlans = set()
        vlan_ranges = set()
        special_vlans = {"any", "all", "untagged"}
        has_vlan_range = False
        has_single_vlan = False
        has_special_vlan = False
        has_any_untagged = False

        validated_endpoints = []
        for endpoint in endpoints:
            validated_endpoint = self._validate_endpoint_dict(endpoint)
            validated_endpoints.append(validated_endpoint)

            vlan_value = endpoint["vlan"]
            if vlan_value in special_vlans:
                vlans.add(vlan_value)
                if vlan_value in {"any", "untagged"}:
                    has_any_untagged = True
                else:
                    has_special_vlan = True
            elif vlan_value.isdigit():
                has_single_vlan = True
                vlans.add(vlan_value)
            elif ":" in vlan_value:
                vlan_ranges.add(vlan_value)
                has_vlan_range = True

            # Check VLAN consistency across endpoints.
            if has_vlan_range and (
                len(vlan_ranges) > 1
                or has_single_vlan
                or has_special_vlan
                or has_any_untagged
            ):
                raise ValueError(
                    "All endpoints must have the same VLAN value if one endpoint is 'all' or a range."
                )

            if has_special_vlan and (
                len(vlans) > 1 or has_single_vlan or has_vlan_range
            ):
                raise ValueError(
                    "All endpoints must have the same VLAN value if one endpoint is 'all' or a range."
                )

        return validated_endpoints

    def _validate_endpoint_dict(self, endpoint_dict: Dict[str, str]) -> Dict[str, str]:
        """Validates a single endpoint dictionary.

        Args:
            endpoint_dict (Dict[str, str]): Endpoint dictionary.

        Returns:
            Dict[str, str]: Validated endpoint dictionary.

        Raises:
            TypeError: If endpoint_dict is not a dictionary.
            ValueError: If endpoint_dict does not contain required keys or VLAN is invalid.
        """
        if not isinstance(endpoint_dict, dict):
            raise TypeError("Endpoints must be a list of dictionaries.")

        # Validate 'port_id'
        if "port_id" not in endpoint_dict or not endpoint_dict["port_id"]:
            raise ValueError("Each endpoint must contain a non-empty 'port_id' key.")
        if not re.match(self.PORT_ID_PATTERN, endpoint_dict["port_id"]):
            raise ValueError(f"Invalid port_id format: {endpoint_dict['port_id']}")

        # Validate 'vlan'
        if "vlan" not in endpoint_dict or not endpoint_dict["vlan"]:
            raise ValueError("Each endpoint must contain a non-empty 'vlan' key.")
        vlan_value = endpoint_dict["vlan"]

        if not isinstance(vlan_value, str):
            raise TypeError("VLAN must be a string.")

        valid_vlans = {"any", "all", "untagged"}

        if vlan_value in valid_vlans:
            pass  # Valid special VLAN value
        elif vlan_value.isdigit():
            vlan_int = int(vlan_value)
            if not (1 <= vlan_int <= 4095):
                raise ValueError(
                    f"Invalid VLAN value: '{vlan_value}'. Must be between 1 and 4095."
                )
        elif ":" in vlan_value:
            vlan_range = vlan_value.split(":")
            if len(vlan_range) != 2:
                raise ValueError(
                    f"Invalid VLAN range values: '{vlan_value}'. Must be 'VLAN ID1:VLAN ID2'."
                )
            try:
                vlan_id1, vlan_id2 = map(int, vlan_range)
                if not (1 <= vlan_id1 < vlan_id2 <= 4095):
                    raise ValueError(
                        f"Invalid VLAN range values: '{vlan_value}'. Must be between 1 and 4095, and VLAN ID1 must be less than VLAN ID2."
                    )
            except ValueError:
                raise ValueError(
                    f"Invalid VLAN range format: '{vlan_value}'. Must be 'VLAN ID1:VLAN ID2'."
                )
        else:
            raise ValueError(
                f"Invalid VLAN value: '{vlan_value}'. Must be 'any', 'all', 'untagged', a string representing an integer between 1 and 4095, or a range."
            )

        return endpoint_dict

    # Notifications Methods
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validates an email address format.

        Args:
            email (str): Email address to validate.

        Returns:
            bool: True if the email address is valid, False otherwise.
        """
        if not isinstance(email, str):
            return False
        email_regex = r"^\S+@\S+$"
        return re.match(email_regex, email) is not None

    def _validate_notifications(
        self, notifications: Optional[List[Dict[str, str]]]
    ) -> Optional[List[Dict[str, str]]]:
        """Validates the notifications attribute.

        Args:
            notifications (Optional[List[Dict[str, str]]]): List of dictionaries representing notifications.

        Returns:
            Optional[List[Dict[str, str]]]: Validated list of notifications.

        Raises:
            TypeError: If notifications is not a list.
            ValueError: If notifications exceed 10 dictionaries or contain invalid emails.
        """
        if notifications is None:
            return None
        if not isinstance(notifications, list):
            raise ValueError("Notifications must be provided as a list.")
        if len(notifications) > 10:
            raise ValueError("Notifications can contain at most 10 email addresses.")

        validated_notifications = []
        for notification in notifications:
            if not isinstance(notification, dict):
                raise ValueError("Each notification must be a dictionary.")
            if "email" not in notification:
                raise ValueError(
                    "Each notification dictionary must contain a key 'email'."
                )
            if not self.is_valid_email(notification["email"]):
                raise ValueError(
                    f"Invalid email address or email format: {notification['email']}"
                )
            validated_notifications.append(notification)
        return validated_notifications

    def _is_valid_iso8601(self, timestamp: str) -> bool:
        """Checks if the provided string is a valid ISO8601 formatted timestamp.

        Args:
            timestamp (str): The timestamp to validate.

        Returns:
            bool: True if the timestamp is valid, False otherwise.
        """
        timestamp_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        return re.match(timestamp_pattern, timestamp) is not None

    # Scheduling Methods
    def _validate_scheduling(
        self, scheduling: Optional[Dict[str, str]]
    ) -> Optional[Dict[str, str]]:
        """Validates the provided scheduling configuration.

        Args:
            scheduling (Optional[Dict[str, str]]): Scheduling configuration.

        Raises:
            TypeError: If scheduling is not a dictionary and value is not a string.
            ValueError: If scheduling contains invalid keys or values.
        """
        if scheduling is None:
            return None

        if not isinstance(scheduling, dict):
            raise TypeError("Scheduling must be a dictionary.")

        valid_keys = {"start_time", "end_time"}
        for key in scheduling:
            if key not in valid_keys:
                raise ValueError(f"Invalid scheduling key: {key}")

            time = scheduling[key]
            if not isinstance(time, str):
                raise TypeError(f"{key} must be a string.")
            if not self._is_valid_iso8601(time):
                raise ValueError(
                    f"Invalid '{key}' format. Use ISO8601 format (YYYY-MM-DDTHH:mm:SSZ)."
                )

        if "start_time" in scheduling and "end_time" in scheduling:
            if scheduling["end_time"] <= scheduling["start_time"]:
                raise ValueError("End time must be after start time.")

        return scheduling

    # QOS Metrics Methods
    def _validate_qos_metric(
        self, qos_metrics: Optional[Dict[str, Dict[str, Union[int, bool]]]]
    ) -> None:
        """Validates the provided quality of service metrics.

        Args:
            qos_metrics (Optional[Dict[str, Dict[str, Union[int, bool]]]]): Quality of service metrics.

        Raises:
            TypeError: If qos_metrics is not a dictionary and values are invalid types.
            ValueError: If qos_metrics contains invalid keys or values.
        """
        if qos_metrics is None:
            return

        if not isinstance(qos_metrics, dict):
            raise TypeError("QoS metrics must be a dictionary.")

        valid_keys = {"min_bw", "max_delay", "max_number_oxps"}
        for key, value_dict in qos_metrics.items():
            if key not in valid_keys:
                raise ValueError(f"Invalid QoS metric: {key}")
            if not isinstance(value_dict, dict):
                raise TypeError(f"QoS metric value for '{key}' must be a dictionary.")
            self._validate_qos_metric_value(key, value_dict)

    def _validate_qos_metric_value(
        self, key: str, value_dict: Dict[str, Union[int, bool]]
    ) -> None:
        """Validates the value dictionary for a specific QoS metric.

        Args:
            key (str): The key for the Qos Metric.
            value_dict (Dict[str, Union[int, bool]]): The value dictionary for the QoS metric.

        Raises:
            ValueError: If the value for the metric is out of the expected range.
            TypeError: If value or strict values are of incorrect type.
        """
        if "value" not in value_dict:
            raise ValueError(f"Missing required key 'value' in QoS metric for '{key}'")
        if not isinstance(value_dict["value"], int):
            raise TypeError(f"QoS value for '{key}' must be an integer.")
        if "strict" in value_dict and not isinstance(value_dict["strict"], bool):
            raise TypeError(f"'strict' in QoS metric of '{key}' must be a boolean.")

        # Specific range checks for each key
        if key == "min_bw":
            if not 0 <= value_dict["value"] <= 100:
                raise ValueError("qos_metric 'min_bw' value must be between 0 and 100.")
        elif key == "max_delay":
            if not 0 <= value_dict["value"] <= 1000:
                raise ValueError(
                    "qos_metric 'max_delay' value must be between 0 and 1000."
                )
        elif key == "max_number_oxps":
            if not 1 <= value_dict["value"] <= 100:
                raise ValueError(
                    "qos_metric 'max_number_oxps' value must be between 1 and 100."
                )

        # 'strict' key validation (default False)
        value_dict.get("strict", False)

    ### SDX Client Methods
    def create_l2vpn(self) -> dict:
        """Creates an L2VPN.

        Returns:
            dict: Dictionary containing the service_id if successful.

        Raises:
            SDXException: If the L2VPN creation fails.
            ValueError: If required attributes are missing.
        """
        # Debugging: Log current state
        self._logger.debug(f"Base URL: {self.base_url}")
        self._logger.debug(f"Name: {self.name}")
        self._logger.debug(f"Endpoints: {self.endpoints}")

        if not self.base_url or not self.name or not self.endpoints:
            raise ValueError(
                "Creating L2VPN requires the base URL, name, and endpoints at minumum."
            )
        if not isinstance(self.endpoints, list):
            raise TypeError("Endpoints must be a list.")

        url = f"{self.base_url}/l2vpn/{self.VERSION}"
        # print(url)

        headers = {
            "Content-Type": "application/json",  # Ensure JSON format
            "Authorization": f"Bearer {self.fabric_token}"
        }

        payload = {"name": self.name, "endpoints": self.endpoints}

        # Add optional attributes if provided.
        if self.description:
            payload["description"] = self.description
        if self.notifications:
            payload["notifications"] = self.notifications
        if self.scheduling:
            payload["scheduling"] = self.scheduling
        if self.qos_metrics:
            payload["qos_metrics"] = self.qos_metrics

        self._logger.debug("Sending request to create L2VPN with payload: %s", payload)

        # Check cache for existing request with same name and endpoints
        cache_key = (
            self.name,
            tuple(endpoint["port_id"] for endpoint in self.endpoints),
        )
        cached_data = self._request_cache.get(cache_key)

        if cached_data:
            _, response_json = cached_data
            return {"service_id": response_json.get("service_id")}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            response_json = response.json()
            cached_data = (payload, response_json)
            self._request_cache[cache_key] = cached_data
            self._logger.info(
                f"L2VPN created successfully with service_id: {response_json.get('service_id', 'UNKNOWN')}"
            )
            return {"service_id": response_json.get("service_id")}
        except HTTPError as e:
            status_code = e.response.status_code
            error_details = None

            try:
                error_details = e.response.json().get("error", None)
            except ValueError:
                error_details = e.response.text

            method_messages = {
                201: "L2VPN Service Created",
                400: "Request does not have a valid JSON or body is incomplete/incorrect",
                401: "Not Authorized",
                402: "Request not compatible (e.g., P2MP L2VPN requested, but only P2P supported)",
                409: "L2VPN Service already exists",
                410: "Can't fulfill the strict QoS requirements",
                411: "Scheduling not possible",
                412: "No path available between endpoints",
                422: "Attribute not supported by the SDX-LC/OXPO",
            }
            error_message = method_messages.get(status_code, "Unknown error occurred.")
            self._logger.error(
                f"Failed to create L2VPN. Status code: {status_code}: {error_message}"
            )
            raise SDXException(
                status_code=status_code,
                method_messages=method_messages,
                message=error_message,
                error_details=error_details,
            )
        except Timeout:
            self._logger.error("The request to create the L2VPN timed out.")
            raise SDXException(message="The request to create the L2VPN timed out.")
        except RequestException as e:
            self._logger.error(f"An error occurred while creating L2VPN: {e}")
            raise SDXException(message=f"An error occurred while creating L2VPN: {e}")

    def update_l2vpn(
        self,
        service_id: str,
        state: Optional[str] = None,
        name: Optional[str] = None,
        endpoints: Optional[List[Dict[str, str]]] = None,
        description: Optional[str] = None,
        notifications: Optional[Dict[str, Union[str, bool]]] = None,
        scheduling: Optional[Dict[str, str]] = None,
        qos_metrics: Optional[Dict[str, Dict[str, Union[int, bool]]]] = None,
    ) -> Optional[Dict[str, str]]:
        """Updates an existing L2VPN using the provided service ID and keyword arguments.

        Args:
            service_id (str): The ID of the L2VPN service to update.
            state (Optional[str]): The new state of the L2VPN, can be 'enabled' or 'disabled'.
            name (Optional[str]): The new name of the L2VPN.
            endpoints (Optional[List[Dict[str, str]]]): The new list of endpoints.
            description (Optional[str]): The new description of the L2VPN.
            notifications (Optional[Dict[str, Union[str, bool]]]): The new notifications settings.
            scheduling (Optional[Dict[str, str]]): The new scheduling information.
            qos_metrics (Optional[Dict[str, Dict[str, Union[int, bool]]]]): The new QoS metrics.

        Returns:
            Optional[Dict[str, str]]: A confirmation message with teh service_id on success, or raises an error on failure.

        Raises:
            SDXException: If the API request fails.
            ValueError: If any parameter is invalid.
        """

        url = f"{self.base_url}/l2vpn/{self.VERSION}/{service_id}"

        headers = {
            "Content-Type": "application/json",  # Ensure JSON format
            "Authorization": f"Bearer {self.fabric_token}"
        }

        payload = {"service_id": service_id}

        if state is not None:
            if state.lower() in ["enabled", "disabled"]:
                payload["state"] = state.lower()
            else:
                raise ValueError(
                    "Invalid state value. The 'state' attribute can only by changed to 'enabled' or 'disabled'."
                )

        attributes = {
            "name": name,
            "endpoints": endpoints,
            "description": description,
            "notifications": notifications,
            "scheduling": scheduling,
            "qos_metrics": qos_metrics,
        }

        for attr, value in attributes.items():
            if value is not None:
                payload[attr] = value

        self._logger.debug(f"Sending request to update L2VPN with payload: {payload}")

        try:
            response = requests.patch(
                url, json=payload, headers=headers, timeout=120
            )
            response.raise_for_status()
            self._logger.info(
                f"L2VPN update request sent to {url}, with payload: {payload}."
            )

            # No response body on success, so return a success message
            if response.status_code == 201:
                self._logger.info(
                    f"L2VPN with service_id {service_id} was successfully updated."
                )
                return {
                    "description": "L2VPN Service Modified",
                    "service_id": service_id,
                }

        except HTTPError as e:
            status_code = e.response.status_code
            error_details = None

            try:
                error_details = e.response.json().get("error", None)
            except ValueError:
                error_details = e.response.text

            method_messages = {
                201: "L2VPN Service Modified",
                400: "Request does not have a valid JSON or body is incomplete/incorrect",
                401: "Not Authorized",
                402: "Request not compatible (e.g., P2MP L2VPN requested, but only P2P supported)",
                404: "L2VPN Service ID not found",
                409: "Conflicts with a different L2VPN",
                410: "Can't fulfill the strict QoS requirements",
                411: "Scheduling not possible",
            }
            error_message = method_messages.get(status_code, "Unknown error occurred.")
            self._logger.error(
                f"Failed to update L2VPN. Status code: {status_code}: {error_message}"
            )
            raise SDXException(
                status_code=status_code,
                method_messages=method_messages,
                message=error_message,
                error_details=error_details,
            )
        except Timeout:
            self._logger.error("Request timed out.")
            raise SDXException("The request to update the L2VPN timed out.")
        except RequestException as e:
            self._logger.error(f"Failed to update L2VPN: {e}")
            raise SDXException(f"Failed to update L2VPN: {e}")

    def get_l2vpn(
        self, service_id: str, format: str = "dataframe"
    ) -> Union[pd.DataFrame, SDXResponse]:
        """Retrieves details of an existing L2VPN using the provided service ID.

        Args:
            service_id (str): The ID of the L2VPN to retrieve.
            format (str): The output format, either "dataframe" (default) or "json".

        Returns:
            Parsed response from the SDX API in the form of the json formatted
                SDXResponse or a DataFrame.

        Raises:
            SDXException: If the API request fails.
        """

        url = f"{self.base_url}/l2vpn/{self.VERSION}/{service_id}"

        headers = {
            "Content-Type": "application/json",  # Ensure JSON format
            "Authorization": f"Bearer {self.fabric_token}"
        }

        try:
            response = requests.get(url, headers=headers, timeout=120)
            response.raise_for_status()
            response_json = response.json()
            self._logger.info(f"L2VPN retrieval request sent to {url}.")
            self._logger.info(f"Full response: {response_json}")
            l2vpn_data = response_json.get(service_id)

            if l2vpn_data is None:
                raise SDXException(f"L2VPN with ID {service_id} not found.")

            # Create SDXResponse object, store it, and unpack it for display
            sdx_response = SDXResponse(l2vpn_data)
            self.last_sdx_response = sdx_response

            # Format as DataFrame if requested
            if format == "dataframe":
                # Flatten the endpoints for each row in the DataFrame
                node_info_list = [
                    {
                        **vars(
                            sdx_response
                        ),  # Convert SDXResponse attributes to dictionary
                        "port_id": endpoint.get("port_id"),
                        "vlan": endpoint.get("vlan"),
                    }
                    for endpoint in sdx_response.endpoints
                ]

                ordered_columns = [
                    "service_id",
                    "name",
                    "port_id",
                    "vlan",
                    "description",
                    "qos_metrics",
                    "notifications",
                    "ownership",
                    "creation_date",
                    "archived_date",
                    "status",
                    "state",
                    "counters_location",
                    "last_modified",
                    "current_path",
                    "oxp_service_ids",
                ]

                df = pd.DataFrame(node_info_list)
                return df[ordered_columns] if not df.empty else df

            elif format == "json":
                return vars(sdx_response)

            else:
                raise ValueError("Invalid format specified. Use 'dataframe' or 'json'.")

        except HTTPError as e:
            status_code = e.response.status_code
            error_details = None

            try:
                error_details = e.response.json().get("error", None)
            except ValueError:
                error_details = e.response.text

            method_messages = {
                200: "OK",
                401: "Not Authorized",
                404: "Service ID not found",
            }

            error_message = method_messages.get(status_code, "Unknown error occurred.")
            self._logger.error(
                f"Failed to retrieve L2VPN. Status code: {status_code}: {error_message}"
            )

            raise SDXException(
                status_code=status_code,
                method_messages=method_messages,
                message=error_message,
                error_details=error_details,
            )
        except Timeout:
            self._logger.error("Request timed out.")
            raise SDXException("The request to create the L2VPN timed out.")
        except RequestException as e:
            logging.error(f"Failed to retrieve L2VPN: {e}")
            raise SDXException(f"Failed to retrieve L2VPN: {e}")

    def get_all_l2vpns(
        self, archived: bool = False, format: str = "dataframe"
    ) -> Union[pd.DataFrame, Dict[str, SDXResponse]]:
        """
        Retrieves all L2VPNs, either archived or active.

        Args:
            archived(bool): If True, retrieve only archived L2VPNs. If False, retrieve only active L2VPNS.
            format (str): The output format, either "dataframe" (default) or "json".

        Returns:
            All l2vpns in the form of a dataframe or json dictionary.

        Raises:
            SDXException: If the API request fails with a known error code and description.
            ValueError: If an invalid parameters are provided.
        """

        if archived:
            url = f"{self.base_url}/l2vpn/{self.VERSION}/archived"
        else:
            url = f"{self.base_url}/l2vpn/{self.VERSION}"

        self._logger.info(f"Retrieving L2VPNs: URL={url}")

        headers = {
            "Content-Type": "application/json",  # Ensure JSON format
            "Authorization": f"Bearer {self.fabric_token}"
        }
        try:
            response = requests.get(url, headers=headers, timeout=120)
            response.raise_for_status()

            l2vpns_json = response.json()
            self._logger.info(f"L2VPN retrieval request sent to {url}.")
            self._logger.info(f"Retrieved L2VPNs successfully: {l2vpns_json}")

            # Parse each L2VPN JSON into SDXResponse objects
            l2vpns = {
                service_id: SDXResponse(l2vpn_data)
                for service_id, l2vpn_data in l2vpns_json.items()
            }

            # Format data for DataFrame if requested
            if format == "dataframe":
                node_info_list = [
                    {
                        "service_id": service_id,
                        **vars(
                            sdx_response
                        ),  # Convert SDXResponse attributes to dictionary
                    }
                    for service_id, sdx_response in l2vpns.items()
                ]
                return pd.DataFrame(node_info_list)
            elif format == "json":
                return {
                    service_id: vars(sdx_response)
                    for service_id, sdx_response in l2vpns.items()
                }
            else:
                raise ValueError("Invalid format specified. Use 'dataframe' or 'json'.")

        except HTTPError as e:
            status_code = e.response.status_code
            error_details = None

            try:
                error_details = e.response.json().get("error", None)
            except ValueError:
                error_details = e.response.text

            method_messages = {
                200: "OK",
            }

            error_message = method_messages.get(status_code, "Unknown error occurred.")
            self._logger.error(
                f"Failed to retrieve L2VPNs. Status code: {status_code}: {error_message}"
            )
            raise SDXException(
                status_code=status_code,
                method_messages=method_messages,
                message=error_message,
                error_details=error_details,
            )
        except Timeout:
            self._logger.error("Request timed out.")
            raise SDXException("The request to retrieve L2VPN(s) timed out.")
        except RequestException as e:
            self._logger.error(f"Failed to retrieve L2VPN(s): {e}")
            raise SDXException(f"Failed to retrieve L2VPN(s): {e}")

    def delete_l2vpn(self, service_id: str) -> Optional[Dict]:
        """Deletes an L2VPN using the provided L2VPN ID.

        Args:
            service_id (str): The ID of the L2VPN to delete.

        Returns:
            dict: Response from the SDX API.

        Raises:
            SDXException: If the API request fails.
        """
        url = f"{self.base_url}/l2vpn/{self.VERSION}/{service_id}"

        headers = {
            "Content-Type": "application/json",  # Ensure JSON format
            "Authorization": f"Bearer {self.fabric_token}"
        }

        try:
            response = requests.delete(url, headers=headers, timeout=120)
            response.raise_for_status()
            self._logger.info(f"L2VPN deletion request sent to {url}.")
            return response.json() if response.content else None
        except HTTPError as e:
            status_code = e.response.status_code
            error_details = None

            try:
                error_details = e.response.json().get("error", None)
            except ValueError:
                error_details = e.response.text

            method_messages = {
                201: "L2VPN Deleted",
                401: "Not Authorized",
                404: "L2VPN Service ID provided does not exist",
            }

            error_message = method_messages.get(status_code, "Unknown error occurred.")
            self._logger.error(
                f"Failed to delete L2VPN. Status code: {status_code}: {error_message}"
            )

            raise SDXException(
                status_code=status_code,
                method_messages=method_messages,
                message=error_message,
                error_details=error_details,
            )

        except Timeout:
            self._logger.error("Request timed out.")
            raise SDXException("The request to delete the L2VPN timed out.")

        except RequestException as e:
            self._logger.error(f"Failed to delete L2VPN: {e}")
            raise SDXException(message=f"Failed to delete L2VPN: {e}")

    def get_available_ports(
        self, format: str = "dataframe"
    ) -> Union[pd.DataFrame, List[Dict[str, str]]]:
        """Fetches and returns a list of available ports from the SDX topology.

        Args:
            format (str): The output format, either "dataframe" (default) or "json".

        Returns:
            Union[pd.DataFrame, List[Dict[str, str]]]: The available ports in the specified format.

        Raises:
            SDXException: If the API request fails or returns an error.
        """
        topology_url = f"{self.base_url}/topology"

        headers = {
            "Content-Type": "application/json",  # Ensure JSON format
            "Authorization": f"Bearer {self.fabric_token}"
        }

        try:
            response = requests.get(topology_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Extract available ports
            port_list = []
            for node in data.get("nodes", []):
                for port in node.get("ports", []):
                    if port.get("status") == "up" and not port.get("nni"):
                        port_list.append(
                            {"Port ID": port.get("id"), "Status": port.get("status")}
                        )

            # Return in the requested format
            if format == "dataframe":
                df = pd.DataFrame(port_list, index=None)
                return df.style.hide(axis="index")
            elif format == "json":
                return port_list
            else:
                raise ValueError("Invalid format specified. Use 'dataframe' or 'json'.")

        except HTTPError as e:
            status_code = e.response.status_code
            error_details = None

            try:
                error_details = e.response.json().get("error", None)
            except ValueError:
                error_details = e.response.text

            method_messages = {
                400: "Request does not have a valid JSON or body is incomplete/incorrect",
                401: "Not Authorized",
                404: "Topology endpoint not found",
            }
            error_message = method_messages.get(status_code, "Unknown error occurred.")
            self._logger.error(
                f"Failed to retrieve available ports. Status code: {status_code}: {error_message}"
            )
            raise SDXException(
                status_code=status_code,
                method_messages=method_messages,
                message=error_message,
                error_details=error_details,
            )

        except Timeout:
            self._logger.error("The request to retrieve available ports timed out.")
            raise SDXException("The request to retrieve available ports timed out.")

        except RequestException as e:
            self._logger.error(f"Failed to retrieve available ports: {e}")
            raise SDXException(f"Failed to retrieve available ports: {e}")

    # Utility Methods
    def __str__(self) -> str:
        """Returns a string description of the SDXClient instance."""
        return (
            f"SDXClient(name={self.name}, endpoints={self.endpoints}, "
            f"description={self.description}, notifications={self.notifications}, "
            f"scheduling={self.scheduling}, qos_metrics={self.qos_metrics}, "
            f"base_url={self.base_url})"
        )

    def __repr__(self) -> str:
        """Returns a string representation of the SDXClient instance."""
        return (
            f"SDXClient(name={self.name}, endpoints={self.endpoints}, "
            f"description={self.description}, notifications={self.notifications}, "
            f"scheduling={self.scheduling}, qos_metrics={self.qos_metrics}, "
            f"base_url={self.base_url})"
        )
