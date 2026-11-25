"""Pymodbus Exceptions.

Custom exceptions to be used in the Modbus code.
"""

__all__ = [
    "ConnectionException",
    "MessageRegisterException",
    "ModbusIOException",
    "NoSuchIdException",
    "NotImplementedException",
    "ParameterException",
]


class ModbusException(Exception):
    """Base modbus exception."""

    #: Category shown as "[category]" in front of the message, set by subclasses.
    category: str = ""

    def __init__(self, string: str = "") -> None:
        """Initialize the exception.

        :param string: The message to append to the error
        """
        if self.category:
            string = f"[{self.category}] {string}"
        self.string = string
        super().__init__(string)

    def __str__(self) -> str:
        """Return string representation."""
        return f"Modbus Error: {self.string}"

    def isError(self) -> bool:
        """Error"""
        return True


class ModbusIOException(ModbusException):
    """Error resulting from data i/o."""

    category = "Input/Output"

    def __init__(
        self,
        string: str = "",
        function_code: int | None = None,
        *,
        transaction_id: int = 0,
        dev_id: int = 0,
        used_len: int = 0,
    ) -> None:
        """Initialize the exception.

        :param string: The message to append to the error
        :param function_code: Optional function code associated with the error
        :param transaction_id: Optional framing transaction id (e.g. MBAP TID)
        :param dev_id: Optional framing device / unit id
        """
        self.fcode = (
            0x80
            if not function_code
            else function_code + 0x80
            if function_code < 0x80
            else function_code
        )
        self.transaction_id = transaction_id
        self.dev_id = dev_id
        self.used_len = used_len
        super().__init__(string)
        self.message = self.string


class ParameterException(ModbusException):
    """Error resulting from invalid parameter."""

    category = "Invalid Parameter"


class NoSuchIdException(ModbusException):
    """Error resulting from making a request to a id that does not exist."""

    category = "No Such id"


class NotImplementedException(ModbusException):
    """Error resulting from not implemented function."""

    category = "Not Implemented"


class ConnectionException(ModbusException):
    """Error resulting from a bad connection."""

    category = "Connection"


class MessageRegisterException(ModbusException):
    """Error resulting from failing to register a custom message request/response."""

    category = "Error registering message"
