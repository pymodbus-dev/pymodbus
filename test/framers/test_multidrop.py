"""Test server working as slave on a multidrop RS485 line."""
from unittest import mock

import pytest

from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu import ClientDecoder, ServerDecoder
from pymodbus.framer import FramerAscii, FramerRTU


class TestMultidrop:
    """Test that server works on a multidrop line."""

    good_frame = b"\x02\x03\x00\x01\x00}\xd4\x18"

    @pytest.fixture(name="framer")
    def fixture_framer(self):
        """Prepare framer."""
        return FramerRTU(ServerDecoder())

    @pytest.fixture(name="callback")
    def fixture_callback(self):
        """Prepare dummy callback."""
        return mock.Mock()

    def test_ok_frame(self, framer):
        """Test ok frame."""
        serial_event = self.good_frame
        used_len, pdu = framer.processIncomingFrame(serial_event)
        assert pdu
        assert used_len == len(serial_event)

    def test_ok_2frame(self, framer):
        """Test ok frame."""
        serial_event = self.good_frame + self.good_frame
        used_len, pdu = framer.processIncomingFrame(serial_event)
        assert pdu
        assert used_len == len(self.good_frame)
        used_len, pdu = framer.processIncomingFrame(serial_event[used_len:])
        assert pdu
        assert used_len == len(self.good_frame)

    def test_bad_crc(self, framer):
        """Test bad crc."""
        serial_event = b"\x02\x03\x00\x01\x00}\xd4\x19"  # Manually mangled crc
        _, pdu = framer.processIncomingFrame(serial_event)
        assert not pdu

    def test_big_split_response_frame_from_other_id(self, framer):
        """Test split response."""
        # This is a single *response* from device id 1 after being queried for 125 holding register values
        # Because the response is so long it spans several serial events
        framer = FramerRTU(ClientDecoder())
        serial_events = [
            b'\x01\x03\xfa\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00',
            b'\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00',
            b'\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00',
            b'\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00',
            b'\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00',
            b'\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00',
            b'\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00',
            b'\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00',
            b'\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00',
            b'\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00',
            b'\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00',
        ]
        final = b'\x11\x00\x11\x00\x11\x00\x11\x00\x11\x00\x11\xa5\x8f'
        data = b''
        for serial_event in serial_events:
            data += serial_event
            used_len, pdu = framer.processIncomingFrame(data)
            assert not pdu
            assert not used_len
        used_len, pdu = framer.processIncomingFrame(data + final)
        assert pdu
        assert used_len == len(data + final)

    def test_split_frame(self, framer):
        """Test split frame."""
        used_len, pdu = framer.processIncomingFrame(self.good_frame[:5])
        assert not pdu
        assert not used_len
        used_len, pdu = framer.processIncomingFrame(self.good_frame)
        assert pdu
        assert used_len == len(self.good_frame)

    def test_complete_frame_trailing_data_without_id(self, framer):
        """Test trailing data."""
        garbage = b"\x05\x04\x03"  # without id
        serial_event = garbage + self.good_frame
        used_len, pdu = framer.processIncomingFrame(serial_event)
        assert pdu
        assert used_len == len(serial_event)

    def test_complete_frame_trailing_data_with_id(self, framer):
        """Test trailing data."""
        garbage = b"\x05\x04\x03\x02\x01\x00"  # with id
        serial_event = garbage + self.good_frame
        used_len, pdu = framer.processIncomingFrame(serial_event)
        assert pdu
        assert used_len == len(serial_event)

    def test_split_frame_trailing_data_with_id(self, framer):
        """Test split frame."""
        garbage = b"ABCDEF"
        serial_events = garbage + self.good_frame
        used_len, pdu = framer.processIncomingFrame(serial_events[:11])
        assert not pdu
        serial_events = serial_events[used_len:]
        used_len, pdu = framer.processIncomingFrame(serial_events)
        assert pdu
        assert used_len == len(serial_events)

    @pytest.mark.parametrize(
        ("garbage"), [
            b"\x02\x90\x07",
            b"\x02\x10\x07",
            b"\x02\x10\x07\x10",
        ])
    def test_coincidental(self, garbage, framer):
        """Test conincidental."""
        serial_events = garbage + self.good_frame
        used_len, pdu = framer.processIncomingFrame(serial_events[:5])
        assert not pdu
        serial_events = serial_events[used_len:]
        used_len, pdu = framer.processIncomingFrame(serial_events)
        assert pdu
        assert used_len == len(serial_events)

    def test_wrapped_frame(self, framer):
        """Test wrapped frame."""
        garbage = b"\x05\x04\x03\x02\x01\x00"
        serial_event = garbage + self.good_frame + garbage
        # We probably should not respond in this case; in this case we've likely become desynchronized
        # i.e. this probably represents a case where a command came for us, but we didn't get
        # to the serial buffer in time (some other co-routine or perhaps a block on the USB bus)
        # and the master moved on and queried another device
        _, pdu = framer.processIncomingFrame(serial_event)
        assert pdu

    def test_frame_with_trailing_data(self, framer):
        """Test trailing data."""
        garbage = b"\x05\x04\x03\x02\x01\x00"
        serial_event = self.good_frame + garbage
        # We should not respond in this case for identical reasons as test_wrapped_frame
        _, pdu = framer.processIncomingFrame(serial_event)
        assert pdu

    def test_wrong_class(self):
        """Test conincidental."""

        def return_none(_data):
            """Return none."""
            return None

        framer = FramerAscii(ServerDecoder())
        framer.decoder.decode = return_none
        with pytest.raises(ModbusIOException):
            framer.processIncomingFrame(b':1103007C00026E\r\n')

    def test_getFrameStart(self, framer):
        """Test getFrameStart."""
        framer_ok = b"\x02\x03\x00\x01\x00\x7d\xd4\x18"
        _, pdu = framer.processIncomingFrame(framer_ok)
        assert framer_ok[1:-2] == pdu.function_code.to_bytes(1,'big')+pdu.encode()

        framer_2ok = framer_ok + framer_ok
        used_len, pdu = framer.processIncomingFrame(framer_2ok)
        assert pdu
        framer_2ok = framer_2ok[used_len:]
        used_len, pdu = framer.processIncomingFrame(framer_2ok)
        assert pdu
        assert used_len == len(framer_2ok)
