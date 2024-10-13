"""Test server working as slave on a multidrop RS485 line."""
from unittest import mock

import pytest

from pymodbus.exceptions import ModbusIOException
from pymodbus.framer import FramerAscii, FramerRTU
from pymodbus.server.async_io import ServerDecoder


class TestMultidrop:
    """Test that server works on a multidrop line."""

    good_frame = b"\x02\x03\x00\x01\x00}\xd4\x18"

    @pytest.fixture(name="framer")
    def fixture_framer(self):
        """Prepare framer."""
        return FramerRTU(ServerDecoder(), [2])

    @pytest.fixture(name="callback")
    def fixture_callback(self):
        """Prepare dummy callback."""
        return mock.Mock()

    def test_ok_frame(self, framer):
        """Test ok frame."""
        serial_event = self.good_frame
        assert framer.processIncomingFrame(serial_event)

    def test_ok_2frame(self, framer):
        """Test ok frame."""
        serial_event = self.good_frame + self.good_frame
        assert framer.processIncomingFrame(serial_event)
        assert framer.processIncomingFrame(b'')

    def test_bad_crc(self, framer):
        """Test bad crc."""
        serial_event = b"\x02\x03\x00\x01\x00}\xd4\x19"  # Manually mangled crc
        assert not framer.processIncomingFrame(serial_event)

    def test_wrong_id(self, framer):
        """Test frame wrong id."""
        serial_event = b"\x01\x03\x00\x01\x00}\xd4+"  # Frame with good CRC but other id
        assert not framer.processIncomingFrame(serial_event)

    def test_big_split_response_frame_from_other_id(self, framer):
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
            assert not framer.processIncomingFrame(serial_event)

    def test_split_frame(self, framer):
        """Test split frame."""
        serial_events = [self.good_frame[:5], self.good_frame[5:]]
        assert not framer.processIncomingFrame(serial_events[0])
        assert framer.processIncomingFrame(serial_events[1])

    def test_complete_frame_trailing_data_without_id(self, framer):
        """Test trailing data."""
        garbage = b"\x05\x04\x03"  # without id
        serial_event = garbage + self.good_frame
        assert framer.processIncomingFrame(serial_event)

    def test_complete_frame_trailing_data_with_id(self, framer):
        """Test trailing data."""
        garbage = b"\x05\x04\x03\x02\x01\x00"  # with id
        serial_event = garbage + self.good_frame
        assert framer.processIncomingFrame(serial_event)

    def test_split_frame_trailing_data_with_id(self, framer):
        """Test split frame."""
        garbage = b"ABCDEF"
        serial_events = [garbage + self.good_frame[:5], self.good_frame[5:]]
        assert not framer.processIncomingFrame(serial_events[0])
        assert framer.processIncomingFrame(serial_events[1])

    @pytest.mark.parametrize(
        ("garbage"), [
            b"\x02\x90\x07",
            b"\x02\x10\x07",
            b"\x02\x10\x07\x10",
        ])
    def test_coincidental(self, garbage, framer):
        """Test conincidental."""
        serial_events = [garbage, self.good_frame[:5], self.good_frame[5:]]
        assert not framer.processIncomingFrame(serial_events[0])
        assert not framer.processIncomingFrame(serial_events[1])

    def test_wrapped_frame(self, framer):
        """Test wrapped frame."""
        garbage = b"\x05\x04\x03\x02\x01\x00"
        serial_event = garbage + self.good_frame + garbage
        # We probably should not respond in this case; in this case we've likely become desynchronized
        # i.e. this probably represents a case where a command came for us, but we didn't get
        # to the serial buffer in time (some other co-routine or perhaps a block on the USB bus)
        # and the master moved on and queried another device
        assert framer.processIncomingFrame(serial_event)

    def test_frame_with_trailing_data(self, framer):
        """Test trailing data."""
        garbage = b"\x05\x04\x03\x02\x01\x00"
        serial_event = self.good_frame + garbage
        # We should not respond in this case for identical reasons as test_wrapped_frame
        assert framer.processIncomingFrame(serial_event)

    def test_wrong_dev_id(self):
        """Test conincidental."""
        framer = FramerAscii(ServerDecoder(), [87])
        assert not framer.processIncomingFrame(b':0003007C00027F\r\n')

    def test_wrong_class(self):
        """Test conincidental."""

        def return_none(_data):
            """Return none."""
            return None

        framer = FramerAscii(ServerDecoder(), [])
        framer.decoder.decode = return_none
        with pytest.raises(ModbusIOException):
            framer.processIncomingFrame(b':1103007C00026E\r\n')

    def test_getFrameStart(self, framer):
        """Test getFrameStart."""
        framer_ok = b"\x02\x03\x00\x01\x00\x7d\xd4\x18"
        result = framer.processIncomingFrame(framer_ok)
        assert framer_ok[1:-2] == result.function_code.to_bytes(1,'big')+result.encode()

        framer_2ok = framer_ok + framer_ok
        assert framer.processIncomingFrame(framer_2ok)
        assert framer.processIncomingFrame(b'')
        assert not framer.databuffer

        framer.databuffer = framer_ok[:2]
        assert not framer.processIncomingFrame(b'')
        assert framer_ok[:2] == framer.databuffer

        framer.databuffer = framer_ok[:3]
        assert not framer.processIncomingFrame(b'')
        assert framer_ok[:3] == framer.databuffer

        framer_ok = b"\xF0\x03\x00\x01\x00}\xd4\x18"
        assert not framer.processIncomingFrame(framer_ok)
        assert framer.databuffer == framer_ok[-6:]
