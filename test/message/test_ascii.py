"""Test transport."""
import pytest

from pymodbus.message.ascii import MessageAscii


class TestMessageAscii:
    """Test message module."""

    @staticmethod
    @pytest.fixture(name="frame")
    def prepare_frame():
        """Return message object."""
        return MessageAscii([1], False)


    def test_roundtrip_LRC(self):
        """Test combined compute/check LRC."""
        data = b'\x12\x34\x23\x45\x34\x56\x45\x67'
        assert MessageAscii.compute_LRC(data) == 0x1c
        assert MessageAscii.check_LRC(data, 0x1C)

    @pytest.mark.parametrize(
        ("packet", "used_len", "res_id", "res"),
        [
            (b':010100010001FC\r\n', 17, 1, b'\x01\x00\x01\x00\x01'),
            (b':00010001000AF4\r\n', 17, 0, b'\x01\x00\x01\x00\x0a'),
            (b':01010001000AF3\r\n', 17, 1, b'\x01\x00\x01\x00\x0a'),
            (b':61620001000A32\r\n', 17, 97, b'\x62\x00\x01\x00\x0a'),
            (b':01270001000ACD\r\n', 17, 1, b'\x27\x00\x01\x00\x0a'),
            (b':010100', 0, 0, b''), # short frame
            (b':00010001000AF4', 0, 0, b''),
            (b'abc:00010001000AF4', 3, 0, b''), # garble before frame
            (b'abc00010001000AF4', 17, 0, b''), # only garble
            (b':01010001000A00\r\n', 17, 0, b''),
        ],
    )
    def test_decode(self, frame, packet, used_len, res_id, res):
        """Test decode."""
        res_len, tid, dev_id, data = frame.decode(packet)
        assert res_len == used_len
        assert data == res
        assert not tid
        assert dev_id == res_id

    @pytest.mark.parametrize(
        ("data", "dev_id", "res_msg"),
        [
            (b'\x01\x05\x04\x00\x17', 1, b':010105040017DE\r\n'),
            (b'\x03\x07\x06\x00\x73', 2, b':0203070600737B\r\n'),
            (b'\x08\x00\x01', 3, b':03080001F4\r\n'),
            (b'\x84\x01', 2, b':02840179\r\n'),
        ],
    )
    def test_encode(self, frame, data, dev_id, res_msg):
        """Test encode."""
        msg = frame.encode(data, dev_id, 0)
        assert res_msg == msg
        assert dev_id == int(msg[1:3], 16)

    @pytest.mark.parametrize(
        ("data", "dev_id", "res_msg"),
        [
            (b'\x01\x05\x04\x00\x17', 1, b':010105040017DF\r\n'),
            (b'\x03\x07\x06\x00\x73', 2, b':0203070600737D\r\n'),
            (b'\x08\x00\x01', 3, b':03080001F7\r\n'),
            (b'\x84\x01', 2, b':02840179\r\n'),
        ],
    )
    def test_roundtrip(self, frame, data, dev_id, res_msg):
        """Test encode."""
        msg = frame.encode(data, dev_id, 0)
        res_len, _, res_id, res_data = frame.decode(msg)
        assert data == res_data
        assert dev_id == res_id
        assert res_len == len(res_msg)
