"""Test server working as a device on a multidrop RS485 line."""

import pytest

from pymodbus.exceptions import ModbusIOException
from pymodbus.framer import FramerRTU, FramerSocket
from pymodbus.pdu import DecodePDU


class TestFaultyResponses:
    """Test that server works on a multidrop line."""

    good_frame = b"\x00\x01\x00\x00\x00\x05\x00\x03\x02\x00\x01"

    @pytest.fixture(name="framer")
    def fixture_framer(self):
        """Prepare framer."""
        return FramerSocket(DecodePDU(False))

    def test_ok_frame(self, framer):
        """Test ok frame."""
        used_len, pdu = framer.handleFrame(self.good_frame, 0, 0)
        assert pdu
        assert used_len == len(self.good_frame)

    def test_1917_frame(self):
        """Test invalid frame in issue 1917."""
        recv = b"\x01\x86\x02\x00\x01"
        framer = FramerRTU(DecodePDU(False))
        used_len, pdu = framer.handleFrame(recv, 0, 0)
        assert not pdu
        assert not used_len

    def test_faulty_frame1(self, framer):
        """Test ok frame."""
        faulty_frame = b"\x00\x04\x00\x00\x00\x05\x00\x03\x0a\x00\x04"
        with pytest.raises(ModbusIOException):
            framer.handleFrame(faulty_frame, 0, 0)
        used_len, pdu = framer.handleFrame(self.good_frame, 0, 0)
        assert pdu
        assert used_len == len(self.good_frame)
