"""Test framer."""

import pytest

from pymodbus.factory import ClientDecoder
from pymodbus.framer.tls import FramerTLS


class TestMFramerTLS:
    """Test module."""

    @staticmethod
    @pytest.fixture(name="frame")
    def prepare_frame():
        """Return message object."""
        return FramerTLS(ClientDecoder(), [0])


    @pytest.mark.parametrize(
        ("packet", "used_len"),
        [
            (b"\x03\x01\x14\xb5", 4),
            (b"\x84\x02", 2),
        ],
    )
    def test_decode(self, frame, packet, used_len,):
        """Test decode."""
        res_len, data = frame.decode(packet)
        assert res_len == used_len
        assert packet == data
        assert not frame.incoming_tid
        assert not frame.incoming_dev_id


    @pytest.mark.parametrize(
        ("data"),
        [
            (b'\x01\x05\x04\x00\x17'),
            (b'\x03\x07\x06\x00\x73'),
            (b'\x08\x00\x01'),
            (b'\x84\x01'),
        ],
    )
    def test_roundtrip(self, frame, data):
        """Test encode."""
        msg = frame.encode(data, 0, 0)
        res_len, res_data = frame.decode(msg)
        assert data == res_data
        assert not frame.incoming_dev_id
        assert not frame.incoming_tid
