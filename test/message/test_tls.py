"""Test transport."""

import pytest

from pymodbus.message.tls import MessageTLS


class TestMessageSocket:
    """Test message module."""

    @staticmethod
    @pytest.fixture(name="frame")
    def prepare_frame():
        """Return message object."""
        return MessageTLS()


    @pytest.mark.parametrize(
        ("packet", "used_len"),
        [
            (b"\x03\x01\x14\xb5", 4),
            (b"\x84\x02", 2),
        ],
    )
    def test_decode(self, frame, packet, used_len,):
        """Test decode."""
        res_len, tid, dev_id, data = frame.decode(packet)
        assert res_len == used_len
        assert packet == data
        assert not tid
        assert not dev_id


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
        res_len, res_tid, res_id, res_data = frame.decode(msg)
        assert data == res_data
        assert not res_id
        assert not res_tid
