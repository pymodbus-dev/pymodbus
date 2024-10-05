"""Test framer."""

from unittest import mock

import pytest

from pymodbus.factory import ClientDecoder
from pymodbus.framer import FramerType
from pymodbus.framer.ascii import FramerAscii
from pymodbus.framer.rtu import FramerRTU
from pymodbus.framer.socket import FramerSocket
from pymodbus.framer.tls import FramerTLS


class TestFramer:
    """Test module."""

    @pytest.mark.parametrize(("entry"), list(FramerType))
    async def test_framer_init(self, test_framer):
        """Test framer type."""
        test_framer.incomming_dev_id = 1
        assert test_framer.incomming_dev_id

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
                b'\x03\x00\x7c\x00\x02',
                b'\x03\x04\x00\x8d\x00\x8e',
                b'\x83\x02',
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
    def xtest_encode_type(self, frame, frame_expected, data, dev_id, tr_id, inx1, inx2, inx3):
        """Test encode method."""
        if frame == FramerTLS and dev_id + tr_id:
            return
        frame_obj = frame(ClientDecoder(), [0])
        expected = frame_expected[inx1 + inx2 + inx3]
        encoded_data = frame_obj.encode(data, dev_id, tr_id)
        assert encoded_data == expected

    @pytest.mark.parametrize(
        ("entry", "is_server", "data", "dev_id", "tr_id", "expected"),
        [
            (FramerType.ASCII, True, b':0003007C00027F\r\n', 0, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.ASCII, False, b':000304008D008EDE\r\n', 0, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.ASCII, False, b':0083027B\r\n', 0, 0, b'\x83\x02',),  # Exception
            (FramerType.ASCII, True, b':1103007C00026E\r\n', 17, 17, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.ASCII, False, b':110304008D008ECD\r\n', 17, 17, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.ASCII, False, b':1183026A\r\n', 17, 17, b'\x83\x02',),  # Exception
            (FramerType.ASCII, True, b':FF03007C000280\r\n', 255, 255, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.ASCII, False, b':FF0304008D008EDF\r\n', 255, 255, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.ASCII, False, b':FF83027C\r\n', 255, 255, b'\x83\x02',),  # Exception
            (FramerType.RTU, True, b'\x00\x03\x00\x7c\x00\x02\x04\x02', 0, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.RTU, False, b'\x00\x03\x04\x00\x8d\x00\x8e\xfa\xbc', 0, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.RTU, False, b'\x00\x83\x02\x91\x31', 0, 0, b'\x83\x02',),  # Exception
            (FramerType.RTU, True, b'\x11\x03\x00\x7c\x00\x02\x07\x43', 17, 17, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.RTU, False, b'\x11\x03\x04\x00\x8d\x00\x8e\xfb\xbd', 17, 17, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.RTU, False, b'\x11\x83\x02\xc1\x34', 17, 17, b'\x83\x02',),  # Exception
            (FramerType.RTU, True, b'\xff\x03\x00|\x00\x02\x10\x0d', 255, 255, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.RTU, False, b'\xff\x03\x04\x00\x8d\x00\x8e\xf5\xb3', 255, 255, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.RTU, False, b'\xff\x83\x02\xa1\x01', 255, 255, b'\x83\x02',),  # Exception
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
            (FramerType.TLS, True, b'\x03\x00\x7c\x00\x02', 0, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (FramerType.TLS, False, b'\x03\x04\x00\x8d\x00\x8e', 0, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (FramerType.TLS, False, b'\x83\x02', 0, 0, b'\x83\x02',),  # Exception
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
    async def xtest_decode_type(self, entry, dummy_async_framer, data, dev_id, tr_id, expected, split):
        """Test encode method."""
        if entry == FramerType.TLS and split != "no":
            return
        if entry == FramerType.RTU:
            return
        dummy_async_framer.callback_request_response = mock.MagicMock()
        if split == "no":
            used_len = dummy_async_framer.callback_data(data)
        elif split == "half":
            split_len = int(len(data) / 2)
            assert not dummy_async_framer.callback_data(data[0:split_len])
            dummy_async_framer.callback_request_response.assert_not_called()
            used_len = dummy_async_framer.callback_data(data)
        else:
            last = len(data)
            for i in range(0, last -1):
                assert not dummy_async_framer.callback_data(data[0:i+1])
                dummy_async_framer.callback_request_response.assert_not_called()
            used_len = dummy_async_framer.callback_data(data)
        assert used_len == len(data)
        dummy_async_framer.callback_request_response.assert_called_with(expected, dev_id, tr_id)

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
            # (FramerType.RTU, b'\x00\x83\x02\x91\x21', [ # bad crc
            #      (5, b''),
            #]),
            #(FramerType.RTU, b'\x00\x83\x02\xf0\x91\x31', [ # dummy char in stream, bad crc
            #     (5, b''),
            #]),
            # (FramerType.RTU, b'\x00\x83\x02\x91\x21\x00\x83\x02\x91\x31', [ # bad crc + good CRC
            #    (10, b'\x83\x02'),
            #]),
            #(FramerType.RTU, b'\x00\x83\x02\xf0\x91\x31\x00\x83\x02\x91\x31', [ # dummy char in stream, bad crc  + good CRC
            #     (11, b''),
            #]),

            # (FramerType.RTU, b'\x00\x83\x02\x91\x31', 0),  # garble in front
            # (FramerType.ASCII, b'abc:0003007C00027F\r\n', [  # garble in front
            #     (20, b'\x03\x00\x7c\x00\x02'),
            # ]),

            # (FramerType.RTU, b'\x00\x83\x02\x91\x31', 0),  # garble after
            # (FramerType.ASCII, b':0003007C00017F\r\nabc', [  # bad crc, garble after
            #     (17, b''),
            # ]),
            # (FramerType.ASCII, b':0003007C00017F\r\nabcdefghijkl', [  # bad crc, garble after
            #     (29, b''),
            # ]),
            # (FramerType.ASCII, b':0003007C00027F\r\nabc', [  # good crc, garble after
            #     (17, b'\x03\x00\x7c\x00\x02'),
            # ]),
            # (FramerType.RTU, b'\x00\x83\x02\x91\x31', 0),  # part second framer
            # (FramerType.ASCII, b':0003007C00017F\r\n:0003', [ # bad crc, part second framer
            #     (17, b''),
            # ]),
        ]
    )
    async def xtest_decode_complicated(self, dummy_async_framer, data, exp):
        """Test encode method."""
        for ent in exp:
            used_len, res_data = dummy_async_framer.handle.decode(data)
            assert used_len == ent[0]
            assert res_data == ent[1]
