"""Test client sync."""
import socket
from itertools import count
from unittest import mock

import pytest
import serial

from pymodbus import FramerType
from pymodbus.client import (
    ModbusSerialClient,
    ModbusTcpClient,
    ModbusTlsClient,
    ModbusUdpClient,
)
from pymodbus.exceptions import ConnectionException
from pymodbus.framer import (
    FramerAscii,
    FramerRTU,
    FramerSocket,
    FramerTLS,
)
from test.conftest import mockSocket


# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#


class TestSynchronousClient:  # pylint: disable=too-many-public-methods
    """Unittest for the pymodbus.client module."""

    # -----------------------------------------------------------------------#
    # Test UDP Client
    # -----------------------------------------------------------------------#

    def test_basic_syn_udp_client(self):
        """Test the basic methods for the udp sync client."""
        # receive/send
        client = ModbusUdpClient("127.0.0.1")
        client.socket = mockSocket()
        assert not client.send(None)
        assert client.send(b"\x50") == 1
        assert client.recv(1) == b"\x50"

        # connect/disconnect
        assert client.connect()
        assert client.connected
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        assert str(client) == "ModbusUdpClient 127.0.0.1:502"

    def test_udp_client_is_socket_open(self):
        """Test the udp client is_socket_open method."""
        client = ModbusUdpClient("127.0.0.1")
        assert client.is_socket_open()

    def test_udp_client_send(self):
        """Test the udp client send method."""
        client = ModbusUdpClient("127.0.0.1")
        with pytest.raises(ConnectionException):
            client.send(None)
        client.socket = mockSocket()
        assert not client.send(None)
        assert client.send("1234") == 4

    def test_udp_client_recv(self):
        """Test the udp client receive method."""
        client = ModbusUdpClient("127.0.0.1")
        with pytest.raises(ConnectionException):
            client.recv(1024)
        client.socket = mockSocket()
        client.socket.mock_prepare_receive(b"\x00" * 4)
        assert client.recv(0) == b""
        assert client.recv(4) == b"\x00" * 4

    def test_udp_client_recv_duplicate(self):
        """Test the udp client receive method."""
        test_msg = b"\x00\x01\x00\x00\x00\x05\x01\x04\x02\x00\x03"
        client = ModbusUdpClient("127.0.0.1")
        client.socket = mockSocket(copy_send=False)
        client.socket.mock_prepare_receive(test_msg)
        client.socket.mock_prepare_receive(test_msg)
        reply_ok = client.read_input_registers(0x820, 1, 1)
        assert not reply_ok.isError()
        reply_ok = client.read_input_registers(0x40, 10, 1)
        assert not reply_ok.isError()
        client.close()

    def test_udp_client_repr(self):
        """Test udp client representation."""
        client = ModbusUdpClient("127.0.0.1")
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} socket={client.socket}, "
            f"ipaddr={client.comm_params.host}, port={client.comm_params.port}, timeout={client.comm_params.timeout_connect}>"
        )
        assert repr(client) == rep

    # -----------------------------------------------------------------------#
    # Test TCP Client
    # -----------------------------------------------------------------------#

    def test_syn_tcp_client_instantiation(self):
        """Test sync tcp client."""
        client = ModbusTcpClient("127.0.0.1")
        assert client

    @mock.patch("pymodbus.client.tcp.select")
    def test_basic_syn_tcp_client(self, mock_select):
        """Test the basic methods for the tcp sync client."""
        # receive/send
        mock_select.select.return_value = [True]
        client = ModbusTcpClient("127.0.0.1")
        client.socket = mockSocket()
        assert not client.send(None)
        assert client.send(b"\x45") == 1
        assert client.recv(1) == b"\x45"

        # connect/disconnect
        assert client.connected
        assert client.connect()
        mock_select.select.side_effect = ValueError
        with pytest.raises(ConnectionException):
            client.recv(1)
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        assert str(client) == "ModbusTcpClient 127.0.0.1:502"

    def test_tcp_client_is_socket_open(self):
        """Test the tcp client is_socket_open method."""
        client = ModbusTcpClient("127.0.0.1")
        assert not client.is_socket_open()

    def test_tcp_client_send(self):
        """Test the tcp client send method."""
        client = ModbusTcpClient("127.0.0.1")
        with pytest.raises(ConnectionException):
            client.send(None)
        client.socket = mockSocket()
        assert not client.send(None)
        assert client.send("1234") == 4

    @mock.patch("pymodbus.client.tcp.time")
    @mock.patch("pymodbus.client.tcp.select")
    def test_tcp_client_recv(self, mock_select, mock_time):
        """Test the tcp client receive method."""
        mock_select.select.return_value = [True]
        mock_time.time.side_effect = count()
        client = ModbusTcpClient("127.0.0.1")
        with pytest.raises(ConnectionException):
            client.recv(1024)
        client.socket = mockSocket()
        assert client.recv(0) == b""
        client.socket.mock_prepare_receive(b"\x00" * 4)
        assert client.recv(4) == b"\x00" * 4

        mock_socket = mock.MagicMock()
        mock_socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02"])
        client.socket = mock_socket
        client.comm_params.timeout_connect = 3
        assert client.recv(3) == b"\x00\x01\x02"
        mock_socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02"])
        assert client.recv(2) == b"\x00\x01"
        mock_select.select.return_value = [False]
        assert client.recv(2) == b""
        client.socket = mockSocket()
        client.socket.mock_prepare_receive(b"\x00")
        mock_select.select.return_value = [True]
        assert client.recv(None) in b"\x00"

        mock_socket = mock.MagicMock()
        mock_socket.recv.return_value = b""
        client.socket = mock_socket
        with pytest.raises(ConnectionException):
            client.recv(1024)
        mock_socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02", b""])
        client.socket = mock_socket
        assert client.recv(1024) == b"\x00\x01\x02"

    def test_tcp_client_repr(self):
        """Test tcp client."""
        client = ModbusTcpClient("127.0.0.1")
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} socket={client.socket}, "
            f"ipaddr={client.comm_params.host}, port={client.comm_params.port}, timeout={client.comm_params.timeout_connect}>"
        )
        assert repr(client) == rep

    def test_tcp_client_register(self):
        """Test tcp client."""

        class CustomRequest:  # pylint: disable=too-few-public-methods
            """Dummy custom request."""

            function_code = 79

        client = ModbusTcpClient("127.0.0.1")
        client.framer = mock.Mock()
        client.register(CustomRequest)
        client.framer.decoder.register.assert_called_once_with(CustomRequest)

    # -----------------------------------------------------------------------#
    # Test TLS Client
    # -----------------------------------------------------------------------#

    def test_syn_tls_client_instantiation(self):
        """Test sync tls client."""
        # default SSLContext
        client = ModbusTlsClient("127.0.0.1")
        assert client
        assert isinstance(client.framer, FramerTLS)
        assert client.comm_params.sslctx

    @mock.patch("pymodbus.client.tcp.select")
    def test_basic_syn_tls_client(self, mock_select):
        """Test the basic methods for the tls sync client."""
        # receive/send
        mock_select.select.return_value = [True]
        client = ModbusTlsClient("localhost")
        client.socket = mockSocket()
        assert not client.send(None)
        assert client.send(b"\x45") == 1
        assert client.recv(1) == b"\x45"

        # connect/disconnect
        assert not client.connected
        assert client.connect()
        client.close()

        # already closed socket
        client.socket = False
        client.close()
        assert str(client) == "ModbusTlsClient localhost:802"

        client = ModbusTcpClient("127.0.0.1")
        client.socket = mockSocket()
        assert not client.send(None)
        assert client.send(b"\x45") == 1
        assert client.recv(1) == b"\x45"

    def test_tls_client_send(self):
        """Test the tls client send method."""
        client = ModbusTlsClient("127.0.0.1")
        with pytest.raises(ConnectionException):
            client.send(None)
        client.socket = mockSocket()
        assert not client.send(None)
        assert client.send("1234") == 4

    @mock.patch("pymodbus.client.tcp.time")
    @mock.patch("pymodbus.client.tcp.select")
    def test_tls_client_recv(self, mock_select, mock_time):
        """Test the tls client receive method."""
        mock_select.select.return_value = [True]
        client = ModbusTlsClient("127.0.0.1")
        with pytest.raises(ConnectionException):
            client.recv(1024)
        mock_time.time.side_effect = count()

        client.socket = mockSocket()
        client.socket.mock_prepare_receive(b"\x00" * 4)
        assert client.recv(0) == b""
        assert client.recv(4) == b"\x00" * 4

        client.comm_params.timeout_connect = 2
        client.socket.mock_prepare_receive(b"\x00")
        assert b"\x00" in client.recv(None)

    def test_tls_client_repr(self):
        """Test tls client."""
        client = ModbusTlsClient("127.0.0.1")
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} socket={client.socket}, "
            f"ipaddr={client.comm_params.host}, port={client.comm_params.port}, sslctx={client.comm_params.sslctx}, "
            f"timeout={client.comm_params.timeout_connect}>"
        )
        assert repr(client) == rep

    def test_tls_client_register(self):
        """Test tls client."""

        class CustomRequest:  # pylint: disable=too-few-public-methods
            """Dummy custom request."""

            function_code = 79

        client = ModbusTlsClient("127.0.0.1")
        client.framer = mock.Mock()
        client.register(CustomRequest)
        client.framer.decoder.register.assert_called_once_with(CustomRequest)

    # -----------------------------------------------------------------------#
    # Test Serial Client
    # -----------------------------------------------------------------------#
    def test_sync_serial_client_instantiation(self):
        """Test sync serial client."""
        client = ModbusSerialClient("/dev/null")
        assert client
        assert isinstance(
            ModbusSerialClient("/dev/null", framer=FramerType.ASCII).framer,
            FramerAscii,
        )
        assert isinstance(
            ModbusSerialClient("/dev/null", framer=FramerType.RTU).framer,
            FramerRTU,
        )
        assert isinstance(
            ModbusSerialClient("/dev/null", framer=FramerType.SOCKET).framer,
            FramerSocket,
        )

    def test_sync_serial_rtu_client_timeouts(self):
        """Test sync serial rtu."""
        client = ModbusSerialClient("/dev/null", framer=FramerType.RTU, baudrate=9600)
        assert client.silent_interval == round((3.5 * 10 / 9600), 6)
        client = ModbusSerialClient("/dev/null", framer=FramerType.RTU, baudrate=38400)
        assert client.silent_interval == round((1.75 / 1000), 6)

    @mock.patch("serial.Serial")
    def test_basic_sync_serial_client(self, mock_serial):
        """Test the basic methods for the serial sync client."""
        # receive/send
        mock_serial.in_waiting = 0
        mock_serial.write = lambda x: len(x)  # pylint: disable=unnecessary-lambda

        mock_serial.read = lambda size: b"\x00" * size
        client = ModbusSerialClient("/dev/null")
        client.socket = mock_serial
        client.state = 0
        assert not client.send(None)
        client.state = 0
        assert client.send(b"\x00") == 1
        assert client.recv(1) == b"\x00"

        # connect/disconnect
        assert client.connected
        assert client.connect()
        client.close()

        # rtu connect/disconnect
        rtu_client = ModbusSerialClient("/dev/null", framer=FramerType.RTU)
        assert rtu_client.connect()
        assert rtu_client.socket.inter_byte_timeout == rtu_client.inter_byte_timeout
        rtu_client.close()
        assert str(client) == "ModbusSerialClient /dev/null:0"

        # already closed socket
        client.socket = None
        client.close()

    def test_serial_client_connect(self):
        """Test the serial client connection method."""
        with mock.patch.object(serial, "Serial") as mock_method:
            mock_method.return_value = mock.MagicMock()
            client = ModbusSerialClient("/dev/null")
            assert client.connect()

        with mock.patch.object(serial, "Serial") as mock_method:
            mock_method.side_effect = serial.SerialException()
            client = ModbusSerialClient("/dev/null")
            assert not client.connect()

    @mock.patch("serial.Serial")
    def test_serial_client_is_socket_open(self, mock_serial):
        """Test the serial client is_socket_open method."""
        client = ModbusSerialClient("/dev/null")
        assert not client.is_socket_open()
        client.socket = mock_serial
        assert client.is_socket_open()

    @mock.patch("serial.Serial")
    def test_serial_client_send(self, mock_serial):
        """Test the serial client send method."""
        mock_serial.in_waiting = None
        mock_serial.write = lambda x: len(x)  # pylint: disable=unnecessary-lambda
        client = ModbusSerialClient("/dev/null")
        with pytest.raises(ConnectionException):
            client.send(None)
        client.socket = mock_serial
        client.state = 0
        assert not client.send(None)
        client.state = 0
        assert client.send("1234") == 4


    @mock.patch("serial.Serial")
    def test_serial_client_cleanup_buffer_before_send(self, mock_serial):
        """Test the serial client send method."""
        mock_serial.in_waiting = 4
        mock_serial.read = lambda x: b"1" * x
        mock_serial.write = lambda x: len(x)  # pylint: disable=unnecessary-lambda
        client = ModbusSerialClient("/dev/null")
        with pytest.raises(ConnectionException):
            client.send(None)
        client.socket = mock_serial
        client.state = 0
        assert not client.send(None)
        client.state = 0
        assert client.send("1234") == 4

    def test_serial_client_recv(self):
        """Test the serial client receive method."""
        client = ModbusSerialClient("/dev/null")
        with pytest.raises(ConnectionException):
            client.recv(1024)
        client.socket = mockSocket()
        assert client.recv(0) == b""
        client.socket.mock_prepare_receive(b"\x00" * 4)
        assert client.recv(4) == b"\x00" * 4
        client.socket = mockSocket()
        client.socket.mock_prepare_receive(b"")
        assert client.recv(None) == b""
        client.socket.timeout = 0
        assert client.recv(0) == b""

    def test_serial_client_recv_split(self):
        """Test the serial client receive method."""
        client = ModbusSerialClient("/dev/null")
        with pytest.raises(ConnectionException):
            client.recv(1024)
        client.socket = mockSocket(copy_send=False)
        client.socket.mock_prepare_receive(b'')
        client.socket.mock_prepare_receive(b'\x11\x03\x06\xAE')
        client.socket.mock_prepare_receive(b'\x41\x56\x52\x43\x40\x49')
        client.socket.mock_prepare_receive(b'\xAD')
        reply_ok = client.read_input_registers(0x820, 3, slave=17)
        assert not reply_ok.isError()
        client.close()


    def test_serial_client_repr(self):
        """Test serial client."""
        client = ModbusSerialClient("/dev/null")
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} socket={client.socket}, "
            f"framer={client.framer}, timeout={client.comm_params.timeout_connect}>"
        )
        assert repr(client) == rep

    def test_serial_client_with(self):
        """Test with block."""
        with mock.patch("pymodbus.client.serial.ModbusSerialClient.connect"), ModbusSerialClient("/dev/null") as client:
                assert client
                client.socket = mockSocket()

    def test_syn_family(self):
        """Test family test."""
        assert ModbusTcpClient.get_address_family("::0") == socket.AF_INET6
        assert ModbusTcpClient.get_address_family("192.168.1.1") == socket.AF_INET
