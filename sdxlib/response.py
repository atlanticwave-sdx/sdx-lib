# sdxlib/response.py
"""
Normalize API responses into consistent dicts.
"""

from typing import Dict, Any, List, Optional


def normalize_l2vpn_response(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "service_id": data.get("service_id", "unknown"),
        "name": data.get("name", ""),
        "endpoints": data.get("endpoints", []),
        "ownership": data.get("ownership", ""),
        "creation_date": data.get("creation_date", ""),
        "archived_date": data.get("archived_date", ""),
        "status": data.get("status", ""),
        "state": data.get("state", ""),
        "counters_location": data.get("counters_location", ""),
        "last_modified": data.get("last_modified", ""),
        "current_path": data.get("current_path", []),
        "oxp_service_ids": data.get("oxp_service_ids", []),
        "description": data.get("description"),
        "notifications": data.get("notifications"),
        "scheduling": data.get("scheduling"),
        "qos_metrics": data.get("qos_metrics"),
    }

