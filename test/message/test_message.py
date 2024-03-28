"""Test transport."""

from unittest import mock

import pytest

from pymodbus.message import MessageType
from pymodbus.message.ascii import MessageAscii
from pymodbus.message.rtu import MessageRTU
from pymodbus.message.socket import MessageSocket
from pymodbus.message.tls import MessageTLS
from pymodbus.transport import CommParams


class TestMessage:
    """Test message module."""

    @staticmethod
    @pytest.fixture(name="msg")
    async def prepare_message(dummy_message):
        """Return message object."""
        return dummy_message(
            MessageType.RAW,
            CommParams(),
            False,
            [1],
        )


    @pytest.mark.parametrize(("entry"), list(MessageType))
    async def test_message_init(self, entry, dummy_message):
        """Test message type."""
        msg = dummy_message(entry.value,
            CommParams(),
            False,
            [1],
        )
        assert msg.msg_handle

    @pytest.mark.parametrize(("data", "res_len", "cx", "rc"), [
        (b'12345', 5, 1, [(5, 0, 0, b'12345')]),  # full frame
        (b'12345', 0, 0, [(0, 0, 0, b'')]),  # not full frame, need more data
        (b'12345', 5, 0, [(5, 0, 0, b'')]),  # faulty frame, skipped
        (b'1234512345', 10, 2, [(5, 0, 0, b'12345'), (5, 0, 0, b'12345')]),  # 2 full frames
        (b'12345678', 5, 1, [(5, 0, 0, b'12345'), (0, 0, 0, b'')]),  # full frame, not full frame
        (b'67812345', 8, 1, [(3, 0, 0, b''), (5, 0, 0, b'12345')]), # garble first, full frame next
        (b'12345678', 5, 0, [(5, 0, 0, b''), (0, 0, 0, b'')]),      # garble first, not full frame
        (b'12345678', 8, 0, [(5, 0, 0, b''), (3, 0, 0, b'')]),      # garble first, faulty frame
    ])
    async def test_message_callback(self, msg, data, res_len, cx, rc):
        """Test message type."""
        msg.callback_request_response = mock.Mock()
        msg.msg_handle.decode = mock.MagicMock(side_effect=iter(rc))
        assert msg.callback_data(data) == res_len
        assert msg.callback_request_response.call_count == cx
        if cx:
            msg.callback_request_response.assert_called_with(b'12345', 0, 0)
        else:
            msg.callback_request_response.assert_not_called()

    async def test_message_build_send(self, msg):
        """Test message type."""
        msg.msg_handle.encode = mock.MagicMock(return_value=(b'decode'))
        msg.build_send(b'decode', 1, 0)
        msg.msg_handle.encode.assert_called_once()
        msg.send.assert_called_once()
        msg.send.assert_called_with(b'decode', None)

    @pytest.mark.parametrize(
        ("dev_id", "res"), [
        (0, False),
        (1, True),
        (2, False),
        ])
    async def test_validate_id(self, msg, dev_id, res):
        """Test message type."""
        assert res == msg.validate_device_id(dev_id)

    @pytest.mark.parametrize(
        ("data", "res_len", "res_id", "res_tid", "res_data"), [
        (b'\x00\x01', 0, 0, 0, b''),
        (b'\x01\x02\x03', 3, 1, 2, b'\x03'),
        (b'\x04\x05\x06\x07\x08\x09\x00\x01\x02\x03', 10, 4, 5, b'\x06\x07\x08\x09\x00\x01\x02\x03'),
    ])
    async def test_decode(self, msg,  data, res_id, res_tid, res_len, res_data):
        """Test decode method in all types."""
        t_len, t_id, t_tid, t_data = msg.msg_handle.decode(data)
        assert res_len == t_len
        assert res_id == t_id
        assert res_tid == t_tid
        assert res_data == t_data

    @pytest.mark.parametrize(
        ("data", "dev_id", "tid", "res_data"), [
        (b'\x01\x02', 5, 6, b'\x05\x06\x01\x02'),
        (b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09', 17, 25, b'\x11\x19\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09'),
    ])
    async def test_encode(self, msg, data, dev_id, tid, res_data):
        """Test decode method in all types."""
        t_data = msg.msg_handle.encode(data, dev_id, tid)
        assert res_data == t_data

    @pytest.mark.parametrize(
        ("func", "lrc", "expect"),
        [(MessageAscii.check_LRC, 0x1c, True),
         (MessageAscii.check_LRC, 0x0c, False),
         (MessageAscii.compute_LRC, None, 0x1c),
         (MessageRTU.check_CRC, 0xE2DB, True),
         (MessageRTU.check_CRC, 0xDBE2, False),
         (MessageRTU.compute_CRC, None, 0xE2DB),
        ]
    )
    def test_LRC_CRC(self, func, lrc, expect):
        """Test check_LRC."""
        data = b'\x12\x34\x23\x45\x34\x56\x45\x67'
        assert expect == func(data, lrc) if lrc else func(data)

    def test_roundtrip_LRC(self):
        """Test combined compute/check LRC."""
        data = b'\x12\x34\x23\x45\x34\x56\x45\x67'
        assert MessageAscii.compute_LRC(data) == 0x1c
        assert MessageAscii.check_LRC(data, 0x1C)

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



class TestMessages:
    """Test message classes."""

    @pytest.mark.parametrize(
        ("frame", "frame_expected"),
        [
            (MessageAscii, [
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
            (MessageRTU, [
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
            (MessageSocket, [
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
            (MessageTLS, [
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
        ("inx3", "tid"),
        [
            (0, 0),
            (9, 3077),
        ]
    )
    def test_encode(self, frame, frame_expected, data, dev_id, tid, inx1, inx2, inx3):
        """Test encode method."""
        if ((frame != MessageSocket and tid) or
            (frame == MessageTLS and dev_id)):
            return
        frame_obj = frame()
        expected = frame_expected[inx1 + inx2 + inx3]
        encoded_data = frame_obj.encode(data, dev_id, tid)
        assert encoded_data == expected

    @pytest.mark.parametrize(
        ("msg_type", "data", "dev_id", "tid", "expected"),
        [
            (MessageType.ASCII, b':0003007C00027F\r\n', 0, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (MessageType.ASCII, b':000304008D008EDE\r\n', 0, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (MessageType.ASCII, b':0083027B\r\n', 0, 0, b'\x83\x02',),  # Exception
            (MessageType.ASCII, b':1103007C00026E\r\n', 17, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (MessageType.ASCII, b':110304008D008ECD\r\n', 17, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (MessageType.ASCII, b':1183026A\r\n', 17, 0, b'\x83\x02',),  # Exception
            (MessageType.ASCII, b':FF03007C000280\r\n', 255, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (MessageType.ASCII, b':FF0304008D008EDF\r\n', 255, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (MessageType.ASCII, b':FF83027C\r\n', 255, 0, b'\x83\x02',),  # Exception
            (MessageType.RTU, b'\x00\x03\x00\x7c\x00\x02\x04\x02', 0, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (MessageType.RTU, b'\x00\x03\x04\x00\x8d\x00\x8e\xfa\xbc', 0, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (MessageType.RTU, b'\x00\x83\x02\x91\x31', 0, 0, b'\x83\x02',),  # Exception
            (MessageType.RTU, b'\x11\x03\x00\x7c\x00\x02\x07\x43', 17, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (MessageType.RTU, b'\x11\x03\x04\x00\x8d\x00\x8e\xfb\xbd', 17, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (MessageType.RTU, b'\x11\x83\x02\xc1\x34', 17, 0, b'\x83\x02',),  # Exception
            (MessageType.RTU, b'\xff\x03\x00|\x00\x02\x10\x0d', 255, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (MessageType.RTU, b'\xff\x03\x04\x00\x8d\x00\x8e\xf5\xb3', 255, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (MessageType.RTU, b'\xff\x83\x02\xa1\x01', 255, 0, b'\x83\x02',),  # Exception
            (MessageType.SOCKET, b'\x00\x00\x00\x00\x00\x06\x00\x03\x00\x7c\x00\x02', 0, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (MessageType.SOCKET, b'\x00\x00\x00\x00\x00\x07\x00\x03\x04\x00\x8d\x00\x8e', 0, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (MessageType.SOCKET, b'\x00\x00\x00\x00\x00\x03\x00\x83\x02', 0, 0, b'\x83\x02',),  # Exception
            (MessageType.SOCKET, b'\x00\x00\x00\x00\x00\x06\x11\x03\x00\x7c\x00\x02', 17, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (MessageType.SOCKET, b'\x00\x00\x00\x00\x00\x07\x11\x03\x04\x00\x8d\x00\x8e', 17, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (MessageType.SOCKET, b'\x00\x00\x00\x00\x00\x03\x11\x83\x02', 17, 0, b'\x83\x02',),  # Exception
            (MessageType.SOCKET, b'\x00\x00\x00\x00\x00\x06\xff\x03\x00\x7c\x00\x02', 255, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (MessageType.SOCKET, b'\x00\x00\x00\x00\x00\x07\xff\x03\x04\x00\x8d\x00\x8e', 255, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (MessageType.SOCKET, b'\x00\x00\x00\x00\x00\x03\xff\x83\x02', 255, 0, b'\x83\x02',),  # Exception
            (MessageType.SOCKET, b'\x0c\x05\x00\x00\x00\x06\x00\x03\x00\x7c\x00\x02', 0, 3077, b"\x03\x00\x7c\x00\x02",),  # Request
            (MessageType.SOCKET, b'\x0c\x05\x00\x00\x00\x07\x00\x03\x04\x00\x8d\x00\x8e', 0, 3077, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (MessageType.SOCKET, b'\x0c\x05\x00\x00\x00\x03\x00\x83\x02', 0, 3077, b'\x83\x02',),  # Exception
            (MessageType.SOCKET, b'\x0c\x05\x00\x00\x00\x06\x11\x03\x00\x7c\x00\x02', 17, 3077, b"\x03\x00\x7c\x00\x02",),  # Request
            (MessageType.SOCKET, b'\x0c\x05\x00\x00\x00\x07\x11\x03\x04\x00\x8d\x00\x8e', 17, 3077, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (MessageType.SOCKET, b'\x0c\x05\x00\x00\x00\x03\x11\x83\x02', 17, 3077, b'\x83\x02',),  # Exception
            (MessageType.SOCKET, b'\x0c\x05\x00\x00\x00\x06\xff\x03\x00\x7c\x00\x02', 255, 3077, b"\x03\x00\x7c\x00\x02",),  # Request
            (MessageType.SOCKET, b'\x0c\x05\x00\x00\x00\x07\xff\x03\x04\x00\x8d\x00\x8e', 255, 3077, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (MessageType.SOCKET, b'\x0c\x05\x00\x00\x00\x03\xff\x83\x02', 255, 3077, b'\x83\x02',),  # Exception
            (MessageType.TLS, b'\x03\x00\x7c\x00\x02', 0, 0, b"\x03\x00\x7c\x00\x02",),  # Request
            (MessageType.TLS, b'\x03\x04\x00\x8d\x00\x8e', 0, 0, b"\x03\x04\x00\x8d\x00\x8e",),  # Response
            (MessageType.TLS, b'\x83\x02', 0, 0, b'\x83\x02',),  # Exception
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
    async def test_decode(self, dummy_message, msg_type, data, dev_id, tid, expected, split):
        """Test encode method."""
        if msg_type == MessageType.RTU:
            pytest.skip("Waiting on implementation!")
        if msg_type == MessageType.TLS and split != "no":
            return
        frame = dummy_message(
            msg_type,
            CommParams(),
            False,
            [1],
        )
        frame.callback_request_response = mock.Mock()
        if split == "no":
            used_len = frame.callback_data(data)

        elif split == "half":
            split_len = int(len(data) / 2)
            assert not frame.callback_data(data[0:split_len])
            frame.callback_request_response.assert_not_called()
            used_len = frame.callback_data(data)
        else:
            last = len(data)
            for i in range(0, last -1):
                assert not frame.callback_data(data[0:i+1])
                frame.callback_request_response.assert_not_called()
            used_len = frame.callback_data(data)
        assert used_len == len(data)
        frame.callback_request_response.assert_called_with(expected, dev_id, tid)

    @pytest.mark.parametrize(
        ("frame", "data", "exp_len"),
        [
            (MessageAscii, b':0003007C00017F\r\n', 17),  # bad crc
            # (MessageAscii, b'abc:0003007C00027F\r\n', 3),  # garble in front
            # (MessageAscii, b':0003007C00017F\r\nabc', 17),  # bad crc, garble after
            # (MessageAscii, b':0003007C00017F\r\n:0003', 17),  # part second message
            (MessageRTU, b'\x00\x83\x02\x91\x31', 0),  # bad crc
            # (MessageRTU, b'\x00\x83\x02\x91\x31', 0),  # garble in front
            # (MessageRTU, b'\x00\x83\x02\x91\x31', 0),  # garble after
            # (MessageRTU, b'\x00\x83\x02\x91\x31', 0),  # part second message
        ]
    )
    async def test_decode_bad_crc(self, frame, data, exp_len):
        """Test encode method."""
        if frame == MessageRTU:
            pytest.skip("Waiting for implementation.")
        frame_obj = frame()
        used_len, _, _, data = frame_obj.decode(data)
        assert used_len == exp_len
        assert not data
