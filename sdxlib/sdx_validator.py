# sdx_validator.py

import logging
import re
import hashlib
import base64
from typing import Optional, List, Dict, Union
from requests.exceptions import HTTPError
from sdxlib.sdx_token_auth import TokenAuthentication
from sdxlib.sdx_exception import SDXException


class SDXValidator:
    """Validation utilities for SDXClient."""

    PORT_ID_PATTERN = r"^urn:sdx:port:[a-zA-Z0-9.,-_\/]+:[a-zA-Z0-9.,-_\/]+:[a-zA-Z0-9.,-_\/]+$"

    @staticmethod
    def validate_required_url(BASE_URL: str, url_env: str) -> str:
        """
        Validates the environment string and returns the correct SDX API URL.
        Args:
        BASE_URL: constant defined with base url
        url_env (str): Must include 'test' or 'prod' (case-insensitive).
        Returns:
        str: Full URL for the SDX API.
        Raises:
        ValueError: If input is invalid or does not match expected environments.
        """
        if not isinstance(url_env, str) or not url_env.strip():
            raise ValueError("Environment must be a non-empty string.")
        env = url_env.strip().lower()
        if "test" in env or "prod" in env:
            return f"{BASE_URL}{url_env}"
        else:
            raise ValueError("Environment must include either 'test' or 'prod'.")

    @staticmethod
    def validate_required_attributes(base_url: str, name: Optional[str], endpoints: Optional[List[Dict[str, str]]]) -> None:
        if not base_url or not name or not endpoints:
            raise ValueError("Base URL, name, and endpoints are required.")

    @staticmethod
    def validate_non_empty_string(value: str, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string.")
        return value

    @staticmethod
    def validate_name(name: Optional[str]) -> Optional[str]:
        if name and (not isinstance(name, str) or len(name) > 50):
            raise ValueError("Name must be a non-empty string with max 50 characters.")
        return name

    @staticmethod
    def validate_ownership(ownership: Optional[str]) -> Optional[str]:
        if ownership is None:
            ownership = TokenAuthentication().load_token().token_sub

        if not isinstance(ownership, str) or not ownership.startswith("http://cilogon.org/"):
            raise ValueError("Invalid sub claim. Must be a CILogon-issued sub string.")

        sha256_hash = hashlib.sha256(ownership.encode("utf-8")).digest()
        b64_encoded = base64.urlsafe_b64encode(sha256_hash).decode("utf-8")
        return b64_encoded[:16]

    @staticmethod
    def verify_ownership(ownership: str, stored_hash: str) -> bool:
        return SDXValidator.validate_ownership(ownership) == stored_hash

    @staticmethod
    def validate_description(description: Optional[str]) -> Optional[str]:
        if description and len(description) > 255:
            raise ValueError("Description must be less than 256 characters.")
        return description

    @staticmethod
    def is_valid_email(email: str) -> bool:
        if isinstance(email, str):
            return re.match(r"^\S+@\S+$", email)
        return False

    @staticmethod
    def validate_notifications(notifications: Optional[List[Dict[str, str]]]) -> Optional[List[Dict[str, str]]]:
        if notifications is None:
            notifications = [{"email": TokenAuthentication().load_token().token_eppn}]

        if not isinstance(notifications, list):
            raise ValueError("Notifications must be provided as a list.")
        if len(notifications) > 10:
            raise ValueError("Notifications can contain at most 10 email addresses.")

        validated = []
        for n in notifications:
            if not isinstance(n, dict) or "email" not in n:
                raise ValueError("Each notification must be a dict with an 'email' key.")
            if not SDXValidator.is_valid_email(n["email"]):
                raise ValueError(f"Invalid email format: {n['email']}")
            validated.append(n)

        return validated

    @staticmethod
    def _validate_vlan_range(vlan_range: str) -> Dict[str, str]:
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

        if vlan_value in {"any", "all", "untagged"}:
            return endpoint_dict

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

        if has_vlan_range and (len(vlan_values) > 1 or has_special_vlan or has_single_vlan):
            raise ValueError("All endpoints must have the same VLAN value if one uses a range.")
        if has_special_vlan and (len(vlan_values) > 1 or has_vlan_range or has_single_vlan):
            raise ValueError("All endpoints must have the same VLAN value if one uses 'any', 'all', or 'untagged'.")

        return validated_endpoints

    @staticmethod
    def is_valid_iso8601(timestamp: str) -> bool:
        return re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", timestamp) is not None

    @staticmethod
    def validate_scheduling(scheduling: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
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
        logger.error(f"HTTP error occurred during {operation}: {e}")
        error_details = None
        status_code = getattr(e.response, "status_code", "Unknown")

        try:
            if "application/json" in e.response.headers.get("Content-Type", ""):
                try:
                    error_json = e.response.json()
                    error_details = error_json.get("error", "No detailed error provided.") if isinstance(error_json, dict) else str(error_json)
                except ValueError:
                    error_details = "Invalid JSON response"
            else:
                error_details = e.response.text
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

    @staticmethod
    def has_permission(
        logger: logging.Logger,
        user_id: Optional[str],
        ownership: Optional[str],
        services_func,
        service_id: Optional[str] = None
    ) -> bool:
        """
        Checks whether the user has permission to operate on the given service.
        """
        if not user_id or not ownership:
            logger.warning("[has_permission] Session is incomplete.")
            return False

        status_code, response, error = services_func(method="GET")

        if status_code != 200 or not isinstance(response, dict):
            logger.warning(f"[has_permission] Failed to fetch services: {error}")
            return False

        service_ids = response.get("services", [])
        if service_id and service_id not in service_ids:
            logger.warning(f"[has_permission] Unauthorized service_id: {service_id}")
            return False

        return True

