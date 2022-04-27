#!/usr/bin/env python3
""" Test server asyncio. """
import logging
import asyncio
import time
import ssl
import pytest
import asynctest
from asynctest.mock import patch, Mock

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server.async_io import (
    StartTcpServer,
    StartTlsServer,
    StartUdpServer,
    StopServer,
    ModbusServerFactory,
)
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.exceptions import NoSuchSlaveException

# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#
_logger = logging.getLogger()


class AsyncioServerTest(asynctest.TestCase): # pylint: disable=too-many-public-methods
    """ Unittest for the pymodbus.server.asyncio module.

    The scope of this unit test is the life-cycle management of the network
    connections and server objects.

    This unittest suite does not attempt to test any of the underlying protocol details
    """

    # -----------------------------------------------------------------------#
    # Setup/TearDown
    # -----------------------------------------------------------------------#
    def setUp(self):
        """ Initialize the test environment by setting up a dummy store and context. """
        self.store = ModbusSlaveContext(di=ModbusSequentialDataBlock(0, [17] * 100),
                                        co=ModbusSequentialDataBlock(0, [17] * 100),
                                        hr=ModbusSequentialDataBlock(0, [17] * 100),
                                        ir=ModbusSequentialDataBlock(0, [17] * 100))
        self.context = ModbusServerContext(slaves=self.store, single=True)

    def tearDown(self):
        """ Cleans up the test environment """

    # -----------------------------------------------------------------------#
    # Test ModbusConnectedRequestHandler
    #-----------------------------------------------------------------------#

    async def test_start_tcp_server(self):
        """ Test that the modbus tcp asyncio server starts correctly """
        identity = ModbusDeviceIdentification(info_name={'VendorName': 'VendorName'})
        self.loop = asynctest.Mock(self.loop) # pylint: disable=attribute-defined-outside-init
        server = await StartTcpServer(context=self.context,loop=self.loop,identity=identity)
        self.assertEqual(server.control.Identity.VendorName, 'VendorName')
        self.loop.create_server.assert_called_once()

    async def test_tcp_server_serve_no_defer(self):
        """ Test StartTcpServer without deferred start (immediate execution of server) """
        with patch('asyncio.base_events.Server.serve_forever', #NOSONAR
                new_callable=asynctest.CoroutineMock) as serve:
            await StartTcpServer(context=self.context,address=("127.0.0.1",
                    0), loop=self.loop, defer_start=False)
            serve.assert_awaited()

    async def test_tcp_server_serve_forever_twice(self):
        """ Call on serve_forever() twice should result in a runtime error """
        server = await StartTcpServer(context=self.context,address=("127.0.0.1", 0), loop=self.loop)
        asyncio.create_task(server.serve_forever())
        await server.serving
        with self.assertRaises(RuntimeError):

            await server.serve_forever()
        server.server_close()

    async def test_tcp_server_receive_data(self):
        """ Test data sent on socket is received by internals - doesn't not process data """
        data = b'\x01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x19'
        server = await StartTcpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        asyncio.create_task(server.serve_forever())

        await server.serving
        with patch('pymodbus.transaction.ModbusSocketFramer.processIncomingPacket', #NOSONAR
                new_callable=Mock) as process:
            # process = server.framer.processIncomingPacket = Mock()
            connected = self.loop.create_future()
            random_port = server.server.sockets[0].getsockname()[1]  # get the random server port

            class BasicClient(asyncio.BaseProtocol):
                """ Basic client. """

                def connection_made(self, transport):
                    """ Connection made. """
                    self.transport = transport # pylint: disable=attribute-defined-outside-init
                    self.transport.write(data)
                    connected.set_result(True)

                def eof_received(self):
                    """ EOF received. """

            await self.loop.create_connection(BasicClient, host='127.0.0.1',port=random_port)
            await asyncio.sleep(0.1) # this may be better done
            # by making an internal hook in the actual implementation
            # if this unit test fails on a machine,
            # see if increasing the sleep time makes a difference,
            # if it does blame author for a fix

            process.assert_called_once()
            self.assertTrue( process.call_args[1]["data"] == data )
            server.server_close()

    @pytest.mark.skipif(pytest.IS_WINDOWS, reason="To fix")
    async def test_tcp_server_roundtrip(self):
        """ Test sending and receiving data on tcp socket """
        data = b"\x01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x01" # unit 1, read register
        expected_response = b'\x01\x00\x00\x00\x00\x05\x01\x03\x02\x00\x11'
                # value of 17 as per context
        server = await StartTcpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        asyncio.create_task(server.serve_forever())
        await server.serving
        random_port = server.server.sockets[0].getsockname()[1]  # get the random server port
        connected, done = self.loop.create_future(), self.loop.create_future()
        received_value = None

        class BasicClient(asyncio.BaseProtocol):
            """ Basic client. """

            def connection_made(self, transport):
                """ Connection made. """
                self.transport = transport # pylint: disable=attribute-defined-outside-init
                self.transport.write(data)
                connected.set_result(True)

            def data_received(self, data): # pylint: disable=no-self-use
                """ Data received. """
                nonlocal received_value, done
                received_value = data
                done.set_result(True)

            def eof_received(self):
                """ EOF received. """

        transport, _ = await self.loop.create_connection(BasicClient,
                host='127.0.0.1', port=random_port)
        await asyncio.wait_for(done, timeout=0.1)

        self.assertEqual(received_value, expected_response)

        transport.close()
        await asyncio.sleep(0)
        server.server_close()

    @pytest.mark.skipif(pytest.IS_WINDOWS, reason="To fix")
    async def test_tcp_server_connection_lost(self):
        """ Test tcp stream interruption """

        server = await StartTcpServer(context=self.context,
                address=("127.0.0.1", 0), loop=self.loop)
        asyncio.create_task(server.serve_forever())
        await server.serving
        random_port = server.server.sockets[0].getsockname()[1]  # get the random server port
        step1 = self.loop.create_future()
        time.sleep(1)

        class BasicClient(asyncio.BaseProtocol):
            """ Basic client. """

            def connection_made(self, transport):
                """ Connection made. """
                self.transport = transport # pylint: disable=attribute-defined-outside-init
                step1.set_result(True)

        _, protocol = await self.loop.create_connection(BasicClient,
                host='127.0.0.1', port=random_port)
        await step1
        # On Windows we seem to need to give this an extra chance to finish,
        # otherwise there ends up being an active connection at the assert.
        await asyncio.sleep(0.2)
        self.assertEqual(len(server.active_connections), 1)

        protocol.transport.close()
            # close isn't synchronous and there's no
            # notification that it's done
        await asyncio.sleep(0.2)  # so we have to wait a bit
        self.assertFalse(server.active_connections)

        server.server_close()


    async def test_tcp_server_close_active_connection(self):
        """ Test server_close() while there are active TCP connections """
        server = await StartTcpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        asyncio.create_task(server.serve_forever())

        await server.serving

        random_port = server.server.sockets[0].getsockname()[1]  # get the random server port

        step1 = self.loop.create_future()
        self.loop.create_future()

        class BasicClient(asyncio.BaseProtocol):
            """ Basic client. """

            def connection_made(self, transport):
                """ Connection made. """
                self.transport = transport # pylint: disable=attribute-defined-outside-init
                step1.set_result(True)

        await self.loop.create_connection(BasicClient, host='127.0.0.1', port=random_port)
        await step1

        # On Windows we seem to need to give this an extra chance to finish,
        # otherwise there ends up being an active connection at the assert.
        await asyncio.sleep(0.5)
        server.server_close()

        # close isn't synchronous and there's no notification that it's done
        # so we have to wait a bit
        await asyncio.sleep(0.5)
        self.assertTrue( not server.active_connections )


    async def test_tcp_server_no_slave(self):
        """ Test unknown slave unit exception """
        context = ModbusServerContext(slaves={0x01: self.store, 0x02: self.store  }, single=False)
        data = b"\x01\x00\x00\x00\x00\x06\x05\x03\x00\x00\x00\x01"
                # get slave 5 function 3 (holding register)
        server = await StartTcpServer(context=context,address=("127.0.0.1", 0),loop=self.loop)
        asyncio.create_task(server.serve_forever())
        await server.serving
        random_port = server.server.sockets[0].getsockname()[1]  # get the random server port
        connect = self.loop.create_future()
        receive = self.loop.create_future()
        eof = self.loop.create_future()

        class BasicClient(asyncio.BaseProtocol):
            """ Basic client. """

            def connection_made(self, transport):
                """ Connection made. """
                self.transport = transport # pylint: disable=attribute-defined-outside-init
                transport.write(data)
                connect.set_result(True)
                _logger.debug("Client connected")

            def data_received(self, data): #NOSONAR pylint: disable=no-self-use,unused-argument
                """ Data received. """
                receive.set_result(True)
                _logger.debug("Client received data")

            def eof_received(self): # pylint: disable=no-self-use
                """ EOF received. """
                eof.set_result(True)
                _logger.debug("Client stream eof")

        await self.loop.create_connection(BasicClient, host='127.0.0.1', port=random_port)
        await asyncio.wait_for(connect, timeout=0.1)
        self.assertFalse(eof.done())
        server.server_close()


    async def test_tcp_server_modbus_error(self):
        """ Test sending garbage data on a TCP socket should drop the connection """
        data = b"\x01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x01"
            # get slave 5 function 3 (holding register)
        server = await StartTcpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        asyncio.create_task(server.serve_forever())

        await server.serving
        with patch("pymodbus.register_read_message.ReadHoldingRegistersRequest.execute",
                   side_effect=NoSuchSlaveException):
            connect, receive, eof = self.loop.create_future(),\
                self.loop.create_future(), self.loop.create_future()
            random_port = server.server.sockets[0].getsockname()[1]  # get the random server port

            class BasicClient(asyncio.BaseProtocol):
                """ Basic client. """
                def connection_made(self, transport):
                    """ Connection made. """
                    _logger.debug("Client connected")
                    self.transport = transport # pylint: disable=attribute-defined-outside-init
                    transport.write(data)
                    connect.set_result(True)

                def data_received(self, data): #NOSONAR pylint: disable=no-self-use,unused-argument
                    """ Data receivec. """
                    _logger.debug("Client received data")
                    receive.set_result(True)

                def eof_received(self): # pylint: disable=no-self-use
                    """ EOF received. """
                    _logger.debug("Client stream eof")
                    eof.set_result(True)

            transport, _ = await self.loop.create_connection(BasicClient,
                    host='127.0.0.1', port=random_port)
            await asyncio.wait_for(connect, timeout=0.1)
            await asyncio.wait_for(receive, timeout=0.1)
            self.assertFalse(eof.done())
            transport.close()
            server.server_close()


    async def test_tcp_server_internal_exception(self):
        """ Test sending garbage data on a TCP socket should drop the connection """
        data = b"\x01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x01"
            # get slave 5 function 3 (holding register)
        server = await StartTcpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        asyncio.create_task(server.serve_forever())

        await server.serving
        with patch("pymodbus.register_read_message.ReadHoldingRegistersRequest.execute",
                   side_effect=Exception):
            connect, receive, eof = self.loop.create_future(),\
                    self.loop.create_future(), self.loop.create_future()
            random_port = server.server.sockets[0].getsockname()[1]  # get the random server port

            class BasicClient(asyncio.BaseProtocol):
                """ Basic client. """

                def connection_made(self, transport):
                    """ Connection made. """
                    _logger.debug("Client connected")
                    self.transport = transport # pylint: disable=attribute-defined-outside-init
                    transport.write(data)
                    connect.set_result(True)

                def data_received(self, data): #NOSONAR pylint: disable=no-self-use,unused-argument
                    """ Data received. """
                    _logger.debug("Client received data")
                    receive.set_result(True)

                def eof_received(self): # pylint: disable=no-self-use
                    """ EOF received. """
                    _logger.debug("Client stream eof")
                    eof.set_result(True)

            transport, _ = await self.loop.create_connection(BasicClient,
                    host='127.0.0.1', port=random_port)
            await asyncio.wait_for(connect, timeout=0.1)
            await asyncio.wait_for(receive, timeout=0.1)
            self.assertFalse(eof.done())
            transport.close()
            server.server_close()

    # -----------------------------------------------------------------------#
    # Test ModbusTlsProtocol

    # -----------------------------------------------------------------------#
    async def test_start_tls_server(self):
        """ Test that the modbus tls asyncio server starts correctly """
        with patch.object(ssl.SSLContext, 'load_cert_chain'):
            identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
            self.loop = asynctest.Mock(self.loop) # pylint: disable=attribute-defined-outside-init
            server = await StartTlsServer(context=self.context, loop=self.loop, identity=identity)
            self.assertEqual(server.control.Identity.VendorName, 'VendorName')
            self.assertTrue(server.sslctx is not None)
            self.loop.create_server.assert_called_once()

    async def test_tls_server_serve_forever(self):
        """ Test StartTcpServer serve_forever() method """
        with patch('asyncio.base_events.Server.serve_forever',
                new_callable=asynctest.CoroutineMock) as serve:
            with patch.object(ssl.SSLContext, 'load_cert_chain'):
                server = await StartTlsServer(context=self.context,
                        address=("127.0.0.1", 0), loop=self.loop)
                await server.serve_forever()
                serve.assert_awaited()

    async def test_tls_server_serve_forever_twice(self):
        """ Call on serve_forever() twice should result in a runtime error """
        with patch.object(ssl.SSLContext, 'load_cert_chain'):
            server = await StartTlsServer(context=self.context,
                    address=("127.0.0.1", 0), loop=self.loop)
            asyncio.create_task(server.serve_forever())
            await server.serving
            with pytest.raises(RuntimeError):
                await server.serve_forever()
            server.server_close()

    # -----------------------------------------------------------------------#
    # Test ModbusUdpProtocol
    # -----------------------------------------------------------------------#

    async def test_start_udp_server(self):
        """ Test that the modbus udp asyncio server starts correctly """
        identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
        self.loop = asynctest.Mock(self.loop) # pylint: disable=attribute-defined-outside-init
        server = await StartUdpServer(context=self.context,loop=self.loop,identity=identity)
        self.assertEqual(server.control.Identity.VendorName, 'VendorName')
        self.loop.create_datagram_endpoint.assert_called_once()

    async def test_udp_server_serve_forever_start(self):
        """ Test StartUdpServer serve_forever() method """
        with patch('asyncio.base_events.Server.serve_forever',
            new_callable=asynctest.CoroutineMock) as serve:
            server = await StartTcpServer(context=self.context,
                        address=("127.0.0.1", 0), loop=self.loop)
            await server.serve_forever()
            serve.assert_awaited()


    async def test_udp_server_serve_forever_close(self):
        """ Test StartUdpServer serve_forever() method """
        server = await StartUdpServer(context=self.context,address=("127.0.0.1", 0), loop=self.loop)
        asyncio.create_task(server.serve_forever())

        await server.serving

        self.assertTrue(asyncio.isfuture(server.on_connection_terminated))
        self.assertFalse(server.on_connection_terminated.done())

        server.server_close()
        self.assertTrue(server.protocol.is_closing())

    async def test_udp_server_serve_forever_twice(self):
        """ Call on serve_forever() twice should result in a runtime error """
        identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
        server = await StartUdpServer(context=self.context,address=("127.0.0.1", 0),
                                      loop=self.loop,identity=identity)
        asyncio.create_task(server.serve_forever())
        await server.serving
        with self.assertRaises(RuntimeError):
            await server.serve_forever()
        server.server_close()


    async def test_udp_server_receive_data(self):
        """ Test that the sending data on datagram socket gets data pushed to framer """
        server = await StartUdpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        asyncio.create_task(server.serve_forever())
        await server.serving
        with patch('pymodbus.transaction.ModbusSocketFramer.processIncomingPacket',
                new_callable=Mock) as process:
            server.endpoint.datagram_received(data=b"12345", addr=("127.0.0.1", 12345))
            await asyncio.sleep(0.1)
            process.seal()
            process.assert_called_once()
            self.assertTrue( process.call_args[1]["data"] == b"12345" )

            server.server_close()


    async def test_udp_server_send_data(self):
        """ Test that the modbus udp asyncio server correctly sends data outbound """
        ModbusDeviceIdentification(info={0x00: 'VendorName'})
        data = b'x\01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x19'
        server = await StartUdpServer(context=self.context,address=("127.0.0.1", 0))
        asyncio.create_task(server.serve_forever())

        await server.serving
        random_port = server.protocol._sock.getsockname()[1] # pylint: disable=protected-access
        received = server.endpoint.datagram_received = Mock(wraps=server.endpoint.datagram_received)
        done = self.loop.create_future()
        received_value = None

        class BasicClient(asyncio.DatagramProtocol):
            """ Basic client. """

            def connection_made(self, transport):
                self.transport = transport # pylint: disable=attribute-defined-outside-init
                self.transport.sendto(data)

            def datagram_received(self, data, addr):
                nonlocal received_value, done
                print("received")
                received_value = data
                done.set_result(True)
                self.transport.close()

        await self.loop.create_datagram_endpoint( BasicClient,
            remote_addr=('127.0.0.1', random_port))

        await asyncio.sleep(0.1)

        received.assert_called_once()
        self.assertEqual(received.call_args[0][0], data)

        server.server_close()

        self.assertTrue(server.protocol.is_closing())
        await asyncio.sleep(0.1)


    async def test_udp_server_roundtrip(self):
        """ Test sending and receiving data on udp socket"""
        data = b"\x01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x01" # unit 1, read register
        expected_response = b'\x01\x00\x00\x00\x00\x05'\
                            b'\x01\x03\x02\x00\x11' # value of 17 as per context
        server = await StartUdpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        asyncio.create_task(server.serve_forever())

        await server.serving

        random_port = server.protocol._sock.getsockname()[1] # pylint: disable=protected-access

        _, done = self.loop.create_future(), self.loop.create_future()
        received_value = None

        class BasicClient(asyncio.DatagramProtocol):
            """ Basic client. """

            def connection_made(self, transport):
                self.transport = transport # pylint: disable=attribute-defined-outside-init
                self.transport.sendto(data)

            def datagram_received(self, data, addr):
                nonlocal received_value, done
                print("received")
                received_value = data
                done.set_result(True)

        transport, _ = await self.loop.create_datagram_endpoint(BasicClient,
                                                remote_addr=('127.0.0.1', random_port))
        await asyncio.wait_for(done, timeout=0.1)

        self.assertEqual(received_value, expected_response)

        transport.close()
        await asyncio.sleep(0)
        server.server_close()

    async def test_udp_server_exception(self):
        """ Test sending garbage data on a TCP socket should drop the connection """
        garbage = b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
        server = await StartUdpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        asyncio.create_task(server.serve_forever())

        await server.serving
        with patch('pymodbus.transaction.ModbusSocketFramer.processIncomingPacket',
                   new_callable=lambda: Mock(side_effect=Exception)):
            connect, receive, _ = self.loop.create_future(),\
                            self.loop.create_future(), self.loop.create_future()
            random_port = server.protocol._sock.getsockname()[1]  # get the random server port pylint: disable=protected-access

            class BasicClient(asyncio.DatagramProtocol):
                """ Basic client. """

                def connection_made(self, transport):
                    _logger.debug("Client connected")
                    self.transport = transport # pylint: disable=attribute-defined-outside-init
                    transport.sendto(garbage)
                    connect.set_result(True)

                def datagram_received(self, data, addr):
                    nonlocal receive
                    _logger.debug("Client received data")
                    receive.set_result(True)

            _, _ = await self.loop.create_datagram_endpoint(BasicClient,
                                                            remote_addr=('127.0.0.1', random_port))
            await asyncio.wait_for(connect, timeout=0.1)
            self.assertFalse(receive.done())
            self.assertFalse(server.protocol._sock._closed) # pylint: disable=protected-access

            server.server_close()

    # -----------------------------------------------------------------------#
    # Test ModbusServerFactory
    # -----------------------------------------------------------------------#
    def test_modbus_server_factory(self): # pylint: disable=no-self-use
        """ Test the base class for all the clients """
        with pytest.warns(DeprecationWarning):
            ModbusServerFactory(store=None)

    def test_stop_server(self): # pylint: disable=no-self-use
        """ Test stop server. """
        with pytest.warns(DeprecationWarning):
            StopServer()

    async def test_tcp_server_exception(self):
        """ Sending garbage data on a TCP socket should drop the connection """
        garbage = b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
        server = await StartTcpServer(context=self.context,
                            address=("127.0.0.1", 0), loop=self.loop)
        asyncio.create_task(server.serve_forever())
        await server.serving
        with patch('pymodbus.transaction.ModbusSocketFramer.processIncomingPacket',
                   new_callable=lambda: Mock(side_effect=Exception)):
            connect, receive, eof = self.loop.create_future(),\
                                    self.loop.create_future(), self.loop.create_future()
            random_port = server.server.sockets[0].getsockname()[1]  # get the random server port

            class BasicClient(asyncio.BaseProtocol):
                """ Basic client. """

                def connection_made(self, transport):
                    """ Connection made. """
                    _logger.debug("Client connected")
                    self.transport = transport # pylint: disable=attribute-defined-outside-init
                    transport.write(garbage)
                    connect.set_result(True)

                def data_received(self, data): #NOSONAR pylint: disable=no-self-use,unused-argument
                    """ Data received. """
                    _logger.debug("Client received data")
                    receive.set_result(True)

                def eof_received(self): # pylint: disable=no-self-use
                    """ Eof received. """
                    _logger.debug("Client stream eof")
                    eof.set_result(True)

            _, _ = await self.loop.create_connection(BasicClient, host='127.0.0.1',
                                                    port=random_port)
            await asyncio.wait_for(connect, timeout=0.1)
            await asyncio.wait_for(eof, timeout=0.1)
            # neither of these should timeout if the test is successful
            server.server_close()


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    asynctest.main()
