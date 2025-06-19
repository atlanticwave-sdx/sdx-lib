import os
import json
import jwt  # PyJWT library for decoding JWT tokens
import requests
import mysql.connector
import http.client
import ssl
import re
import hashlib
import base64
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


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
            self.token_iss = self.token_decoded.get("iss", None)  # Issuer
            self.token_aud = self.token_decoded.get("aud", None)  # Audience

            # Remove 'http://cilogon.org' from it
            sub_extract = self.token_sub.replace('http://cilogon.org', '')

            # Replace 'serverA', 'serverB', ..., 'serverZ' with 'serverX'
            sub_extract = re.sub(r'server[A-Z]', 'serverX', sub_extract)

            # Get SHA-256 hash as hex string (like PHP)
            hashed_hex = hashlib.sha256(sub_extract.encode('utf-8')).hexdigest()

            # Base64 encode the hex string (as bytes)
            base64_encoded = base64.b64encode(hashed_hex.encode('utf-8')).decode('utf-8')

            # Trim to first 16 characters
            trimmed_output = base64_encoded[:16]

            connection = mysql.connector.connect(
                host='190.103.184.199',
                port=3306,  # Must be exposed in docker-compose.yml
                database='your_database_name',  # From your script
                user='your_user',  # From your script
                password='your_password'  # From your script
            )
            cursor = connection.cursor(dictionary=True)  # dictionary=True for dict results

            # Prepare query with WHERE clause and parameter placeholder
            query = "SELECT * FROM meican_user WHERE login = %s"
            params = (trimmed_output,)

            cursor.execute(query, params)

            # Fetch all results
            users = cursor.fetchall()

            # Print each user
            for user in users:
                print(user)
                user_id = user['id']
                is_active = user['is_active']
                user_registration_token = user['registration_token']

            # Clean up
            cursor.close()
            # connection.close()

            if not users:
                login = trimmed_output
                authkey = secrets.token_urlsafe(12)
                password = hashlib.sha256('test'.encode('utf-8')).hexdigest()
                language = 'en-US'
                date_format = 'dd/MM/yyyy'
                time_zone = 'HH:mm'
                time_format = 'New_York'
                if "email" in self.token_decoded:
                    email = self.token_decoded['email']
                else:
                    email = 'test@test.com'
                if "given_name" in self.token_decoded and "family_name" in self.token_decoded:
                    name = self.token_decoded['given_name'] + self.token_decoded['family_name']
                else:
                    name = 'userXYZ'
                registration_token = secrets.token_urlsafe(12)[:20]

                cursor = connection.cursor(dictionary=True)  # dictionary=True for dict results
                # Prepare INSERT query
                query = "INSERT INTO meican_user (login,password,authkey,email,name,registration_token,language,date_format,time_zone,time_format) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                values = (login, password, authkey, email, name, registration_token, language, date_format, time_zone,
                          time_format)

                # Execute query
                cursor.execute(query, values)

                # Commit the transaction
                connection.commit()

                print(f"{cursor.rowcount} row inserted.")
                exit()

            else:
                if is_active == 0:
                    if "eppn" in self.token_decoded and "email" in self.token_decoded:
                        cursor = connection.cursor(dictionary=True)  # dictionary=True for dict results
                        # Insert into meican_user_domain
                        try:
                            cursor.execute(
                                "INSERT INTO meican_user_domain (id, user_id) VALUES (%s, %s)",
                                (user_id, user_id)
                            )
                        except mysql.connector.Error as e:
                            print("Insert failed (meican_user_domain):", e)

                        # Insert into meican_auth_assignment
                        try:
                            cursor.execute(
                                "INSERT INTO meican_auth_assignment (item_name, user_id) VALUES (%s, %s)",
                                ('g10', user_id)
                            )
                        except mysql.connector.Error as e:
                            print("Insert failed (meican_auth_assignment):", e)

                        # Insert into meican_user_topology_domain
                        try:
                            cursor.execute(
                                "INSERT INTO meican_user_topology_domain (id, user_id, domain) VALUES (%s, %s, %s)",
                                (user_id, user_id, 'ampath.net,sax.net,tenet.ac.za')
                            )
                        except mysql.connector.Error as e:
                            print("Insert failed (meican_user_topology_domain):", e)

                        connection.commit()
                        print("All inserts attempted.")
                        # Example update query
                        query = "UPDATE meican_user SET is_active = %s WHERE id = %s"
                        values = ("1", user_id)  # Replace with actual values

                        cursor.execute(query, values)
                        connection.commit()

                        print(f"{cursor.rowcount} row(s) updated.")
                        exit()

                    else:
                        email_address_to_send = 'muhaziz@fiu.edu'  # we can replace this or ask from user where to send the verification email in sdxlib
                        # Config
                        smtp_server = 'smtp.gmail.com'
                        smtp_port = 587
                        smtp_username = 'meican.sdx@gmail.com'  # Your Gmail address
                        smtp_password = 'ikgzcvqiniraboci'  # Use App Password if 2FA is on
                        from_email = 'meican.sdx@gmail.com'
                        to_email = email_address_to_send  # Replace with $email equivalent
                        base_url = '127.0.0.1'  # Replace with actual base_url
                        registration_token_email = user_registration_token  # Replace with token

                        # Compose message
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = 'Verify your MEICAN email'
                        msg['From'] = from_email
                        msg['To'] = to_email

                        # Email content
                        text = "Verify your email\nClick on the link below to verify your MEICAN email\n" \
                               f"https://{base_url}/aaa/login/verifyemail?token={registration_token_email}"

                        html = f"""\
                        <html>
                          <body>
                            <b>Verify your email</b>
                            <p>Click on the link below to verify your MEICAN email</p>
                            <a href="https://{base_url}/aaa/login/verifyemail?token={registration_token_email}">
                                https://{base_url}/aaa/login/verifyemail?token={registration_token_email}
                            </a>
                          </body>
                        </html>
                        """

                        # Attach plain and HTML versions
                        msg.attach(MIMEText(text, 'plain'))
                        msg.attach(MIMEText(html, 'html'))

                        # Send email
                        try:
                            with smtplib.SMTP(smtp_server, smtp_port) as server:
                                server.starttls()
                                server.login(smtp_username, smtp_password)
                                server.sendmail(from_email, to_email, msg.as_string())
                            print("Email sent successfully.")
                        except Exception as e:
                            print("Failed to send email:", str(e))

                        exit()

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
