"""Test server working as slave on a multidrop RS485 line."""
from unittest import mock

import pytest

from pymodbus.exceptions import ModbusIOException
from pymodbus.factory import ClientDecoder
from pymodbus.framer import ModbusSocketFramer


class TestFaultyResponses:
    """Test that server works on a multidrop line."""

    slaves = [0]

    good_frame = b"\x00\x01\x00\x00\x00\x05\x00\x03\x02\x00\x01"

    @pytest.fixture(name="framer")
    def fixture_framer(self):
        """Prepare framer."""
        return ModbusSocketFramer(ClientDecoder())

    @pytest.fixture(name="callback")
    def fixture_callback(self):
        """Prepare dummy callback."""
        return mock.Mock()

    def test_ok_frame(self, framer, callback):
        """Test ok frame."""
        framer.processIncomingPacket(self.good_frame, callback, self.slaves)
        callback.assert_called_once()

    def test_faulty_frame1(self, framer, callback):
        """Test ok frame."""
        faulty_frame = b"\x00\x04\x00\x00\x00\x05\x00\x03\x0a\x00\x04"
        with pytest.raises(ModbusIOException):
            framer.processIncomingPacket(faulty_frame, callback, self.slaves)
        callback.assert_not_called()
        framer.processIncomingPacket(self.good_frame, callback, self.slaves)
        callback.assert_called_once()
