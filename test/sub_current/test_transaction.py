"""Test transaction."""
from unittest import mock

from pymodbus.exceptions import (
    ModbusIOException,
)
from pymodbus.factory import ServerDecoder
from pymodbus.framer import (
    FramerAscii,
    FramerRTU,
    FramerSocket,
    FramerTLS,
)
from pymodbus.pdu import ModbusRequest
from pymodbus.transaction import (
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
        self._tcp = FramerSocket(self.decoder, [])
        self._tls = FramerTLS(self.decoder, [])
        self._rtu = FramerRTU(self.decoder, [])
        self._ascii = FramerAscii(self.decoder, [])
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
        client.framer.processIncomingFrame = mock.MagicMock()
        client.framer.processIncomingFrame.return_value = None
        client.framer.buildFrame = mock.MagicMock()
        client.framer.buildFrame.return_value = b"deadbeef"
        client.send = mock.MagicMock()
        client.send.return_value = len(b"deadbeef")
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
        client.framer.processIncomingFrame.side_effect = mock.MagicMock(
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
            0, self._manager.getNextTID(), False
        )
        self._manager.addTransaction(handle)
        result = self._manager.getTransaction(handle.transaction_id)
        assert handle is result

    def test_delete_transaction_manager_transaction(self):
        """Test deleting a transaction from the dict transaction manager."""
        self._manager.reset()
        handle = ModbusRequest(
            0, self._manager.getNextTID(), False
        )
        self._manager.addTransaction(handle)
        self._manager.delTransaction(handle.transaction_id)
        assert not self._manager.getTransaction(handle.transaction_id)

    # ----------------------------------------------------------------------- #
    # TCP tests
    # ----------------------------------------------------------------------- #
    def test_tcp_framer_transaction_ready(self):
        """Test a tcp frame transaction."""

        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00\x08"
        assert self._tcp.processIncomingFrame(msg)
        self._tcp.databuffer = msg

    def test_tcp_framer_transaction_full(self):
        """Test a full tcp frame transaction."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00\x08"
        result = self._tcp.processIncomingFrame(msg)
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg[7:]

    def test_tcp_framer_transaction_half(self):
        """Test a half completed tcp frame transaction."""
        msg1 = b"\x00\x01\x12\x34\x00"
        msg2 = b"\x06\xff\x02\x01\x02\x00\x08"
        assert not self._tcp.processIncomingFrame(msg1)
        result = self._tcp.processIncomingFrame(msg2)
        assert result
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg2[2:]

    def test_tcp_framer_transaction_half2(self):
        """Test a half completed tcp frame transaction."""
        msg1 = b"\x00\x01\x12\x34\x00\x06\xff"
        msg2 = b"\x02\x01\x02\x00\x08"
        assert not self._tcp.processIncomingFrame(msg1)
        result = self._tcp.processIncomingFrame(msg2)
        assert result
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg2

    def test_tcp_framer_transaction_half3(self):
        """Test a half completed tcp frame transaction."""
        msg1 = b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00"
        msg2 = b"\x08"
        assert not self._tcp.processIncomingFrame(msg1)
        result = self._tcp.processIncomingFrame(msg2)
        assert result
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg1[7:] + msg2

    def test_tcp_framer_transaction_short(self):
        """Test that we can get back on track after an invalid message."""
        msg1 = b''
        msg2 = b"\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00\x08"
        assert not self._tcp.processIncomingFrame(msg1)
        result = self._tcp.processIncomingFrame(msg2)
        assert result
        assert result.function_code.to_bytes(1,'big') + result.encode() == msg2[7:]

    def test_tcp_framer_populate(self):
        """Test a tcp frame packet build."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        result = self._tcp.processIncomingFrame(msg)
        assert result
        assert result.slave_id == 0xFF
        assert result.transaction_id == 0x0001

    @mock.patch.object(ModbusRequest, "encode")
    def test_tcp_framer_packet(self, mock_encode):
        """Test a tcp frame packet build."""
        message = ModbusRequest(0, 0, False)
        message.transaction_id = 0x0001
        message.slave_id = 0xFF
        message.function_code = 0x01
        expected = b"\x00\x01\x00\x00\x00\x02\xff\x01"
        mock_encode.return_value = b""
        actual = self._tcp.buildFrame(message)
        assert expected == actual

    # ----------------------------------------------------------------------- #
    # TLS tests
    # ----------------------------------------------------------------------- #
    def test_framer_tls_framer_transaction_ready(self):
        """Test a tls frame transaction."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        assert not self._tcp.processIncomingFrame(msg[0:4])
        assert self._tcp.processIncomingFrame(msg[4:])

    def test_framer_tls_framer_transaction_full(self):
        """Test a full tls frame transaction."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        assert self._tcp.processIncomingFrame(msg)

    def test_framer_tls_incoming_packet(self):
        """Framer tls incoming packet."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        result = self._tls.processIncomingFrame(msg)
        assert result

    def test_framer_tls_framer_populate(self):
        """Test a tls frame packet build."""
        msg = b"\x00\x01\x12\x34\x00\x06\xff\x02\x12\x34\x01\x02"
        assert self._tcp.processIncomingFrame(msg)

    @mock.patch.object(ModbusRequest, "encode")
    def test_framer_tls_framer_packet(self, mock_encode):
        """Test a tls frame packet build."""
        message = ModbusRequest(0, 0, False)
        message.function_code = 0x01
        expected = b"\x01"
        mock_encode.return_value = b""
        actual = self._tls.buildFrame(message)
        assert expected == actual

    # ----------------------------------------------------------------------- #
    # RTU tests
    # ----------------------------------------------------------------------- #
    def test_rtu_framer_transaction_ready(self):
        """Test if the checks for a complete frame work."""
        msg_parts = [b"\x00\x01\x00", b"\x00\x00\x01\xfc\x1b"]
        assert not self._rtu.processIncomingFrame(msg_parts[0])
        assert self._rtu.processIncomingFrame(msg_parts[1])

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
        self._rtu.processIncomingFrame(msg, callback)
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
        self._rtu.processIncomingFrame(msg_parts[0], callback)
        assert not result
        self._rtu.processIncomingFrame(msg_parts[1], callback)
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
        self._rtu.processIncomingFrame(msg, callback)
        assert int(msg[0]) == result.slave_id

    @mock.patch.object(ModbusRequest, "encode")
    def test_rtu_framer_packet(self, mock_encode):
        """Test a rtu frame packet build."""
        message = ModbusRequest(0, 0, False)
        message.slave_id = 0xFF
        message.function_code = 0x01
        expected = b"\xff\x01\x81\x80"  # only header + CRC - no data
        mock_encode.return_value = b""
        actual = self._rtu.buildFrame(message)
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
        self._rtu.processIncomingFrame(msg, callback)
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
        self._rtu.processIncomingFrame(msg, callback)
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
        self._rtu.processIncomingFrame(msg, callback)
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
        self._ascii.processIncomingFrame(msg, callback)
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
        self._ascii.processIncomingFrame(msg, callback)
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
        self._ascii.processIncomingFrame(msg_parts[0], callback)
        assert not result
        self._ascii.processIncomingFrame(msg_parts[1], callback)
        assert result

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
        self._ascii.processIncomingFrame(msg, callback)
        assert result
