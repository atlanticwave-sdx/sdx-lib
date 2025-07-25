import os
import json
import jwt  # PyJWT library for decoding JWT tokens
import requests


class TokenAuthentication:
    """
    A class to handle token-based authentication using Fabric Credential Manager
    for secure communication with SDX Controller.
    """

    def __init__(self):
        """
        Initializes the TokenAuthentication class with optional token path, endpoint, and slice name.
        If no path is provided, uses the environment variable FABRIC_TOKEN_LOCATION
        or defaults to /home/fabric/.tokens.json.

        Args:
            token_path (str, optional): Path to the token file. Defaults to None.
            eppn (str, optional): The eppn (Education Person Persistent Identifier) 
            is a claim or attribute often included in authentication tokens,
            particularly in the context of Federated Identity systems, 
            such as those used in higher education and research institutions.
            endpoint (str, optional): The API endpoint to validate the token against. Defaults to 'sax.net/sdx/topology'.
            slice_name (str, optional): The name of the slice to initialize. Defaults to "Slice-AWSDX".
        """
        self.token_path = "/home/fabric/.tokens.json"
        self.fabric_token = None
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
        self.proxy_hostname = "sdxapi.atlanticwave-sdx.ai"
        self.proxy_port = "443"
        self.endpoint = "topology"

    def load_token(self):
        """
        Load and decode the JWT token from the token file.
        
        Reads the token JSON file, decodes the JWT, and extracts key claims 
        such as the 'kid', 'iss', and 'aud'. Handles errors related to missing 
        token files or invalid token formats.
        """
        if not os.path.exists(self.token_path):
            print("Error: Token file not found!")

        # print("FABRIC Token Path:", self.token_path)

        try:
            # Read the token JSON file
            with open(self.token_path, "r") as f:
                token_data = json.load(f)

            self.fabric_token = token_data.get("id_token", None)
            if not self.fabric_token:
                print("Error: Token is missing!")

            # Decode JWT header (to get 'kid')
            self.token_header = jwt.get_unverified_header(self.fabric_token)
            self.token_kid = self.token_header.get("kid", None)

            # Decode JWT token without verifying the signature (useful for debugging)
            self.token_decoded = jwt.decode(self.fabric_token, options={"verify_signature": False})

            self.token_sub = self.token_decoded.get("sub", None)  # unique identifier for the use
            self.token_eppn = self.token_decoded.get("eppn", None)  # Eduperson Persistent Identifier
            self.token_given_name = self.token_decoded.get("given_name", None)  # First Name
            self.token_family_name = self.token_decoded.get("family_name", None)  # Last Name
            self.token_iss = self.token_decoded.get("iss", None)  # Issuer
            self.token_aud = self.token_decoded.get("aud", None)  # Audience

            return self

        except json.JSONDecodeError:
            print("Error: Failed to decode token JSON file!")
        except jwt.DecodeError:
            print("Error: Failed to decode JWT token!")
        except Exception as e:
            print(f"Unexpected Error: {e}")

    def validate_token(self):
        """
        Validate the token by sending a request to the SDX API.

        Sends a GET request to the specified endpoint to verify if the token is valid.
        Logs the response status and checks for an empty response before parsing the JSON.
        """
        if not self.proxy_hostname or not self.proxy_port:
            print("Error: Proxy hostname and port are not set!")

        # Construct the URL using proxy_hostname and proxy_port
        URL = f"https://{self.proxy_hostname}:{self.proxy_port}/api/"

        headers = {
            "Content-Type": "application/json",  # Ensure JSON format
            "Authorization": f"Bearer {self.fabric_token}"  # Use the decoded token
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
