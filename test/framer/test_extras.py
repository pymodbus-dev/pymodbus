"""Test transaction."""
from unittest.mock import patch

import pytest

from pymodbus.exceptions import ModbusIOException
from pymodbus.framer import (
    FramerAscii,
    FramerRTU,
    FramerSocket,
    FramerTLS,
)
from pymodbus.pdu import DecodePDU


TEST_MESSAGE = b"\x7b\x01\x03\x00\x00\x00\x05\x85\xC9\x7d"


class TestExtras:
    """Test for the framer module."""

    def setup_method(self):
        """Set up the test environment."""
        self.client = None
        self.decoder = DecodePDU(True)
        self._tcp = FramerSocket(self.decoder)
        self._tls = FramerTLS(self.decoder)
        self._rtu = FramerRTU(self.decoder)
        self._ascii = FramerAscii(self.decoder)


    def test_tcp_framer_transaction_half2(self):
        """Test a half completed tcp frame transaction."""
        msg1 = b"\x00\x01\x00\x00\x00\x06\xff"
        msg2 = b"\x02\x01\x02\x00\x08"
        used_len, pdu = self._tcp.handleFrame(msg1, 0, 0)
        assert not pdu
        assert not used_len
        used_len, pdu = self._tcp.handleFrame(msg1+msg2, 0, 0)
        assert pdu
        assert used_len == len(msg1) + len(msg2)
        assert pdu.function_code.to_bytes(1,'big') + pdu.encode() == msg2

    def test_tcp_framer_transaction_half3(self):
        """Test a half completed tcp frame transaction."""
        msg1 = b"\x00\x01\x00\x00\x00\x06\xff\x02\x01\x02\x00"
        msg2 = b"\x08"
        used_len, pdu = self._tcp.handleFrame(msg1, 0, 0)
        assert not pdu
        assert not used_len
        used_len, pdu = self._tcp.handleFrame(msg1+msg2, 0, 0)
        assert pdu
        assert used_len == len(msg1) + len(msg2)
        assert pdu.function_code.to_bytes(1,'big') + pdu.encode() == msg1[7:] + msg2

    def test_tcp_framer_transaction_short(self):
        """Test that we can get back on track after an invalid message."""
        msg1 = b''
        msg2 = b"\x00\x01\x00\x00\x00\x06\xff\x02\x01\x02\x00\x08"
        used_len, pdu = self._tcp.handleFrame(msg1, 0, 0)
        assert not pdu
        assert not used_len
        used_len, pdu = self._tcp.handleFrame(msg1+msg2, 0, 0)
        assert pdu
        assert used_len == len(msg1) + len(msg2)
        assert pdu.function_code.to_bytes(1,'big') + pdu.encode() == msg2[7:]

    def test_tcp_framer_transaction_wrong_id(self):
        """Test a half completed tcp frame transaction."""
        msg = b"\x00\x01\x00\x00\x00\x06\xff\x02\x01\x02\x00\x08"
        used_len, pdu = self._tcp.handleFrame(msg, 1, 0)
        assert not pdu
        assert used_len == len(msg)

    def test_tcp_framer_transaction_wrong_tid(self):
        """Test a half completed tcp frame transaction."""
        msg = b"\x00\x01\x00\x00\x00\x06\xff\x02\x01\x02\x00\x08"
        used_len, pdu = self._tcp.handleFrame(msg, 0, 10)
        assert not pdu
        assert used_len == len(msg)

    def test_tcp_framer_transaction_wrong_fc(self):
        """Test a half completed tcp frame transaction."""
        msg = b"\x00\x01\x00\x00\x00\x06\xff\x70\x01\x02\x00\x08"
        with pytest.raises(ModbusIOException):
            self._tcp.handleFrame(msg, 0, 0)

    def test_tls_incoming_packet(self):
        """Framer tls incoming packet."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00\x08"
        _, pdu = self._tls.handleFrame(msg, 0, 0)
        assert pdu

    def test_rtu_process_incoming_packets(self):
        """Test rtu process incoming packets."""
        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        _, pdu = self._rtu.handleFrame(msg, 0, 0)
        assert pdu

    def test_rtu_short_packets(self):
        """Test rtu process incoming packets."""
        msg1 = b"\x00\x01"
        msg2 = b"\x00\x00\x00\x01\xfc\x1b"
        used_len, pdu = self._rtu.handleFrame(msg1, 0, 0)
        assert not used_len
        assert not pdu
        used_len, pdu = self._rtu.handleFrame(msg1+msg2, 0, 0)
        assert used_len == len(msg1) + len(msg2)
        assert pdu

    def test_rtu_calculate(self):
        """Test rtu process incoming packets."""
        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        with patch("pymodbus.pdu.ReadCoilsRequest.calculateRtuFrameSize", return_value=0):
            used_len, pdu = self._rtu.handleFrame(msg, 0, 0)
            assert not used_len
            assert not pdu

    def test_rtu_wrong_fc(self):
        """Test rtu process incoming packets."""
        msg = b"\x00\x70\x00\x00\x00\x71\xfc\x1b"
        used_len, pdu = self._rtu.handleFrame(msg, 0, 0)
        assert not pdu
        assert not used_len

    def test_ascii_process_incoming_packets(self):
        """Test ascii process incoming packet."""
        msg = b":F7031389000A60\r\n"
        _, pdu = self._ascii.handleFrame(msg, 0, 0)
        assert pdu

    def test_rtu_decode_exception(self):
        """Test that the RTU framer can decode errors."""
        msg = b"\x00\x90\x02\x9c\x01"
        _, pdu = self._rtu.handleFrame(msg, 0, 0)
        assert pdu

    def test_rtu_dsetMultidrop(self):
        """Test that the RTU framer can define multidrop."""
        self._rtu.setMultidrop([1,2,3])

    def test_rtu_dsetMultidrop2(self):
        """Test that the RTU framer can use multidrop."""
        self._rtu.setMultidrop([1,2,3])
        msg = b"\x05\x90\x02\x9c\x01"
        cut, pdu = self._rtu.handleFrame(msg, 0, 0)
        assert cut
        assert not pdu
