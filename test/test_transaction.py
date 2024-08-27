"""Test transaction."""
from unittest import mock

from pymodbus.exceptions import (
    ModbusIOException,
)
from pymodbus.factory import ServerDecoder
from pymodbus.pdu import ModbusRequest
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
    ModbusTransactionManager,
    SyncModbusTransactionManager,
)


TEST_MESSAGE = b"\x7b\x01\x03\x00\x00\x00\x05\x85\xC9\x7d"


class TestTransaction:  # pylint: disable=too-many-public-methods
    """Unittest for the pymodbus.transaction module."""

    client = None
    decoder = None
    _tcp = None
    _tls = None
    _rtu = None
    _ascii = None
    _manager = None
    _tm = None

    # ----------------------------------------------------------------------- #
    # Test Construction
    # ----------------------------------------------------------------------- #
    def setup_method(self):
        """Set up the test environment."""
        self.client = None
        self.decoder = ServerDecoder()
        self._tcp = ModbusSocketFramer(decoder=self.decoder, client=None)
        self._tls = ModbusTlsFramer(decoder=self.decoder, client=None)
        self._rtu = ModbusRtuFramer(decoder=self.decoder, client=None)
        self._ascii = ModbusAsciiFramer(decoder=self.decoder, client=None)
        self._manager = SyncModbusTransactionManager(self.client, 3)

    # ----------------------------------------------------------------------- #
    # Modbus transaction manager
    # ----------------------------------------------------------------------- #

    def test_calculate_expected_response_length(self):
        """Test calculate expected response length."""
        self._manager.client = mock.MagicMock()
        self._manager.client.framer = mock.MagicMock()
        self._manager._set_adu_size()  # pylint: disable=protected-access
        assert not self._manager._calculate_response_length(  # pylint: disable=protected-access
            0
        )
        self._manager.base_adu_size = 10
        assert (
            self._manager._calculate_response_length(5)  # pylint: disable=protected-access
            == 15
        )

    def test_calculate_exception_length(self):
        """Test calculate exception length."""
        for framer, exception_length in (
            ("ascii", 11),
            ("rtu", 5),
            ("tcp", 9),
            ("tls", 2),
            ("dummy", None),
        ):
            self._manager.client = mock.MagicMock()
            if framer == "ascii":
                self._manager.client.framer = self._ascii
            elif framer == "rtu":
                self._manager.client.framer = self._rtu
            elif framer == "tcp":
                self._manager.client.framer = self._tcp
            elif framer == "tls":
                self._manager.client.framer = self._tls
            else:
                self._manager.client.framer = mock.MagicMock()

            self._manager._set_adu_size()  # pylint: disable=protected-access
            assert (
                self._manager._calculate_exception_length()  # pylint: disable=protected-access
                == exception_length
            )

    @mock.patch.object(SyncModbusTransactionManager, "_recv")
    @mock.patch.object(ModbusTransactionManager, "getTransaction")
    def test_execute(self, mock_get_transaction, mock_recv):
        """Test execute."""
        client = mock.MagicMock()
        client.framer = self._ascii
        client.framer._buffer = b"deadbeef"  # pylint: disable=protected-access
        client.framer.processIncomingPacket = mock.MagicMock()
        client.framer.processIncomingPacket.return_value = None
        client.framer.buildPacket = mock.MagicMock()
        client.framer.buildPacket.return_value = b"deadbeef"
        client.framer.sendPacket = mock.MagicMock()
        client.framer.sendPacket.return_value = len(b"deadbeef")
        client.framer.decode_data = mock.MagicMock()
        client.framer.decode_data.return_value = {
            "slave": 1,
            "fcode": 222,
            "length": 27,
        }
        request = mock.MagicMock()
        request.get_response_pdu_size.return_value = 10
        request.slave_id = 1
        request.function_code = 222
        trans = SyncModbusTransactionManager(client, 3)
        mock_recv.reset_mock(
            return_value=b"abcdef"
        )
        assert trans.retries == 3

        mock_get_transaction.return_value = b"response"
        response = trans.execute(request)
        assert response == b"response"
        # No response
        mock_recv.reset_mock(
            return_value=b"abcdef"
        )
        trans.transactions = {}
        mock_get_transaction.return_value = None
        response = trans.execute(request)
        assert isinstance(response, ModbusIOException)

        # No response with retries
        mock_recv.reset_mock(
            side_effect=iter([b"", b"abcdef"])
        )
        response = trans.execute(request)
        assert isinstance(response, ModbusIOException)

        # wrong handle_local_echo
        mock_recv.reset_mock(
            side_effect=iter([b"abcdef", b"deadbe", b"123456"])
        )
        client.comm_params.handle_local_echo = True
        assert trans.execute(request).message == "[Input/Output] Wrong local echo"
        client.comm_params.handle_local_echo = False

        # retry on invalid response
        mock_recv.reset_mock(
            side_effect=iter([b"", b"abcdef", b"deadbe", b"123456"])
        )
        response = trans.execute(request)
        assert isinstance(response, ModbusIOException)

        # Unable to decode response
        mock_recv.reset_mock(
            side_effect=ModbusIOException()
        )
        client.framer.processIncomingPacket.side_effect = mock.MagicMock(
            side_effect=ModbusIOException()
        )
        assert isinstance(trans.execute(request), ModbusIOException)

    def test_transaction_manager_tid(self):
        """Test the transaction manager TID."""
        for tid in range(1, self._manager.getNextTID() + 10):
            assert tid + 1 == self._manager.getNextTID()
        self._manager.reset()
        assert self._manager.getNextTID() == 1

    def test_get_transaction_manager_transaction(self):
        """Test the getting a transaction from the transaction manager."""
        self._manager.reset()
        handle = ModbusRequest(
            0, self._manager.getNextTID(), 0, False
        )
        self._manager.addTransaction(handle)
        result = self._manager.getTransaction(handle.transaction_id)
        assert handle is result

    def test_delete_transaction_manager_transaction(self):
        """Test deleting a transaction from the dict transaction manager."""
        self._manager.reset()
        handle = ModbusRequest(
            0, self._manager.getNextTID(), 0, False
        )
        self._manager.addTransaction(handle)
        self._manager.delTransaction(handle.transaction_id)
        assert not self._manager.getTransaction(handle.transaction_id)

    # ----------------------------------------------------------------------- #
    # TCP tests
    # ----------------------------------------------------------------------- #
    def test_tcp_framer_transaction_ready(self):
        """Test a tcp frame transaction."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00\x08"
        self._tcp.processIncomingPacket(msg, callback, [1])
        self._tcp._buffer = msg  # pylint: disable=protected-access
        callback(b'')

    def test_tcp_framer_transaction_full(self):
        """Test a full tcp frame transaction."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00\x08"
        self._tcp.processIncomingPacket(msg, callback, [0, 1])
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg[7:]

    def test_tcp_framer_transaction_half(self):
        """Test a half completed tcp frame transaction."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg1 = b"\x00\x01\x12\x34\x00"
        msg2 = b"\x06\xff\x02\x01\x02\x00\x08"
        self._tcp.processIncomingPacket(msg1, callback, [0, 1])
        assert not result
        self._tcp.processIncomingPacket(msg2, callback, [0, 1])
        assert result
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg2[2:]

    def test_tcp_framer_transaction_half2(self):
        """Test a half completed tcp frame transaction."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg1 = b"\x00\x01\x12\x34\x00\x06\xff"
        msg2 = b"\x02\x01\x02\x00\x08"
        self._tcp.processIncomingPacket(msg1, callback, [0, 1])
        assert not result
        self._tcp.processIncomingPacket(msg2, callback, [0, 1])
        assert result
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg2

    def test_tcp_framer_transaction_half3(self):
        """Test a half completed tcp frame transaction."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg1 = b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00"
        msg2 = b"\x08"
        self._tcp.processIncomingPacket(msg1, callback, [0, 1])
        assert not result
        self._tcp.processIncomingPacket(msg2, callback, [0, 1])
        assert result
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg1[7:] + msg2

    def test_tcp_framer_transaction_short(self):
        """Test that we can get back on track after an invalid message."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        # msg1 = b"\x99\x99\x99\x99\x00\x01\x00\x17"
        msg1 = b''
        msg2 = b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00\x08"
        self._tcp.processIncomingPacket(msg1, callback, [0, 1])
        assert not result
        self._tcp.processIncomingPacket(msg2, callback, [0, 1])
        assert result
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg2[7:]

    def test_tcp_framer_populate(self):
        """Test a tcp frame packet build."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        expected = ModbusRequest(0, 0, 0, False)
        expected.transaction_id = 0x0001
        expected.protocol_id = 0x1234
        expected.slave_id = 0xFF
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        self._tcp.processIncomingPacket(msg, callback, [0, 1])
        # assert self._tcp.checkFrame()
        # actual = ModbusRequest()
        # self._tcp.populateResult(actual)
        # for name in ("transaction_id", "protocol_id", "slave_id"):
        #     assert getattr(expected, name) == getattr(actual, name)

    @mock.patch.object(ModbusRequest, "encode")
    def test_tcp_framer_packet(self, mock_encode):
        """Test a tcp frame packet build."""
        message = ModbusRequest(0, 0, 0, False)
        message.transaction_id = 0x0001
        message.protocol_id = 0x0000
        message.slave_id = 0xFF
        message.function_code = 0x01
        expected = b"\x00\x01\x00\x00\x00\x02\xff\x01"
        mock_encode.return_value = b""
        actual = self._tcp.buildPacket(message)
        assert expected == actual

    # ----------------------------------------------------------------------- #
    # TLS tests
    # ----------------------------------------------------------------------- #
    def test_framer_tls_framer_transaction_ready(self):
        """Test a tls frame transaction."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        self._tcp.processIncomingPacket(msg[0:4], callback, [0, 1])
        assert not result
        self._tcp.processIncomingPacket(msg[4:], callback, [0, 1])
        assert result

    def test_framer_tls_framer_transaction_full(self):
        """Test a full tls frame transaction."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        self._tcp.processIncomingPacket(msg, callback, [0, 1])
        assert result

    def test_framer_tls_framer_transaction_half(self):
        """Test a half completed tls frame transaction."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        self._tcp.processIncomingPacket(msg[0:8], callback, [0, 1])
        assert not result
        self._tcp.processIncomingPacket(msg[8:], callback, [0, 1])
        assert result

    def test_framer_tls_framer_transaction_short(self):
        """Test that we can get back on track after an invalid message."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        self._tcp.processIncomingPacket(msg[0:2], callback, [0, 1])
        assert not result
        self._tcp.processIncomingPacket(msg[2:], callback, [0, 1])
        assert result

    def test_framer_tls_framer_decode(self):
        """Testmessage decoding."""
        msg1 = b""
        msg2 = b"\x01\x12\x34\x00\x08"
        result = self._tls.decode_data(msg1)
        assert not result
        result = self._tls.decode_data(msg2)
        assert result == {"fcode": 1}

    def test_framer_tls_incoming_packet(self):
        """Framer tls incoming packet."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"

        slave = 0x01
        msg_result = None

        def mock_callback(result):
            """Mock callback."""
            nonlocal msg_result

            msg_result = result.encode()

        self._tls.processIncomingPacket(msg, mock_callback, slave)
        # assert msg == msg_result

        # self._tls.isFrameReady = mock.MagicMock(return_value=True)
        # x = mock.MagicMock(return_value=False)
        # self._tls._validate_slave_id = x
        # self._tls.processIncomingPacket(msg, mock_callback, slave)
        # assert not self._tls._buffer
        # self._tls.advanceFrame()
        # x = mock.MagicMock(return_value=True)
        # self._tls._validate_slave_id = x
        # self._tls.processIncomingPacket(msg, mock_callback, slave)
        # assert msg[1:] == msg_result
        # self._tls.advanceFrame()

    def test_framer_tls_process(self):
        """Framer tls process."""
        # class MockResult:
        #     """Mock result."""

        #     def __init__(self, code):
        #         """Init."""
        #         self.function_code = code

        # def mock_callback(_arg):
        #     """Mock callback."""

        # self._tls.decoder.decode = mock.MagicMock(return_value=None)
        # with pytest.raises(ModbusIOException):
        #     self._tls._process(mock_callback)

        # result = MockResult(0x01)
        # self._tls.decoder.decode = mock.MagicMock(return_value=result)
        # with pytest.raises(InvalidMessageReceivedException):
        #    self._tls._process(
        #         mock_callback, error=True
        #     )
        # self._tls._process(mock_callback)
        # assert not self._tls._buffer

    def test_framer_tls_framer_populate(self):
        """Test a tls frame packet build."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        self._tcp.processIncomingPacket(msg, callback, [0, 1])
        assert result

    @mock.patch.object(ModbusRequest, "encode")
    def test_framer_tls_framer_packet(self, mock_encode):
        """Test a tls frame packet build."""
        message = ModbusRequest(0, 0, 0, False)
        message.function_code = 0x01
        expected = b"\x01"
        mock_encode.return_value = b""
        actual = self._tls.buildPacket(message)
        assert expected == actual

    # ----------------------------------------------------------------------- #
    # RTU tests
    # ----------------------------------------------------------------------- #
    def test_rtu_framer_transaction_ready(self):
        """Test if the checks for a complete frame work."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg_parts = [b"\x00\x01\x00", b"\x00\x00\x01\xfc\x1b"]
        self._rtu.processIncomingPacket(msg_parts[0], callback, [0, 1])
        assert not result
        self._rtu.processIncomingPacket(msg_parts[1], callback, [0, 1])
        assert result

    def test_rtu_framer_transaction_full(self):
        """Test a full rtu frame transaction."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        self._rtu.processIncomingPacket(msg, callback, [0, 1])
        assert result

    def test_rtu_framer_transaction_half(self):
        """Test a half completed rtu frame transaction."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg_parts = [b"\x00\x01\x00", b"\x00\x00\x01\xfc\x1b"]
        self._rtu.processIncomingPacket(msg_parts[0], callback, [0, 1])
        assert not result
        self._rtu.processIncomingPacket(msg_parts[1], callback, [0, 1])
        assert result

    def test_rtu_framer_populate(self):
        """Test a rtu frame packet build."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        self._rtu.processIncomingPacket(msg, callback, [0, 1])
        header_dict = self._rtu._header  # pylint: disable=protected-access
        assert len(msg) == header_dict["len"]
        assert int(msg[0]) == header_dict["uid"]
        assert msg[-2:] == header_dict["crc"]

    @mock.patch.object(ModbusRequest, "encode")
    def test_rtu_framer_packet(self, mock_encode):
        """Test a rtu frame packet build."""
        message = ModbusRequest(0, 0, 0, False)
        message.slave_id = 0xFF
        message.function_code = 0x01
        expected = b"\xff\x01\x81\x80"  # only header + CRC - no data
        mock_encode.return_value = b""
        actual = self._rtu.buildPacket(message)
        assert expected == actual

    def test_rtu_decode_exception(self):
        """Test that the RTU framer can decode errors."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b"\x00\x90\x02\x9c\x01"
        self._rtu.processIncomingPacket(msg, callback, [0, 1])
        assert result

    def test_process(self):
        """Test process."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        self._rtu.processIncomingPacket(msg, callback, [0, 1])
        assert result

    def test_rtu_process_incoming_packets(self):
        """Test rtu process incoming packets."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        slave = 0x00

        self._rtu.processIncomingPacket(msg, callback, slave)
        assert result

    # ----------------------------------------------------------------------- #
    # ASCII tests
    # ----------------------------------------------------------------------- #
    def test_ascii_framer_transaction_ready(self):
        """Test a ascii frame transaction."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b":F7031389000A60\r\n"
        self._ascii.processIncomingPacket(msg, callback, [0,1])
        assert result

    def test_ascii_framer_transaction_full(self):
        """Test a full ascii frame transaction."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b"sss:F7031389000A60\r\n"
        self._ascii.processIncomingPacket(msg, callback, [0,1])
        assert result

    def test_ascii_framer_transaction_half(self):
        """Test a half completed ascii frame transaction."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg_parts = (b"sss:F7031389", b"000A60\r\n")
        self._ascii.processIncomingPacket(msg_parts[0], callback, [0,1])
        assert not result
        self._ascii.processIncomingPacket(msg_parts[1], callback, [0,1])
        assert result

    def test_ascii_framer_populate(self):
        """Test a ascii frame packet build."""
        request = ModbusRequest(0, 0, 0, False)
        self._ascii.populateResult(request)
        assert not request.slave_id

    @mock.patch.object(ModbusRequest, "encode")
    def test_ascii_framer_packet(self, mock_encode):
        """Test a ascii frame packet build."""
        message = ModbusRequest(0, 0, 0, False)
        message.slave_id = 0xFF
        message.function_code = 0x01
        expected = b":FF0100\r\n"
        mock_encode.return_value = b""
        actual = self._ascii.buildPacket(message)
        assert expected == actual

    def test_ascii_process_incoming_packets(self):
        """Test ascii process incoming packet."""
        count = 0
        result = None
        def callback(data):
            """Simulate callback."""
            nonlocal count, result
            count += 1
            result = data

        msg = b":F7031389000A60\r\n"
        self._ascii.processIncomingPacket(msg, callback, [0,1])
        assert result
