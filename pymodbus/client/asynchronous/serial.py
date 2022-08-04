"""SERIAL communication."""
import asyncio
import logging

from serial_asyncio import create_serial_connection

from pymodbus.factory import ClientDecoder
from pymodbus.client.async_helper import ModbusClientProtocol
from pymodbus.transaction import ModbusRtuFramer

_logger = logging.getLogger(__name__)


class AsyncModbusSerialClient:  # pylint: disable=too-many-instance-attributes
    """Actual Async Serial Client to be used.

    To use do::
        from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient
    """

    transport = None
    framer = None

    def __init__(
        self,
        port,
        protocol_class=ModbusClientProtocol,
        modbus_decoder=ClientDecoder,
        framer=ModbusRtuFramer,
        timeout=10,
        # Serial setup parameters
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        # Extra parameters for serial_async (experimental)
        **kwargs,
    ):
        """Initialize Asyncio Modbus Serial Client.

        :param port: The serial port to attach to
        :param protocol_class: Protocol used to talk to modbus device.
        :param modbus_decoder: Message decoder.
        :param framer: Modbus framer
        :param timeout: The timeout between serial requests (default 3s)

        :param baudrate: The baud rate to use for the serial device
        :param bytesize: The bytesize of the serial messages
        :param parity: Which kind of parity to use
        :param stopbits: The number of stop bits to use

        :param **kwargs: extra parameters for serial_async (experimental)
        :return: client object
        """
        self.port = port
        self.protocol_class = protocol_class
        self.framer = framer(modbus_decoder())
        self.timeout = timeout

        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
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
        await self.connect()

    async def connect(self):
        """Connect Async client."""
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
        """Notify successful connection."""
        _logger.info("Serial connected.")
        if not self._connected:
            self._connected_event.set()
            self.protocol = protocol
        else:
            _logger.error("Factory protocol connect callback called while connected.")

    def protocol_lost_connection(self, protocol):
        """Notify lost connection."""
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
