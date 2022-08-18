"""**Modbus client async serial communication.**

The serial communication is RS-485 based, and usually used vith a usb RS485 dongle.

Example::

    from pymodbus.client import AsyncModbusSerialClient

    async def run():
        client = AsyncModbusSerialClient(
            "dev/pty0",  # serial port
            # Common optional paramers:
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

        await client.connect()
        ...
        await client.close()
"""
import asyncio
import logging

from serial_asyncio import create_serial_connection

from pymodbus.client.base import ModbusClientProtocol
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.client.base import ModbusBaseClient

_logger = logging.getLogger(__name__)


class AsyncModbusSerialClient(ModbusBaseClient):
    r"""Modbus client for async serial (RS-485) communication.

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

    transport = None
    framer = None

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
        if self._connected and self.protocol and self.protocol.transport:
            self.protocol.transport.close()

    def _create_protocol(self):
        """Create protocol."""
        protocol = ModbusClientProtocol(framer=self.framer)
        protocol.factory = self
        return protocol

    @property
    def _connected(self):
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
