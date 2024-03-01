"""Test framers."""
from unittest import mock

import pytest

from pymodbus import Framer
from pymodbus.bit_read_message import ReadCoilsRequest
from pymodbus.client.base import ModbusBaseClient
from pymodbus.exceptions import ModbusIOException
from pymodbus.factory import ClientDecoder
from pymodbus.framer import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
)
from pymodbus.transport import CommType
from pymodbus.utilities import ModbusTransactionState


BASE_PORT = 6600


TEST_MESSAGE = b"\x00\x01\x00\x01\x00\n\xec\x1c"


class TestFramers:
    """Test framers."""

    slaves = [2, 17]

    @staticmethod
    @pytest.fixture(name="rtu_framer")
    def fixture_rtu_framer():
        """RTU framer."""
        return ModbusRtuFramer(ClientDecoder())

    @staticmethod
    @pytest.fixture(name="ascii_framer")
    def fixture_ascii_framer():
        """Ascii framer."""
        return ModbusAsciiFramer(ClientDecoder())


    @pytest.mark.parametrize(
    "framer",
    [
        ModbusRtuFramer,
        ModbusAsciiFramer,
        ModbusBinaryFramer,
    ],
)
    def test_framer_initialization(self, framer):
        """Test framer initialization."""
        decoder = ClientDecoder()
        framer = framer(decoder)
        assert framer.client is None
        assert framer._buffer == b""  # pylint: disable=protected-access
        assert framer.decoder == decoder
        if isinstance(framer, ModbusAsciiFramer):
            assert framer._header == {  # pylint: disable=protected-access
                "tid": 0,
                "pid": 0,
                "lrc": "0000",
                "len": 0,
                "uid": 0x00,
                "crc": b"\x00\x00",
            }
            assert framer._hsize == 0x02  # pylint: disable=protected-access
            assert framer._start == b":"  # pylint: disable=protected-access
            assert framer._end == b"\r\n"  # pylint: disable=protected-access
        elif isinstance(framer, ModbusRtuFramer):
            assert framer._header == {  # pylint: disable=protected-access
                "tid": 0,
                "pid": 0,
                "lrc": "0000",
                "uid": 0x00,
                "len": 0,
                "crc": b"\x00\x00",
            }
            assert framer._hsize == 0x01  # pylint: disable=protected-access
            assert framer._end == b"\x0d\x0a"  # pylint: disable=protected-access
            assert framer._min_frame_size == 4  # pylint: disable=protected-access
        else:
            assert framer._header == {  # pylint: disable=protected-access
                "tid": 0,
                "pid": 0,
                "lrc": "0000",
                "crc": b"\x00\x00",
                "len": 0,
                "uid": 0x00,
            }
            assert framer._hsize == 0x01  # pylint: disable=protected-access
            assert framer._start == b"\x7b"  # pylint: disable=protected-access
            assert framer._end == b"\x7d"  # pylint: disable=protected-access
            assert framer._repeat == [  # pylint: disable=protected-access
                b"}"[0],
                b"{"[0],
            ]


    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (b"", 0),
            (b"\x02\x01\x01\x00Q\xcc", 1),
            (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD", 1),  # valid frame
            (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAC", 0),  # invalid frame CRC
        ],
    )
    def test_check_frame(self, rtu_framer, data, expected):
        """Test check frame."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        rtu_framer.processIncomingPacket(data, callback, self.slaves)
        assert count == expected


    @pytest.mark.parametrize(
        ("data", "header", "res"),
        [
            (b"", {"uid": 0x00, "len": 0, "crc": b"\x00\x00"}, 0),
            (b"abcd", {"uid": 0x00, "len": 2, "crc": b"\x00\x00"}, 0),
            (
                b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\x12\x03",  # real case, frame size is 11
                {"uid": 0x00, "len": 11, "crc": b"\x00\x00"},
                1,
            ),
        ],
    )
    def test_rtu_advance_framer(self, rtu_framer, data, header, res):
        """Test rtu advance framer."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        rtu_framer._header = header  # pylint: disable=protected-access
        rtu_framer.processIncomingPacket(data, callback, self.slaves)
        assert count == res


    @pytest.mark.parametrize("data", [b"", b"abcd"])
    def test_rtu_reset_framer(self, rtu_framer, data):
        """Test rtu reset framer."""
        rtu_framer._buffer = data  # pylint: disable=protected-access
        rtu_framer.resetFrame()
        assert rtu_framer._header == {  # pylint: disable=protected-access
            "lrc": "0000",
            "crc": b"\x00\x00",
            "len": 0,
            "uid": 0x00,
            "pid": 0,
            "tid": 0,
        }


    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (b"", 0),
            (b"\x11", 0),
            (b"\x11\x03", 0),
            (b"\x11\x03\x06", 0),
            (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49", 0),
            (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD", 1),
            (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\xAB\xCD", 1),
        ],
    )
    def test_is_frame_ready(self, rtu_framer, data, expected):
        """Test is frame ready."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        rtu_framer.processIncomingPacket(data, callback, self.slaves)
        assert count == expected


    @pytest.mark.parametrize(
        "data",
        [
            b"",
            b"\x11",
            b"\x11\x03",
            b"\x11\x03\x06",
            b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x43",
        ],
    )
    def test_rtu_populate_header_fail(self, rtu_framer, data):
        """Test rtu populate header fail."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        rtu_framer.processIncomingPacket(data, callback, self.slaves)
        assert not count


    @pytest.mark.parametrize(
        ("data", "header"),
        [
            (
                b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD",
                {
                    "crc": b"\x49\xAD",
                    "uid": 17,
                    "len": 11,
                    "tid": 17,
                },
            ),
            (
                b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\x11\x03",
                {
                    "crc": b"\x49\xAD",
                    "uid": 17,
                    "len": 11,
                    "tid": 17,
                },
            ),
        ],
    )
    def test_rtu_populate_header(self, rtu_framer, data, header):
        """Test rtu populate header."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        rtu_framer.processIncomingPacket(data, callback, self.slaves)
        assert rtu_framer._header == header  # pylint: disable=protected-access


    def test_get_frame(self, rtu_framer):
        """Test get frame."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        data = b"\x02\x01\x01\x00Q\xcc"
        rtu_framer.processIncomingPacket(data, callback, self.slaves)
        assert count
        assert result.function_code.to_bytes(1,'big') + result.encode() == b"\x01\x01\x00"


    def test_populate_result(self, rtu_framer):
        """Test populate result."""
        rtu_framer._header["uid"] = 255  # pylint: disable=protected-access
        result = mock.Mock()
        rtu_framer.populateResult(result)
        assert result.slave_id == 255


    @pytest.mark.parametrize(
        ("data", "slaves", "reset_called", "cb_called"),
        [
            (b"\x11", [17], 0, 0),  # not complete frame
            (b"\x11\x03", [17], 0, 0),  # not complete frame
            (b"\x11\x03\x06", [17], 0, 0),  # not complete frame
            (b"\x11\x03\x06\xAE\x41\x56\x52\x43", [17], 0, 0),  # not complete frame
            (
                b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40",
                [17],
                0,
                0,
            ),  # not complete frame
            (
                b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49",
                [17],
                0,
                0,
            ),  # not complete frame
            (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAC", [17], 1, 0),  # bad crc
            (
                b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD",
                [17],
                0,
                1,
            ),  # good frame
            (
                b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD",
                [16],
                0,
                0,
            ),  # incorrect slave id
            (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\x11\x03", [17], 0, 1),
            # good frame + part of next frame
        ],
    )
    def test_rtu_incoming_packet(self, rtu_framer, data, slaves, reset_called, cb_called):
        """Test rtu process incoming packet."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        with mock.patch.object(
            rtu_framer, "resetFrame", wraps=rtu_framer.resetFrame
        ) as mock_reset:
            rtu_framer.processIncomingPacket(data, callback, slaves)
            assert count == cb_called
            assert mock_reset.call_count == reset_called


    async def test_send_packet(self, rtu_framer):
        """Test send packet."""
        message = TEST_MESSAGE
        client = ModbusBaseClient(
            Framer.ASCII,
            host="localhost",
            port=BASE_PORT + 1,
            CommType=CommType.TCP,
        )
        client.state = ModbusTransactionState.TRANSACTION_COMPLETE
        client.silent_interval = 1
        client.last_frame_end = 1
        client.comm_params.timeout_connect = 0.25
        client.idle_time = mock.Mock(return_value=1)
        client.send = mock.Mock(return_value=len(message))
        rtu_framer.client = client
        assert rtu_framer.sendPacket(message) == len(message)
        client.state = ModbusTransactionState.PROCESSING_REPLY
        assert rtu_framer.sendPacket(message) == len(message)


    def test_recv_packet(self, rtu_framer):
        """Test receive packet."""
        message = TEST_MESSAGE
        client = mock.Mock()
        client.recv.return_value = message
        rtu_framer.client = client
        assert rtu_framer.recvPacket(len(message)) == message

    def test_process(self, rtu_framer):
        """Test process."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        data = TEST_MESSAGE
        rtu_framer.processIncomingPacket(data, callback, self.slaves)
        assert not count

    @pytest.mark.parametrize(("slaves", "res"), [([16], 0), ([17], 1)])
    def test_validate__slave_id(self,rtu_framer, slaves, res):
        """Test validate slave."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        data = b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\x12\x03"
        rtu_framer.processIncomingPacket(data, callback, slaves)
        assert count == res

    @pytest.mark.parametrize("data", [b":010100010001FC\r\n", b""])
    def test_decode_ascii_data(self, ascii_framer, data):
        """Test decode ascii."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        ascii_framer.processIncomingPacket(data, callback, [1])
        if result:
            assert result.slave_id == 1
            assert result.function_code == 1
        else:
            assert not result

    def test_recv_split_packet(self):
        """Test receive packet."""
        response_ok = False

        def _handle_response(_reply):
            """Handle response."""
            nonlocal response_ok
            response_ok = True

        message = bytearray(b"\x00\x01\x00\x00\x00\x0b\x01\x03\x08\x00\xb5\x12\x2f\x37\x21\x00\x03")
        for i in range(0, len(message)):
            part1 = message[:i]
            part2 = message[i:]
            response_ok = False
            framer = ModbusSocketFramer(ClientDecoder())
            if i:
                framer.processIncomingPacket(part1, _handle_response, slave=0)
                assert not response_ok, "Response should not be accepted"
            framer.processIncomingPacket(part2, _handle_response, slave=0)
            assert response_ok, "Response is valid, but not accepted"


    def test_recv_socket_exception_packet(self):
        """Test receive packet."""
        response_ok = False

        def _handle_response(_reply):
            """Handle response."""
            nonlocal response_ok
            response_ok = True

        message = bytearray(b"\x00\x02\x00\x00\x00\x03\x01\x84\x02")
        response_ok = False
        framer = ModbusSocketFramer(ClientDecoder())
        framer.processIncomingPacket(message, _handle_response, slave=0)
        assert response_ok, "Response is valid, but not accepted"

        message = bytearray(b"\x00\x01\x00\x00\x00\x0b\x01\x03\x08\x00\xb5\x12\x2f\x37\x21\x00\x03")
        response_ok = False
        framer = ModbusSocketFramer(ClientDecoder())
        framer.processIncomingPacket(message, _handle_response, slave=0)
        assert response_ok, "Response is valid, but not accepted"

    # ---- 100% coverage
    @pytest.mark.parametrize(
        ("framer", "message"),
        [
            (ModbusAsciiFramer, b':00010001000AF4\r\n',),
            (ModbusBinaryFramer, b'{\x00\x01\x00\x01\x00\n\xec\x1c}',),
            (ModbusRtuFramer, b"\x00\x01\x00\x01\x00\n\xec\x1c",),
            (ModbusSocketFramer, b'\x00\x00\x00\x00\x00\x06\x00\x01\x00\x01\x00\n',),
        ]
    )
    def test_build_packet(self, framer, message):
        """Test build packet."""
        test_framer =  framer(ClientDecoder())
        request = ReadCoilsRequest(1, 10)
        assert test_framer.buildPacket(request) == message


    @pytest.mark.parametrize(
        ("framer", "message"),
        [
            (ModbusAsciiFramer, b':01010001000AF3\r\n',),
            (ModbusBinaryFramer, b'A{\x01\x01\x00\x01\x00\n\xed\xcd}',),
            (ModbusRtuFramer, b"\x01\x01\x03\x01\x00\n\xed\x89",),
            (ModbusSocketFramer, b'\x00\x00\x00\x00\x00\x06\x01\x01\x00\x01\x00\n',),
        ]
    )
    @pytest.mark.parametrize(("slave"), [0x01, 0x02])
    def test_processincomingpacket_ok(self, framer, message, slave):
        """Test processIncomingPacket."""
        test_framer =  framer(ClientDecoder())
        test_framer.processIncomingPacket(message, mock.Mock(), slave)


    @pytest.mark.parametrize(
        ("framer", "message"),
        [
            (ModbusAsciiFramer, b':01270001000ACD\r\n',),
            (ModbusBinaryFramer, b'{\x01\x1a\x00\x01\x00\n\x89\xcf}',),
            (ModbusRtuFramer, b"\x01\x03\x03\x01\x00\n\x94\x49",),
            (ModbusSocketFramer, b'\x00\x00\x00\x00\x00\x06\x01\x27\x00\x01\x00\n',),
        ]
    )
    def test_processincomingpacket_not_ok(self, framer, message):
        """Test processIncomingPacket."""
        test_framer =  framer(ClientDecoder())
        with pytest.raises(ModbusIOException):
            test_framer.processIncomingPacket(message, mock.Mock(), 0x01)

    @pytest.mark.parametrize(
        ("framer", "message"),
        [
            (ModbusAsciiFramer, b':61620001000AF4\r\n',),
            (ModbusBinaryFramer, b'{\x61\x62\x00\x01\x00\n\xec\x1c}',),
            (ModbusRtuFramer, b"\x61\x62\x00\x01\x00\n\xec\x1c",),
            (ModbusSocketFramer, b'\x00\x00\x00\x00\x00\x06\x61\x62\x00\x01\x00\n',),
        ]
    )
    @pytest.mark.parametrize("expected", [{"fcode": 98, "slave": 97}])
    def test_decode_data(self, framer, message, expected):
        """Test decode data."""
        test_framer =  framer(ClientDecoder())
        decoded = test_framer.decode_data(b'')
        assert decoded == {}
        decoded = test_framer.decode_data(message)
        assert decoded["fcode"] == expected["fcode"]
        assert decoded["slave"] == expected["slave"]

    def test_binary_framer_preflight(self):
        """Test binary framer _preflight."""
        test_framer =  ModbusBinaryFramer(ClientDecoder())
        assert test_framer._preflight(b'A{B}C') == b'A{{B}}C'  # pylint: disable=protected-access
