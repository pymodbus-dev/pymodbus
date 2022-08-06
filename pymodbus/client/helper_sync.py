"""Modbus Client Common.

This is a common client mixin that can be used by
both the synchronous and asynchronous clients to
simplify the interface.
"""
# pylint: disable=missing-type-doc
import sys
import logging

from pymodbus.bit_read_message import ReadCoilsRequest, ReadDiscreteInputsRequest
from pymodbus.bit_write_message import WriteMultipleCoilsRequest, WriteSingleCoilRequest
from pymodbus.register_read_message import (
    ReadHoldingRegistersRequest,
    ReadInputRegistersRequest,
    ReadWriteMultipleRegistersRequest,
)
from pymodbus.register_write_message import (
    MaskWriteRegisterRequest,
    WriteMultipleRegistersRequest,
    WriteSingleRegisterRequest,
)
from pymodbus.exceptions import (
    ConnectionException,
    NotImplementedException,
)
from pymodbus.utilities import ModbusTransactionState, hexlify_packets
from pymodbus.transaction import DictTransactionManager
from pymodbus.constants import Defaults

_logger = logging.getLogger(__name__)


class ModbusClientMixin:
    """Modbus client mixin that provides additional factory methods.

    for all the current modbus methods. This can be used
    instead of the normal pattern of::

       # instead of this
       client = ModbusClient(...)
       request = ReadCoilsRequest(1,10)
       response = client.execute(request)

       # now like this
       client = ModbusClient(...)
       response = client.read_coils(1, 10)
    """

    state = ModbusTransactionState.IDLE
    last_frame_end = 0
    silent_interval = 0

    def read_coils(self, address, count=1, **kwargs):
        """Read coils.

        :param address: The starting address to read from
        :param count: The number of coils to read
        :param kwargs:
        :returns: A deferred response handle
        """
        request = ReadCoilsRequest(address, count, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def read_discrete_inputs(self, address, count=1, **kwargs):
        """Read discrete inputs.

        :param address: The starting address to read from
        :param count: The number of discretes to read
        :param kwargs:
        :returns: A deferred response handle
        """
        request = ReadDiscreteInputsRequest(address, count, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def write_coil(self, address, value, **kwargs):
        """Write_coil.

        :param address: The starting address to write to
        :param value: The value to write to the specified address
        :param kwargs:
        :returns: A deferred response handle
        """
        request = WriteSingleCoilRequest(address, value, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def write_coils(self, address, values, **kwargs):
        """Write coils.

        :param address: The starting address to write to
        :param values: The values to write to the specified address
        :param kwargs:
        :returns: A deferred response handle
        """
        request = WriteMultipleCoilsRequest(address, values, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def write_register(self, address, value, **kwargs):
        """Write register.

        :param address: The starting address to write to
        :param value: The value to write to the specified address
        :param kwargs:
        :returns: A deferred response handle
        """
        request = WriteSingleRegisterRequest(address, value, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def write_registers(self, address, values, **kwargs):
        """Write registers.

        :param address: The starting address to write to
        :param values: The values to write to the specified address
        :param kwargs:
        :returns: A deferred response handle
        """
        request = WriteMultipleRegistersRequest(address, values, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def read_holding_registers(self, address, count=1, **kwargs):
        """Read holding registers.

        :param address: The starting address to read from
        :param count: The number of registers to read
        :param kwargs:
        :returns: A deferred response handle
        """
        request = ReadHoldingRegistersRequest(address, count, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def read_input_registers(self, address, count=1, **kwargs):
        """Read input registers.

        :param address: The starting address to read from
        :param count: The number of registers to read
        :param kwargs:
        :returns: A deferred response handle
        """
        request = ReadInputRegistersRequest(address, count, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def readwrite_registers(self, *args, **kwargs):
        """Read/Write registers

        :param args:
        :param kwargs:
        :returns: A deferred response handle
        """
        request = ReadWriteMultipleRegistersRequest(*args, **kwargs)
        return self.execute(request)  # pylint: disable=no-member

    def mask_write_register(self, *args, **kwargs):
        """Mask write register.

        :args:
        :returns: A deferred response handle
        """
        request = MaskWriteRegisterRequest(*args, **kwargs)
        return self.execute(request)  # pylint: disable=no-member


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
