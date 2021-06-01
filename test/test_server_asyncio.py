#!/usr/bin/env python
from pymodbus.compat import IS_PYTHON3, PYTHON_VERSION
import pytest
import asynctest
import asyncio
import logging
import time
_logger = logging.getLogger()
if IS_PYTHON3: # Python 3
    from asynctest.mock import patch, Mock, MagicMock

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.factory import ServerDecoder
from pymodbus.server.asynchronous import ModbusTcpProtocol, ModbusUdpProtocol
from pymodbus.server.async_io import StartTcpServer, StartTlsServer, StartUdpServer, StartSerialServer, StopServer, ModbusServerFactory
from pymodbus.server.async_io import ModbusConnectedRequestHandler, ModbusBaseRequestHandler
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.compat import byte2int
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.exceptions import NoSuchSlaveException, ModbusIOException

import sys

import ssl

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
import platform
from distutils.version import LooseVersion

IS_DARWIN = platform.system().lower() == "darwin"
OSX_SIERRA = LooseVersion("10.12")
if IS_DARWIN:
    IS_HIGH_SIERRA_OR_ABOVE = LooseVersion(platform.mac_ver()[0])
    SERIAL_PORT = '/dev/ptyp0' if not IS_HIGH_SIERRA_OR_ABOVE else '/dev/ttyp0'
else:
    IS_HIGH_SIERRA_OR_ABOVE = False
    SERIAL_PORT = "/dev/ptmx"


@pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
class AsyncioServerTest(asynctest.TestCase):
    '''
    This is the unittest for the pymodbus.server.asyncio module

    The scope of this unit test is the life-cycle management of the network
    connections and server objects.

    This unittest suite does not attempt to test any of the underlying protocol details
    '''

    #-----------------------------------------------------------------------#
    # Setup/TearDown
    #-----------------------------------------------------------------------#
    def setUp(self):
        '''
        Initialize the test environment by setting up a dummy store and context
        '''
        self.store = ModbusSlaveContext( di=ModbusSequentialDataBlock(0, [17]*100),
                                         co=ModbusSequentialDataBlock(0, [17]*100),
                                         hr=ModbusSequentialDataBlock(0, [17]*100),
                                         ir=ModbusSequentialDataBlock(0, [17]*100))
        self.context = ModbusServerContext(slaves=self.store, single=True)

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    #-----------------------------------------------------------------------#
    # Test ModbusConnectedRequestHandler
    #-----------------------------------------------------------------------#
    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testStartTcpServer(self):
        ''' Test that the modbus tcp asyncio server starts correctly '''
        identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
        self.loop = asynctest.Mock(self.loop)
        server = yield from StartTcpServer(context=self.context,loop=self.loop,identity=identity)
        self.assertEqual(server.control.Identity.VendorName, 'VendorName')
        if PYTHON_VERSION >= (3, 6):
            self.loop.create_server.assert_called_once()

    @pytest.mark.skipif(PYTHON_VERSION < (3, 7), reason="requires python3.7 or above")
    @asyncio.coroutine
    def testTcpServerServeNoDefer(self):
        ''' Test StartTcpServer without deferred start (immediate execution of server) '''
        with patch('asyncio.base_events.Server.serve_forever', new_callable=asynctest.CoroutineMock) as serve:
            server = yield from StartTcpServer(context=self.context,address=("127.0.0.1", 0), loop=self.loop, defer_start=False)
            serve.assert_awaited()

    @pytest.mark.skipif(PYTHON_VERSION < (3, 7), reason="requires python3.7 or above")
    @asyncio.coroutine
    def testTcpServerServeForever(self):
        ''' Test StartTcpServer serve_forever() method '''
        with patch('asyncio.base_events.Server.serve_forever', new_callable=asynctest.CoroutineMock) as serve:
            server = yield from StartTcpServer(context=self.context,address=("127.0.0.1", 0), loop=self.loop)
            yield from server.serve_forever()
            serve.assert_awaited()

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testTcpServerServeForeverTwice(self):
        ''' Call on serve_forever() twice should result in a runtime error '''
        server = yield from StartTcpServer(context=self.context,address=("127.0.0.1", 0), loop=self.loop)
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving
        with self.assertRaises(RuntimeError):
            yield from server.serve_forever()
        server.server_close()

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testTcpServerReceiveData(self):
        ''' Test data sent on socket is received by internals - doesn't not process data '''
        data = b'\x01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x19'
        server = yield from StartTcpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving
        with patch('pymodbus.transaction.ModbusSocketFramer.processIncomingPacket', new_callable=Mock) as process:
        # process = server.framer.processIncomingPacket = Mock()
            connected = self.loop.create_future()
            random_port = server.server.sockets[0].getsockname()[1] # get the random server port

            class BasicClient(asyncio.BaseProtocol):
                def connection_made(self, transport):
                    self.transport = transport
                    self.transport.write(data)
                    connected.set_result(True)

                def eof_received(self):
                    pass

            transport, protocol = yield from self.loop.create_connection(BasicClient, host='127.0.0.1',port=random_port)
            yield from asyncio.sleep(0.1) # this may be better done by making an internal hook in the actual implementation
            # if this unit test fails on a machine, see if increasing the sleep time makes a difference, if it does
            # blame author for a fix

            if PYTHON_VERSION >= (3, 6):
                process.assert_called_once()
            self.assertTrue( process.call_args[1]["data"] == data )
            server.server_close()

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testTcpServerRoundtrip(self):
        ''' Test sending and receiving data on tcp socket '''
        data = b"\x01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x01" # unit 1, read register
        expected_response = b'\x01\x00\x00\x00\x00\x05\x01\x03\x02\x00\x11' # value of 17 as per context
        server = yield from StartTcpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving

        random_port = server.server.sockets[0].getsockname()[1] # get the random server port

        connected, done = self.loop.create_future(),self.loop.create_future()
        received_value = None

        class BasicClient(asyncio.BaseProtocol):
            def connection_made(self, transport):
                self.transport = transport
                self.transport.write(data)
                connected.set_result(True)

            def data_received(self, data):
                nonlocal received_value, done
                received_value = data
                done.set_result(True)

            def eof_received(self):
                pass

        transport, protocol = yield from self.loop.create_connection(BasicClient, host='127.0.0.1',port=random_port)
        yield from asyncio.wait_for(done, timeout=0.1)

        self.assertEqual(received_value, expected_response)

        transport.close()
        yield from asyncio.sleep(0)
        server.server_close()

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testTcpServerConnectionLost(self):
        ''' Test tcp stream interruption '''
        data = b"\x01\x00\x00\x00\x00\x06\x01\x01\x00\x00\x00\x01"
        server = yield from StartTcpServer(context=self.context, address=("127.0.0.1", 0), loop=self.loop)

        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving

        random_port = server.server.sockets[0].getsockname()[1]     # get the random server port

        step1 = self.loop.create_future()
        # done = self.loop.create_future()
        # received_value = None
        time.sleep(1)

        class BasicClient(asyncio.BaseProtocol):
            def connection_made(self, transport):
                self.transport = transport
                step1.set_result(True)

        transport, protocol = yield from self.loop.create_connection(BasicClient, host='127.0.0.1', port=random_port)
        yield from step1
        # On Windows we seem to need to give this an extra chance to finish,
        # otherwise there ends up being an active connection at the assert.
        yield from asyncio.sleep(0.0)
        self.assertTrue(len(server.active_connections) == 1)

        protocol.transport.close()  # close isn't synchronous and there's no notification that it's done
        # so we have to wait a bit
        allowed_delay = 1
        deadline = time.monotonic() + allowed_delay
        while time.monotonic() <= deadline:
            yield from asyncio.sleep(0.1)
            if len(server.active_connections) == 0:
                break
        else:
            self.assertTrue(
                len(server.active_connections) == 0,
                msg="connections not closed within {} seconds".format(allowed_delay),
            )

        server.server_close()

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testTcpServerCloseActiveConnection(self):
        ''' Test server_close() while there are active TCP connections '''
        data = b"\x01\x00\x00\x00\x00\x06\x01\x01\x00\x00\x00\x01"
        server = yield from StartTcpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving

        random_port = server.server.sockets[0].getsockname()[1] # get the random server port

        step1 = self.loop.create_future()
        done = self.loop.create_future()
        received_value = None

        class BasicClient(asyncio.BaseProtocol):
            def connection_made(self, transport):
                self.transport = transport
                step1.set_result(True)

        transport, protocol = yield from self.loop.create_connection(BasicClient, host='127.0.0.1',port=random_port)
        yield from step1

        # On Windows we seem to need to give this an extra chance to finish,
        # otherwise there ends up being an active connection at the assert.
        yield from asyncio.sleep(0.0)
        server.server_close()

        # close isn't synchronous and there's no notification that it's done
        # so we have to wait a bit
        yield from asyncio.sleep(0.0)
        self.assertTrue( len(server.active_connections) == 0 )

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testTcpServerNoSlave(self):
        ''' Test unknown slave unit exception '''
        context = ModbusServerContext(slaves={0x01: self.store, 0x02: self.store  }, single=False)
        data = b"\x01\x00\x00\x00\x00\x06\x05\x03\x00\x00\x00\x01" # get slave 5 function 3 (holding register)
        server = yield from StartTcpServer(context=context,address=("127.0.0.1", 0),loop=self.loop)
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving
        connect, receive, eof = self.loop.create_future(),self.loop.create_future(),self.loop.create_future()
        received_data = None
        random_port = server.server.sockets[0].getsockname()[1] # get the random server port

        class BasicClient(asyncio.BaseProtocol):
            def connection_made(self, transport):
                _logger.debug("Client connected")
                self.transport = transport
                transport.write(data)
                connect.set_result(True)

            def data_received(self, data):
                _logger.debug("Client received data")
                receive.set_result(True)
                received_data = data

            def eof_received(self):
                _logger.debug("Client stream eof")
                eof.set_result(True)

        transport, protocol = yield from self.loop.create_connection(BasicClient, host='127.0.0.1',port=random_port)
        yield from asyncio.wait_for(connect, timeout=0.1)
        self.assertFalse(eof.done())
        server.server_close()

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testTcpServerModbusError(self):
        ''' Test sending garbage data on a TCP socket should drop the connection '''
        data = b"\x01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x01"  # get slave 5 function 3 (holding register)
        server = yield from StartTcpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving
        with patch("pymodbus.register_read_message.ReadHoldingRegistersRequest.execute",
                   side_effect=NoSuchSlaveException):
            connect, receive, eof = self.loop.create_future(),self.loop.create_future(),self.loop.create_future()
            received_data = None
            random_port = server.server.sockets[0].getsockname()[1] # get the random server port

            class BasicClient(asyncio.BaseProtocol):
                def connection_made(self, transport):
                    _logger.debug("Client connected")
                    self.transport = transport
                    transport.write(data)
                    connect.set_result(True)

                def data_received(self, data):
                    _logger.debug("Client received data")
                    receive.set_result(True)
                    received_data = data

                def eof_received(self):
                    _logger.debug("Client stream eof")
                    eof.set_result(True)

            transport, protocol = yield from self.loop.create_connection(BasicClient, host='127.0.0.1',port=random_port)
            yield from asyncio.wait_for(connect, timeout=0.1)
            yield from asyncio.wait_for(receive, timeout=0.1)
            self.assertFalse(eof.done())
            transport.close()
            server.server_close()

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testTcpServerInternalException(self):
        ''' Test sending garbage data on a TCP socket should drop the connection '''
        data = b"\x01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x01"  # get slave 5 function 3 (holding register)
        server = yield from StartTcpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving
        with patch("pymodbus.register_read_message.ReadHoldingRegistersRequest.execute",
                   side_effect=Exception):
            connect, receive, eof = self.loop.create_future(),self.loop.create_future(),self.loop.create_future()
            received_data = None
            random_port = server.server.sockets[0].getsockname()[1] # get the random server port

            class BasicClient(asyncio.BaseProtocol):
                def connection_made(self, transport):
                    _logger.debug("Client connected")
                    self.transport = transport
                    transport.write(data)
                    connect.set_result(True)

                def data_received(self, data):
                    _logger.debug("Client received data")
                    receive.set_result(True)
                    received_data = data

                def eof_received(self):
                    _logger.debug("Client stream eof")
                    eof.set_result(True)

            transport, protocol = yield from self.loop.create_connection(BasicClient, host='127.0.0.1',port=random_port)
            yield from asyncio.wait_for(connect, timeout=0.1)
            yield from asyncio.wait_for(receive, timeout=0.1)
            self.assertFalse(eof.done())

            transport.close()
            server.server_close()


    #-----------------------------------------------------------------------#
    # Test ModbusTlsProtocol
    #-----------------------------------------------------------------------#
    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testStartTlsServer(self):
        ''' Test that the modbus tls asyncio server starts correctly '''
        with patch.object(ssl.SSLContext, 'load_cert_chain') as mock_method:
            identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
            self.loop = asynctest.Mock(self.loop)
            server = yield from StartTlsServer(context=self.context,loop=self.loop,identity=identity)
            self.assertEqual(server.control.Identity.VendorName, 'VendorName')
            self.assertIsNotNone(server.sslctx)
            if PYTHON_VERSION >= (3, 6):
                self.loop.create_server.assert_called_once()

    @pytest.mark.skipif(PYTHON_VERSION < (3, 7), reason="requires python3.7 or above")
    @asyncio.coroutine
    def testTlsServerServeNoDefer(self):
        ''' Test StartTcpServer without deferred start (immediate execution of server) '''
        with patch('asyncio.base_events.Server.serve_forever', new_callable=asynctest.CoroutineMock) as serve:
            with patch.object(ssl.SSLContext, 'load_cert_chain') as mock_method:
                server = yield from StartTlsServer(context=self.context,address=("127.0.0.1", 0), loop=self.loop, defer_start=False)
                serve.assert_awaited()

    @pytest.mark.skipif(PYTHON_VERSION < (3, 7), reason="requires python3.7 or above")
    @asyncio.coroutine
    def testTlsServerServeForever(self):
        ''' Test StartTcpServer serve_forever() method '''
        with patch('asyncio.base_events.Server.serve_forever', new_callable=asynctest.CoroutineMock) as serve:
            with patch.object(ssl.SSLContext, 'load_cert_chain') as mock_method:
                server = yield from StartTlsServer(context=self.context,address=("127.0.0.1", 0), loop=self.loop)
                yield from server.serve_forever()
                serve.assert_awaited()

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testTlsServerServeForeverTwice(self):
        ''' Call on serve_forever() twice should result in a runtime error '''
        with patch.object(ssl.SSLContext, 'load_cert_chain') as mock_method:
            server = yield from StartTlsServer(context=self.context,address=("127.0.0.1", 0), loop=self.loop)
            if PYTHON_VERSION >= (3, 7):
                server_task = asyncio.create_task(server.serve_forever())
            else:
                server_task = asyncio.ensure_future(server.serve_forever())
            yield from server.serving
            with self.assertRaises(RuntimeError):
                yield from server.serve_forever()
            server.server_close()


    #-----------------------------------------------------------------------#
    # Test ModbusUdpProtocol
    #-----------------------------------------------------------------------#

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testStartUdpServer(self):
        ''' Test that the modbus udp asyncio server starts correctly '''
        identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
        self.loop = asynctest.Mock(self.loop)
        server = yield from StartUdpServer(context=self.context,loop=self.loop,identity=identity)
        self.assertEqual(server.control.Identity.VendorName, 'VendorName')
        if PYTHON_VERSION >= (3, 6):
            self.loop.create_datagram_endpoint.assert_called_once()

    # async def testUdpServerServeNoDefer(self):
    #     ''' Test StartUdpServer without deferred start - NOT IMPLEMENTED - this test is hard to do without additional
    #       internal plumbing added to the implementation '''
    #     asyncio.base_events.Server.serve_forever = asynctest.CoroutineMock()
    #     server = yield from StartUdpServer(address=("127.0.0.1", 0), loop=self.loop, defer_start=False)
    #     server.server.serve_forever.assert_awaited()

    @pytest.mark.skipif(PYTHON_VERSION < (3, 7), reason="requires python3.7 or above")
    @asyncio.coroutine
    def testUdpServerServeForeverStart(self):
        ''' Test StartUdpServer serve_forever() method '''
        with patch('asyncio.base_events.Server.serve_forever', new_callable=asynctest.CoroutineMock) as serve:
            server = yield from StartTcpServer(context=self.context,address=("127.0.0.1", 0), loop=self.loop)
            yield from server.serve_forever()
            serve.assert_awaited()

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testUdpServerServeForeverClose(self):
        ''' Test StartUdpServer serve_forever() method '''
        server = yield from StartUdpServer(context=self.context,address=("127.0.0.1", 0), loop=self.loop)
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving

        self.assertTrue(asyncio.isfuture(server.on_connection_terminated))
        self.assertFalse(server.on_connection_terminated.done())

        server.server_close()
        self.assertTrue(server.protocol.is_closing())

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testUdpServerServeForeverTwice(self):
        ''' Call on serve_forever() twice should result in a runtime error '''
        identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
        server = yield from StartUdpServer(context=self.context,address=("127.0.0.1", 0),
                                      loop=self.loop,identity=identity)
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving
        with self.assertRaises(RuntimeError):
            yield from server.serve_forever()
        server.server_close()

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testUdpServerReceiveData(self):
        ''' Test that the sending data on datagram socket gets data pushed to framer '''
        server = yield from StartUdpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving
        with patch('pymodbus.transaction.ModbusSocketFramer.processIncomingPacket',new_callable=Mock) as process:

            server.endpoint.datagram_received(data=b"12345", addr=("127.0.0.1", 12345))
            yield from asyncio.sleep(0.1)
            process.seal()

            if PYTHON_VERSION >= (3, 6):
                process.assert_called_once()
            self.assertTrue( process.call_args[1]["data"] == b"12345" )

            server.server_close()

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testUdpServerSendData(self):
        ''' Test that the modbus udp asyncio server correctly sends data outbound '''
        identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
        data = b'x\01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x19'
        server = yield from StartUdpServer(context=self.context,address=("127.0.0.1", 0))
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving
        random_port = server.protocol._sock.getsockname()[1]
        received = server.endpoint.datagram_received = Mock(wraps=server.endpoint.datagram_received)
        done = self.loop.create_future()
        received_value = None

        class BasicClient(asyncio.DatagramProtocol):
            def connection_made(self, transport):
                self.transport = transport
                self.transport.sendto(data)

            def datagram_received(self, data, addr):
                nonlocal received_value, done
                print("received")
                received_value = data
                done.set_result(True)
                self.transport.close()

        transport, protocol = yield from self.loop.create_datagram_endpoint( BasicClient,
            remote_addr=('127.0.0.1', random_port))

        yield from asyncio.sleep(0.1)

        if PYTHON_VERSION >= (3, 6):
            received.assert_called_once()
        self.assertEqual(received.call_args[0][0], data)

        server.server_close()

        self.assertTrue(server.protocol.is_closing())
        yield from asyncio.sleep(0.1)

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testUdpServerRoundtrip(self):
        ''' Test sending and receiving data on udp socket'''
        data = b"\x01\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x01" # unit 1, read register
        expected_response = b'\x01\x00\x00\x00\x00\x05\x01\x03\x02\x00\x11' # value of 17 as per context
        server = yield from StartUdpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving

        random_port = server.protocol._sock.getsockname()[1]

        connected, done = self.loop.create_future(),self.loop.create_future()
        received_value = None

        class BasicClient(asyncio.DatagramProtocol):
            def connection_made(self, transport):
                self.transport = transport
                self.transport.sendto(data)

            def datagram_received(self, data, addr):
                nonlocal received_value, done
                print("received")
                received_value = data
                done.set_result(True)

        transport, protocol = yield from self.loop.create_datagram_endpoint( BasicClient,
                                                                        remote_addr=('127.0.0.1', random_port))
        yield from asyncio.wait_for(done, timeout=0.1)

        self.assertEqual(received_value, expected_response)

        transport.close()
        yield from asyncio.sleep(0)
        server.server_close()

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testUdpServerException(self):
        ''' Test sending garbage data on a TCP socket should drop the connection '''
        garbage = b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
        server = yield from StartUdpServer(context=self.context,address=("127.0.0.1", 0),loop=self.loop)
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving
        with patch('pymodbus.transaction.ModbusSocketFramer.processIncomingPacket',
                   new_callable=lambda: Mock(side_effect=Exception)) as process:
            connect, receive, eof = self.loop.create_future(),self.loop.create_future(),self.loop.create_future()
            received_data = None
            random_port = server.protocol._sock.getsockname()[1]  # get the random server port

            class BasicClient(asyncio.DatagramProtocol):
                def connection_made(self, transport):
                    _logger.debug("Client connected")
                    self.transport = transport
                    transport.sendto(garbage)
                    connect.set_result(True)

                def datagram_received(self, data, addr):
                    nonlocal receive
                    _logger.debug("Client received data")
                    receive.set_result(True)
                    received_data = data

            transport, protocol = yield from self.loop.create_datagram_endpoint(BasicClient,
                                                                           remote_addr=('127.0.0.1', random_port))
            yield from asyncio.wait_for(connect, timeout=0.1)
            self.assertFalse(receive.done())
            self.assertFalse(server.protocol._sock._closed)
            server.server_close()

    # -----------------------------------------------------------------------#
    # Test ModbusServerFactory
    # -----------------------------------------------------------------------#
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testModbusServerFactory(self):
        ''' Test the base class for all the clients '''
        with self.assertWarns(DeprecationWarning):
            factory = ModbusServerFactory(store=None)

    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testStopServer(self):
        with self.assertWarns(DeprecationWarning):
            StopServer()

    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testTcpServerException(self):
        ''' Sending garbage data on a TCP socket should drop the connection '''
        garbage = b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
        server = yield from StartTcpServer(context=self.context, address=("127.0.0.1", 0), loop=self.loop)
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving
        with patch('pymodbus.transaction.ModbusSocketFramer.processIncomingPacket',
                   new_callable=lambda: Mock(side_effect=Exception)) as process:
            connect, receive, eof = self.loop.create_future(), self.loop.create_future(), self.loop.create_future()
            received_data = None
            random_port = server.server.sockets[0].getsockname()[1]  # get the random server port

            class BasicClient(asyncio.BaseProtocol):
                def connection_made(self, transport):
                    _logger.debug("Client connected")
                    self.transport = transport
                    transport.write(garbage)
                    connect.set_result(True)

                def data_received(self, data):
                    _logger.debug("Client received data")
                    receive.set_result(True)
                    received_data = data

                def eof_received(self):
                    _logger.debug("Client stream eof")
                    eof.set_result(True)

            transport, protocol = yield from self.loop.create_connection(BasicClient, host='127.0.0.1',
                                                                         port=random_port)
            yield from asyncio.wait_for(connect, timeout=0.1)
            yield from asyncio.wait_for(eof, timeout=0.1)
            # neither of these should timeout if the test is successful
            server.server_close()


    @asyncio.coroutine
    @pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
    def testTcpServerException(self):
        ''' Sending garbage data on a TCP socket should drop the connection '''
        garbage = b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
        server = yield from StartTcpServer(context=self.context, address=("127.0.0.1", 0), loop=self.loop)
        if PYTHON_VERSION >= (3, 7):
            server_task = asyncio.create_task(server.serve_forever())
        else:
            server_task = asyncio.ensure_future(server.serve_forever())
        yield from server.serving
        with patch('pymodbus.transaction.ModbusSocketFramer.processIncomingPacket',
                   new_callable=lambda: Mock(side_effect=Exception)) as process:
            connect, receive, eof = self.loop.create_future(), self.loop.create_future(), self.loop.create_future()
            received_data = None
            random_port = server.server.sockets[0].getsockname()[1]  # get the random server port

            class BasicClient(asyncio.BaseProtocol):
                def connection_made(self, transport):
                    _logger.debug("Client connected")
                    self.transport = transport
                    transport.write(garbage)
                    connect.set_result(True)

                def data_received(self, data):
                    _logger.debug("Client received data")
                    receive.set_result(True)
                    received_data = data

                def eof_received(self):
                    _logger.debug("Client stream eof")
                    eof.set_result(True)

            transport, protocol = yield from self.loop.create_connection(BasicClient, host='127.0.0.1',
                                                                         port=random_port)
            yield from asyncio.wait_for(connect, timeout=0.1)
            yield from asyncio.wait_for(eof, timeout=0.1)
            # neither of these should timeout if the test is successful
            server.server_close()



# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    asynctest.main()
