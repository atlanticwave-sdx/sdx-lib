import logging
import re
from typing import Optional, List, Dict, Union
from requests.exceptions import RequestException, HTTPError, Timeout

from sdxlib.sdx_exception import SDXException

class SDXValidator:
    """ Validation utilities for SDXClient."""
    
    PORT_ID_PATTERN = r"^urn:sdx:port:[a-zA-Z0-9.,-_\/]+:[a-zA-Z0-9.,-_\/]+:[a-zA-Z0-9.,-_\/]+$"
    
    @staticmethod
    def validate_required_attributes(base_url: str, name: Optional[str], endpoints: Optional[List[Dict[str, str]]]) -> None:
        """ Validates required attributes before making an API request."""
        if not base_url or not name or not endpoints:
            raise ValueError("Base URL, name, and endpoints are required.")
    
    @staticmethod
    def validate_non_empty_string(value: str, field_name: str) -> str:
        """ Validates that a string is non-empty."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string.")
        return value

    @staticmethod
    def validate_name(name: Optional[str]) -> Optional[str]:
        """ Validates the name attribute."""
        if name and (not isinstance(name, str) or len(name) > 50):
            raise ValueError("Name must be a non-empty string with max 50 characters.")
        return name

    @staticmethod
    def validate_description(description: Optional[str]) -> Optional[str]:
        """ Validates the description attribute."""
        if description and len(description) > 255:
            raise ValueError("Description must be less than 256 characters.")
        return description

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validates an email address format."""
        if not isinstance(email, str):
            return False
        email_regex = r"^\S+@\S+$"
        return re.match(email_regex, email) is not None

    @staticmethod
    def validate_notifications(notifications: Optional[List[Dict[str, str]]]) -> Optional[List[Dict[str, str]]]:
        """ Validates the notifications attribute."""
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
                raise ValueError("Each notification dictionary must contain a key 'email'.")
            if not SDXValidator.is_valid_email(notification["email"]):
                raise ValueError(f"Invalid email address or email format: {notification['email']}")
            validated_notifications.append(notification)
        return validated_notifications

    @staticmethod
    def _validate_vlan_range(vlan_range: str) -> Dict[str, str]:
        """Validates VLAN range format.
        Args:
        vlan_range (str): VLAN range in format 'ID1:ID2'.
        Returns:
        Dict[str, str]: Validated VLAN range.
        Raises:
        ValueError: If the VLAN range is not valid.
        """
        try:
            vlan_id1, vlan_id2 = map(int, vlan_range.split(":"))
            if 1 <= vlan_id1 < vlan_id2 <= 4095:
                return {"vlan": vlan_range}
        except ValueError:
            pass

        raise ValueError(
            f"Invalid VLAN range format: '{vlan_range}'. Must be 'VLAN ID1:VLAN ID2' "
            "with values between 1 and 4095, where ID1 < ID2."
        )

    @staticmethod
    def validate_endpoint_dict(endpoint_dict: Dict[str, str]) -> Dict[str, str]:
        """ Validates a single endpoint dictionary.
        Args:
        endpoint_dict (Dict[str, str]): Endpoint dictionary.
        Returns:
        Dict[str, str]: Validated endpoint dictionary.
        Raises:
        TypeError: If endpoint_dict is not a dictionary.
        ValueError: If endpoint_dict does not contain required keys or VLAN is invalid.
        """
        if not isinstance(endpoint_dict, dict):
            raise TypeError("Endpoint must be a dictionary.")

        port_id = endpoint_dict.get("port_id")
        vlan_value = endpoint_dict.get("vlan")

        if not port_id or not isinstance(port_id, str):
            raise ValueError("Each endpoint must contain a valid 'port_id' key.")
        if not re.match(SDXValidator.PORT_ID_PATTERN, port_id):
            raise ValueError(f"Invalid port_id format: {port_id}")

        if not vlan_value or not isinstance(vlan_value, str):
            raise ValueError("Each endpoint must contain a valid 'vlan' key.")

        # Validate VLAN values
        if vlan_value in {"any", "all", "untagged"}:
            return endpoint_dict  # Valid special VLAN

        if vlan_value.isdigit():
            if 1 <= int(vlan_value) <= 4095:
                return endpoint_dict
            raise ValueError(f"Invalid VLAN value: '{vlan_value}'. Must be between 1 and 4095.")

        if ":" in vlan_value:
            return SDXValidator._validate_vlan_range(vlan_value)

        raise ValueError(
            f"Invalid VLAN value: '{vlan_value}'. Must be 'any', 'all', 'untagged', "
            "a number between 1 and 4095, or a range in 'VLAN ID1:VLAN ID2' format."
        )

    @staticmethod
    def validate_endpoints(endpoints: Optional[List[Dict[str, str]]]) -> List[Dict[str, str]]:
        """ Validates a list of endpoints.
        Args:
        endpoints (Optional[List[Dict[str, str]]]): List of endpoint dictionaries.
        Returns:
        List[Dict[str, str]]: Validated list of endpoint dictionaries.
        Raises:
        TypeError: If endpoints is not a list.
        ValueError: If endpoints list is empty, has fewer than 2 entries,
                    or contains inconsistent VLAN configurations.
        """
        if not endpoints:
            return []

        if not isinstance(endpoints, list):
            raise TypeError("Endpoints must be a list.")
        if len(endpoints) < 2:
            raise ValueError("Endpoints must contain at least 2 entries.")

        special_vlans = {"any", "all", "untagged"}
        validated_endpoints = [SDXValidator.validate_endpoint_dict(ep) for ep in endpoints]
        vlan_values = {ep["vlan"] for ep in validated_endpoints}

        has_special_vlan = vlan_values & special_vlans
        has_vlan_range = any(":" in vlan for vlan in vlan_values)
        has_single_vlan = any(vlan.isdigit() for vlan in vlan_values)

        # Ensure VLAN consistency across endpoints
        if has_vlan_range and (len(vlan_values) > 1 or has_special_vlan or has_single_vlan):
            raise ValueError("All endpoints must have the same VLAN value if one uses a range.")

        if has_special_vlan and (len(vlan_values) > 1 or has_vlan_range or has_single_vlan):
            raise ValueError("All endpoints must have the same VLAN value if one uses 'any', 'all', or 'untagged'.")

        return validated_endpoints

    @staticmethod
    def is_valid_iso8601(timestamp: str) -> bool:
        """Checks if the provided string is a valid ISO8601 formatted timestamp."""
        timestamp_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        return re.match(timestamp_pattern, timestamp) is not None

    @staticmethod
    def validate_scheduling(scheduling: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Validates scheduling dictionary."""
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
            if not SDXValidator.is_valid_iso8601(time):
                raise ValueError(f"Invalid '{key}' format. Use ISO8601 format (YYYY-MM-DDTHH:mm:SSZ).")

        if "start_time" in scheduling and "end_time" in scheduling:
            if scheduling["end_time"] <= scheduling["start_time"]:
                raise ValueError("End time must be after start time.")
        
        return scheduling
        
    @staticmethod
    def validate_qos_metric_value(key: str, value_dict: Dict[str, Union[int, bool]]) -> None:
        """Validates QoS metric values."""
        if "value" not in value_dict or not isinstance(value_dict["value"], int):
            raise ValueError(f"QoS value for '{key}' must be an integer.")
        if "strict" in value_dict and not isinstance(value_dict["strict"], bool):
            raise TypeError(f"'strict' in QoS metric of '{key}' must be a boolean.")

        valid_ranges = {"min_bw": (0, 100), "max_delay": (0, 1000), "max_number_oxps": (1, 100)}
        min_val, max_val = valid_ranges[key]
        if not (min_val <= value_dict["value"] <= max_val):
            raise ValueError(f"{key} must be between {min_val} and {max_val}.")
    
    @staticmethod
    def validate_qos_metrics(qos_metrics: Optional[Dict[str, Dict[str, Union[int, bool]]]]) -> None:
        """Validates QoS metrics."""
        if qos_metrics is None:
            return
        if not isinstance(qos_metrics, dict):
            raise TypeError("QoS metrics must be a dictionary.")
        
        valid_keys = {"min_bw", "max_delay", "max_number_oxps"}
        for key, value_dict in qos_metrics.items():
            if key not in valid_keys or not isinstance(value_dict, dict):
                raise ValueError(f"Invalid QoS metric: {key}")
            SDXValidator.validate_qos_metric_value(key, value_dict)

    @staticmethod
    def handle_http_error(logger: logging.Logger, e: HTTPError, operation: str) -> None:
        """Handles HTTP errors by logging and raising an SDXException."""
        logger.error(f"HTTP error occurred during {operation}: {e}")

        error_details = None
        status_code = getattr(e.response, "status_code", "Unknown")
        
        try:
            # Check if response content is JSON before attempting to parse
            if "application/json" in e.response.headers.get("Content-Type", ""):
                try:
                    error_json = e.response.json()
                    error_details = error_json.get("error", "No detailed error provided.") if isinstance(error_json, dict) else str(error_json)
                except ValueError:
                    error_details = "Invalid JSON response"
            else:
                error_details = e.response.text  # Use raw text if not JSON
        except AttributeError:
            error_details = "Error details unavailable"

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
        logger.error(f"Failed to {operation}. Status code: {status_code}: {error_message}")

        return {
            "status_code": status_code,
            "method_messages": method_messages,
            "message": error_message,
            "error_details": error_details
        }