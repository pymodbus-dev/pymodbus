"""Test framer."""
from unittest import mock

import pytest

from pymodbus.framer import (
    FramerAscii,
    FramerBase,
    FramerRTU,
    FramerSocket,
    FramerTLS,
    FramerType,
)
from pymodbus.pdu import DecodePDU, ModbusPDU
from test.framer.generator import set_calls


class TestFramer:
    """Test module."""

    def test_setup(self, entry, is_server):
        """Test setup."""
        assert entry == FramerType.RTU
        assert not is_server
        set_calls()

    def test_base(self):
        """Test FramerBase."""
        framer = FramerBase(DecodePDU(False))
        framer.decode(b'')
        framer.encode(b'', 0, 0)
        framer.encode(b'', 2, 0)

    @pytest.mark.parametrize(("entry"), list(FramerType))
    async def test_framer_init(self, test_framer):
        """Test framer type."""
        assert test_framer

    @pytest.mark.parametrize(
        ("func", "test_compare", "expect"),
        [(FramerAscii.check_LRC, 0x1c, True),
         (FramerAscii.check_LRC, 0x0c, False),
         (FramerAscii.compute_LRC, None, 0x1c),
         (FramerRTU.check_CRC, 0xE2DB, True),
         (FramerRTU.check_CRC, 0xDBE2, False),
         (FramerRTU.compute_CRC, None, 0xE2DB),
        ]
    )
    def test_LRC_CRC(self, func, test_compare, expect):
        """Test check_LRC."""
        data = b'\x12\x34\x23\x45\x34\x56\x45\x67'
        assert expect == func(data, test_compare) if test_compare else func(data)

    def test_roundtrip_LRC(self):
        """Test combined compute/check LRC."""
        data = b'\x12\x34\x23\x45\x34\x56\x45\x67'
        assert FramerAscii.compute_LRC(data) == 0x1c
        assert FramerAscii.check_LRC(data, 0x1C)

    def test_crc16_table(self):
        """Test the crc16 table is prefilled."""
        assert len(FramerRTU.crc16_table) == 256
        assert isinstance(FramerRTU.crc16_table[0], int)
        assert isinstance(FramerRTU.crc16_table[255], int)

    def test_roundtrip_CRC(self):
        """Test combined compute/check CRC."""
        data = b'\x12\x34\x23\x45\x34\x56\x45\x67'
        assert FramerRTU.compute_CRC(data) == 0xE2DB
        assert FramerRTU.check_CRC(data, 0xE2DB)

    async def test_handleFrame2(self):
        """Test handleFrame."""
        test_framer = FramerRTU(DecodePDU(True))
        msg = b"\xfe\x04\x00\x03\x00\x01\xd5\xc5\x00"
        used_len, pdu = test_framer.handleFrame(msg, 0, 0)
        assert used_len == len(msg)
        assert pdu


class TestFramerType:
    """Test classes."""

    @pytest.mark.parametrize(
        ("frame", "frame_expected"),
        [
            (FramerAscii, [
                b':0003007C00027F\r\n',
                b':000304008D008EDE\r\n',
                b':0083027B\r\n',
                b':1103007C00026E\r\n',
                b':110304008D008ECD\r\n',
                b':1183026A\r\n',
                b':FF03007C000280\r\n',
                b':FF0304008D008EDF\r\n',
                b':FF83027C\r\n',
                b':0003007C00027F\r\n',
                b':000304008D008EDE\r\n',
                b':0083027B\r\n',
                b':1103007C00026E\r\n',
                b':110304008D008ECD\r\n',
                b':1183026A\r\n',
                b':FF03007C000280\r\n',
                b':FF0304008D008EDF\r\n',
                b':FF83027C\r\n',
                b':0003007C00027F\r\n',
                b':000304008D008EDE\r\n',
                b':0083027B\r\n',
                b':1103007C00026E\r\n',
                b':110304008D008ECD\r\n',
                b':1183026A\r\n',
                b':FF03007C000280\r\n',
                b':FF0304008D008EDF\r\n',
                b':FF83027C\r\n',
            ]),
            (FramerRTU, [
                b'\x00\x03\x00\x7c\x00\x02\x04\x02',
                b'\x00\x03\x04\x00\x8d\x00\x8e\xfa\xbc',
                b'\x00\x83\x02\x91\x31',
                b'\x11\x03\x00\x7c\x00\x02\x07\x43',
                b'\x11\x03\x04\x00\x8d\x00\x8e\xfb\xbd',
                b'\x11\x83\x02\xc1\x34',
                b'\xff\x03\x00\x7c\x00\x02\x10\x0d',
                b'\xff\x03\x04\x00\x8d\x00\x8e\xf5\xb3',
                b'\xff\x83\x02\xa1\x01',
                b'\x00\x03\x00\x7c\x00\x02\x04\x02',
                b'\x00\x03\x04\x00\x8d\x00\x8e\xfa\xbc',
                b'\x00\x83\x02\x91\x31',
                b'\x11\x03\x00\x7c\x00\x02\x07\x43',
                b'\x11\x03\x04\x00\x8d\x00\x8e\xfb\xbd',
                b'\x11\x83\x02\xc1\x34',
                b'\xff\x03\x00\x7c\x00\x02\x10\x0d',
                b'\xff\x03\x04\x00\x8d\x00\x8e\xf5\xb3',
                b'\xff\x83\x02\xa1\x01',
                b'\x00\x03\x00\x7c\x00\x02\x04\x02',
                b'\x00\x03\x04\x00\x8d\x00\x8e\xfa\xbc',
                b'\x00\x83\x02\x91\x31',
                b'\x11\x03\x00\x7c\x00\x02\x07\x43',
                b'\x11\x03\x04\x00\x8d\x00\x8e\xfb\xbd',
                b'\x11\x83\x02\xc1\x34',
                b'\xff\x03\x00\x7c\x00\x02\x10\x0d',
                b'\xff\x03\x04\x00\x8d\x00\x8e\xf5\xb3',
                b'\xff\x83\x02\xa1\x01',
            ]),
            (FramerSocket, [
                b'\x00\x00\x00\x00\x00\x06\x00\x03\x00\x7c\x00\x02',
                b'\x00\x00\x00\x00\x00\x07\x00\x03\x04\x00\x8d\x00\x8e',
                b'\x00\x00\x00\x00\x00\x03\x00\x83\x02',
                b'\x00\x00\x00\x00\x00\x06\x11\x03\x00\x7c\x00\x02',
                b'\x00\x00\x00\x00\x00\x07\x11\x03\x04\x00\x8d\x00\x8e',
                b'\x00\x00\x00\x00\x00\x03\x11\x83\x02',
                b'\x00\x00\x00\x00\x00\x06\xff\x03\x00\x7c\x00\x02',
                b'\x00\x00\x00\x00\x00\x07\xff\x03\x04\x00\x8d\x00\x8e',
                b'\x00\x00\x00\x00\x00\x03\xff\x83\x02',
                b'\x0c\x05\x00\x00\x00\x06\x00\x03\x00\x7c\x00\x02',
                b'\x0c\x05\x00\x00\x00\x07\x00\x03\x04\x00\x8d\x00\x8e',
                b'\x0c\x05\x00\x00\x00\x03\x00\x83\x02',
                b'\x0c\x05\x00\x00\x00\x06\x11\x03\x00\x7c\x00\x02',
                b'\x0c\x05\x00\x00\x00\x07\x11\x03\x04\x00\x8d\x00\x8e',
                b'\x0c\x05\x00\x00\x00\x03\x11\x83\x02',
                b'\x0c\x05\x00\x00\x00\x06\xff\x03\x00\x7c\x00\x02',
                b'\x0c\x05\x00\x00\x00\x07\xff\x03\x04\x00\x8d\x00\x8e',
                b'\x0c\x05\x00\x00\x00\x03\xff\x83\x02',
            ]),
            (FramerTLS, [
                b'\x00\x00\x00\x00\x00\x06\x00\x03\x00\x7c\x00\x02',
                b'\x00\x00\x00\x00\x00\x07\x00\x03\x04\x00\x8d\x00\x8e',
                b'\x00\x00\x00\x00\x00\x03\x00\x83\x02',
                b'\x00\x00\x00\x00\x00\x06\x11\x03\x00\x7c\x00\x02',
                b'\x00\x00\x00\x00\x00\x07\x11\x03\x04\x00\x8d\x00\x8e',
                b'\x00\x00\x00\x00\x00\x03\x11\x83\x02',
                b'\x00\x00\x00\x00\x00\x06\xff\x03\x00\x7c\x00\x02',
                b'\x00\x00\x00\x00\x00\x07\xff\x03\x04\x00\x8d\x00\x8e',
                b'\x00\x00\x00\x00\x00\x03\xff\x83\x02',
                b'\x0c\x05\x00\x00\x00\x06\x00\x03\x00\x7c\x00\x02',
                b'\x0c\x05\x00\x00\x00\x07\x00\x03\x04\x00\x8d\x00\x8e',
                b'\x0c\x05\x00\x00\x00\x03\x00\x83\x02',
                b'\x0c\x05\x00\x00\x00\x06\x11\x03\x00\x7c\x00\x02',
                b'\x0c\x05\x00\x00\x00\x07\x11\x03\x04\x00\x8d\x00\x8e',
                b'\x0c\x05\x00\x00\x00\x03\x11\x83\x02',
                b'\x0c\x05\x00\x00\x00\x06\xff\x03\x00\x7c\x00\x02',
                b'\x0c\x05\x00\x00\x00\x07\xff\x03\x04\x00\x8d\x00\x8e',
                b'\x0c\x05\x00\x00\x00\x03\xff\x83\x02',
            ]),
        ]
    )
    @pytest.mark.parametrize(
        ("inx1", "data"),
        [
            (0, b"\x03\x00\x7c\x00\x02",),  # Request
            (1, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (2, b'\x83\x02',),  # Exception
        ]
    )
    @pytest.mark.parametrize(
        ("inx2", "dev_id"),
        [
            (0, 0),
            (3, 17),
            (6, 255),
        ]
    )
    @pytest.mark.parametrize(
        ("inx3", "tr_id"),
        [
            (0, 0),
            (9, 3077),
        ]
    )
    def test_encode_type(self, frame, frame_expected, data, dev_id, tr_id, inx1, inx2, inx3):
        """Test encode method."""
        if frame == FramerTLS and dev_id + tr_id:
            return
        frame_obj = frame(DecodePDU(False))
        expected = frame_expected[inx1 + inx2 + inx3]
        encoded_data = frame_obj.encode(data, dev_id, tr_id)
        assert encoded_data == expected

    @pytest.mark.parametrize(
        ("entry", "is_server", "data", "dev_id", "tr_id", "expected"),
        [
            (FramerType.ASCII, True, b':0003007C00027F\r\n', 0, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.ASCII, False, b':000304008D008EDE\r\n', 0, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.ASCII, False, b':0083027B\r\n', 0, 0, b'\x83\x02',),  # Exception
            (FramerType.ASCII, True, b':1103007C00026E\r\n', 17, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.ASCII, False, b':110304008D008ECD\r\n', 17, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.ASCII, False, b':1183026A\r\n', 17, 0, b'\x83\x02',),  # Exception
            (FramerType.ASCII, True, b':FF03007C000280\r\n', 255, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.ASCII, False, b':FF0304008D008EDF\r\n', 255, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.ASCII, False, b':FF83027C\r\n', 255, 0, b'\x83\x02',),  # Exception
            (FramerType.RTU, True, b'\x00\x03\x00\x7c\x00\x02\x04\x02', 0, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.RTU, False, b'\x00\x03\x04\x00\x8d\x00\x8e\xfa\xbc', 0, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.RTU, False, b'\x00\x83\x02\x91\x31', 0, 0, b'\x83\x02',),  # Exception
            (FramerType.RTU, True, b'\x11\x03\x00\x7c\x00\x02\x07\x43', 17, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.RTU, False, b'\x11\x03\x04\x00\x8d\x00\x8e\xfb\xbd', 17, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.RTU, False, b'\x11\x83\x02\xc1\x34', 17, 0, b'\x83\x02',),  # Exception
            (FramerType.RTU, True, b'\xff\x03\x00|\x00\x02\x10\x0d', 255, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.RTU, False, b'\xff\x03\x04\x00\x8d\x00\x8e\xf5\xb3', 255, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.RTU, False, b'\xff\x83\x02\xa1\x01', 255, 0, b'\x83\x02',),  # Exception
            (FramerType.SOCKET, True, b'\x00\x00\x00\x00\x00\x06\x00\x03\x00\x7c\x00\x02', 0, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.SOCKET, False, b'\x00\x00\x00\x00\x00\x07\x00\x03\x04\x00\x8d\x00\x8e', 0, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.SOCKET, False, b'\x00\x00\x00\x00\x00\x03\x00\x83\x02', 0, 0, b'\x83\x02',),  # Exception
            (FramerType.SOCKET, True, b'\x00\x00\x00\x00\x00\x06\x11\x03\x00\x7c\x00\x02', 17, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.SOCKET, False, b'\x00\x00\x00\x00\x00\x07\x11\x03\x04\x00\x8d\x00\x8e', 17, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.SOCKET, False, b'\x00\x00\x00\x00\x00\x03\x11\x83\x02', 17, 0, b'\x83\x02',),  # Exception
            (FramerType.SOCKET, True, b'\x00\x00\x00\x00\x00\x06\xff\x03\x00\x7c\x00\x02', 255, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.SOCKET, False, b'\x00\x00\x00\x00\x00\x07\xff\x03\x04\x00\x8d\x00\x8e', 255, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.SOCKET, False, b'\x00\x00\x00\x00\x00\x03\xff\x83\x02', 255, 0, b'\x83\x02',),  # Exception
            (FramerType.SOCKET, True, b'\x0c\x05\x00\x00\x00\x06\x00\x03\x00\x7c\x00\x02', 0, 3077, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.SOCKET, False, b'\x0c\x05\x00\x00\x00\x07\x00\x03\x04\x00\x8d\x00\x8e', 0, 3077, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.SOCKET, False, b'\x0c\x05\x00\x00\x00\x03\x00\x83\x02', 0, 3077, b'\x83\x02',),  # Exception
            (FramerType.SOCKET, True, b'\x0c\x05\x00\x00\x00\x06\x11\x03\x00\x7c\x00\x02', 17, 3077, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.SOCKET, False, b'\x0c\x05\x00\x00\x00\x07\x11\x03\x04\x00\x8d\x00\x8e', 17, 3077, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.SOCKET, False, b'\x0c\x05\x00\x00\x00\x03\x11\x83\x02', 17, 3077, b'\x83\x02',),  # Exception
            (FramerType.SOCKET, True, b'\x0c\x05\x00\x00\x00\x06\xff\x03\x00\x7c\x00\x02', 255, 3077, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.SOCKET, False, b'\x0c\x05\x00\x00\x00\x07\xff\x03\x04\x00\x8d\x00\x8e', 255, 3077, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.SOCKET, False, b'\x0c\x05\x00\x00\x00\x03\xff\x83\x02', 255, 3077, b'\x83\x02',),  # Exception
            (FramerType.TLS, True, b'\x00\x00\x00\x00\x00\x06\x00\x03\x00\x7c\x00\x02', 0, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.TLS, False, b'\x00\x00\x00\x00\x00\x07\x00\x03\x04\x00\x8d\x00\x8e', 0, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.TLS, False, b'\x00\x00\x00\x00\x00\x03\x00\x83\x02', 0, 0, b'\x83\x02',),  # Exception
        ]
    )
    @pytest.mark.parametrize(
        ("split"),
        [
            "no",
            "half",
            "single",
        ]
    )
    async def test_decode_type(self, entry, test_framer, data, dev_id, tr_id, expected, split):
        """Test encode method."""
        if entry == FramerType.TLS and split != "no":
            return
        if entry == FramerType.RTU:
            return
        if split == "no":
            used_len, res_dev_id, res_tid, res_data = test_framer.decode(data)
        elif split == "half":
            split_len = int(len(data) / 2)
            used_len, res_dev_id, res_tid, res_data = test_framer.decode(data[0:split_len])
            assert not used_len
            assert not res_data
            assert not res_dev_id
            assert not res_tid
            used_len, res_dev_id, res_tid, res_data = test_framer.decode(data)
        else:
            last = len(data)
            for i in range(0, last -1):
                used_len, res_dev_id, res_tid, res_data = test_framer.decode(data[0:i+1])
                assert not used_len
                assert not res_data
                assert not res_dev_id
                assert not res_tid
            used_len, res_dev_id, res_tid, res_data = test_framer.decode(data)
        assert used_len == len(data)
        assert res_data == expected
        assert dev_id == res_dev_id
        assert tr_id == res_tid

    @pytest.mark.parametrize(
        ("entry", "data", "exp"),
        [
            (FramerType.ASCII, b':0003007C00017F\r\n', [  # bad crc
                (17, b''),
            ]),
            (FramerType.ASCII, b':0003007C00027F\r\n:0003007C00027F\r\n', [  # double good crc
                (17, b'\x03\x00\x7c\x00\x02'),
                (17, b'\x03\x00\x7c\x00\x02'),
            ]),
            (FramerType.ASCII, b':0003007C00017F\r\n:0003007C00027F\r\n', [  # bad crc + good CRC
                (34, b'\x03\x00\x7c\x00\x02'),
            ]),
            (FramerType.ASCII, b'abc:0003007C00027F\r\n', [  # garble in front
                (20, b'\x03\x00\x7c\x00\x02'),
            ]),
            (FramerType.ASCII, b':0003007C00017F\r\nabc', [  # bad crc, garble after
                (17, b''),
            ]),
            (FramerType.ASCII, b':0003007C00017F\r\nabcdefghijkl', [  # bad crc, garble after
                (29, b''),
            ]),
            (FramerType.ASCII, b':0003007C00027F\r\nabc', [  # good crc, garble after
                (17, b'\x03\x00\x7c\x00\x02'),
            ]),
            (FramerType.ASCII, b':0003007C00017F\r\n:0003', [ # bad crc, part second framer
                (17, b''),
            ]),
            (FramerType.SOCKET, b'\x00\x00\x00\x00\x00\x06\x00\x03\x00\x7c\x00\x02\x00\x00\x00\x00\x00\x06\x00\x03\x00\x7c\x00\x02',  [ # double good crc
                 (12, b"\x03\x00\x7c\x00\x02"),
                 (12, b"\x03\x00\x7c\x00\x02"),
            ]),
            (FramerType.SOCKET, b'\x0c\x05\x00\x00\x00\x02\xff\x83\x02', [  # Exception
                 (9, b'\x83\x02'),
            ]),
            (FramerType.RTU, b'\x00\x83\x02\x91\x21', [ # bad crc
                 (0, b''),
                 (0, b''),
            ]),
            (FramerType.RTU, b'\x00\x83\x02\xf0\x91\x31', [ # dummy char in stream, bad crc
                 (0, b''),
                 (0, b''),
            ]),
            (FramerType.RTU, b'\x00\x83\x02\x91\x21\x00\x83\x02\x91\x31', [ # bad crc + good CRC
                (0, b''),
                (0, b''),
            ]),
            (FramerType.RTU, b'\x00\x83\x02\xf0\x91\x31\x00\x83\x02\x91\x31', [ # dummy char in stream, bad crc  + good CRC
                 (0, b''),
                 (0, b''),
            ]),
        ]
    )
    async def test_decode_complicated(self, test_framer, data, exp):
        """Test encode method."""
        for ent in exp:
            used_len, _, _, res_data = test_framer.decode(data)
            data = data[used_len:]
            assert used_len == ent[0]
            assert res_data == ent[1]

    @pytest.mark.parametrize(
        ("entry", "data", "dev_id", "res_msg"),
        [
            (FramerType.ASCII, b'\x01\x05\x04\x00\x17', 1, b':010105040017DF\r\n'),
            (FramerType.ASCII, b'\x03\x07\x06\x00\x73', 2, b':0203070600737D\r\n'),
            (FramerType.ASCII,b'\x08\x00\x01', 3, b':03080001F7\r\n'),
            (FramerType.ASCII,b'\x84\x01', 2, b':02840179\r\n'),
            (FramerType.RTU, b'\x01\x01\x00', 2, b'\x02\x01\x01\x00\x51\xcc'),
            (FramerType.RTU, b'\x03\x06\xAE\x41\x56\x52\x43\x40', 17, b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD'),
            (FramerType.RTU, b'\x01\x03\x01\x00\x0a', 1, b'\x01\x01\x03\x01\x00\x0a\xed\x89'),
            (FramerType.SOCKET, b'\x01\x05\x04\x00\x17', 31, b'\x00\x05\x00\x00\x00\x06\x07\x01\x05\x04\x00\x17'),
            (FramerType.SOCKET, b'\x03\x07\x06\x00\x73', 32, b'\x00\x09\x00\x00\x00\x06\x02\x03\x07\x06\x00\x73'),
            (FramerType.SOCKET, b'\x08\x00\x01', 33, b'\x00\x06\x00\x00\x00\x04\x03\x08\x00\x01'),
            (FramerType.SOCKET, b'\x84\x01', 34, b'\x00\x08\x00\x00\x00\x03\x04\x84\x01'),
            (FramerType.TLS, b'\x01\x05\x04\x00\x17', 31, b'\x00\x05\x00\x00\x00\x06\x07\x01\x05\x04\x00\x17'),
            (FramerType.TLS, b'\x03\x07\x06\x00\x73', 32, b'\x00\x09\x00\x00\x00\x06\x02\x03\x07\x06\x00\x73'),
            (FramerType.TLS, b'\x08\x00\x01', 33, b'\x00\x06\x00\x00\x00\x04\x03\x08\x00\x01'),
            (FramerType.TLS, b'\x84\x01', 34, b'\x00\x08\x00\x00\x00\x03\x04\x84\x01'),
         ],
    )
    def test_roundtrip(self, test_framer, data, dev_id, res_msg):
        """Test encode."""
        msg = test_framer.encode(data, dev_id, 0)
        res_len, res_dev_id, _, res_data = test_framer.decode(msg)
        assert data == res_data
        assert dev_id == res_dev_id
        assert res_len == len(res_msg)

    @pytest.mark.parametrize(("entry"), [FramerType.RTU])
    def test_framer_decode(self, test_framer):
        """Test dummy decode."""
        msg = b''
        res_len, _, _, res_data = test_framer.decode(msg)
        assert not res_len
        assert not res_data

    @pytest.mark.parametrize(("is_server"), [False])
    async def test_handleFrame_no(self, test_framer):
        """Test handleFrame."""
        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        with mock.patch.object(test_framer, "decode") as mock_process:
            mock_process.side_effect = [(5, 0, 0, None), (0, 0, 0, None)]
            used_len, pdu = test_framer.handleFrame(msg, 0, 0)
            assert used_len == 5
            assert not pdu

    @pytest.mark.parametrize(("is_server"), [True])
    async def test_handleFrame1(self, test_framer):
        """Test handleFrame."""
        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        _, pdu = test_framer.handleFrame(msg, 0, 0)
        assert pdu

    @pytest.mark.parametrize(("is_server"), [True])
    @pytest.mark.parametrize(("entry", "msg"), [
        (FramerType.SOCKET, b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00\x08"),
        (FramerType.TLS, b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00\x08"),
        (FramerType.RTU, b"\x00\x01\x00\x00\x00\x01\xfc\x1b"),
        (FramerType.ASCII, b":F7031389000A60\r\n"),
    ])
    def test_handleFrame2(self, test_framer, msg):
        """Test a tcp frame transaction."""
        used_len, pdu = test_framer.handleFrame(msg, 0, 0)
        assert pdu
        assert used_len == len(msg)

    @pytest.mark.parametrize(("is_server"), [True])
    @pytest.mark.parametrize(("half"), [False, True])
    @pytest.mark.parametrize(("entry", "msg", "dev_id", "tid"), [
        (FramerType.SOCKET, b"\x00\x01\x00\x00\x00\x06\xff\x02\x01\x02\x00\x08", 0xff, 1),
        (FramerType.TLS, b"\x00\x01\x00\x00\x00\x06\xff\x02\x01\x02\x00\x08", 0xff, 1),
        (FramerType.RTU, b"\x00\x01\x00\x00\x00\x01\xfc\x1b", 0, 0),
        (FramerType.ASCII, b":F7031389000A60\r\n", 0xf7, 0),
    ])
    def test_handleFrame_roundtrip(self, entry, test_framer, msg, dev_id, tid, half):
        """Test a tcp frame transaction."""
        if half and entry != FramerType.TLS:
            data_len = int(len(msg) / 2)
            used_len, pdu = test_framer.handleFrame(msg[:data_len], 0, 0)
            assert not pdu
            assert not used_len
            used_len, result = test_framer.handleFrame(msg, 0, 0)
        else:
            used_len, result = test_framer.handleFrame(msg, 0, 0)
        assert used_len == len(msg)
        assert result
        assert result.dev_id == dev_id
        assert result.transaction_id == tid
        expected = test_framer.encode(
            result.function_code.to_bytes(1,'big') + result.encode(),
            dev_id, 1)
        assert msg == expected

    @pytest.mark.parametrize(("is_server"), [True])
    @pytest.mark.parametrize(("entry", "msg"), [
        (FramerType.SOCKET, b"\x00\x01\x00\x00\x00\x02\xff\x01"),
        (FramerType.TLS, b"\x00\x01\x00\x00\x00\x02\xff\x01"),
        (FramerType.RTU, b"\xff\x01\x81\x80"),
        (FramerType.ASCII, b":FF0100\r\n"),
    ])
    def test_framer_encode(self, test_framer, msg):
        """Test a tcp frame transaction."""
        with mock.patch.object(ModbusPDU, "encode") as mock_encode:
            message = ModbusPDU()
            message.transaction_id = 0x0001
            message.dev_id = 0xFF
            message.function_code = 0x01
            mock_encode.return_value = b""

            actual = test_framer.buildFrame(message)
            assert msg == actual
