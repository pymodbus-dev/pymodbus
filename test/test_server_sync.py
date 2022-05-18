#!/usr/bin/env python3
"""Test server sync."""
import ssl
import socket
import unittest
import socketserver
from unittest.mock import patch, Mock
import pytest
import serial

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server.sync import ModbusBaseRequestHandler
from pymodbus.server.sync import ModbusSingleRequestHandler
from pymodbus.server.sync import ModbusConnectedRequestHandler
from pymodbus.server.sync import ModbusDisconnectedRequestHandler
from pymodbus.server.sync import (
    ModbusTcpServer,
    ModbusTlsServer,
    ModbusUdpServer,
    ModbusSerialServer,
)
from pymodbus.server.sync import (
    StartTcpServer,
    StartTlsServer,
    StartUdpServer,
    StartSerialServer,
)
from pymodbus.server.tls_helper import sslctx_provider
from pymodbus.exceptions import NotImplementedException
from pymodbus.bit_read_message import ReadCoilsRequest, ReadCoilsResponse
from pymodbus.datastore import ModbusServerContext
from pymodbus.transaction import ModbusTlsFramer


# --------------------------------------------------------------------------- #
# Mock Classes
# --------------------------------------------------------------------------- #
class MockServer:  # pylint: disable=too-few-public-methods
    """Mock server."""

    def __init__(self):
        """Init."""
        self.framer = lambda _, client=None: "framer"
        self.decoder = "decoder"
        self.threads = []
        self.context = {}


# --------------------------------------------------------------------------- #
# Fixture
# --------------------------------------------------------------------------- #


class SynchronousServerTest(unittest.TestCase):
    """Unittest for the pymodbus.server.sync module."""

    # ----------------------------------------------------------------------- #
    # Test Base Request Handler
    # ----------------------------------------------------------------------- #

    def test_base_handler_undefined_methods(self):
        """Test the base handler undefined methods"""
        handler = socketserver.BaseRequestHandler(None, None, None)
        handler.__class__ = ModbusBaseRequestHandler
        self.assertRaises(
            NotImplementedException, lambda: handler.send(None)  # pylint: disable=no-member
        )
        self.assertRaises(
            NotImplementedException, lambda: handler.handle()  # pylint: disable=unnecessary-lambda
        )

    def test_base_handler_methods(self):
        """Test the base class for all the clients"""
        request = ReadCoilsRequest(1, 1)
        address = ("server", 12345)
        server = MockServer()
        with patch.object(ModbusBaseRequestHandler, "handle") as mock_handle:
            with patch.object(ModbusBaseRequestHandler, "send") as mock_send:
                mock_handle.return_value = True
                mock_send.return_value = True
                handler = ModbusBaseRequestHandler(request, address, server)
                self.assertEqual(handler.running, True)
                self.assertEqual(handler.framer, "framer")

                handler.execute(request)
                self.assertEqual(mock_send.call_count, 1)

                server.context[0x00] = object()
                handler.execute(request)
                self.assertEqual(mock_send.call_count, 2)

    # ----------------------------------------------------------------------- #
    # Test Single Request Handler
    # ----------------------------------------------------------------------- #
    def test_modbus_single_request_handler_send(self):
        """Test modbus single request handler."""
        handler = socketserver.BaseRequestHandler(None, None, None)
        handler.__class__ = ModbusSingleRequestHandler
        handler.framer = Mock()
        handler.framer.buildPacket.return_value = b"message"
        handler.request = Mock()
        request = ReadCoilsResponse([1])
        handler.send(request)  # pylint: disable=no-member
        self.assertEqual(handler.request.send.call_count, 1)

        request.should_respond = False
        handler.send(request)  # pylint: disable=no-member
        self.assertEqual(handler.request.send.call_count, 1)

    def test_modbus_single_request_handler_handle(self):
        """Test modbus single request handler."""
        handler = socketserver.BaseRequestHandler(None, None, None)
        handler.__class__ = ModbusSingleRequestHandler
        handler.framer = Mock()
        handler.framer.buildPacket.return_value = b"message"
        handler.request = Mock()
        handler.socket = Mock()
        handler.server = Mock()
        handler.request.recv.return_value = b"\x12\x34"

        # exit if we are not running
        handler.running = False
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 0)

        # run forever if we are running
        def _callback1(
            parm1, parm2, *args, **kwargs
        ):  # pylint: disable=unused-argument
            handler.running = False  # stop infinite loop

        handler.framer.processIncomingPacket.side_effect = _callback1
        handler.running = True
        # Ugly hack
        handler.server.context = ModbusServerContext(slaves={-1: None}, single=False)
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 1)

        # exceptions are simply ignored
        def _callback2(
            parm1, parm2, *args, **kwargs
        ):  # pylint: disable=unused-argument
            if handler.framer.processIncomingPacket.call_count == 2:
                raise Exception("example exception")
            handler.running = False  # stop infinite loop

        handler.framer.processIncomingPacket.side_effect = _callback2
        handler.running = True
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 3)

    # ----------------------------------------------------------------------- #
    # Test Connected Request Handler
    # ----------------------------------------------------------------------- #
    def test_modbus_connected_request_handler_send(self):
        """Test modbus connected request handler."""
        handler = socketserver.BaseRequestHandler(None, None, None)
        handler.__class__ = ModbusConnectedRequestHandler
        handler.framer = Mock()
        handler.framer.buildPacket.return_value = b"message"
        handler.request = Mock()
        request = ReadCoilsResponse([1])
        handler.send(request)  # pylint: disable=no-member
        self.assertEqual(handler.request.send.call_count, 1)

        request.should_respond = False
        handler.send(request)  # pylint: disable=no-member
        self.assertEqual(handler.request.send.call_count, 1)

    def test_modbus_connected_request_handler_handle(self):
        """Test modbus connected request handler."""
        handler = socketserver.BaseRequestHandler(None, None, None)
        handler.__class__ = ModbusConnectedRequestHandler
        handler.server = Mock()
        handler.framer = Mock()
        handler.framer.buildPacket.return_value = b"message"
        handler.request = Mock()
        handler.request.recv.return_value = b"\x12\x34"

        # exit if we are not running
        handler.running = False
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 0)

        # run forever if we are running
        def _callback(parm1, parm2, *args, **kwargs):  # pylint: disable=unused-argument
            handler.running = False  # stop infinite loop

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
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 4)

    # ----------------------------------------------------------------------- #
    # Test Disconnected Request Handler
    # ----------------------------------------------------------------------- #
    def test_modbus_disconnected_request_handler_send(self):
        """Test modbus disconnect request handler."""
        handler = socketserver.BaseRequestHandler(None, None, None)
        handler.__class__ = ModbusDisconnectedRequestHandler
        handler.framer = Mock()
        handler.server = Mock()
        handler.framer.buildPacket.return_value = b"message"
        handler.request = Mock()
        handler.socket = Mock()
        request = ReadCoilsResponse([1])
        handler.send(request)  # pylint: disable=no-member
        self.assertEqual(handler.socket.sendto.call_count, 1)

        request.should_respond = False
        handler.send(request)  # pylint:disable=no-member
        self.assertEqual(handler.socket.sendto.call_count, 1)

    def test_modbus_disconnected_request_handler_handle(self):
        """Test modbus disconned request handler."""
        handler = socketserver.BaseRequestHandler(None, None, None)
        handler.__class__ = ModbusDisconnectedRequestHandler
        handler.framer = Mock()
        handler.server = Mock()
        handler.framer.buildPacket.return_value = b"message"
        handler.request = (b"\x12\x34", handler.request)

        # exit if we are not running
        handler.running = False
        handler.handle()
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 0)

        # run forever if we are running
        def _callback(parm1, parm2):  # pylint: disable=unused-argument
            handler.running = False  # stop infinite loop

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
        self.assertEqual(handler.framer.processIncomingPacket.call_count, 4)

    # ----------------------------------------------------------------------- #
    # Test TCP Server
    # ----------------------------------------------------------------------- #
    def test_tcp_server_close(self):
        """Test that the synchronous TCP server closes correctly"""
        identity = ModbusDeviceIdentification(info={0x00: "VendorName"})
        server = ModbusTcpServer(
            context=None, identity=identity, bind_and_activate=False
        )
        server.threads.append(Mock(**{"running": True}))
        server.server_close()
        self.assertEqual(server.control.Identity.VendorName, "VendorName")
        self.assertFalse(server.threads[0].running)

    def test_tcp_server_process(self):
        """Test that the synchronous TCP server processes requests"""
        with patch("socketserver.ThreadingTCPServer") as mock_server:
            server = ModbusTcpServer(None)
            server.process_request("request", "client")
            self.assertTrue(mock_server.process_request.called)

    # ----------------------------------------------------------------------- #
    # Test TLS Server
    # ----------------------------------------------------------------------- #
    def test_tls_ssl_ctx_provider(self):
        """Test that sslctx_provider() produce SSLContext correctly"""
        with patch.object(ssl.SSLContext, "load_cert_chain"):
            sslctx = sslctx_provider(reqclicert=True)
            self.assertIsNotNone(sslctx)
            self.assertEqual(type(sslctx), ssl.SSLContext)
            self.assertEqual(sslctx.verify_mode, ssl.CERT_REQUIRED)

            sslctx_old = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            sslctx_new = sslctx_provider(sslctx=sslctx_old)
            self.assertEqual(sslctx_new, sslctx_old)

    def test_tls_server_init(self):
        """Test that the synchronous TLS server initial correctly"""
        with patch.object(socketserver.TCPServer, "server_activate"):
            with patch.object(ssl.SSLContext, "load_cert_chain"):
                identity = ModbusDeviceIdentification(info={0x00: "VendorName"})
                server = ModbusTlsServer(
                    context=None,
                    identity=identity,
                    reqclicert=True,
                    bind_and_activate=False,
                )
                self.assertIs(server.framer, ModbusTlsFramer)
                server.server_activate()
                self.assertIsNotNone(server.sslctx)
                self.assertEqual(server.sslctx.verify_mode, ssl.CERT_REQUIRED)
                self.assertEqual(type(server.socket), ssl.SSLSocket)
                server.server_close()

    def test_tls_server_close(self):
        """Test that the synchronous TLS server closes correctly"""
        with patch.object(ssl.SSLContext, "load_cert_chain"):
            identity = ModbusDeviceIdentification(info={0x00: "VendorName"})
            server = ModbusTlsServer(
                context=None, identity=identity, bind_and_activate=False
            )
            server.threads.append(Mock(**{"running": True}))
            server.server_close()
            self.assertEqual(server.control.Identity.VendorName, "VendorName")
            self.assertFalse(server.threads[0].running)

    def test_tls_server_process(self):
        """Test that the synchronous TLS server processes requests"""
        with patch("socketserver.ThreadingTCPServer") as mock_server:
            with patch.object(ssl.SSLContext, "load_cert_chain"):
                server = ModbusTlsServer(None)
                server.process_request("request", "client")
                self.assertTrue(mock_server.process_request.called)

    # ----------------------------------------------------------------------- #
    # Test UDP Server
    # ----------------------------------------------------------------------- #
    def test_udp_server_close(self):
        """Test that the synchronous UDP server closes correctly"""
        identity = ModbusDeviceIdentification(info={0x00: "VendorName"})
        server = ModbusUdpServer(
            context=None, identity=identity, bind_and_activate=False
        )
        server.server_activate()
        server.threads.append(Mock(**{"running": True}))
        server.server_close()
        self.assertEqual(server.control.Identity.VendorName, "VendorName")
        self.assertFalse(server.threads[0].running)

    def test_udp_server_process(self):
        """Test that the synchronous UDP server processes requests"""
        with patch("socketserver.ThreadingUDPServer") as mock_server:
            server = ModbusUdpServer(None)
            request = ("data", "socket")
            server.process_request(request, "client")
            self.assertTrue(mock_server.process_request.called)

    # ----------------------------------------------------------------------- #
    # Test Serial Server
    # ----------------------------------------------------------------------- #
    def test_serial_server_connect(self):
        """Test serial server connect."""
        with patch.object(serial, "Serial") as mock_serial:
            mock_serial.write = lambda x: len(x)  # pylint: disable=unnecessary-lambda
            mock_serial.read = lambda size: "\x00" * size
            identity = ModbusDeviceIdentification(info={0x00: "VendorName"})
            server = ModbusSerialServer(context=None, identity=identity, port="dummy")
            self.assertEqual(
                server.handler.__class__.__name__, "CustomSingleRequestHandler"
            )
            self.assertEqual(server.control.Identity.VendorName, "VendorName")

            server._connect()  # pylint: disable=protected-access

        with patch.object(serial, "Serial") as mock_serial:
            mock_serial.write = lambda x: len(x)  # pylint: disable=unnecessary-lambda
            mock_serial.read = lambda size: "\x00" * size
            mock_serial.side_effect = serial.SerialException()
            server = ModbusSerialServer(None, port="dummy")
            self.assertEqual(server.socket, None)

    def test_serial_server_serve_forever(self):  # pylint: disable=no-self-use
        """Test that the synchronous serial server closes correctly"""
        with patch.object(serial, "Serial"):
            with patch(
                "pymodbus.server.sync.CustomSingleRequestHandler"
            ) as mock_handler:
                server = ModbusSerialServer(None)
                instance = mock_handler.return_value
                instance.response_manipulator.side_effect = server.server_close
                server.serve_forever()
                instance.response_manipulator.assert_any_call()

    def test_serial_server_close(self):  # pylint: disable=no-self-use
        """Test that the synchronous serial server closes correctly"""
        with patch.object(serial, "Serial") as mock_serial:
            instance = mock_serial.return_value
            server = ModbusSerialServer(None)
            server.server_close()
            instance.close.assert_any_call()

    # ----------------------------------------------------------------------- #
    # Test Synchronous Factories
    # ----------------------------------------------------------------------- #
    def test_start_tcp_server(self):  # pylint: disable=no-self-use
        """Test the tcp server starting factory"""
        with patch.object(ModbusTcpServer, "serve_forever"):
            StartTcpServer(bind_and_activate=False)

    def test_start_tls_server(self):  # pylint: disable=no-self-use
        """Test the tls server starting factory"""
        with patch.object(ModbusTlsServer, "serve_forever"):
            with patch.object(ssl.SSLContext, "load_cert_chain"):
                StartTlsServer(bind_and_activate=False)

    def test_start_udp_server(self):  # pylint: disable=no-self-use
        """Test the udp server starting factory"""
        with patch.object(ModbusUdpServer, "serve_forever"):
            with patch.object(socketserver.UDPServer, "server_bind"):
                StartUdpServer()

    def test_start_serial_server(self):  # pylint: disable=no-self-use
        """Test the serial server starting factory"""
        with patch.object(ModbusSerialServer, "serve_forever"):
            StartSerialServer(port=pytest.SERIAL_PORT)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    unittest.main()
