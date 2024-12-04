class ServiceUnavailableError(Exception):
    """Exception raised when the service is temporarily unavailable."""
    def __init__(self, message):
        super().__init__(message)
