#!/usr/bin/env python
from pymodbus.compat import IS_PYTHON3
import unittest
if IS_PYTHON3: # Python 3
    from unittest.mock import patch, Mock
else: # Python 2
    from mock import patch, Mock
import serial
import socket

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server.sync import ModbusBaseRequestHandler
from pymodbus.server.sync import ModbusSingleRequestHandler
from pymodbus.server.sync import ModbusConnectedRequestHandler
from pymodbus.server.sync import ModbusDisconnectedRequestHandler
from pymodbus.server.sync import ModbusTcpServer, ModbusUdpServer, ModbusSerialServer
from pymodbus.server.sync import StartTcpServer, StartUdpServer, StartSerialServer
from pymodbus.exceptions import NotImplementedException
from pymodbus.bit_read_message import ReadCoilsRequest, ReadCoilsResponse
import sys
from pymodbus.compat import socketserver

SERIAL_PORT = "/dev/ptmx"
if sys.platform == "darwin":
    SERIAL_PORT = "/dev/ptyp0"
#---------------------------------------------------------------------------#
# Mock Classes
#---------------------------------------------------------------------------#
class MockServer(object):
    def __init__(self):
        self.framer  = lambda _: "framer"
        self.decoder = "decoder"
        self.threads = []
        self.context = {}


#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class SynchronousServerTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.server.sync module
    '''

    #-----------------------------------------------------------------------#
    # Test Base Request Handler
    #-----------------------------------------------------------------------#

    def testBaseHandlerUndefinedMethods(self):
        ''' Test the base handler undefined methods'''
        handler = socketserver.BaseRequestHandler(None, None, None)
        handler.__class__ = ModbusBaseRequestHandler
        self.assertRaises(NotImplementedException, lambda: handler.send(None))
        self.assertRaises(NotImplementedException, lambda: handler.handle())

    def testBaseHandlerMethods(self):
        ''' Test the base class for all the clients '''
        request = ReadCoilsRequest(1, 1)
        address = ('server', 12345)
        server  = MockServer()
        
        with patch.object(ModbusBaseRequestHandler, 'handle') as mock_handle:
            with patch.object(ModbusBaseRequestHandler, 'send') as mock_send:
                mock_handle.return_value = True
                mock_send.return_value = True
                handler = ModbusBaseRequestHandler(request, address, server)
                self.assertEqual(handler.running, True)
                self.assertEqual(handler.framer, 'framer')

                handler.execute(request)
                self.assertEqual(mock_send.call_count, 1)

                server.context[0x00] = object()
                handler.execute(request)
                self.assertEqual(mock_send.call_count, 2)

    #-----------------------------------------------------------------------#
    # Test Single Request Handler
    #-----------------------------------------------------------------------#
    def testModbusSingleRequestHandlerSend(self):
        handler = socketserver.BaseRequestHandler(None, None, None)
        handler.__class__ = ModbusSingleRequestHandler
        handler.framer  = Mock()
        handler.framer.buildPacket.return_value = b"message"
        handler.request = Mock()
        request = ReadCoilsResponse([1])
        handler.send(request)
        self.assertEqual(handler.request.send.call_count, 1)

        request.should_respond = False
        handler.send(request)
        self.assertEqual(handler.request.send.call_count, 1)

    def testModbusSingleRequestHandlerHandle(self):
        handler = socketserver.BaseRequestHandler(None, None, None)
        handler.__class__ = ModbusSingleRequestHandler
        handler.framer  = Mock()
        handler.framer.buildPacket.return_value = b"message"
        handler.request = Mock()
        handler.request.recv.return_value = b"\x12\x34"

        # exit if we are not running
        handler.running = False
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 0)

        # run forever if we are running
        def _callback1(a, b):
            handler.running = False # stop infinite loop
        handler.framer.processIncomingPacket.side_effect = _callback1
        handler.running = True
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 1)

        # exceptions are simply ignored
        def _callback2(a, b):
            if handler.framer.processIncomingPacket.call_count == 2:
                raise Exception("example exception")
            else: handler.running = False # stop infinite loop
        handler.framer.processIncomingPacket.side_effect = _callback2
        handler.running = True
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 3)

    #-----------------------------------------------------------------------#
    # Test Connected Request Handler
    #-----------------------------------------------------------------------#
    def testModbusConnectedRequestHandlerSend(self):
        handler = socketserver.BaseRequestHandler(None, None, None)
        handler.__class__ = ModbusConnectedRequestHandler
        handler.framer  = Mock()
        handler.framer.buildPacket.return_value = b"message"
        handler.request = Mock()
        request = ReadCoilsResponse([1])
        handler.send(request)
        self.assertEqual(handler.request.send.call_count, 1)

        request.should_respond = False
        handler.send(request)
        self.assertEqual(handler.request.send.call_count, 1)

    def testModbusConnectedRequestHandlerHandle(self):
        handler = socketserver.BaseRequestHandler(None, None, None)
        handler.__class__ = ModbusConnectedRequestHandler
        handler.framer  = Mock()
        handler.framer.buildPacket.return_value = b"message"
        handler.request = Mock()
        handler.request.recv.return_value = b"\x12\x34"

        # exit if we are not running
        handler.running = False
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 0)

        # run forever if we are running
        def _callback(a, b):
            handler.running = False # stop infinite loop
        handler.framer.processIncomingPacket.side_effect = _callback
        handler.running = True
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 1)

        # socket errors cause the client to disconnect
        handler.framer.processIncomingPacket.side_effect = socket.error()
        handler.running = True
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 2)

        # every other exception causes the client to disconnect
        handler.framer.processIncomingPacket.side_effect = Exception()
        handler.running = True
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 3)

        # receiving no data causes the client to disconnect
        handler.request.recv.return_value = None
        handler.running = True
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 3)

    #-----------------------------------------------------------------------#
    # Test Disconnected Request Handler
    #-----------------------------------------------------------------------#
    def testModbusDisconnectedRequestHandlerSend(self):
        handler = socketserver.BaseRequestHandler(None, None, None)
        handler.__class__ = ModbusDisconnectedRequestHandler
        handler.framer  = Mock()
        handler.framer.buildPacket.return_value = b"message"
        handler.request = Mock()
        request = ReadCoilsResponse([1])
        handler.send(request)
        self.assertEqual(handler.request.sendto.call_count, 1)

        request.should_respond = False
        handler.send(request)
        self.assertEqual(handler.request.sendto.call_count, 1)

    def testModbusDisconnectedRequestHandlerHandle(self):
        handler = socketserver.BaseRequestHandler(None, None, None)
        handler.__class__ = ModbusDisconnectedRequestHandler
        handler.framer  = Mock()
        handler.framer.buildPacket.return_value = b"message"
        handler.request = (b"\x12\x34", handler.request)

        # exit if we are not running
        handler.running = False
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 0)

        # run forever if we are running
        def _callback(a, b):
            handler.running = False # stop infinite loop
        handler.framer.processIncomingPacket.side_effect = _callback
        handler.running = True
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 1)

        # socket errors cause the client to disconnect
        handler.request = (b"\x12\x34", handler.request)
        handler.framer.processIncomingPacket.side_effect = socket.error()
        handler.running = True
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 2)

        # every other exception causes the client to disconnect
        handler.request = (b"\x12\x34", handler.request)
        handler.framer.processIncomingPacket.side_effect = Exception()
        handler.running = True
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 3)

        # receiving no data causes the client to disconnect
        handler.request = (None, handler.request)
        handler.running = True
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 3)

    #-----------------------------------------------------------------------#
    # Test TCP Server
    #-----------------------------------------------------------------------#
    def testTcpServerClose(self):
        ''' test that the synchronous TCP server closes correctly '''
        with patch.object(socket.socket, 'bind') as mock_socket:
            identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
            server = ModbusTcpServer(context=None, identity=identity)
            server.threads.append(Mock(**{'running': True}))
            server.server_close()
            self.assertEqual(server.control.Identity.VendorName, 'VendorName')
            self.assertFalse(server.threads[0].running)

    def testTcpServerProcess(self):
        ''' test that the synchronous TCP server processes requests '''
        with patch('pymodbus.compat.socketserver.ThreadingTCPServer') as mock_server:
            server = ModbusTcpServer(None)
            server.process_request('request', 'client')
            self.assertTrue(mock_server.process_request.called)

    #-----------------------------------------------------------------------#
    # Test UDP Server
    #-----------------------------------------------------------------------#
    def testUdpServerClose(self):
        ''' test that the synchronous UDP server closes correctly '''
        with patch.object(socket.socket, 'bind') as mock_socket:
            identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
            server = ModbusUdpServer(context=None, identity=identity)
            server.threads.append(Mock(**{'running': True}))
            server.server_close()
            self.assertEqual(server.control.Identity.VendorName, 'VendorName')
            self.assertFalse(server.threads[0].running)

    def testUdpServerProcess(self):
        ''' test that the synchronous UDP server processes requests '''
        with patch('pymodbus.compat.socketserver.ThreadingUDPServer') as mock_server:
            server = ModbusUdpServer(None)
            request = ('data', 'socket')
            server.process_request(request, 'client')
            self.assertTrue(mock_server.process_request.called)

    #-----------------------------------------------------------------------#
    # Test Serial Server
    #-----------------------------------------------------------------------#
    def testSerialServerConnect(self):
        with patch.object(serial, 'Serial') as mock_serial:
                # mock_serial.return_value = "socket"
                mock_serial.write = lambda x: len(x)
                mock_serial.read = lambda size: '\x00' * size
                identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
                server = ModbusSerialServer(context=None, identity=identity, port="dummy")
                # # mock_serial.return_value = "socket"
                # self.assertEqual(server.socket.port, "dummy")
                self.assertEquals(server.handler.__class__.__name__, "CustomSingleRequestHandler")
                self.assertEqual(server.control.Identity.VendorName, 'VendorName')

                server._connect()
                # self.assertEqual(server.socket, "socket")

        with patch.object(serial, 'Serial') as mock_serial:
            mock_serial.write = lambda x: len(x)
            mock_serial.read = lambda size: '\x00' * size
            mock_serial.side_effect = serial.SerialException()
            server = ModbusSerialServer(None, port="dummy")
            self.assertEqual(server.socket, None)

    def testSerialServerServeForever(self):
        ''' test that the synchronous serial server closes correctly '''
        with patch.object(serial, 'Serial') as mock_serial:
            with patch('pymodbus.server.sync.CustomSingleRequestHandler') as mock_handler:
                server = ModbusSerialServer(None)
                instance = mock_handler.return_value
                instance.handle.side_effect = server.server_close
                server.serve_forever()
                instance.handle.assert_any_call()

    def testSerialServerClose(self):
        ''' test that the synchronous serial server closes correctly '''
        with patch.object(serial, 'Serial') as mock_serial:
            instance = mock_serial.return_value
            server = ModbusSerialServer(None)
            server.server_close()
            instance.close.assert_any_call()

    #-----------------------------------------------------------------------#
    # Test Synchronous Factories
    #-----------------------------------------------------------------------#
    def testStartTcpServer(self):
        ''' Test the tcp server starting factory '''
        with patch.object(ModbusTcpServer, 'serve_forever') as mock_server:
            with patch.object(socketserver.TCPServer, 'server_bind') as mock_binder:
                StartTcpServer()

    def testStartUdpServer(self):
        ''' Test the udp server starting factory '''
        with patch.object(ModbusUdpServer, 'serve_forever') as mock_server:
            with patch.object(socketserver.UDPServer, 'server_bind') as mock_binder:
                StartUdpServer()

    def testStartSerialServer(self):
        ''' Test the serial server starting factory '''
        with patch.object(ModbusSerialServer, 'serve_forever') as mock_server:
            StartSerialServer(port=SERIAL_PORT)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
