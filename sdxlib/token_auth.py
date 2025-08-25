import os
import json
import jwt  # PyJWT library for decoding JWT tokens
import requests
from sdxlib.config import BASE_URL, PROXY_HOSTNAME, PROXY_PORT, FABRIC_TOKEN_PATH

class TokenAuth:
    """
    A class to handle token-based authentication
    for secure communication with SDX Controller.
    """

    def __init__(self):
        """
        Initializes the Token class
        """
        self.token = None
        self.token_header = None
        self.token_payload = None
        self.token_sub = None
        self.token_eppn = None
        self.token_given_name = None
        self.token_family_name = None
        self.token_kid = None
        self.token_decoded = None
        self.token_iss = None
        self.token_aud = None

    def _get_fabric_token(self):
        if not os.path.exists(FABRIC_TOKEN_PATH):
            print("Error: Token file not found!")
            raise FileNotFoundError(f"Token file not found at {FABRIC_TOKEN_PATH}")
        try:
            # Read the token JSON file
            with open(FABRIC_TOKEN_PATH, "r") as f:
                token_data = json.load(f)

            fabric_token = token_data.get("id_token", None)
            if fabric_token:
                self.token = fabric_token
                # Decode JWT header (to get 'kid')
                self.token_header = jwt.get_unverified_header(fabric_token)
                self.token_kid = self.token_header.get("kid", None)

                # Decode JWT token without verifying the signature (useful for debugging)
                self.token_decoded = jwt.decode(fabric_token, options={"verify_signature": False})

                self.token_sub = self.token_decoded.get("sub", None)  # unique identifier for the use
                self.token_eppn = self.token_decoded.get("eppn", None)  # Eduperson Persistent Identifier
                self.token_given_name = self.token_decoded.get("given_name", None)  # First Name
                self.token_family_name = self.token_decoded.get("family_name", None)  # Last Name
                self.token_iss = self.token_decoded.get("iss", None)  # Issuer
                self.token_aud = self.token_decoded.get("aud", None)  # Audience

                return self
            else:
                print("Error: Token is missing!")

        except json.JSONDecodeError:
            print("Error: Failed to decode fabric token JSON file!")
        except jwt.DecodeError:
            print("Error: Failed to decode fabric JWT token!")
        except Exception as e:
            print(f"Fabric Token Unexpected Error: {e}")

    def load_token(self, source = "fabric"):
        """
        Load and decode the JWT token from the token file.
        
        Reads the token JSON file, decodes the JWT, and extracts key claims 
        such as the 'kid', 'iss', and 'aud'. Handles errors related to missing 
        token files or invalid token formats.
        """
        if source == "fabric":
            return self._get_fabric_token()

    def validate_token(self):
        """
        Validate the token by sending a request to the SDX API.

        Sends a GET request to the specified endpoint to verify if the token is valid.
        Logs the response status and checks for an empty response before parsing the JSON.
        """
        if not PROXY_HOSTNAME or not PROXY_PORT:
            print("Error: Proxy hostname and port are not set!")

        # Construct the URL using proxy_hostname and proxy_port
        URL = f"https://{PROXY_HOSTNAME}:{PROXY_PORT}/api/"

        headers = {
            "Content-Type": "application/json",  # Ensure JSON format
            "Authorization": f"Bearer {self.token}"  # Use the decoded token
        }

        try:
            # Send GET request to validate token
            response = requests.get(URL + self.endpoint, headers=headers)

            # Log response status and raw text before parsing
            print(f"HTTP Status: {response.status_code}")

            # Check if response is empty before trying to parse JSON
            if not response.text.strip():
                print("Error: Response body is empty!")

        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")

        # Try parsing JSON with error handling
        try:
            response_data = response.json()
            print("Token is valid!")
            print("Response Data:", response_data)  # Print API response

        except json.JSONDecodeError as e:
            print("JSON Decode Error:", str(e))
            # print("Raw Response Text:", response.text)  # Print raw response for debugging
