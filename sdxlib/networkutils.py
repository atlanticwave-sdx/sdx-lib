import os
import subprocess
import socket

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
