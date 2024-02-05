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


@pytest.fixture(name="rtu_framer")
def fixture_rtu_framer():
    """RTU framer."""
    return ModbusRtuFramer(ClientDecoder())

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
def test_framer_initialization(framer):
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
    "data",
    [
        (b"", False),
        (b"\x02\x01\x01\x00Q\xcc", True),
        (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD", True),  # valid frame
        (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAC", False),  # invalid frame CRC
    ],
)
def test_check_frame(rtu_framer, data):
    """Test check frame."""
    data, expected = data
    rtu_framer._buffer = data  # pylint: disable=protected-access
    assert expected == rtu_framer.checkFrame()


@pytest.mark.parametrize(
    "data",
    [
        (b"", {"uid": 0x00, "len": 0, "crc": b"\x00\x00"}, b""),
        (b"abcd", {"uid": 0x00, "len": 2, "crc": b"\x00\x00"}, b"cd"),
        (
            b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\x12\x03",  # real case, frame size is 11
            {"uid": 0x00, "len": 11, "crc": b"\x00\x00"},
            b"\x12\x03",
        ),
    ],
)
def test_rtu_advance_framer(rtu_framer, data):
    """Test rtu advance framer."""
    before_buf, before_header, after_buf = data

    rtu_framer._buffer = before_buf  # pylint: disable=protected-access
    rtu_framer._header = before_header  # pylint: disable=protected-access
    rtu_framer.advanceFrame()
    assert rtu_framer._header == {  # pylint: disable=protected-access
        "uid": 0x00,
        "len": 0,
        "crc": b"\x00\x00",
    }
    assert rtu_framer._buffer == after_buf  # pylint: disable=protected-access


@pytest.mark.parametrize("data", [b"", b"abcd"])
def test_rtu_reset_framer(rtu_framer, data):
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
    "data",
    [
        (b"", False),
        (b"\x11", False),
        (b"\x11\x03", False),
        (b"\x11\x03\x06", False),
        (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49", False),
        (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD", True),
        (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\xAB\xCD", True),
    ],
)
def test_is_frame_ready(rtu_framer, data):
    """Test is frame ready."""
    data, expected = data
    rtu_framer._buffer = data  # pylint: disable=protected-access
    # rtu_framer.advanceFrame()
    assert rtu_framer.isFrameReady() == expected


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
def test_rtu_populate_header_fail(rtu_framer, data):
    """Test rtu populate header fail."""
    with pytest.raises(IndexError):
        rtu_framer.populateHeader(data)


@pytest.mark.parametrize(
    "data",
    [
        (
            b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD",
            {
                "crc": b"\x49\xAD",
                "uid": 17,
                "len": 11,
                "lrc": "0000",
                "tid": 17,
                "pid": 0,
            },
        ),
        (
            b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\x11\x03",
            {
                "crc": b"\x49\xAD",
                "uid": 17,
                "len": 11,
                "lrc": "0000",
                "tid": 17,
                "pid": 0,
            },
        ),
    ],
)
def test_rtu_populate_header(rtu_framer, data):
    """Test rtu populate header."""
    buffer, expected = data
    rtu_framer.populateHeader(buffer)
    assert rtu_framer._header == expected  # pylint: disable=protected-access


def test_get_frame(rtu_framer):
    """Test get frame."""
    rtu_framer._buffer = b"\x02\x01\x01\x00Q\xcc"  # pylint: disable=protected-access
    rtu_framer.populateHeader(b"\x02\x01\x01\x00Q\xcc")
    assert rtu_framer.getFrame() == b"\x01\x01\x00"


def test_populate_result(rtu_framer):
    """Test populate result."""
    rtu_framer._header["uid"] = 255  # pylint: disable=protected-access
    result = mock.Mock()
    rtu_framer.populateResult(result)
    assert result.slave_id == 255


@pytest.mark.parametrize(
    "data",
    [
        (b"\x11", 17, False, False),  # not complete frame
        (b"\x11\x03", 17, False, False),  # not complete frame
        (b"\x11\x03\x06", 17, False, False),  # not complete frame
        (b"\x11\x03\x06\xAE\x41\x56\x52\x43", 17, False, False),  # not complete frame
        (
            b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40",
            17,
            False,
            False,
        ),  # not complete frame
        (
            b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49",
            17,
            False,
            False,
        ),  # not complete frame
        (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAC", 17, True, False),  # bad crc
        (
            b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD",
            17,
            False,
            True,
        ),  # good frame
        (
            b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD",
            16,
            False,
            False,
        ),  # incorrect slave id
        (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\x11\x03", 17, False, True),
        # good frame + part of next frame
    ],
)
def test_rtu_incoming_packet(rtu_framer, data):
    """Test rtu process incoming packet."""
    buffer, slaves, reset_called, process_called = data

    with mock.patch.object(
        rtu_framer,
        "_process",
        wraps=rtu_framer._process,  # pylint: disable=protected-access
    ) as mock_process, mock.patch.object(
        rtu_framer, "resetFrame", wraps=rtu_framer.resetFrame
    ) as mock_reset:
        rtu_framer.processIncomingPacket(buffer, mock.Mock(), slaves)
        assert mock_process.call_count == (1 if process_called else 0)
        assert mock_reset.call_count == (1 if reset_called else 0)


def test_send_packet(rtu_framer):
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


def test_recv_packet(rtu_framer):
    """Test receive packet."""
    message = TEST_MESSAGE
    client = mock.Mock()
    client.recv.return_value = message
    rtu_framer.client = client
    assert rtu_framer.recvPacket(len(message)) == message

def test_process(rtu_framer):
    """Test process."""
    rtu_framer._buffer = TEST_MESSAGE  # pylint: disable=protected-access
    with pytest.raises(ModbusIOException):
        rtu_framer._process(None)  # pylint: disable=protected-access


def test_validate__slave_id(rtu_framer):
    """Test validate slave."""
    rtu_framer.populateHeader(TEST_MESSAGE)
    assert rtu_framer._validate_slave_id([0], False)  # pylint: disable=protected-access
    assert rtu_framer._validate_slave_id([1], True)  # pylint: disable=protected-access


@pytest.mark.parametrize("data", [b":010100010001FC\r\n", b""])
def test_decode_ascii_data(ascii_framer, data):
    """Test decode ascii."""
    data = ascii_framer.decode_data(data)
    assert isinstance(data, dict)
    if data:
        assert data.get("slave") == 1
        assert data.get("fcode") == 1
    else:
        assert not data

def test_recv_split_packet():
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


def test_recv_socket_exception_packet():
    """Test receive packet."""
    response_ok = False

    def _handle_response(_reply):
        """Handle response."""
        nonlocal response_ok
        response_ok = True

    message = bytearray(b"\x00\x02\x00\x00\x00\x02\x01\x84\x02")
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
def test_build_packet(framer, message):
    """Test build packet."""
    test_framer =  framer(ClientDecoder())
    request = ReadCoilsRequest(1, 10)
    assert test_framer.buildPacket(request) == message


@pytest.mark.parametrize(
    ("framer", "message"),
    [
        (ModbusAsciiFramer, b':00010001000AF4\r\n',),
        (ModbusBinaryFramer, b'{\x00\x01\x00\x01\x00\n\xec\x1c}',),
        (ModbusRtuFramer, b"\x00\x01\x00\x01\x00\n\xec\x1c",),
        (ModbusSocketFramer, b'\x00\x00\x00\x00\x00\x06\x00\x01\x00\x01\x00\n',),
    ]
)
def test_processincomingpacket(framer, message):
    """Test processIncomingPacket."""
    test_framer =  framer(ClientDecoder())
    with mock.patch.object(
        framer,
        "_process",
        wraps=test_framer._process,  # pylint: disable=protected-access
    ), mock.patch.object(
        test_framer, "resetFrame", wraps=test_framer.resetFrame
    ):
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
def test_decode_data(framer, message, expected):
    """Test decode data."""
    test_framer =  framer(ClientDecoder())
    decoded = test_framer.decode_data(b'')
    assert decoded == {}
    decoded = test_framer.decode_data(message)
    assert decoded["fcode"] == expected["fcode"]
    assert decoded["slave"] == expected["slave"]
