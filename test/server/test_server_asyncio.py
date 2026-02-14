"""Test server asyncio."""
import asyncio
import logging
import ssl
from asyncio import CancelledError, Task
from contextlib import suppress
from unittest import mock

import pytest

from pymodbus import FramerType, ModbusDeviceIdentification
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.exceptions import NoSuchIdException
from pymodbus.server import (
    ModbusSerialServer,
    ModbusTcpServer,
    ModbusTlsServer,
    ModbusUdpServer,
    ModbusBaseServer,
)


_logger = logging.getLogger()

SERV_IP = "127.0.0.1"
SERV_ADDR = ("127.0.0.1", 0)
TEST_DATA = b"\x01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x01"


class BasicClient(asyncio.BaseProtocol):
    """Basic client."""

    connected: asyncio.Future
    data: bytes
    dataTo: bytes
    received_data: bytes
    done: asyncio.Future
    eof: asyncio.Future
    transport: asyncio.BaseTransport | None = None
    protocol: asyncio.BaseProtocol | None = None

    def connection_made(self, transport):
        """Get Connection made."""
        _logger.debug("TEST Client connected")
        if BasicClient.connected is not None:
            BasicClient.connected.set_result(True)

        self.transport = transport
        if BasicClient.data is not None:
            _logger.debug("TEST Client write data")
            self.transport.write(BasicClient.data)  # type: ignore[union-attr]
        if BasicClient.dataTo is not None:
            _logger.debug("TEST Client sendTo data")
            self.transport.sendto(BasicClient.dataTo)  # type: ignore[union-attr]

    def data_received(self, data):
        """Get Data received."""
        _logger.debug("TEST Client data received")
        BasicClient.received_data = data
        if BasicClient.done is not None:  # pragma: no cover
            BasicClient.done.set_result(True)

    def datagram_received(self, data, _addr):
        """Get Datagram received."""
        _logger.debug("TEST Client datagram received")
        BasicClient.received_data = data
        if BasicClient.done is not None:  # pragma: no cover
            BasicClient.done.set_result(True)
        self.transport.close()  # type: ignore[union-attr]

    def connection_lost(self, exc):
        """EOF received."""
        txt = f"TEST Client stream lost: {exc}"
        _logger.debug(txt)
        if BasicClient.eof:
            BasicClient.eof.set_result(True)

    def eof_received(self):
        """Accept other end terminates connection."""

    @classmethod
    def clear(cls):
        """Prepare for new round."""
        if BasicClient.transport:
            BasicClient.transport.close()
            BasicClient.transport = None
        BasicClient.data = None  # type: ignore[assignment]
        BasicClient.connected = None # type: ignore[assignment]
        BasicClient.done = None # type: ignore[assignment]
        BasicClient.received_data = None # type: ignore[assignment]
        BasicClient.eof = None # type: ignore[assignment]
        BasicClient.my_protocol = None  # type: ignore[attr-defined]


class TestAsyncioServer:
    """Unittest for the pymodbus.server.asyncio module.

    The scope of this test is the life-cycle management of the network
    connections and server objects.

    This test suite does not attempt to test any of the underlying protocol details
    """

    server: ModbusBaseServer | None = None
    task: Task | None = None
    loop: asyncio.AbstractEventLoop | None = None
    store: ModbusDeviceContext | None = None
    context: ModbusServerContext | None = None
    identity: ModbusDeviceIdentification | None = None

    @pytest.fixture(autouse=True)
    async def _setup_teardown(self):
        """Initialize the test environment by setting up a dummy store and context."""
        self.loop = asyncio.get_running_loop()
        self.store = ModbusDeviceContext(
            di=ModbusSequentialDataBlock(0, [17] * 100),
            co=ModbusSequentialDataBlock(0, [17] * 100),
            hr=ModbusSequentialDataBlock(0, [17] * 100),
            ir=ModbusSequentialDataBlock(0, [17] * 100),
        )
        self.context = ModbusServerContext(devices=self.store, single=True)
        self.identity = ModbusDeviceIdentification(
            info_name={"VendorName": "VendorName"}
        )
        yield

        # teardown
        if self.server is not None:
            await self.server.shutdown()
            self.server = None
        if self.task is not None:
            await asyncio.sleep(0.1)
            if not self.task.cancelled():  # pragma: no cover
                self.task.cancel()
                with suppress(CancelledError):
                    await self.task
                self.task = None
        BasicClient.clear()
        await asyncio.sleep(0.1)

    def handle_task(self, result):
        """Handle task exit."""
        with suppress(CancelledError):
            result = result.result()

    async def start_server(
        self, do_forever=True, do_serial=False, do_tls=False, do_udp=False, do_ident=False, serv_addr=SERV_ADDR,
    ):
        """Handle setup and control of tcp server."""
        args = {
            "context": self.context,
            "address": SERV_ADDR,
        }
        if do_ident:
            args["identity"] = self.identity
        if do_tls:
            self.server = ModbusTlsServer(
                self.context,
                framer=FramerType.TLS,
                identity=self.identity,
                address=serv_addr
            )
        elif do_udp:
            self.server = ModbusUdpServer(
                self.context,
                framer=FramerType.SOCKET,
                identity=self.identity,
                address=serv_addr
            )
        elif do_serial:
            self.server = ModbusSerialServer(
                self.context,
                framer=FramerType.RTU,
                identity=self.identity,
                port="/dev/ttyb",
                baudrate=19200,
                allow_multiple_devices=True
            )
        else:
            self.server = ModbusTcpServer(
                self.context,
                framer=FramerType.SOCKET,
                identity=self.identity,
                address=serv_addr
            )
        assert self.server
        if do_forever:
            self.task = asyncio.create_task(self.server.serve_forever())
            self.task.set_name("Run server")
            self.task.add_done_callback(self.handle_task)
            assert not self.task.cancelled()
            await asyncio.sleep(0.5)
            # TO BE FIXED await asyncio.wait_for(self.server.serving, timeout=0.1)
            if not do_udp:
                assert self.server.transport
        elif not do_udp:  # pylint: disable=confusing-consecutive-elif
            assert not self.server.transport
        assert self.server.control.Identity.VendorName == "VendorName"
        await asyncio.sleep(0.1)

    async def connect_server(self):
        """Handle connect to server."""
        BasicClient.connected = asyncio.Future()
        BasicClient.done = asyncio.Future()
        BasicClient.eof = asyncio.Future()
        random_port = self.server.transport.sockets[0].getsockname()[  # type: ignore[union-attr]
            1
        ]  # get the random server port
        (
            BasicClient.transport,
            BasicClient.my_protocol,
        ) = await self.loop.create_connection(  # type: ignore[union-attr]
            BasicClient, host="127.0.0.1", port=random_port
        )
        await asyncio.wait_for(BasicClient.connected, timeout=0.1)
        await asyncio.sleep(0.1)

    async def test_async_start_server_no_loop(self):
        """Test that the modbus tcp asyncio server starts correctly."""
        await self.start_server(do_forever=False)

    async def test_async_start_server(self):
        """Test that the modbus tcp asyncio server starts correctly."""
        await self.start_server()

    async def test_async_tcp_server_serve_forever_twice(self):
        """Call on serve_forever() twice should result in a runtime error."""
        await self.start_server()
        with pytest.raises(RuntimeError):
            await self.server.serve_forever()  # type: ignore[union-attr]

    async def test_async_tcp_server_receive_data(self):
        """Test data sent on socket is received by internals - doesn't not process data."""
        BasicClient.data = b"\x01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x19"
        await self.start_server()
        with mock.patch(
            "pymodbus.framer.FramerSocket.handleFrame",
            new_callable=mock.Mock,
        ) as process:
            await self.connect_server()
            process.assert_called_once()
            assert process.call_args[0][0] == BasicClient.data

    async def test_async_tcp_server_roundtrip(self):
        """Test sending and receiving data on tcp socket."""
        expected_response = b"\x01\x00\x00\x00\x00\x05\x01\x03\x02\x00\x11"
        BasicClient.data = TEST_DATA  # device 1, read register
        await self.start_server()
        await self.connect_server()
        await asyncio.wait_for(BasicClient.done, timeout=0.1)
        assert BasicClient.received_data, expected_response

    async def test_async_server_trace_connect_disconnect(self):
        """Test connect/disconnect trace handler."""
        trace_connect = mock.Mock()
        await self.start_server()
        self.server.trace_connect = trace_connect  # type: ignore[union-attr]
        await self.connect_server()
        trace_connect.assert_called_once_with(True)
        trace_connect.reset_mock()

        BasicClient.transport.close()  # type: ignore[union-attr]
        await asyncio.sleep(0.2)  # so we have to wait a bit
        trace_connect.assert_called_once_with(False)

    async def test_async_tcp_server_connection_lost(self):
        """Test tcp stream interruption."""
        await self.start_server()
        await self.connect_server()

        BasicClient.transport.close()  # type: ignore[union-attr]
        await asyncio.sleep(0.2)  # so we have to wait a bit

    async def test_async_tcp_server_shutdown_connection(self):
        """Test server shutdown() while there are active TCP connections."""
        await self.start_server()
        await self.connect_server()

        # On Windows we seem to need to give this an extra chance to finish,
        # otherwise there ends up being an active connection at the assert.
        await asyncio.sleep(0.5)
        await self.server.shutdown()  # type: ignore[union-attr]

    async def test_async_tcp_server_no_device(self):
        """Test unknown device exception."""
        self.context = ModbusServerContext(
            devices={0x01: self.store, 0x02: self.store}, single=False
        )
        BasicClient.data = b"\x01\x00\x00\x00\x00\x06\x05\x03\x00\x00\x00\x01"
        await self.start_server()
        await self.connect_server()
        assert not BasicClient.eof.done()
        await self.server.shutdown()  # type: ignore[union-attr]
        self.server = None

    async def test_async_tcp_server_modbus_error(self):
        """Test sending garbage data on a TCP socket should drop the connection."""
        BasicClient.data = TEST_DATA
        await self.start_server()
        with mock.patch(
            "pymodbus.pdu.register_message.ReadHoldingRegistersRequest.datastore_update",
            side_effect=NoSuchIdException,
        ):
            await self.connect_server()
            await asyncio.wait_for(BasicClient.done, timeout=0.1)

    # -----------------------------------------------------------------------#
    # Test ModbusTlsProtocol
    # -----------------------------------------------------------------------#
    async def test_async_start_tls_server_no_loop(self):
        """Test that the modbus tls asyncio server starts correctly."""
        with mock.patch.object(ssl.SSLContext, "load_cert_chain"):
            await self.start_server(do_tls=True, do_forever=False, do_ident=True)
            assert self.server.control.Identity.VendorName == "VendorName"  # type: ignore[union-attr]

    async def test_async_start_tls_server(self):
        """Test that the modbus tls asyncio server starts correctly."""
        with mock.patch.object(ssl.SSLContext, "load_cert_chain"):
            await self.start_server(do_tls=True, do_ident=True)
            assert self.server.control.Identity.VendorName == "VendorName"  # type: ignore[union-attr]

    async def test_async_tls_server_serve_forever_twice(self):
        """Call on serve_forever() twice should result in a runtime error."""
        with mock.patch.object(ssl.SSLContext, "load_cert_chain"):
            await self.start_server(do_tls=True)
            with pytest.raises(RuntimeError):
                await self.server.serve_forever()  # type: ignore[union-attr]

    async def test_async_start_udp_server_no_loop(self):
        """Test that the modbus udp asyncio server starts correctly."""
        await self.start_server(do_udp=True, do_forever=False, do_ident=True)
        assert self.server.control.Identity.VendorName == "VendorName"  # type: ignore[union-attr]
        assert not self.server.transport  # type: ignore[union-attr]

    async def test_async_start_udp_server(self):
        """Test that the modbus udp asyncio server starts correctly."""
        await self.start_server(do_udp=True, do_ident=True)
        assert self.server.control.Identity.VendorName == "VendorName"  # type: ignore[union-attr]
        assert self.server.transport  # type: ignore[union-attr]

    async def test_async_udp_server_serve_forever_close(self):
        """Test StarAsyncUdpServer serve_forever() method."""
        await self.start_server(do_udp=True)
        await self.server.shutdown()  # type: ignore[union-attr]
        self.server = None

    async def test_async_udp_server_serve_forever_twice(self):
        """Call on serve_forever() twice should result in a runtime error."""
        await self.start_server(do_udp=True, do_ident=True)
        with pytest.raises(RuntimeError):
            await self.server.serve_forever()  # type: ignore[union-attr]

    async def test_async_udp_server_roundtrip(self):
        """Test sending and receiving data on udp socket."""
        expected_response = (
            b"\x01\x00\x00\x00\x00\x05\x01\x03\x02\x00\x11"
        )  # value of 17 as per context
        BasicClient.dataTo = TEST_DATA  # device 1, read register
        BasicClient.done = asyncio.Future()
        await self.start_server(do_udp=True)
        random_port = self.server.transport._sock.getsockname()[1]    # type: ignore[union-attr] # pylint: disable=protected-access
        transport, _ = await self.loop.create_datagram_endpoint(  # type: ignore[union-attr]
            BasicClient, remote_addr=("127.0.0.1", random_port)
        )
        await asyncio.wait_for(BasicClient.done, timeout=0.1)
        assert BasicClient.received_data == expected_response
        transport.close()

    async def test_async_udp_server_exception(self):
        """Test sending garbage data on a TCP socket should drop the connection."""
        BasicClient.dataTo = b"\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
        BasicClient.connected = asyncio.Future()
        BasicClient.done = asyncio.Future()
        await self.start_server(do_udp=True)
        with mock.patch(
            "pymodbus.framer.FramerSocket.handleFrame",
            new_callable=lambda: mock.Mock(side_effect=Exception),
        ):
            # get the random server port pylint: disable=protected-access
            random_port = self.server.transport._sock.getsockname()[1]  # type: ignore[union-attr]
            _, _ = await self.loop.create_datagram_endpoint(  # type: ignore[union-attr]
                BasicClient, remote_addr=("127.0.0.1", random_port)
            )
            await asyncio.wait_for(BasicClient.connected, timeout=0.1)
            assert not BasicClient.done.done()

    async def test_async_serial_server_multipoint(self):
        """Check instantiate serial server."""
        await self.start_server(do_forever=False, do_serial=True)


    async def test_serial_server_multipoint_baudrate(self):
        """Test __init__."""
        store = ModbusDeviceContext(
            di=ModbusSequentialDataBlock(0, [17] * 100),
            co=ModbusSequentialDataBlock(0, [17] * 100),
            hr=ModbusSequentialDataBlock(0, [17] * 100),
            ir=ModbusSequentialDataBlock(0, [17] * 100),
        )
        with pytest.raises(TypeError):
            ModbusSerialServer(
                ModbusServerContext(devices=store, single=True),
                framer=FramerType.RTU,
                baudrate=64200,
                port="/dev/tty01",
                allow_multiple_devices=True,
            )


    async def test_serial_server_multipoint_framer(self):
        """Test __init__."""
        store = ModbusDeviceContext(
            di=ModbusSequentialDataBlock(0, [17] * 100),
            co=ModbusSequentialDataBlock(0, [17] * 100),
            hr=ModbusSequentialDataBlock(0, [17] * 100),
            ir=ModbusSequentialDataBlock(0, [17] * 100),
        )
        with pytest.raises(TypeError):
            ModbusSerialServer(
                ModbusServerContext(devices=store, single=True),
                framer=FramerType.ASCII,
                baudrate=19200,
                port="/dev/tty01",
                allow_multiple_devices=True,
            )
