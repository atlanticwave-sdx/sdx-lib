class SDXException(Exception):
    """Custom exception class for SDXClient API errors.

    Attributes:
        status_code (int): HTTP status code associated with the error.
        method_messages (dict, optional): Dictionary mapping error codes to
            specific messages for a particular method (e.g., create_l2vpn,
            update_l2vpn).
        message (str): General error message describing the exception.
        error_details (str): Additional error details from the API response.
    """

    def __init__(self, status_code=None, method_messages=None, message=None, error_details=None):
        """Initializes an SDXException with status code, message, and optional error details.

        Args:
            status_code (int): HTTP status code.
            method_messages (dict, optional): Dictionary mapping error codes to
                specific messages for a particular method.
            message (str): General error message.
            error_details (str, optional): Additional error details from the API response.

        """
        self.status_code = status_code
        self.method_messages = method_messages or {}
        self.error_details = error_details or ""

        # Get a meaningful message based on the status code and method messages
        self.message = message or self.method_messages.get(status_code, "Unknown error occurred.")

        # Include additional error details, if available
        if self.error_details:
            self.message += f" Additional details: {self.error_details}"

        super().__init__(self.message)

    def __str__(self):
        return f"SDXException: {self.message} (status_code={self.status_code})"
