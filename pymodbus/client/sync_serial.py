"""**Modbus client serial communication.**

The serial communication is RS-485 based, and usually used vith a usb RS485 dongle.

Example::

    from pymodbus.client import ModbusSerialClient

    def run():
        client = ModbusSerialClient(
            port="/dev/pty0",  # serial port
            # Common optional paramers:
            #    modbus_decoder=ClientDecoder,
            #    framer=ModbusRtuFramer,
            #    timeout=10,
            #    retries=3,
            #    retry_on_empty=False,
            #    close_comm_on_error=False,.
            #    strict=True,
            # Serial setup parameters
            #    baudrate=9600,
            #    bytesize=8,
            #    parity="N",
            #    stopbits=1,
            #    handle_local_echo=False,
        )

        client.start()
        ...
        client.stop()
"""
from functools import partial
import logging
import time

import serial

from pymodbus.client.base import ModbusBaseClient
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.utilities import ModbusTransactionState, hexlify_packets

_logger = logging.getLogger(__name__)


class ModbusSerialClient(
    ModbusBaseClient
):  # pylint: disable=too-many-instance-attributes
    r"""Modbus client for serial (RS-485) communication.

    :param port: (positional) Serial port used for communication.
    :param framer: (optional, default ModbusRtuFramer) Framer class.
    :param baudrate: (optional, default 9600) Bits pr second.
    :param bytesize: (optional, default 8) Number of bits pr byte 7-8.
    :param parity: (optional, default None).
    :param stopbits: (optional, default 1) Number of stop bits 0-2 to use.
    :param handle_local_echo: (optional, default false) Handle local echo of the USB-to-RS485 dongle.
    :param \*\*kwargs: (optional) Extra experimental parameters for transport
    :return: client object
    """

    state = ModbusTransactionState.IDLE
    inter_char_timeout = 0
    silent_interval = 0

    def __init__(
        self,
        port,
        framer=ModbusRtuFramer,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        handle_local_echo=False,
        **kwargs,
    ):
        """Initialize Modbus Serial Client."""
        self.host = None
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.handle_local_echo = handle_local_echo
        super().__init__(framer=framer, **kwargs)
        self.socket = None

        self.last_frame_end = None
        if isinstance(self.framer, ModbusRtuFramer):
            if self.baudrate > 19200:
                self.silent_interval = 1.75 / 1000  # ms
            else:
                self._t0 = float((1 + 8 + 2)) / self.baudrate
                self.inter_char_timeout = 1.5 * self._t0
                self.silent_interval = 3.5 * self._t0
            self.silent_interval = round(self.silent_interval, 6)

    def start(self):
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
                if self.strict:
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

    def _send(self, request):  # pylint: disable=missing-type-doc
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

    def _recv(self, size):  # pylint: disable=missing-type-doc
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
