# sdxlib/__init__.py
"""
AtlanticWave-SDX Python Library

Public API:
    - get_topology(token)
    - get_available_ports(token, ...)
    - get_all_l2vpns(token, ...)
    - get_l2vpn(token, service_id, ...)
    - create_l2vpn(token, name, endpoints, ...)
    - update_l2vpn(token, service_id, ...)
    - delete_l2vpn(token, service_id)
"""

from .topology_utils import get_topology, get_available_ports, get_all_l2vpns
from .l2vpn import get_l2vpn, create_l2vpn, update_l2vpn, delete_l2vpn

__all__ = [
    "get_topology",
    "get_available_ports",
    "get_all_l2vpns",
    "get_l2vpn",
    "create_l2vpn",
    "update_l2vpn",
    "delete_l2vpn",
]

__version__ = "1.0.0"

