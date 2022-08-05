"""Sync client."""
# pylint: disable=missing-type-doc
from functools import partial
import logging
import sys
import time

import serial

from pymodbus.client.helper_sync import ModbusClientMixin
from pymodbus.constants import Defaults
from pymodbus.exceptions import (
    ConnectionException,
    NotImplementedException,
)
from pymodbus.factory import ClientDecoder
from pymodbus.transaction import (
    DictTransactionManager,
    ModbusRtuFramer,
)
from pymodbus.utilities import ModbusTransactionState, hexlify_packets

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
_logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# The Synchronous Clients
# --------------------------------------------------------------------------- #


class BaseModbusClient(ModbusClientMixin):
    """Interface for a modbus synchronous client.

    Defined here are all the methods for performing the related
    request methods.
    Derived classes simply need to implement the transport methods and set the correct
    framer.
    """

    def __init__(self, framer, **kwargs):
        """Initialize a client instance.

        :param framer: The modbus framer implementation to use
        """
        self.framer = framer
        self.transaction = DictTransactionManager(self, **kwargs)
        self._debug = False
        self._debugfd = None
        self.broadcast_enable = kwargs.get(
            "broadcast_enable", Defaults.broadcast_enable
        )

    # ----------------------------------------------------------------------- #
    # Client interface
    # ----------------------------------------------------------------------- #
    def connect(self):
        """Connect to the modbus remote host.

        :raises NotImplementedException:
        """
        raise NotImplementedException("Method not implemented by derived class")

    def close(self):
        """Close the underlying socket connection."""

    def is_socket_open(self):
        """Check whether the underlying socket/serial is open or not.

        :raises NotImplementedException:
        """
        raise NotImplementedException(
            f"is_socket_open() not implemented by {self.__str__()}"  # pylint: disable=unnecessary-dunder-call
        )

    def send(self, request):
        """Send request."""
        if self.state != ModbusTransactionState.RETRYING:
            _logger.debug('New Transaction state "SENDING"')
            self.state = ModbusTransactionState.SENDING
        return self._send(request)

    def _send(self, request):
        """Send data on the underlying socket.

        :param request: The encoded request to send
        :raises NotImplementedException:
        """
        raise NotImplementedException("Method not implemented by derived class")

    def recv(self, size):
        """Receive data."""
        return self._recv(size)

    def _recv(self, size):
        """Read data from the underlying descriptor.

        :param size: The number of bytes to read
        :raises NotImplementedException:
        """
        raise NotImplementedException("Method not implemented by derived class")

    # ----------------------------------------------------------------------- #
    # Modbus client methods
    # ----------------------------------------------------------------------- #
    def execute(self, request=None):
        """Execute.

        :param request: The request to process
        :returns: The result of the request execution
        :raises ConnectionException:
        """
        if not self.connect():
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
        if not self.connect():
            raise ConnectionException(f"Failed to connect[{self.__str__()}]")
        return self

    def __exit__(self, klass, value, traceback):
        """Implement the client with exit block."""
        self.close()

    def idle_time(self):
        """Bus Idle Time to initiate next transaction

        :return: time stamp
        """
        if self.last_frame_end is None or self.silent_interval is None:
            return 0
        return self.last_frame_end + self.silent_interval

    def debug_enabled(self):
        """Return a boolean indicating if debug is enabled."""
        return self._debug

    def set_debug(self, debug):
        """Set the current debug flag."""
        self._debug = debug

    def trace(self, writeable):
        """Show trace."""
        if writeable:
            self.set_debug(True)
        self._debugfd = writeable

    def _dump(self, data):
        """Dump."""
        fd = self._debugfd if self._debugfd else sys.stdout
        try:
            fd.write(hexlify_packets(data))
        except Exception as exc:  # pylint: disable=broad-except
            _logger.debug(hexlify_packets(data))
            _logger.exception(exc)

    def register(self, function):
        """Register a function and sub function class with the decoder.

        :param function: Custom function class to register
        """
        self.framer.decoder.register(function)

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return "Null Transport"


# --------------------------------------------------------------------------- #
# Modbus Serial Client Transport Implementation
# --------------------------------------------------------------------------- #


class ModbusSerialClient(
    BaseModbusClient
):  # pylint: disable=too-many-instance-attributes
    """Implementation of a modbus serial client."""

    state = ModbusTransactionState.IDLE
    inter_char_timeout = 0
    silent_interval = 0

    def __init__(self, framer=ModbusRtuFramer, **kwargs):
        """Initialize a serial client instance.

        :param port: The serial port to attach to
        :param stopbits: The number of stop bits to use
        :param bytesize: The bytesize of the serial messages
        :param parity: Which kind of parity to use
        :param baudrate: The baud rate to use for the serial device
        :param timeout: The timeout between serial requests (default 3s)
        :param strict:  Use Inter char timeout for baudrates <= 19200 (adhere
        to modbus standards)
        :param handle_local_echo: Handle local echo of the USB-to-RS485 adaptor
        :param framer: The modbus framer to use (default ModbusRtuFramer)
        """
        self.framer = framer
        self.socket = None
        BaseModbusClient.__init__(self, framer(ClientDecoder(), self), **kwargs)

        self.port = kwargs.get("port", 0)
        self.stopbits = kwargs.get("stopbits", Defaults.Stopbits)
        self.bytesize = kwargs.get("bytesize", Defaults.Bytesize)
        self.parity = kwargs.get("parity", Defaults.Parity)
        self.baudrate = kwargs.get("baudrate", Defaults.Baudrate)
        self.timeout = kwargs.get("timeout", Defaults.Timeout)
        self._strict = kwargs.get("strict", False)
        self.last_frame_end = None
        self.handle_local_echo = kwargs.get("handle_local_echo", False)
        if isinstance(self.framer, ModbusRtuFramer):
            if self.baudrate > 19200:
                self.silent_interval = 1.75 / 1000  # ms
            else:
                self._t0 = float((1 + 8 + 2)) / self.baudrate
                self.inter_char_timeout = 1.5 * self._t0
                self.silent_interval = 3.5 * self._t0
            self.silent_interval = round(self.silent_interval, 6)

    def connect(self):
        """Connect to the modbus serial server.

        :returns: True if connection succeeded, False otherwise
        """
        if self.socket:
            return True
        try:
            self.socket = serial.serial_for_url(
                self.port,
                timeout=self.timeout,
                bytesize=self.bytesize,
                stopbits=self.stopbits,
                baudrate=self.baudrate,
                parity=self.parity,
            )
            if isinstance(self.framer, ModbusRtuFramer):
                if self._strict:
                    self.socket.interCharTimeout = self.inter_char_timeout
                self.last_frame_end = None
        except serial.SerialException as msg:
            _logger.error(msg)
            self.close()
        return self.socket is not None

    def close(self):
        """Close the underlying socket connection."""
        if self.socket:
            self.socket.close()
        self.socket = None

    def _in_waiting(self):
        """Return _in_waiting."""
        in_waiting = "in_waiting" if hasattr(self.socket, "in_waiting") else "inWaiting"

        if in_waiting == "in_waiting":
            waitingbytes = getattr(self.socket, in_waiting)
        else:
            waitingbytes = getattr(self.socket, in_waiting)()
        return waitingbytes

    def _send(self, request):
        """Send data on the underlying socket.

        If receive buffer still holds some data then flush it.

        Sleep if last send finished less than 3.5 character
        times ago.

        :param request: The encoded request to send
        :return: The number of bytes written
        :raises ConnectionException:
        """
        if not self.socket:
            raise ConnectionException(str(self))
        if request:
            try:
                if waitingbytes := self._in_waiting():
                    result = self.socket.read(waitingbytes)
                    if self.state == ModbusTransactionState.RETRYING:
                        txt = f"Sending available data in recv buffer {hexlify_packets(result)}"
                        _logger.debug(txt)
                        return result
                    if _logger.isEnabledFor(logging.WARNING):
                        txt = f"Cleanup recv buffer before send: {hexlify_packets(result)}"
                        _logger.warning(txt)
            except NotImplementedError:
                pass
            if self.state != ModbusTransactionState.SENDING:
                _logger.debug('New Transaction state "SENDING"')
                self.state = ModbusTransactionState.SENDING
            size = self.socket.write(request)
            return size
        return 0

    def _wait_for_data(self):
        """Wait for data."""
        size = 0
        more_data = False
        if self.timeout is not None and self.timeout:
            condition = partial(
                lambda start, timeout: (time.time() - start) <= timeout,
                timeout=self.timeout,
            )
        else:
            condition = partial(lambda dummy1, dummy2: True, dummy2=None)
        start = time.time()
        while condition(start):
            available = self._in_waiting()
            if (more_data and not available) or (more_data and available == size):
                break
            if available and available != size:
                more_data = True
                size = available
            time.sleep(0.01)
        return size

    def _recv(self, size):
        """Read data from the underlying descriptor.

        :param size: The number of bytes to read
        :return: The bytes read
        :raises ConnectionException:
        """
        if not self.socket:
            raise ConnectionException(
                self.__str__()  # pylint: disable=unnecessary-dunder-call
            )
        if size is None:
            size = self._wait_for_data()
        result = self.socket.read(size)
        return result

    def is_socket_open(self):
        """Check if socket is open."""
        if self.socket:
            if hasattr(self.socket, "is_open"):
                return self.socket.is_open
            return self.socket.isOpen()
        return False

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return f"ModbusSerialClient({self.framer} baud[{self.baudrate}])"

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"framer={self.framer}, timeout={self.timeout}>"
        )
