import os
import json
import jwt  # PyJWT library for decoding JWT tokens
import requests
import subprocess
import socket
from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager


class TokenAuthentication:
    """
    A class to handle token-based authentication using Fabric Credential Manager
    for secure communication with SDX Controller.
    """

    def __init__(
            self,
            token_path="/home/fabric/.tokens.json",
            proxy_hostname="sdxapi.atlanticwave-sdx.ai",
            proxy_port="443",
            endpoint="sax.net/sdx/topology",
            slice_name="Slice-AWSDX"):
        """
        Initializes the TokenAuthentication class with optional token path, endpoint, and slice name.
        If no path is provided, uses the environment variable FABRIC_TOKEN_LOCATION
        or defaults to /home/fabric/.tokens.json.

        Args:
            token_path (str, optional): Path to the token file. Defaults to None.
            endpoint (str, optional): The API endpoint to validate the token against. Defaults to 'sax.net/sdx/topology'.
            slice_name (str, optional): The name of the slice to initialize. Defaults to "Slice-AWSDX".
        """
        self.token_path = token_path or os.getenv("FABRIC_TOKEN_LOCATION", "/home/fabric/.tokens.json")
        self.project_id = None
        self.project_name = None
        self.fabric_ip = None
        self.fabric_token = None
        self.token_header = None
        self.token_payload = None
        self.token_kid = None
        self.token_decoded = None
        self.token_iss = None
        self.token_aud = None
        self.proxy_hostname = proxy_hostname
        self.proxy_port = proxy_port
        self.endpoint = endpoint  # API endpoint for token validation

        # Initialize FablibManager to interact with the Fabric API
        self.fablib = fablib_manager()

        # Assign Slice's Name (provided during initialization)
        self.slice_name = slice_name
        # Initialize the slice if slice_name is provided during initialization
        if self.slice_name:
            self.initialize_slice()

    def initialize_slice(self):
        """
        Initialize the slice using the slice_name that was passed during initialization.
        """
        if not self.slice_name:
            print("Error: Slice name not provided!")
            return

        # Initialize the slice using FablibManager
        self.slice = self.fablib.get_slice(self.slice_name)
        if self.slice:
            print(f"Slice '{self.slice_name}' initialized.")
        else:
            print(f"Error: Could not initialize slice '{self.slice_name}'.")

    def show_slice(self):
        """
        Show the details of the initialized slice.
        """
        if self.slice:
            print(f"Showing details for slice: {self.slice_name}")
            self.slice.show()
        else:
            print("Error: Slice is not initialized.")

    def load_token(self):
        """
        Load and decode the JWT token from the token file.
        
        Reads the token JSON file, decodes the JWT, and extracts key claims 
        such as the 'kid', 'iss', and 'aud'. Handles errors related to missing 
        token files or invalid token formats.
        """
        if not os.path.exists(self.token_path):
            print("Error: Token file not found!")

        print("FABRIC Token Path:", self.token_path)

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

            self.token_iss = self.token_decoded.get("iss", None)  # Issuer
            self.token_aud = self.token_decoded.get("aud", None)  # Audience

            print(f"FABRIC JWT Token: {self.fabric_token}")
            print("\n🔍 ✅ Decoded Token Claims:")
            for key, value in self.token_decoded.items():
                print(f"   {key}: {value}")

        except json.JSONDecodeError:
            print("Error: Failed to decode token JSON file!")
        except jwt.DecodeError:
            print("Error: Failed to decode JWT token!")
        except Exception as e:
            print(f"Unexpected Error: {e}")

    def get_project_info(self):
        """
        Retrieve project ID and project name from the Fabric configuration.

        This method assumes that a configuration manager (like fablib) is available
        to retrieve the project information.

        Raises:
            KeyError: If project_id or project_name is not found in the configuration.
        """
        try:
            # Retrieve project information using FablibManager
            config_dict = dict(self.fablib.get_config().items())
            self.project_id = config_dict.get("project_id")
            self.project_name = config_dict.get("project_name")

            if not self.project_id or not self.project_name:
                print("Error: Project ID or Project Name not found!")

            print(f"Project ID: {self.project_id}")
            print(f"Project Name: {self.project_name}")

        except Exception as e:
            print(f"Error retrieving project info: {e}")

    def get_fabric_ip(self):
        """
        Get the public IP address of the fabric by calling an external API (ipify).
        
        The method makes an HTTP GET request to retrieve the public IP address.
        """
        self.fabric_ip = requests.get("https://api64.ipify.org").text
        print(f"Fabric’s public IP: {self.fabric_ip}")

    def trace_route(self, hostname="sdxapi.atlanticwave-sdx.ai"):
        """
        Perform a traceroute to the specified hostname.
        
        Args:
            hostname (str, optional): The hostname to trace route. Defaults to 'sdxapi.atlanticwave-sdx.ai'.
        """
        print("Trace Route:")
        os.system(f"traceroute {hostname}")

    def ping_host(self, hostname="sdxapi.atlanticwave-sdx.ai"):
        """
        Ping the specified hostname and print the result.
        
        Args:
            hostname (str, optional): The hostname to ping. Defaults to 'sdxapi.atlanticwave-sdx.ai'.
        """
        try:
            result = subprocess.run(["ping", "-c", "4", hostname], capture_output=True, text=True, check=True)
            print("Ping:")
            print(result.stdout)  # Print the output of the ping command
        except subprocess.CalledProcessError as e:
            print(f"Ping failed:\n{e.stderr}")

    def check_connection(self, hostname="sdxapi.atlanticwave-sdx.ai", port=443):
        """
        Check the connection to a specific port using both 'nc' and 'socket'.
        
        Args:
            hostname (str, optional): The target hostname. Defaults to 'sdxapi.atlanticwave-sdx.ai'.
            port (int, optional): The port number to check. Defaults to 443.
        """
        try:
            os.system(f"nc -vz -w 10 {hostname} {port}")
            print(f"nc Connection successful to {hostname}:{port}")
        except Exception as e:
            print(f"Connection failed with nc: {e}")

        try:
            sock = socket.create_connection((hostname, port), timeout=10)
            print(f"Socket Connection successful to {hostname}:{port}")
            sock.close()
        except Exception as e:
            print(f"Connection failed with socket: {e}")

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


# Example of using the class
if __name__ == "__main__":
    token_auth = TokenAuthentication()
    token_auth.load_token()
    token_auth.get_project_info()
    token_auth.get_fabric_ip()
    token_auth.trace_route()
    token_auth.ping_host()
    token_auth.check_connection()
    token_auth.validate_token()

