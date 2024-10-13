"""Test transaction."""
from unittest import mock

from pymodbus.factory import ServerDecoder
from pymodbus.framer import (
    FramerAscii,
    FramerRTU,
    FramerSocket,
    FramerTLS,
)
from pymodbus.pdu import ModbusRequest
from pymodbus.transaction import (
    SyncModbusTransactionManager,
)


TEST_MESSAGE = b"\x7b\x01\x03\x00\x00\x00\x05\x85\xC9\x7d"


class TestTransaction:  # pylint: disable=too-many-public-methods
    """Unittest for the pymodbus.transaction module."""

    client = None
    decoder = None
    _tcp = None
    _tls = None
    _rtu = None
    _ascii = None
    _manager = None
    _tm = None

    # ----------------------------------------------------------------------- #
    # Test Construction
    # ----------------------------------------------------------------------- #
    def setup_method(self):
        """Set up the test environment."""
        self.client = None
        self.decoder = ServerDecoder()
        self._tcp = FramerSocket(self.decoder)
        self._tls = FramerTLS(self.decoder)
        self._rtu = FramerRTU(self.decoder)
        self._ascii = FramerAscii(self.decoder)
        self._manager = SyncModbusTransactionManager(self.client, 3)

    def test_tcp_framer_transaction_ready(self):
        """Test a tcp frame transaction."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00\x08"
        assert self._tcp.processIncomingFrame(msg)
        self._tcp.databuffer = msg

    def test_tls_framer_transaction_ready(self):
        """Test a tls frame transaction."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        assert not self._tcp.processIncomingFrame(msg[0:4])
        assert self._tcp.processIncomingFrame(msg[4:])

    def test_rtu_framer_transaction_ready(self):
        """Test if the checks for a complete frame work."""
        msg_parts = [b"\x00\x01\x00", b"\x00\x00\x01\xfc\x1b"]
        assert not self._rtu.processIncomingFrame(msg_parts[0])
        assert self._rtu.processIncomingFrame(msg_parts[1])

    def test_ascii_framer_transaction_ready(self):
        """Test a ascii frame transaction."""
        msg = b":F7031389000A60\r\n"
        assert self._ascii.processIncomingFrame(msg)


    def test_tcp_framer_transaction_full(self):
        """Test a full tcp frame transaction."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00\x08"
        result = self._tcp.processIncomingFrame(msg)
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg[7:]

    def test_tls_framer_transaction_full(self):
        """Test a full tls frame transaction."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        assert self._tcp.processIncomingFrame(msg)

    def test_rtu_framer_transaction_full(self):
        """Test a full rtu frame transaction."""
        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        assert self._rtu.processIncomingFrame(msg)

    def test_tcp_framer_transaction_half(self):
        """Test a half completed tcp frame transaction."""
        msg1 = b"\x00\x01\x12\x34\x00"
        msg2 = b"\x06\xff\x02\x01\x02\x00\x08"
        assert not self._tcp.processIncomingFrame(msg1)
        result = self._tcp.processIncomingFrame(msg2)
        assert result
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg2[2:]

    def test_ascii_framer_transaction_full(self):
        """Test a full ascii frame transaction."""
        msg = b"sss:F7031389000A60\r\n"
        assert self._ascii.processIncomingFrame(msg)

    def test_rtu_framer_transaction_half(self):
        """Test a half completed rtu frame transaction."""
        msg_parts = [b"\x00\x01\x00", b"\x00\x00\x01\xfc\x1b"]
        assert not self._rtu.processIncomingFrame(msg_parts[0])
        assert self._rtu.processIncomingFrame(msg_parts[1])

    def test_ascii_framer_transaction_half(self):
        """Test a half completed ascii frame transaction."""
        msg_parts = (b"sss:F7031389", b"000A60\r\n")
        assert not self._ascii.processIncomingFrame(msg_parts[0])
        assert self._ascii.processIncomingFrame(msg_parts[1])

    def test_tcp_framer_transaction_half2(self):
        """Test a half completed tcp frame transaction."""
        msg1 = b"\x00\x01\x12\x34\x00\x06\xff"
        msg2 = b"\x02\x01\x02\x00\x08"
        assert not self._tcp.processIncomingFrame(msg1)
        result = self._tcp.processIncomingFrame(msg2)
        assert result
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg2

    def test_tcp_framer_transaction_half3(self):
        """Test a half completed tcp frame transaction."""
        msg1 = b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00"
        msg2 = b"\x08"
        assert not self._tcp.processIncomingFrame(msg1)
        result = self._tcp.processIncomingFrame(msg2)
        assert result
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg1[7:] + msg2

    def test_tcp_framer_transaction_short(self):
        """Test that we can get back on track after an invalid message."""
        msg1 = b''
        msg2 = b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00\x08"
        assert not self._tcp.processIncomingFrame(msg1)
        result = self._tcp.processIncomingFrame(msg2)
        assert result
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg2[7:]

    def test_tcp_framer_populate(self):
        """Test a tcp frame packet build."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        result = self._tcp.processIncomingFrame(msg)
        assert result
        assert result.slave_id == 0xFF
        assert result.transaction_id == 0x0001

    def test_tls_framer_populate(self):
        """Test a tls frame packet build."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        assert self._tcp.processIncomingFrame(msg)

    def test_rtu_framer_populate(self):
        """Test a rtu frame packet build."""
        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        result = self._rtu.processIncomingFrame(msg)
        assert int(msg[0]) == result.slave_id

    @mock.patch.object(ModbusRequest, "encode")
    def test_tcp_framer_packet(self, mock_encode):
        """Test a tcp frame packet build."""
        message = ModbusRequest(0, 0, False)
        message.transaction_id = 0x0001
        message.slave_id = 0xFF
        message.function_code = 0x01
        expected = b"\x00\x01\x00\x00\x00\x02\xff\x01"
        mock_encode.return_value = b""
        actual = self._tcp.buildFrame(message)
        assert expected == actual

    @mock.patch.object(ModbusRequest, "encode")
    def test_tls_framer_packet(self, mock_encode):
        """Test a tls frame packet build."""
        message = ModbusRequest(0, 0, False)
        message.function_code = 0x01
        expected = b"\x01"
        mock_encode.return_value = b""
        actual = self._tls.buildFrame(message)
        assert expected == actual

    @mock.patch.object(ModbusRequest, "encode")
    def test_rtu_framer_packet(self, mock_encode):
        """Test a rtu frame packet build."""
        message = ModbusRequest(0, 0, False)
        message.slave_id = 0xFF
        message.function_code = 0x01
        expected = b"\xff\x01\x81\x80"  # only header + CRC - no data
        mock_encode.return_value = b""
        actual = self._rtu.buildFrame(message)
        assert expected == actual

    # -------

    def test_tls_incoming_packet(self):
        """Framer tls incoming packet."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        result = self._tls.processIncomingFrame(msg)
        assert result

    def test_rtu_process_incoming_packets(self):
        """Test rtu process incoming packets."""
        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        assert self._rtu.processIncomingFrame(msg)

    def test_ascii_process_incoming_packets(self):
        """Test ascii process incoming packet."""
        msg = b":F7031389000A60\r\n"
        assert self._ascii.processIncomingFrame(msg)

    def test_rtu_decode_exception(self):
        """Test that the RTU framer can decode errors."""
        msg = b"\x00\x90\x02\x9c\x01"
        assert self._rtu.processIncomingFrame(msg)

    def test_process(self):
        """Test process."""
        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        assert self._rtu.processIncomingFrame(msg)
