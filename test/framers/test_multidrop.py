"""Test server working as slave on a multidrop RS485 line."""
from unittest import mock

import pytest

from pymodbus.framer import FramerRTU, FramerAscii
from pymodbus.server.async_io import ServerDecoder
from pymodbus.exceptions import ModbusIOException


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

    def test_ok_frame(self, framer, callback):
        """Test ok frame."""
        serial_event = self.good_frame
        framer.processIncomingPacket(serial_event, callback)
        callback.assert_called_once()

    def test_ok_2frame(self, framer, callback):
        """Test ok frame."""
        serial_event = self.good_frame + self.good_frame
        framer.processIncomingPacket(serial_event, callback)
        assert callback.call_count == 2

    def test_bad_crc(self, framer, callback):
        """Test bad crc."""
        serial_event = b"\x02\x03\x00\x01\x00}\xd4\x19"  # Manually mangled crc
        framer.processIncomingPacket(serial_event, callback)
        callback.assert_not_called()

    def test_wrong_id(self, framer, callback):
        """Test frame wrong id."""
        serial_event = b"\x01\x03\x00\x01\x00}\xd4+"  # Frame with good CRC but other id
        framer.processIncomingPacket(serial_event, callback)
        callback.assert_not_called()

    def test_big_split_response_frame_from_other_id(self, framer, callback):
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
            framer.processIncomingPacket(serial_event, callback)
        callback.assert_not_called()

    def test_split_frame(self, framer, callback):
        """Test split frame."""
        serial_events = [self.good_frame[:5], self.good_frame[5:]]
        for serial_event in serial_events:
            framer.processIncomingPacket(serial_event, callback)
        callback.assert_called_once()

    def test_complete_frame_trailing_data_without_id(self, framer, callback):
        """Test trailing data."""
        garbage = b"\x05\x04\x03"  # without id
        serial_event = garbage + self.good_frame
        framer.processIncomingPacket(serial_event, callback)
        callback.assert_called_once()

    def test_complete_frame_trailing_data_with_id(self, framer, callback):
        """Test trailing data."""
        garbage = b"\x05\x04\x03\x02\x01\x00"  # with id
        serial_event = garbage + self.good_frame
        framer.processIncomingPacket(serial_event, callback)
        callback.assert_called_once()

    def test_split_frame_trailing_data_with_id(self, framer, callback):
        """Test split frame."""
        garbage = b"ABCDEF"
        serial_events = [garbage + self.good_frame[:5], self.good_frame[5:]]
        for serial_event in serial_events:
            framer.processIncomingPacket(serial_event, callback)
        callback.assert_called_once()

    @pytest.mark.parametrize(
        ("garbage"), [
            b"\x02\x90\x07",
            b"\x02\x10\x07",
            b"\x02\x10\x07\x10",
        ])
    def test_coincidental(self, garbage, framer, callback):
        """Test conincidental."""
        serial_events = [garbage, self.good_frame[:5], self.good_frame[5:]]
        for serial_event in serial_events:
            framer.processIncomingPacket(serial_event, callback)
        callback.assert_called_once()

    def test_wrapped_frame(self, framer, callback):
        """Test wrapped frame."""
        garbage = b"\x05\x04\x03\x02\x01\x00"
        serial_event = garbage + self.good_frame + garbage
        framer.processIncomingPacket(serial_event, callback)

        # We probably should not respond in this case; in this case we've likely become desynchronized
        # i.e. this probably represents a case where a command came for us, but we didn't get
        # to the serial buffer in time (some other co-routine or perhaps a block on the USB bus)
        # and the master moved on and queried another device
        callback.assert_called_once()

    def test_frame_with_trailing_data(self, framer, callback):
        """Test trailing data."""
        garbage = b"\x05\x04\x03\x02\x01\x00"
        serial_event = self.good_frame + garbage
        framer.processIncomingPacket(serial_event, callback)

        # We should not respond in this case for identical reasons as test_wrapped_frame
        callback.assert_called_once()

    def test_wrong_dev_id(self, callback):
        """Test conincidental."""
        framer = FramerAscii(ServerDecoder(), [87])
        framer.processIncomingPacket(b':0003007C00027F\r\n', callback)
        callback.assert_not_called()

    def test_wrong_tid(self, callback):
        """Test conincidental."""
        framer = FramerAscii(ServerDecoder(), [])
        framer.processIncomingPacket(b':1103007C00026E\r\n', callback, tid=117)
        callback.assert_not_called()

    def test_wrong_class(self, callback):
        """Test conincidental."""

        def return_none(_data):
            """Return none."""
            return None
        
        framer = FramerAscii(ServerDecoder(), [])
        framer.decoder.decode = return_none
        with pytest.raises(ModbusIOException):
            framer.processIncomingPacket(b':1103007C00026E\r\n', callback)
        callback.assert_not_called()

    @pytest.mark.skip
    def test_getFrameStart(self, framer):  # pragma: no cover
        """Test getFrameStart."""
        result = None
        count = 0
        def test_callback(data):
            """Check callback."""
            nonlocal result, count
            count += 1
            result = data.function_code.to_bytes(1,'big')+data.encode()

        framer_ok = b"\x02\x03\x00\x01\x00\x7d\xd4\x18"
        framer.processIncomingPacket(framer_ok, test_callback)
        assert framer_ok[1:-2] == result

        count = 0
        framer_2ok = framer_ok + framer_ok
        framer.processIncomingPacket(framer_2ok, test_callback)
        assert count == 2
        assert not framer._buffer  # pylint: disable=protected-access

        framer._buffer = framer_ok[:2]  # pylint: disable=protected-access
        framer.processIncomingPacket(b'', test_callback)
        assert framer_ok[:2] == framer._buffer  # pylint: disable=protected-access

        framer._buffer = framer_ok[:3]  # pylint: disable=protected-access
        framer.processIncomingPacket(b'', test_callback)
        assert framer_ok[:3] == framer._buffer  # pylint: disable=protected-access

        framer_ok = b"\xF0\x03\x00\x01\x00}\xd4\x18"
        framer.processIncomingPacket(framer_ok, test_callback)
        assert framer._buffer == framer_ok[-3:]  # pylint: disable=protected-access
