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
    from unittest.mock import Mock
else:  # Python 2
    from mock import Mock

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
        assert framer._header == {'uid': 0x00, 'len': 0, 'crc': '0000'}
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


@pytest.mark.parametrize("data", [(b'', False),
                                  (b'\x02\x01\x01\x00Q\xcc', True)])
def test_check_frame(rtu_framer, data):
    data, expected = data
    rtu_framer._buffer = data
    assert expected == rtu_framer.checkFrame()


@pytest.mark.parametrize("data", [b'', b'abcd'])
def test_advance_framer(rtu_framer, data):
    rtu_framer._buffer = data
    rtu_framer.advanceFrame()
    assert rtu_framer._header == {}
    assert rtu_framer._buffer == data


@pytest.mark.parametrize("data", [b'', b'abcd'])
def test_reset_framer(rtu_framer, data):
    rtu_framer._buffer = data
    rtu_framer.resetFrame()
    assert rtu_framer._header == {}
    assert rtu_framer._buffer == b''


@pytest.mark.parametrize("data", [(b'', False), (b'abcd', True)])
def test_is_frame_ready(rtu_framer, data):
    data, expected = data
    rtu_framer._buffer = data
    rtu_framer.advanceFrame()
    assert rtu_framer.isFrameReady() == expected


def test_populate_header(rtu_framer):
    rtu_framer.populateHeader(b'abcd')
    assert rtu_framer._header == {'crc': b'd', 'uid': 97, 'len': 5}


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


def test_process_incoming_packet(rtu_framer):
    def cb(res):
        return res


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