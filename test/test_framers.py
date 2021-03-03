import pytest
from pymodbus.factory import ClientDecoder
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.framer.ascii_framer import ModbusAsciiFramer
from pymodbus.framer.binary_framer import ModbusBinaryFramer
from pymodbus.utilities import ModbusTransactionState
from pymodbus.bit_read_message import ReadCoilsRequest
from pymodbus.exceptions import ModbusIOException
from pymodbus.compat import IS_PYTHON3
if IS_PYTHON3:
    from unittest.mock import Mock, patch
else:  # Python 2
    from mock import Mock, patch


@pytest.fixture
def rtu_framer():
    return ModbusRtuFramer(ClientDecoder())


@pytest.fixture
def ascii_framer():
    return ModbusAsciiFramer(ClientDecoder())


@pytest.fixture
def binary_framer():
    return ModbusBinaryFramer(ClientDecoder())


@pytest.mark.parametrize("framer",  [ModbusRtuFramer,
                                     ModbusAsciiFramer,
                                     ModbusBinaryFramer,
                                     ])
def test_framer_initialization(framer):
    decoder = ClientDecoder()
    framer = framer(decoder)
    assert framer.client == None
    assert framer._buffer == b''
    assert framer.decoder == decoder
    if isinstance(framer, ModbusAsciiFramer):
        assert framer._header == {'lrc': '0000', 'len': 0, 'uid': 0x00}
        assert framer._hsize == 0x02
        assert framer._start == b':'
        assert framer._end == b"\r\n"
    elif isinstance(framer, ModbusRtuFramer):
        assert framer._header == {'uid': 0x00, 'len': 0, 'crc': b'\x00\x00'}
        assert framer._hsize == 0x01
        assert framer._end == b'\x0d\x0a'
        assert framer._min_frame_size == 4
    else:
        assert framer._header == {'crc': 0x0000, 'len': 0, 'uid': 0x00}
        assert framer._hsize == 0x01
        assert framer._start == b'\x7b'
        assert framer._end == b'\x7d'
        assert framer._repeat == [b'}'[0], b'{'[0]]


@pytest.mark.parametrize("data", [(b'', {}),
                                  (b'abcd', {'fcode': 98, 'unit': 97})])
def test_decode_data(rtu_framer, data):
    data, expected = data
    decoded = rtu_framer.decode_data(data)
    assert decoded == expected


@pytest.mark.parametrize("data", [
    (b'', False),
    (b'\x02\x01\x01\x00Q\xcc', True),
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD', True),  # valid frame
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAC', False),  # invalid frame CRC
])
def test_check_frame(rtu_framer, data):
    data, expected = data
    rtu_framer._buffer = data
    assert expected == rtu_framer.checkFrame()


@pytest.mark.parametrize("data", [
    (b'', {'uid': 0x00, 'len': 0, 'crc': b'\x00\x00'}, b''),
    (b'abcd', {'uid': 0x00, 'len': 2, 'crc': b'\x00\x00'}, b'cd'),
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\x12\x03',  # real case, frame size is 11
     {'uid': 0x00, 'len': 11, 'crc': b'\x00\x00'}, b'\x12\x03'),
])
def test_rtu_advance_framer(rtu_framer, data):
    before_buf, before_header, after_buf = data

    rtu_framer._buffer = before_buf
    rtu_framer._header = before_header
    rtu_framer.advanceFrame()
    assert rtu_framer._header == {'uid': 0x00, 'len': 0, 'crc': b'\x00\x00'}
    assert rtu_framer._buffer == after_buf


@pytest.mark.parametrize("data", [b'', b'abcd'])
def test_rtu_reset_framer(rtu_framer, data):
    rtu_framer._buffer = data
    rtu_framer.resetFrame()
    assert rtu_framer._header == {'uid': 0x00, 'len': 0, 'crc': b'\x00\x00'}
    assert rtu_framer._buffer == b''


@pytest.mark.parametrize("data", [
    (b'', False),
    (b'\x11', False),
    (b'\x11\x03', False),
    (b'\x11\x03\x06', False),
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49', False),
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD', True),
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\xAB\xCD', True),
])
def test_is_frame_ready(rtu_framer, data):
    data, expected = data
    rtu_framer._buffer = data
    # rtu_framer.advanceFrame()
    assert rtu_framer.isFrameReady() == expected


@pytest.mark.parametrize("data", [
    b'',
    b'\x11',
    b'\x11\x03',
    b'\x11\x03\x06',
    b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x43',
])
def test_rtu_populate_header_fail(rtu_framer, data):
    with pytest.raises(IndexError):
        rtu_framer.populateHeader(data)


@pytest.mark.parametrize("data", [
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD', {'crc': b'\x49\xAD', 'uid': 17, 'len': 11}),
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\x11\x03', {'crc': b'\x49\xAD', 'uid': 17, 'len': 11})
])
def test_rtu_populate_header(rtu_framer, data):
    buffer, expected = data
    rtu_framer.populateHeader(buffer)
    assert rtu_framer._header == expected


def test_add_to_frame(rtu_framer):
    assert rtu_framer._buffer == b''
    rtu_framer.addToFrame(b'abcd')
    assert rtu_framer._buffer == b'abcd'


def test_get_frame(rtu_framer):
    rtu_framer.addToFrame(b'\x02\x01\x01\x00Q\xcc')
    rtu_framer.populateHeader(b'\x02\x01\x01\x00Q\xcc')
    assert rtu_framer.getFrame() == b'\x01\x01\x00'


def test_populate_result(rtu_framer):
    rtu_framer._header['uid'] = 255
    result = Mock()
    rtu_framer.populateResult(result)
    assert result.unit_id == 255


@pytest.mark.parametrize("data", [
    (b'\x11', 17, False, False),  # not complete frame
    (b'\x11\x03', 17, False, False),  # not complete frame
    (b'\x11\x03\x06', 17, False, False),  # not complete frame
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43', 17, False, False),  # not complete frame
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40', 17, False, False),  # not complete frame
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49', 17, False, False),  # not complete frame
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAC', 17, True, False),  # bad crc
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD', 17, False, True),  # good frame
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD', 16, True, False),  # incorrect unit id
    (b'\x11\x03\x06\xAE\x41\x56\x52\x43\x40\x49\xAD\x11\x03', 17, False, True),  # good frame + part of next frame
])
def test_rtu_process_incoming_packet(rtu_framer, data):
    buffer, units, reset_called, process_called = data

    with patch.object(rtu_framer, '_process') as mock_process, \
            patch.object(rtu_framer, 'resetFrame') as mock_reset:
        rtu_framer.processIncomingPacket(buffer, Mock(), units)
        assert mock_process.call_count == (1 if process_called else 0)
        assert mock_reset.call_count == (1 if reset_called else 0)


def test_build_packet(rtu_framer):
    message = ReadCoilsRequest(1, 10)
    assert rtu_framer.buildPacket(message) == b'\x00\x01\x00\x01\x00\n\xec\x1c'


def test_send_packet(rtu_framer):
    message = b'\x00\x01\x00\x01\x00\n\xec\x1c'
    client = Mock()
    client.state = ModbusTransactionState.TRANSACTION_COMPLETE
    client.silent_interval = 1
    client.last_frame_end = 1
    client.timeout = 0.25
    client.idle_time.return_value = 1
    client.send.return_value = len(message)
    rtu_framer.client = client
    assert rtu_framer.sendPacket(message) == len(message)
    client.state = ModbusTransactionState.PROCESSING_REPLY
    assert rtu_framer.sendPacket(message) == len(message)


def test_recv_packet(rtu_framer):
    message = b'\x00\x01\x00\x01\x00\n\xec\x1c'
    client = Mock()
    client.recv.return_value = message
    rtu_framer.client = client
    assert rtu_framer.recvPacket(len(message)) == message


def test_process(rtu_framer):
    def cb(res):
        return res

    rtu_framer._buffer = b'\x00\x01\x00\x01\x00\n\xec\x1c'
    with pytest.raises(ModbusIOException):
        rtu_framer._process(cb)


def test_get_raw_frame(rtu_framer):
    rtu_framer._buffer = b'\x00\x01\x00\x01\x00\n\xec\x1c'
    assert rtu_framer.getRawFrame() == rtu_framer._buffer


def test_validate_unit_id(rtu_framer):
    rtu_framer.populateHeader( b'\x00\x01\x00\x01\x00\n\xec\x1c')
    assert rtu_framer._validate_unit_id([0], False)
    assert rtu_framer._validate_unit_id([1], True)


@pytest.mark.parametrize('data', [b':010100010001FC\r\n',
                         b''])
def test_decode_ascii_data(ascii_framer, data):
    data = ascii_framer.decode_data(data)
    assert isinstance(data, dict)
    if data:
        assert data.get("unit") == 1
        assert data.get("fcode") == 1
    else:
        assert not data
