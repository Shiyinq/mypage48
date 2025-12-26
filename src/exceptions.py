from typing import Optional


class DomainException(Exception):
    """
    Base class for all domain exceptions.
    Simplifies exception writing by auto-setting message from ERROR_MESSAGE.
    """

    ERROR_MESSAGE: Optional[str] = None

    def __init__(self, message: Optional[str] = None):
        """
        Initialize exception with message.

        Args:
            message: Custom message. If None, will use ERROR_MESSAGE from class attribute.
        """
        self.message = message or self.ERROR_MESSAGE or "An error occurred"
        super().__init__(self.message)
