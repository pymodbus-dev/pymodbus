"""Modbus client async serial communication."""
import asyncio
import logging

from serial_asyncio import create_serial_connection

from pymodbus.framer import ModbusFramer
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.client.base import ModbusBaseClient, ModbusClientProtocol
from pymodbus.constants import Defaults

_logger = logging.getLogger(__name__)


class AsyncModbusSerialClient(ModbusBaseClient):
    """**AsyncModbusSerialClient**.

    :param port: Serial port used for communication.
    :param framer: (optional) Framer class.
    :param baudrate: (optional) Bits pr second.
    :param bytesize: (optional) Number of bits pr byte 7-8.
    :param parity: (optional) 'E'ven, 'O'dd or 'N'one
    :param stopbits: (optional) Number of stop bits 0-2¡.
    :param handle_local_echo: (optional) Discard local echo from dongle.
    :param kwargs: (optional) Experimental parameters

    The serial communication is RS-485 based, and usually used vith a usb RS485 dongle.

    Example::

        from pymodbus.client import AsyncModbusSerialClient

        async def run():
            client = AsyncModbusSerialClient("dev/serial0")

            await client.connect()
            ...
            await client.close()
    """

    transport = None
    framer = None

    def __init__(
        self,
        port: str,
        framer: ModbusFramer = ModbusRtuFramer,
        baudrate: int = Defaults.Baudrate,
        bytesize: int = Defaults.Bytesize,
        parity: chr = Defaults.Parity,
        stopbits: int = Defaults.Stopbits,
        handle_local_echo: bool = Defaults.HandleLocalEcho,
        **kwargs: any,
    ) -> None:
        """Initialize Asyncio Modbus Serial Client."""
        super().__init__(framer=framer, **kwargs)
        self.params.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.handle_local_echo = handle_local_echo
        self.loop = None
        self.protocol = None
        self._connected_event = asyncio.Event()

    async def close(self):  # pylint: disable=invalid-overridden-method
        """Stop connection."""
        if self.connected and self.protocol and self.protocol.transport:
            self.protocol.transport.close()

    def _create_protocol(self):
        """Create protocol."""
        protocol = ModbusClientProtocol(framer=self.framer)
        protocol.factory = self
        return protocol

    @property
    def connected(self):
        """Connect internal."""
        return self._connected_event.is_set()

    async def connect(self):  # pylint: disable=invalid-overridden-method
        """Connect Async client."""
        # get current loop, if there are no loop a RuntimeError will be raised
        self.loop = asyncio.get_running_loop()

        _logger.debug("Starting serial connection")
        try:
            await create_serial_connection(
                self.loop,
                self._create_protocol,
                self.params.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                stopbits=self.stopbits,
                parity=self.parity,
                **self.params.kwargs,
            )
            await self._connected_event.wait()
            txt = f"Connected to {self.params.port}"
            _logger.info(txt)
        except Exception as exc:  # pylint: disable=broad-except
            txt = f"Failed to connect: {exc}"
            _logger.warning(txt)

    def protocol_made_connection(self, protocol):
        """Notify successful connection."""
        _logger.info("Serial connected.")
        if not self.connected:
            self._connected_event.set()
            self.protocol = protocol
        else:
            _logger.error("Factory protocol connect callback called while connected.")

    def protocol_lost_connection(self, protocol):
        """Notify lost connection."""
        if self.connected:
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
