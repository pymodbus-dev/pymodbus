"""**Modbus Client common base.**

All client share a set of parameters as well as all methods available to applications,
are defined in :mod:`ModbusBaseClient`.

:mod:`ModbusBaseClient` is normally not referenced outside :mod:`pymodbus`, unless
you want to make a custom client. Custom client class **must** inherit
:mod:`ModbusBaseClient`.

Custom client implementation example::

    from pymodbus.client import ModbusBaseClient

    class myOwnClient(ModbusBaseClient):

        def __init__(self, **kwargs):
            super().__init__(kwargs)

    def run():

        client = myOwnClient(...)
        client.start()
        rr = client.read_coils(0x01)
        client.stop()

.. tip::
    Parameters common for all clients are documented here, and not repeated with each
    client, this is in order to lower the maintenance burden and the risk of the
    documentation being inaccurate.
"""

import logging

from pymodbus.factory import ClientDecoder
from pymodbus.utilities import ModbusTransactionState, hexlify_packets
from pymodbus.transaction import DictTransactionManager
from pymodbus.client.mixin import ModbusClientMixin
from pymodbus.exceptions import (
    NotImplementedException,
    ConnectionException,
)

_logger = logging.getLogger(__name__)

TXT_NOT_IMPLEMENTED = "Method not implemented by derived class"


class ModbusBaseClient(ModbusClientMixin):
    """Base functionality common to all clients.

    :param modbus_decoder: (optional, default ClientDecoder) Modbus message decoder class.
    :param framer: (optional, default depend on client) Modbus Framer class.
    :param timeout: (optional, default 10s) Timeout for a request.
    :param retries: (optional, default 3) Max number of retries pr request.
    :param retry_on_empty: (optional, default false) Retry on empty response.
    :param close_comm_on_error: (optional, default true) Close connection on error.
    :param strict: (optional, default true) Strict timing, 1.5 character between requests.
    :param broadcast_enable: (optional, default false) True to treat id 0 as broadcast address.

    Handles common parameters and defines an internal interface
    which all clients must adhere to.

    Implements common functionality like e.g. `reconnect`.
    """

    def __init__(
        self,
        modbus_decoder=ClientDecoder,
        framer=None,
        timeout=10,
        retries=3,
        retry_on_empty=False,
        close_comm_on_error=True,
        strict=True,
        broadcast_enable=False,
        **kwargs
    ):
        """Initialize a client instance."""

        # get optional parameters or set defaults
        self.framer = framer(modbus_decoder(), self)
        self.timeout = timeout
        self.retries = retries
        self.retry_on_empty = retry_on_empty
        self.close_comm_on_error = close_comm_on_error
        self.strict = strict
        self.broadcast_enable = broadcast_enable
        self.kwargs = kwargs

        # Common variables.
        self.transaction = DictTransactionManager(self, **kwargs)

        # Initialize  mixin
        super().__init__()

    # ----------------------------------------------------------------------- #
    # Client external interface
    # ----------------------------------------------------------------------- #
    def start(self):
        """Connect to the modbus remote host.

        :raises NotImplementedException:
        """
        raise NotImplementedException(TXT_NOT_IMPLEMENTED)

    async def aStart(self):  # pylint: disable=invalid-name
        """Connect to the modbus remote host.

        :raises NotImplementedException:
        """
        raise NotImplementedException(TXT_NOT_IMPLEMENTED)

    def is_socket_open(self):
        """Check whether the underlying socket/serial is open or not.

        :raises NotImplementedException:
        """
        raise NotImplementedException(TXT_NOT_IMPLEMENTED)

    def close(self):
        """Close the underlying socket connection.

        :raises NotImplementedException:
        """
        raise NotImplementedException(TXT_NOT_IMPLEMENTED)

    async def aClose(self):  # pylint: disable=invalid-name
        """Close the underlying socket connection.

        :raises NotImplementedException:
        """
        raise NotImplementedException(TXT_NOT_IMPLEMENTED)

    # ----------------------------------------------------------------------- #
    # ********* TO DO SORTED, old ModbusBaseClient
    # ----------------------------------------------------------------------- #

    def send(self, request):
        """Send request."""
        if self.state != ModbusTransactionState.RETRYING:
            _logger.debug('New Transaction state "SENDING"')
            self.state = ModbusTransactionState.SENDING
        return self._send(request)

    def _send(self, request):  # pylint: disable=missing-type-doc
        """Send data on the underlying socket.

        :param request: The encoded request to send
        :raises NotImplementedException:
        """
        raise NotImplementedException(TXT_NOT_IMPLEMENTED)

    def recv(self, size):
        """Receive data."""
        return self._recv(size)

    def _recv(self, size):  # pylint: disable=missing-type-doc
        """Read data from the underlying descriptor.

        :param size: The number of bytes to read
        :raises NotImplementedException:
        """
        raise NotImplementedException(TXT_NOT_IMPLEMENTED)

    # ----------------------------------------------------------------------- #
    # Modbus client methods
    # ----------------------------------------------------------------------- #

    def execute(self, request=None):  # pylint: disable=missing-type-doc
        """Execute.

        :param request: The request to process
        :returns: The result of the request execution
        :raises ConnectionException:
        """
        if not self.start():
            raise ConnectionException(f"Failed to connect[{str(self)}]")
        return self.transaction.execute(request)

    # ----------------------------------------------------------------------- #
    # The magic methods
    # ----------------------------------------------------------------------- #
    def __enter__(self):
        """Implement the client with enter block.

        :returns: The current instance of the client
        :raises ConnectionException:
        """
        if not self.start():
            raise ConnectionException(f"Failed to connect[{self.__str__()}]")
        return self

    async def __aenter__(self):
        """Implement the client with enter block.

        :returns: The current instance of the client
        :raises ConnectionException:
        """
        if not await self.aStart():
            raise ConnectionException(f"Failed to connect[{self.__str__()}]")
        return self

    def __exit__(self, klass, value, traceback):
        """Implement the client with exit block."""
        self.close()

    async def __aexit__(self, klass, value, traceback):
        """Implement the client with exit block."""
        await self.close()

    def idle_time(self):
        """Bus Idle Time to initiate next transaction

        :return: time stamp
        """
        if self.last_frame_end is None or self.silent_interval is None:
            return 0
        return self.last_frame_end + self.silent_interval

    def _dump(self, data):
        """Dump."""
        _logger.debug(hexlify_packets(data))

    def register(self, function):  # pylint: disable=missing-type-doc
        """Register a function and sub function class with the decoder.

        :param function: Custom function class to register
        """
        self.framer.decoder.register(function)

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return "Null Transport"
