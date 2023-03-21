"""Test server working as slave on a multidrop RS485 line."""
from unittest import mock

import pytest

from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.server.async_io import ServerDecoder


class TestMultidrop:
    """Test that server works on a multidrop line."""

    slaves = [2]

    good_frame = b"\x02\x03\x00\x01\x00}\xd4\x18"

    @pytest.fixture(name="framer")
    def _framer(self):
        """Prepare framer."""
        return ModbusRtuFramer(ServerDecoder())

    @pytest.fixture(name="callback")
    def _callback(self):
        """Prepare dummy callback."""
        return mock.Mock()

    def test_ok_frame(self, framer, callback):
        """Test ok frame."""
        serial_event = self.good_frame
        framer.processIncomingPacket(serial_event, callback, self.slaves)
        callback.assert_called_once()

    def test_bad_crc(self, framer, callback):
        """Test bad crc."""
        serial_event = b"\x02\x03\x00\x01\x00}\xd4\x19"  # Manually mangled crc
        framer.processIncomingPacket(serial_event, callback, self.slaves)
        callback.assert_not_called()

    def test_wrong_unit(self, framer, callback):
        """Test frame wrong unit"""
        serial_event = (
            b"\x01\x03\x00\x01\x00}\xd4+"  # Frame with good CRC but other unit id
        )
        framer.processIncomingPacket(serial_event, callback, self.slaves)
        callback.assert_not_called()

    def test_big_split_response_frame_from_other_unit(self, framer, callback):
        """Test split response."""
        # This is a single *response* from device id 1 after being queried for 125 holding register values
        # Because the response is so long it spans several serial events
        serial_events = [
            b"\x01\x03\xfa\xc4y\xc0\x00\xc4y\xc0\x00\xc4y\xc0\x00\xc4y\xc0\x00\xc4y\xc0\x00Dz\x00\x00C\x96\x00\x00",
            b"?\x05\x1e\xb8DH\x00\x00D\x96\x00\x00D\xfa\x00\x00DH\x00\x00D\x96\x00\x00D\xfa\x00\x00DH\x00",
            b"\x00D\x96\x00\x00D\xfa\x00\x00B\x96\x00\x00B\xb4\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            b"\x00\x00\x00\x00\x00\x00\x00N,",
        ]
        for serial_event in serial_events:
            framer.processIncomingPacket(serial_event, callback, self.slaves)
        callback.assert_not_called()

    def test_split_frame(self, framer, callback):
        """Test split frame."""
        serial_events = [self.good_frame[:5], self.good_frame[5:]]
        for serial_event in serial_events:
            framer.processIncomingPacket(serial_event, callback, self.slaves)
        callback.assert_called_once()

    @pytest.mark.skip
    def test_complete_frame_trailing_data_without_unit_id(self, framer, callback):
        """Test trailing data."""
        garbage = b"\x05\x04\x03"  # Note the garbage doesn't contain our unit id
        serial_event = garbage + self.good_frame
        framer.processIncomingPacket(serial_event, callback, self.slaves)
        callback.assert_called_once()

    @pytest.mark.skip
    def test_complete_frame_trailing_data_with_unit_id(self, framer, callback):
        """Test trailing data."""
        garbage = (
            b"\x05\x04\x03\x02\x01\x00"  # Note the garbage does contain our unit id
        )
        serial_event = garbage + self.good_frame
        framer.processIncomingPacket(serial_event, callback, self.slaves)
        callback.assert_called_once()

    @pytest.mark.skip
    def test_split_frame_trailing_data_with_unit_id(self, framer, callback):
        """Test split frame."""
        garbage = b"\x05\x04\x03\x02\x01\x00"
        serial_events = [garbage + self.good_frame[:5], self.good_frame[5:]]
        for serial_event in serial_events:
            framer.processIncomingPacket(serial_event, callback, self.slaves)
        callback.assert_called_once()

    def test_wrapped_frame(self, framer, callback):
        """Test wrapped frame."""
        garbage = b"\x05\x04\x03\x02\x01\x00"
        serial_event = garbage + self.good_frame + garbage
        framer.processIncomingPacket(serial_event, callback, self.slaves)

        # We probably should not respond in this case; in this case we've likely become desynchronized
        # i.e. this probably represents a case where a command came for us, but we didn't get
        # to the serial buffer in time (some other co-routine or perhaps a block on the USB bus)
        # and the master moved on and queried another device
        callback.assert_not_called()

    @pytest.mark.skip
    def test_frame_with_trailing_data(self, framer, callback):
        """Test trailing data."""
        garbage = b"\x05\x04\x03\x02\x01\x00"
        serial_event = self.good_frame + garbage
        framer.processIncomingPacket(serial_event, callback, self.slaves)

        # We should not respond in this case for identical reasons as test_wrapped_frame
        callback.assert_not_called()
