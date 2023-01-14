"""Test server asyncio."""
import asyncio
import logging
import ssl
import unittest
from asyncio import CancelledError
from unittest.mock import AsyncMock, Mock, patch

import pytest

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.exceptions import NoSuchSlaveException
from pymodbus.server import (
    StartAsyncTcpServer,
    StartAsyncTlsServer,
    StartAsyncUdpServer,
)


_logger = logging.getLogger()

SERV_IP = "127.0.0.1"
SERV_ADDR = ("127.0.0.1", 0)
TEST_DATA = b"\x01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x01"


class BasicClient(asyncio.BaseProtocol):
    """Basic client."""

    connected = None
    data = None
    dataTo = None
    received_data = None
    done = None
    eof = None
    transport = None
    protocol = None

    def connection_made(self, transport):
        """Get Connection made."""
        _logger.debug("TEST Client connected")
        if BasicClient.connected is not None:
            BasicClient.connected.set_result(True)

        self.transport = transport
        if BasicClient.data is not None:
            _logger.debug("TEST Client write data")
            self.transport.write(BasicClient.data)
        if BasicClient.dataTo is not None:
            _logger.debug("TEST Client sendTo data")
            self.transport.sendto(BasicClient.dataTo)

    def data_received(self, data):
        """Get Data received."""
        _logger.debug("TEST Client data received")
        BasicClient.received_data = data
        if BasicClient.done is not None:
            BasicClient.done.set_result(True)

    def datagram_received(self, data, addr):  # pylint: disable=unused-argument
        """Get Datagram received."""
        _logger.debug("TEST Client datagram received")
        BasicClient.received_data = data
        if BasicClient.done is not None:
            BasicClient.done.set_result(True)
        self.transport.close()

    def connection_lost(self, exc):
        """EOF received."""
        txt = f"TEST Client stream lost: {exc}"
        _logger.debug(txt)
        if BasicClient.eof:
            BasicClient.eof.set_result(True)

    @classmethod
    def clear(cls):
        """Prepare for new round"""
        if BasicClient.transport:
            BasicClient.transport.close()
            BasicClient.transport = None
        BasicClient.data = None
        BasicClient.connected = None
        BasicClient.done = None
        BasicClient.received_data = None
        BasicClient.eof = None
        BasicClient.protocol = None


class AsyncioServerTest(
    unittest.IsolatedAsyncioTestCase
):  # pylint: disable=too-many-public-methods
    """Unittest for the pymodbus.server.asyncio module.

    The scope of this unit test is the life-cycle management of the network
    connections and server objects.

    This unittest suite does not attempt to test any of the underlying protocol details
    """

    def __init__(self, name):
        """Initialize."""
        super().__init__(name)
        self.store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [17] * 100),
            co=ModbusSequentialDataBlock(0, [17] * 100),
            hr=ModbusSequentialDataBlock(0, [17] * 100),
            ir=ModbusSequentialDataBlock(0, [17] * 100),
        )
        self.context = ModbusServerContext(slaves=self.store, single=True)
        self.identity = ModbusDeviceIdentification(
            info_name={"VendorName": "VendorName"}
        )
        self.server = None
        self.task = None
        self.loop = None

    # -----------------------------------------------------------------------#
    #  Setup/TearDown
    # -----------------------------------------------------------------------#
    def setUp(self):
        """Initialize the test environment by setting up a dummy store and context."""

    async def asyncSetUp(self):
        """Initialize the test environment by setting up a dummy store and context."""
        self.loop = asyncio.get_running_loop()

    async def asyncTearDown(self):
        """Clean up the test environment"""
        if self.server is not None:
            await self.server.server_close()
            self.server = None
        if self.task is not None:
            await asyncio.sleep(0.1)
            if not self.task.cancelled():
                self.task.cancel()
                try:
                    await self.task
                except CancelledError:
                    pass
                self.task = None
        self.context = ModbusServerContext(slaves=self.store, single=True)
        BasicClient.clear()

    def tearDown(self):
        """Clean up the test environment."""

    def handle_task(self, result):
        """Handle task exit."""
        try:
            result = result.result()
        except CancelledError:
            pass

    async def start_server(
        self, do_forever=True, do_defer=True, do_tls=False, do_udp=False, do_ident=False
    ):
        """Handle setup and control of tcp server."""
        args = {
            "context": self.context,
            "address": SERV_ADDR,
            "defer_start": do_defer,
        }
        if do_ident:
            args["identity"] = self.identity
        if do_tls:
            self.server = await StartAsyncTlsServer(**args)
        elif do_udp:
            self.server = await StartAsyncUdpServer(**args)
        else:
            self.server = await StartAsyncTcpServer(**args)
        self.assertIsNotNone(self.server)
        if do_forever:
            self.task = asyncio.create_task(self.server.serve_forever())
            self.task.add_done_callback(self.handle_task)
            self.assertFalse(self.task.cancelled())
            await asyncio.wait_for(self.server.serving, timeout=0.1)
            if not do_udp:
                self.assertIsNotNone(self.server.server)
        elif not do_udp:  # pylint: disable=confusing-consecutive-elif
            self.assertIsNone(self.server.server)
        self.assertEqual(self.server.control.Identity.VendorName, "VendorName")
        await asyncio.sleep(0.1)

    async def connect_server(self):
        """Handle connect to server"""
        BasicClient.connected = self.loop.create_future()
        BasicClient.done = self.loop.create_future()
        BasicClient.eof = self.loop.create_future()
        random_port = self.server.server.sockets[0].getsockname()[
            1
        ]  # get the random server port
        BasicClient.transport, BasicClient.protocol = await self.loop.create_connection(
            BasicClient, host="127.0.0.1", port=random_port
        )
        await asyncio.wait_for(BasicClient.connected, timeout=0.1)
        await asyncio.sleep(0.1)

    # -----------------------------------------------------------------------#
    #  Test ModbusConnectedRequestHandler
    # -----------------------------------------------------------------------#

    async def test_async_start_server_no_loop(self):
        """Test that the modbus tcp asyncio server starts correctly"""
        await self.start_server(do_forever=False)

    async def test_async_start_server(self):
        """Test that the modbus tcp asyncio server starts correctly"""
        await self.start_server()

    async def test_async_tcp_server_serve_forever_twice(self):
        """Call on serve_forever() twice should result in a runtime error"""
        await self.start_server()
        with self.assertRaises(RuntimeError):
            await self.server.serve_forever()

    async def test_async_tcp_server_receive_data(self):
        """Test data sent on socket is received by internals - doesn't not process data"""
        BasicClient.data = b"\x01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x19"
        await self.start_server()
        with patch(
            "pymodbus.transaction.ModbusSocketFramer.processIncomingPacket",
            new_callable=Mock,
        ) as process:
            await self.connect_server()
            process.assert_called_once()
            self.assertTrue(process.call_args[1]["data"] == BasicClient.data)

    async def test_async_tcp_server_roundtrip(self):
        """Test sending and receiving data on tcp socket"""
        expected_response = b"\x01\x00\x00\x00\x00\x05\x01\x03\x02\x00\x11"
        BasicClient.data = TEST_DATA  # unit 1, read register
        await self.start_server()
        await self.connect_server()
        await asyncio.wait_for(BasicClient.done, timeout=0.1)
        self.assertEqual(BasicClient.received_data, expected_response)

    async def test_async_tcp_server_connection_lost(self):
        """Test tcp stream interruption"""
        await self.start_server()
        await self.connect_server()
        self.assertEqual(len(self.server.active_connections), 1)

        BasicClient.protocol.transport.close()
        await asyncio.sleep(0.2)  # so we have to wait a bit
        self.assertFalse(self.server.active_connections)

    async def test_async_tcp_server_close_active_connection(self):
        """Test server_close() while there are active TCP connections"""
        await self.start_server()
        await self.connect_server()

        # On Windows we seem to need to give this an extra chance to finish,
        # otherwise there ends up being an active connection at the assert.
        await asyncio.sleep(0.5)
        await self.server.server_close()

    async def test_async_tcp_server_no_slave(self):
        """Test unknown slave unit exception"""
        self.context = ModbusServerContext(
            slaves={0x01: self.store, 0x02: self.store}, single=False
        )
        BasicClient.data = b"\x01\x00\x00\x00\x00\x06\x05\x03\x00\x00\x00\x01"
        await self.start_server()
        await self.connect_server()
        self.assertFalse(BasicClient.eof.done())
        self.server.server_close()
        self.server = None

    async def test_async_tcp_server_modbus_error(self):
        """Test sending garbage data on a TCP socket should drop the connection"""
        BasicClient.data = TEST_DATA
        await self.start_server()
        with patch(
            "pymodbus.register_read_message.ReadHoldingRegistersRequest.execute",
            side_effect=NoSuchSlaveException,
        ):
            await self.connect_server()
            await asyncio.wait_for(BasicClient.done, timeout=0.1)

    # -----------------------------------------------------------------------#
    # Test ModbusTlsProtocol
    # -----------------------------------------------------------------------#
    async def test_async_start_tls_server_no_loop(self):
        """Test that the modbus tls asyncio server starts correctly"""
        with patch.object(ssl.SSLContext, "load_cert_chain"):
            await self.start_server(do_tls=True, do_forever=False, do_ident=True)
            self.assertEqual(self.server.control.Identity.VendorName, "VendorName")
            self.assertIsNotNone(self.server.sslctx)

    async def test_async_start_tls_server(self):
        """Test that the modbus tls asyncio server starts correctly"""
        with patch.object(ssl.SSLContext, "load_cert_chain"):
            await self.start_server(do_tls=True, do_ident=True)
            self.assertEqual(self.server.control.Identity.VendorName, "VendorName")
            self.assertIsNotNone(self.server.sslctx)

    async def test_async_tls_server_serve_forever(self):
        """Test StartAsyncTcpServer serve_forever() method"""
        with patch(
            "asyncio.base_events.Server.serve_forever", new_callable=AsyncMock
        ) as serve:
            with patch.object(ssl.SSLContext, "load_cert_chain"):
                await self.start_server(do_tls=True, do_forever=False)
                await self.server.serve_forever()
                serve.assert_awaited()

    async def test_async_tls_server_serve_forever_twice(self):
        """Call on serve_forever() twice should result in a runtime error"""
        with patch.object(ssl.SSLContext, "load_cert_chain"):
            await self.start_server(do_tls=True)
            with pytest.raises(RuntimeError):
                await self.server.serve_forever()

    # -----------------------------------------------------------------------#
    # Test ModbusUdpProtocol
    # -----------------------------------------------------------------------#

    async def test_async_start_udp_server_no_loop(self):
        """Test that the modbus udp asyncio server starts correctly"""
        await self.start_server(do_udp=True, do_forever=False, do_ident=True)
        self.assertEqual(self.server.control.Identity.VendorName, "VendorName")
        self.assertIsNone(self.server.protocol)

    async def test_async_start_udp_server(self):
        """Test that the modbus udp asyncio server starts correctly"""
        await self.start_server(do_udp=True, do_ident=True)
        self.assertEqual(self.server.control.Identity.VendorName, "VendorName")
        self.assertFalse(self.server.protocol is None)

    async def test_async_udp_server_serve_forever_start(self):
        """Test StartAsyncUdpServer serve_forever() method"""
        with patch(
            "asyncio.base_events.Server.serve_forever", new_callable=AsyncMock
        ) as serve:
            await self.start_server(do_forever=False, do_ident=True)
            await self.server.serve_forever()
            serve.assert_awaited()

    async def test_async_udp_server_serve_forever_close(self):
        """Test StarAsyncUdpServer serve_forever() method"""
        await self.start_server(do_udp=True)
        self.assertTrue(asyncio.isfuture(self.server.on_connection_terminated))
        self.assertFalse(self.server.on_connection_terminated.done())

        await self.server.server_close()
        # TBD self.assertTrue(self.server.protocol.is_closing())
        self.server = None

    async def test_async_udp_server_serve_forever_twice(self):
        """Call on serve_forever() twice should result in a runtime error"""
        await self.start_server(do_udp=True, do_ident=True)
        with self.assertRaises(RuntimeError):
            await self.server.serve_forever()

    @pytest.mark.skipif(pytest.IS_WINDOWS, reason="Windows have a timeout problem.")
    async def test_async_udp_server_receive_data(self):
        """Test that the sending data on datagram socket gets data pushed to framer"""
        await self.start_server(do_udp=True)
        with patch(
            "pymodbus.transaction.ModbusSocketFramer.processIncomingPacket",
            new_callable=Mock,
        ) as process:
            self.server.endpoint.datagram_received(data=b"12345", addr=(SERV_IP, 12345))
            await asyncio.sleep(0.1)
            process.seal()
            process.assert_called_once()
            self.assertTrue(process.call_args[1]["data"] == b"12345")

    async def test_async_udp_server_send_data(self):
        """Test that the modbus udp asyncio server correctly sends data outbound"""
        BasicClient.dataTo = b"x\01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x19"
        await self.start_server(do_udp=True)
        random_port = self.server.protocol._sock.getsockname()[  # pylint: disable=protected-access
            1
        ]
        received = self.server.endpoint.datagram_received = Mock(
            wraps=self.server.endpoint.datagram_received
        )
        await self.loop.create_datagram_endpoint(
            BasicClient, remote_addr=("127.0.0.1", random_port)
        )
        await asyncio.sleep(0.1)
        received.assert_called_once()
        self.assertEqual(received.call_args[0][0], BasicClient.dataTo)
        await self.server.server_close()
        self.server = None

    async def test_async_udp_server_roundtrip(self):
        """Test sending and receiving data on udp socket"""
        expected_response = b"\x01\x00\x00\x00\x00\x05\x01\x03\x02\x00\x11"  # value of 17 as per context
        BasicClient.dataTo = TEST_DATA  # unit 1, read register
        BasicClient.done = self.loop.create_future()
        await self.start_server(do_udp=True)
        random_port = self.server.protocol._sock.getsockname()[  # pylint: disable=protected-access
            1
        ]
        transport, _ = await self.loop.create_datagram_endpoint(
            BasicClient, remote_addr=("127.0.0.1", random_port)
        )
        await asyncio.wait_for(BasicClient.done, timeout=0.1)
        self.assertEqual(BasicClient.received_data, expected_response)
        transport.close()

    async def test_async_udp_server_exception(self):
        """Test sending garbage data on a TCP socket should drop the connection"""
        BasicClient.dataTo = b"\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
        BasicClient.connected = self.loop.create_future()
        BasicClient.done = self.loop.create_future()
        await self.start_server(do_udp=True)
        with patch(
            "pymodbus.transaction.ModbusSocketFramer.processIncomingPacket",
            new_callable=lambda: Mock(side_effect=Exception),
        ):
            # get the random server port pylint: disable=protected-access
            random_port = self.server.protocol._sock.getsockname()[1]
            _, _ = await self.loop.create_datagram_endpoint(
                BasicClient, remote_addr=("127.0.0.1", random_port)
            )
            await asyncio.wait_for(BasicClient.connected, timeout=0.1)
            self.assertFalse(BasicClient.done.done())
            self.assertFalse(
                self.server.protocol._sock._closed  # pylint: disable=protected-access
            )

    async def test_async_tcp_server_exception(self):
        """Send garbage data on a TCP socket should drop the connection"""
        BasicClient.data = b"\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
        await self.start_server()
        with patch(
            "pymodbus.transaction.ModbusSocketFramer.processIncomingPacket",
            new_callable=lambda: Mock(side_effect=Exception),
        ):
            await self.connect_server()
            await asyncio.wait_for(BasicClient.eof, timeout=0.1)
            # neither of these should timeout if the test is successful
