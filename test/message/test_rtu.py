"""Test transport."""
import pytest

from pymodbus.message.rtu import MessageRTU


class TestMessageRTU:
    """Test message module."""

    @staticmethod
    @pytest.fixture(name="frame")
    def prepare_frame():
        """Return message object."""
        return MessageRTU([1], False)


    @pytest.mark.parametrize(
        ("data", "dev_id", "res_msg"),
        [
            (b'\x01\x01\x00', 2, b'\x02\x01\x01\x00\x51\xcc'),
            (b'\x03\x06\xAE\x41\x56\x52\x43\x40', 17, b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD'),
            (b'\x01\x03\x01\x00\x0a', 1, b'\x01\x01\x03\x01\x00\x0a\xed\x89'),
        ],
    )
    def xtest_roundtrip(self, frame, data, dev_id, res_msg):
        """Test encode."""
        msg = frame.encode(data, dev_id, 0)
        res_len, _, res_id, res_data = frame.decode(msg)
        assert data == res_data
        assert dev_id == res_id
        assert res_len == len(res_msg)
