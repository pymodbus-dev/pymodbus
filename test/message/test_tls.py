"""Test transport."""

import pytest

from pymodbus.message.tls import MessageTLS


class TestMessageSocket:
    """Test message module."""

    @staticmethod
    @pytest.fixture(name="frame")
    def prepare_frame():
        """Return message object."""
        return MessageTLS([1], False)


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
    def xtest_decode(self, frame, packet, used_len, res_id, res_tid, res):
        """Test decode."""
        res_len, tid, dev_id, data = frame.decode(packet)
        assert res_len == used_len
        assert res == data
        assert res_tid == tid
        assert dev_id == res_id

    @pytest.mark.parametrize(
        ("data", "dev_id", "tid", "res_msg"),
        [
            (b'\x01\x05\x04\x00\x17', 7, 5, b'\x00\x05\x00\x00\x00\x06\x07\x01\x05\x04\x00\x17'),
            (b'\x03\x07\x06\x00\x73', 2, 9, b'\x00\x09\x00\x00\x00\x06\x02\x03\x07\x06\x00\x73'),
            (b'\x08\x00\x01', 3, 6, b'\x00\x06\x00\x00\x00\x04\x03\x08\x00\x01'),
            (b'\x84\x01', 4, 8, b'\x00\x08\x00\x00\x00\x03\x04\x84\x01'),
        ],
    )
    def xtest_encode(self, frame, data, dev_id, tid, res_msg):
        """Test encode."""
        msg = frame.encode(data, dev_id, tid)
        assert res_msg == msg
        assert dev_id == int(msg[6])
        assert tid == int.from_bytes(msg[0:2], 'big')

    @pytest.mark.parametrize(
        ("data", "dev_id", "tid", "res_msg"),
        [
            (b'\x01\x05\x04\x00\x17', 7, 5, b'\x00\x05\x00\x00\x00\x06\x07\x01\x05\x04\x00\x17'),
            (b'\x03\x07\x06\x00\x73', 2, 9, b'\x00\x09\x00\x00\x00\x06\x02\x03\x07\x06\x00\x73'),
            (b'\x08\x00\x01', 3, 6, b'\x00\x06\x00\x00\x00\x04\x03\x08\x00\x01'),
            (b'\x84\x01', 4, 8, b'\x00\x08\x00\x00\x00\x03\x04\x84\x01'),
        ],
    )
    def xtest_roundtrip(self, frame, data, dev_id, tid, res_msg):
        """Test encode."""
        msg = frame.encode(data, dev_id, tid)
        res_len, res_tid, res_id, res_data = frame.decode(msg)
        assert data == res_data
        assert dev_id == res_id
        assert tid == res_tid
        assert res_len == len(res_msg)
