# sdxlib/token_auth.py
from typing import Dict

class TokenAuth:
    """
    Minimal helper: receive a Bearer token (from the HTTP header) and
    provide headers for downstream SDX calls. No file I/O, no fablib.
    """
    def __init__(self, token: str):
        if not token:
            raise ValueError("Bearer token is required")
        self.token = token

    def bearer_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

