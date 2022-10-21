"""Test framers."""
from unittest.mock import Mock, patch

import pytest

from pymodbus.bit_read_message import ReadCoilsRequest
from pymodbus.client import ModbusBaseClient
from pymodbus.exceptions import ModbusIOException
from pymodbus.factory import ClientDecoder
from pymodbus.framer.ascii_framer import ModbusAsciiFramer
from pymodbus.framer.binary_framer import ModbusBinaryFramer
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.utilities import ModbusTransactionState


TEST_MESSAGE = b"\x00\x01\x00\x01\x00\n\xec\x1c"


@pytest.fixture
def rtu_framer():
    """RTU framer."""
    return ModbusRtuFramer(ClientDecoder())


@pytest.fixture
def ascii_framer():
    """Ascii framer."""
    return ModbusAsciiFramer(ClientDecoder())


# @pytest.fixture
# def binary_framer():
#     """Binary framer."""
#     return ModbusBinaryFramer(ClientDecoder())


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
    assert framer.client is None  # nosec
    assert framer._buffer == b""  # nosec pylint: disable=protected-access
    assert framer.decoder == decoder  # nosec
    if isinstance(framer, ModbusAsciiFramer):
        assert framer._header == {  # nosec pylint: disable=protected-access
            "lrc": "0000",
            "len": 0,
            "uid": 0x00,
        }
        assert framer._hsize == 0x02  # nosec pylint: disable=protected-access
        assert framer._start == b":"  # nosec pylint: disable=protected-access
        assert framer._end == b"\r\n"  # nosec pylint: disable=protected-access
    elif isinstance(framer, ModbusRtuFramer):
        assert framer._header == {  # nosec pylint: disable=protected-access
            "uid": 0x00,
            "len": 0,
            "crc": b"\x00\x00",
        }
        assert framer._hsize == 0x01  # nosec pylint: disable=protected-access
        assert framer._end == b"\x0d\x0a"  # nosec pylint: disable=protected-access
        assert framer._min_frame_size == 4  # nosec pylint: disable=protected-access
    else:
        assert framer._header == {  # nosec pylint: disable=protected-access
            "crc": 0x0000,
            "len": 0,
            "uid": 0x00,
        }
        assert framer._hsize == 0x01  # nosec pylint: disable=protected-access
        assert framer._start == b"\x7b"  # nosec pylint: disable=protected-access
        assert framer._end == b"\x7d"  # nosec pylint: disable=protected-access
        assert framer._repeat == [  # nosec pylint: disable=protected-access
            b"}"[0],
            b"{"[0],
        ]


@pytest.mark.parametrize("data", [(b"", {}), (b"abcd", {"fcode": 98, "unit": 97})])
def test_decode_data(rtu_framer, data):  # pylint: disable=redefined-outer-name
    """Test decode data."""
    data, expected = data
    decoded = rtu_framer.decode_data(data)
    assert decoded == expected  # nosec


@pytest.mark.parametrize(
    "data",
    [
        (b"", False),
        (b"\x02\x01\x01\x00Q\xcc", True),
        (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD", True),  # valid frame
        (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAC", False),  # invalid frame CRC
    ],
)
def test_check_frame(rtu_framer, data):  # pylint: disable=redefined-outer-name
    """Test check frame."""
    data, expected = data
    rtu_framer._buffer = data  # pylint: disable=protected-access
    assert expected == rtu_framer.checkFrame()  # nosec


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
def test_rtu_advance_framer(rtu_framer, data):  # pylint: disable=redefined-outer-name
    """Test rtu advance framer."""
    before_buf, before_header, after_buf = data

    rtu_framer._buffer = before_buf  # pylint: disable=protected-access
    rtu_framer._header = before_header  # pylint: disable=protected-access
    rtu_framer.advanceFrame()
    assert rtu_framer._header == {  # nosec pylint: disable=protected-access
        "uid": 0x00,
        "len": 0,
        "crc": b"\x00\x00",
    }
    assert rtu_framer._buffer == after_buf  # nosec pylint: disable=protected-access


@pytest.mark.parametrize("data", [b"", b"abcd"])
def test_rtu_reset_framer(rtu_framer, data):  # pylint: disable=redefined-outer-name
    """Test rtu reset framer."""
    rtu_framer._buffer = data  # pylint: disable=protected-access
    rtu_framer.resetFrame()
    assert rtu_framer._header == {  # nosec pylint: disable=protected-access
        "uid": 0x00,
        "len": 0,
        "crc": b"\x00\x00",
    }
    assert rtu_framer._buffer == b""  # nosec pylint: disable=protected-access


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
def test_is_frame_ready(rtu_framer, data):  # pylint: disable=redefined-outer-name
    """Test is frame ready."""
    data, expected = data
    rtu_framer._buffer = data  # pylint: disable=protected-access
    # rtu_framer.advanceFrame()
    assert rtu_framer.isFrameReady() == expected  # nosec


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
def test_rtu_populate_header_fail(
    rtu_framer, data
):  # pylint: disable=redefined-outer-name
    """Test rtu populate header fail."""
    with pytest.raises(IndexError):
        rtu_framer.populateHeader(data)


@pytest.mark.parametrize(
    "data",
    [
        (
            b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD",
            {"crc": b"\x49\xAD", "uid": 17, "len": 11},
        ),
        (
            b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\x11\x03",
            {"crc": b"\x49\xAD", "uid": 17, "len": 11},
        ),
    ],
)
def test_rtu_populate_header(rtu_framer, data):  # pylint: disable=redefined-outer-name
    """Test rtu populate header."""
    buffer, expected = data
    rtu_framer.populateHeader(buffer)
    assert rtu_framer._header == expected  # nosec pylint: disable=protected-access


def test_add_to_frame(rtu_framer):  # pylint: disable=redefined-outer-name
    """Test add to frame."""
    assert rtu_framer._buffer == b""  # nosec pylint: disable=protected-access
    rtu_framer.addToFrame(b"abcd")
    assert rtu_framer._buffer == b"abcd"  # nosec pylint: disable=protected-access


def test_get_frame(rtu_framer):  # pylint: disable=redefined-outer-name
    """Test get frame."""
    rtu_framer.addToFrame(b"\x02\x01\x01\x00Q\xcc")
    rtu_framer.populateHeader(b"\x02\x01\x01\x00Q\xcc")
    assert rtu_framer.getFrame() == b"\x01\x01\x00"  # nosec


def test_populate_result(rtu_framer):  # pylint: disable=redefined-outer-name
    """Test populate result."""
    rtu_framer._header["uid"] = 255  # pylint: disable=protected-access
    result = Mock()
    rtu_framer.populateResult(result)
    assert result.unit_id == 255  # nosec


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
            True,
            False,
        ),  # incorrect unit id
        (b"\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\x11\x03", 17, False, True),
        # good frame + part of next frame
    ],
)
def test_rtu_incoming_packet(rtu_framer, data):  # pylint: disable=redefined-outer-name
    """Test rtu process incoming packet."""
    buffer, units, reset_called, process_called = data

    with patch.object(
        rtu_framer,
        "_process",
        wraps=rtu_framer._process,  # pylint: disable=protected-access
    ) as mock_process, patch.object(
        rtu_framer, "resetFrame", wraps=rtu_framer.resetFrame
    ) as mock_reset:
        rtu_framer.processIncomingPacket(buffer, Mock(), units)
        assert mock_process.call_count == (1 if process_called else 0)  # nosec
        assert mock_reset.call_count == (1 if reset_called else 0)  # nosec


def test_build_packet(rtu_framer):  # pylint: disable=redefined-outer-name
    """Test build packet."""
    message = ReadCoilsRequest(1, 10)
    assert rtu_framer.buildPacket(message) == TEST_MESSAGE  # nosec


def test_send_packet(rtu_framer):  # pylint: disable=redefined-outer-name
    """Test send packet."""
    message = TEST_MESSAGE
    client = ModbusBaseClient(framer=ModbusRtuFramer)
    client.state = ModbusTransactionState.TRANSACTION_COMPLETE
    client.silent_interval = 1
    client.last_frame_end = 1
    client.params.timeout = 0.25
    client.idle_time = Mock(return_value=1)
    client.send = Mock(return_value=len(message))
    rtu_framer.client = client
    assert rtu_framer.sendPacket(message) == len(message)  # nosec
    client.state = ModbusTransactionState.PROCESSING_REPLY
    assert rtu_framer.sendPacket(message) == len(message)  # nosec


def test_recv_packet(rtu_framer):  # pylint: disable=redefined-outer-name
    """Test receive packet."""
    message = TEST_MESSAGE
    client = Mock()
    client.recv.return_value = message
    rtu_framer.client = client
    assert rtu_framer.recvPacket(len(message)) == message  # nosec


def test_process(rtu_framer):  # pylint: disable=redefined-outer-name
    """Test process."""

    rtu_framer._buffer = TEST_MESSAGE  # pylint: disable=protected-access
    with pytest.raises(ModbusIOException):
        rtu_framer._process(None)  # pylint: disable=protected-access


def test_get_raw_frame(rtu_framer):  # pylint: disable=redefined-outer-name
    """Test get raw frame."""
    rtu_framer._buffer = TEST_MESSAGE  # pylint: disable=protected-access
    assert (
        rtu_framer.getRawFrame()
        == rtu_framer._buffer  # nosec pylint: disable=protected-access
    )


def test_validate_unit_id(rtu_framer):  # pylint: disable=redefined-outer-name
    """Test validate unit."""
    rtu_framer.populateHeader(TEST_MESSAGE)
    assert rtu_framer._validate_unit_id(  # nosec pylint: disable=protected-access
        [0], False
    )
    assert rtu_framer._validate_unit_id(  # nosec pylint: disable=protected-access
        [1], True
    )


@pytest.mark.parametrize("data", [b":010100010001FC\r\n", b""])
def test_decode_ascii_data(ascii_framer, data):  # pylint: disable=redefined-outer-name
    """Test decode ascii."""
    data = ascii_framer.decode_data(data)
    assert isinstance(data, dict)  # nosec
    if data:
        assert data.get("unit") == 1  # nosec
        assert data.get("fcode") == 1  # nosec
    else:
        assert not data  # nosec
