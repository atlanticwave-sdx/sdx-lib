from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager

class FablibHandler:
    """
    A class to handle the creation of FablibManager and to show slice details.
    """

    def __init__(self, slice_name="Slice-AWSDX"):
        """
        Initializes the FablibHandler class with an optional slice name.
        
        Args:
            slice_name (str, optional): The name of the slice to initialize. Defaults to None.
        """
        self.project_id = None
        self.project_name = None
        self.fabric_ip = None
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
            self.slice.show()  # Assuming that the slice has a 'show()' method
        else:
            print("Error: Slice is not initialized.")

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
