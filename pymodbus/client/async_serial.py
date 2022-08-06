"""Modbus client async serial communication.

The serial communication is RS-485 based, and usually used vith a usb rs-485 dongle.

Example::

    from pymodbus.client import AsyncModbusSerialClient

    async def run():
        client = AsyncModbusSerialClient(
            "dev/pty0",  # serial port
            # Common optional paramers:
            #    protocol_class=ModbusClientProtocol,
            #    modbus_decoder=ClientDecoder,
            #    framer=ModbusRtuFramer,
            #    timeout=10,
            #    retries=3,
            #    retry_on_empty=False,
            #    close_comm_on_error=False,
            #    strict=True,
            # Serial setup parameters
            #    baudrate=9600,
            #    bytesize=8,
            #    parity="N",
            #    stopbits=1,
            #    handle_local_echo=False,
        )

        await client.start()
        ...
        await client.stop()
"""
import asyncio
import logging

from serial_asyncio import create_serial_connection

from pymodbus.factory import ClientDecoder
from pymodbus.client.helper_async import ModbusClientProtocol
from pymodbus.transaction import ModbusRtuFramer

_logger = logging.getLogger(__name__)


class AsyncModbusSerialClient:  # pylint: disable=too-many-instance-attributes
    r"""Modbus client for async serial (RS-485) communication.

    :param port: (positional) Serial port used for communication.
    :param protocol_class: (optional, default ModbusClientProtocol) Protocol communication class.
    :param modbus_decoder: (optional, default ClientDecoder) Message decoder class.
    :param framer: (optional, default ModbusRtuFramer) Framer class.
    :param timeout: (optional, default 3s) Timeout for a request.
    :param retries: (optional, default 3) Max number of retries pr request.
    :param retry_on_empty: (optional, default false) Retry on empty response.
    :param close_comm_on_error: (optional, default true) Close connection on error.
    :param strict: (optional, default true) Strict timing, 1.5 character between requests.
    :param baudrate: (optional, default 9600) Bits pr second.
    :param bytesize: (optional, default 8) Number of bits pr byte 7-8.
    :param parity: (optional, default None).
    :param stopbits: (optional, default 1) Number of stop bits 0-2 to use.
    :param handle_local_echo: (optional, default false) Handle local echo of the USB-to-RS485 dongle.
    :param \*\*kwargs: (optional) Extra experimental parameters for transport
    :return: client object
    """

    transport = None
    framer = None

    def __init__(  # pylint: disable=too-many-arguments
        # Positional parameters
        self,
        port,
        # Common optional paramers:
        protocol_class=ModbusClientProtocol,
        modbus_decoder=ClientDecoder,
        framer=ModbusRtuFramer,
        timeout=10,
        retries=3,
        retry_on_empty=False,
        close_comm_on_error=False,
        strict=True,

        # Serial setup parameters
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        handle_local_echo=False,

        # Extra parameters for serial_async (experimental)
        **kwargs,
    ):
        """Initialize Asyncio Modbus Serial Client."""
        self.port = port
        self.protocol_class = protocol_class
        self.framer = framer(modbus_decoder())
        self.timeout = timeout
        self.retries = retries
        self.retry_on_empty = retry_on_empty
        self.close_comm_on_error = close_comm_on_error
        self.strict = strict

        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.handle_local_echo = handle_local_echo

        self.kwargs = kwargs

        self.loop = None
        self.protocol = None
        self._connected_event = asyncio.Event()

    def stop(self):
        """Stop connection."""
        if self._connected and self.protocol and self.protocol.transport:
            self.protocol.transport.close()

    def _create_protocol(self):
        """Create protocol."""
        protocol = self.protocol_class(framer=self.framer)
        protocol.factory = self
        return protocol

    @property
    def _connected(self):
        """Connect internal."""
        return self._connected_event.is_set()

    async def start(self):
        """Connect Async client."""
        # get current loop, if there are no loop a RuntimeError will be raised
        self.loop = asyncio.get_running_loop()

        _logger.debug("Starting serial connection")
        try:
            await create_serial_connection(
                self.loop,
                self._create_protocol,
                self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                stopbits=self.stopbits,
                parity=self.parity,
                **self.kwargs,
            )
            await self._connected_event.wait()
            txt = f"Connected to {self.port}"
            _logger.info(txt)
        except Exception as exc:  # pylint: disable=broad-except
            txt = f"Failed to connect: {exc}"
            _logger.warning(txt)

    def protocol_made_connection(self, protocol):
        """Notify successful connection.

        :meta private:
        """
        _logger.info("Serial connected.")
        if not self._connected:
            self._connected_event.set()
            self.protocol = protocol
        else:
            _logger.error("Factory protocol connect callback called while connected.")

    def protocol_lost_connection(self, protocol):
        """Notify lost connection.

        :meta private:
        """
        if self._connected:
            _logger.info("Serial lost connection.")
            if protocol is not self.protocol:
                _logger.error(
                    "Serial: protocol is not self.protocol."
                )

            self._connected_event.clear()
            self.protocol = None
            # if self.host:
            #     asyncio.asynchronous(self._reconnect())
        else:
            _logger.error("Serial, lost_connection but not connected.")
