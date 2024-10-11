"""Test server working as slave on a multidrop RS485 line."""
from unittest import mock

import pytest

from pymodbus.exceptions import ModbusIOException
from pymodbus.factory import ClientDecoder
from pymodbus.framer import FramerRTU, FramerSocket


class TestFaultyResponses:
    """Test that server works on a multidrop line."""

    good_frame = b"\x00\x01\x00\x00\x00\x05\x00\x03\x02\x00\x01"

    @pytest.fixture(name="framer")
    def fixture_framer(self):
        """Prepare framer."""
        return FramerSocket(ClientDecoder(), [])

    @pytest.fixture(name="callback")
    def fixture_callback(self):
        """Prepare dummy callback."""
        return mock.Mock()

    def test_ok_frame(self, framer, callback):
        """Test ok frame."""
        framer.processIncomingFrame(self.good_frame, callback)
        callback.assert_called_once()

    def test_1917_frame(self, callback):
        """Test invalid frame in issue 1917."""
        recv = b"\x01\x86\x02\x00\x01"
        framer = FramerRTU(ClientDecoder(), [0])
        framer.processIncomingFrame(recv, callback)
        callback.assert_not_called()

    def test_faulty_frame1(self, framer, callback):
        """Test ok frame."""
        faulty_frame = b"\x00\x04\x00\x00\x00\x05\x00\x03\x0a\x00\x04"
        with pytest.raises(ModbusIOException):
            framer.processIncomingFrame(faulty_frame, callback)
        callback.assert_not_called()
        framer.processIncomingFrame(self.good_frame, callback)
        callback.assert_called_once()
