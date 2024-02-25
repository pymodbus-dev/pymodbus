"""Test transport."""

import pytest

from pymodbus.message.socket import MessageSocket


class TestMessageSocket:
    """Test message module."""

    @staticmethod
    @pytest.fixture(name="frame")
    def prepare_frame():
        """Return message object."""
        return MessageSocket([1], False)


    @pytest.mark.parametrize(
        ("packet", "used_len", "res_id", "res_tid", "res"),
        [
            (b"\x00\x09\x00\x00\x00\x05\x01\x03\x01\x14\xb5", 11, 1, 9, b'\x03\x01\x14\xb5'),
            (b"\x00\x02\x00\x00\x00\x03\x07\x84\x02", 9, 7, 2, b'\x84\x02'),
            (b"\x00\x02\x00", 0, 0, 0, b''),  # very short frame
            (b"\x00\x09\x00\x00\x00\x05\x01\x03\x01", 0, 0, 0, b''),  # short frame
            (b"\x00\x02\x00\x00\x00\x03\x07\x84", 0, 0, 0, b''),  # short frame -1 byte
        ],
    )
    def test_decode(self, frame, packet, used_len, res_id, res_tid, res):
        """Test decode."""
        res_len, tid, dev_id, data = frame.decode(packet)
        assert res_len == used_len
        assert res == data
        assert res_tid == tid
        assert dev_id == res_id

    @pytest.mark.parametrize(
        ("data", "dev_id", "res_msg"),
        [
            (b'\x01\x05\x04\x00\x17', 1, b':010105040017DE\r\n'),
            (b'\x03\x07\x06\x00\x73', 2, b':0203070600737B\r\n'),
            (b'\x08\x00\x01', 3, b':03080001F4\r\n'),
        ],
    )
    def xtest_encode(self, frame, data, dev_id, res_msg):
        """Test encode."""
        msg = frame.encode(data, dev_id, 0)
        assert res_msg == msg
        assert dev_id == int(msg[1:3], 16)

    @pytest.mark.parametrize(
        ("data", "dev_id", "res_msg"),
        [
            # (b"\x00\x01\x00\x00\x00\x0b\x01\x03\x08\x00\xb5\x12\x2f\x37\x21\x00\x03", 1, b'\x08\x00\xb5\x12\x2f\x37\x21\x00\x03'),
            # (b'\x03\x07\x06\x00\x73', 2, b':0203070600737D\r\n'),
            # (b'\x08\x00\x01', 3, b':03080001F7\r\n'),
        ],
    )
    def xtest_roundtrip(self, frame, data, dev_id, res_msg):
        """Test encode."""
        msg = frame.encode(data, dev_id, 0)
        res_len, _, res_id, res_data = frame.decode(msg)
        assert data == res_data
        assert dev_id == res_id
        assert res_len == len(res_msg)
