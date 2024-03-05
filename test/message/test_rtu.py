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

    def test_crc16_table(self):
        """Test the crc16 table is prefilled."""
        assert len(MessageRTU.crc16_table) == 256
        assert isinstance(MessageRTU.crc16_table[0], int)
        assert isinstance(MessageRTU.crc16_table[255], int)

    def test_roundtrip_CRC(self):
        """Test combined compute/check CRC."""
        data = b'\x12\x34\x23\x45\x34\x56\x45\x67'
        assert MessageRTU.compute_CRC(data) == 0xE2DB
        assert MessageRTU.check_CRC(data, 0xE2DB)

    #   b"\x02\x01\x01\x00Q\xcc"
    #   b"\x01\x01\x03\x01\x00\n\xed\x89"
    #   b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x43"
    #   b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD"

    #   b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\x11\x03" # good frame + part of next frame

    #   b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAC"  # invalid frame CRC
    #   b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAC"  # bad crc
    #   b"\x61\x62\x00\x01\x00\n\xec\x1c"  # bad function code
    #   b"\x01\x03\x03\x01\x00\n\x94\x49" # Not ok

    # test frame ready
    # (b"", False),
    # (b"\x11", False),
    # (b"\x11\x03", False),
    # (b"\x11\x03\x06", False),
    # (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49", False),
    # (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD", True),
    # (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\xAB\xCD", True),


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
    def xtest_decode(self, frame, packet, used_len, res_id, res):
        """Test decode."""
        res_len, tid, dev_id, data = frame.decode(packet)
        assert res_len == used_len
        assert data == res
        assert not tid
        assert dev_id == res_id

    @pytest.mark.parametrize(
        ("data", "dev_id", "res_msg"),
        [
            (b'\x01\x01\x00', 2, b'\x02\x01\x01\x00\x51\xcc'),
            (b'\x03\x06\xAE\x41\x56\x52\x43\x40', 17, b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD'),
            (b'\x01\x03\x01\x00\x0a', 1, b'\x01\x01\x03\x01\x00\x0a\xed\x89'),
        ],
    )
    def test_encode(self, frame, data, dev_id, res_msg):
        """Test encode."""
        msg = frame.encode(data, dev_id, 0)
        assert res_msg == msg
        assert dev_id == int(msg[0])

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
