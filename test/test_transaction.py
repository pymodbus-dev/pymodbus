"""Test transaction."""
import unittest
from binascii import a2b_hex
from itertools import count
from unittest.mock import MagicMock, patch

from pymodbus.exceptions import (
    InvalidMessageReceivedException,
    ModbusIOException,
)
from pymodbus.factory import ServerDecoder
from pymodbus.pdu import ModbusRequest
from pymodbus.transaction import (
    DictTransactionManager,
    FifoTransactionManager,
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
    ModbusTransactionManager,
)


TEST_MESSAGE = b"\x7b\x01\x03\x00\x00\x00\x05\x85\xC9\x7d"


class ModbusTransactionTest(  # pylint: disable=too-many-public-methods
    unittest.TestCase
):
    """Unittest for the pymodbus.transaction module."""

    # ----------------------------------------------------------------------- #
    # Test Construction
    # ----------------------------------------------------------------------- #
    def setUp(self):
        """Set up the test environment"""
        self.client = None
        self.decoder = ServerDecoder()
        self._tcp = ModbusSocketFramer(decoder=self.decoder, client=None)
        self._tls = ModbusTlsFramer(decoder=self.decoder, client=None)
        self._rtu = ModbusRtuFramer(decoder=self.decoder, client=None)
        self._ascii = ModbusAsciiFramer(decoder=self.decoder, client=None)
        self._binary = ModbusBinaryFramer(decoder=self.decoder, client=None)
        self._manager = DictTransactionManager(self.client)
        self._queue_manager = FifoTransactionManager(self.client)
        self._tm = ModbusTransactionManager(self.client)

    def tearDown(self):
        """Clean up the test environment"""
        del self._manager
        del self._tcp
        del self._tls
        del self._rtu
        del self._ascii

    # ----------------------------------------------------------------------- #
    # Base transaction manager
    # ----------------------------------------------------------------------- #

    def test_calculate_expected_response_length(self):
        """Test calculate expected response length."""
        self._tm.client = MagicMock()
        self._tm.client.framer = MagicMock()
        self._tm._set_adu_size()  # pylint: disable=protected-access
        self.assertEqual(
            self._tm._calculate_response_length(0),  # pylint: disable=protected-access
            None,
        )
        self._tm.base_adu_size = 10
        self.assertEqual(
            self._tm._calculate_response_length(5),  # pylint: disable=protected-access
            15,
        )

    def test_calculate_exception_length(self):
        """Test calculate exception length."""
        for framer, exception_length in (
            ("ascii", 11),
            ("binary", 7),
            ("rtu", 5),
            ("tcp", 9),
            ("tls", 2),
            ("dummy", None),
        ):
            self._tm.client = MagicMock()
            if framer == "ascii":
                self._tm.client.framer = self._ascii
            elif framer == "binary":
                self._tm.client.framer = self._binary
            elif framer == "rtu":
                self._tm.client.framer = self._rtu
            elif framer == "tcp":
                self._tm.client.framer = self._tcp
            elif framer == "tls":
                self._tm.client.framer = self._tls
            else:
                self._tm.client.framer = MagicMock()

            self._tm._set_adu_size()  # pylint: disable=protected-access
            self.assertEqual(
                self._tm._calculate_exception_length(),  # pylint: disable=protected-access
                exception_length,
            )

    @patch("pymodbus.transaction.time")
    def test_execute(self, mock_time):
        """Test execute."""
        mock_time.time.side_effect = count()

        client = MagicMock()
        client.framer = self._ascii
        client.framer._buffer = b"deadbeef"  # pylint: disable=protected-access
        client.framer.processIncomingPacket = MagicMock()
        client.framer.processIncomingPacket.return_value = None
        client.framer.buildPacket = MagicMock()
        client.framer.buildPacket.return_value = b"deadbeef"
        client.framer.sendPacket = MagicMock()
        client.framer.sendPacket.return_value = len(b"deadbeef")
        client.framer.decode_data = MagicMock()
        client.framer.decode_data.return_value = {"unit": 1, "fcode": 222, "length": 27}
        request = MagicMock()
        request.get_response_pdu_size.return_value = 10
        request.unit_id = 1
        request.function_code = 222
        trans = ModbusTransactionManager(client)
        trans._recv = MagicMock(  # pylint: disable=protected-access
            return_value=b"abcdef"
        )
        self.assertEqual(trans.retries, 3)
        self.assertEqual(trans.retry_on_empty, False)

        trans.getTransaction = MagicMock()
        trans.getTransaction.return_value = "response"
        response = trans.execute(request)
        self.assertEqual(response, "response")
        # No response
        trans._recv = MagicMock(  # pylint: disable=protected-access
            return_value=b"abcdef"
        )
        trans.transactions = []
        trans.getTransaction = MagicMock()
        trans.getTransaction.return_value = None
        response = trans.execute(request)
        self.assertIsInstance(response, ModbusIOException)

        # No response with retries
        trans.retry_on_empty = True
        trans._recv = MagicMock(  # pylint: disable=protected-access
            side_effect=iter([b"", b"abcdef"])
        )
        response = trans.execute(request)
        self.assertIsInstance(response, ModbusIOException)

        # wrong handle_local_echo
        trans._recv = MagicMock(  # pylint: disable=protected-access
            side_effect=iter([b"abcdef", b"deadbe", b"123456"])
        )
        client.handle_local_echo = True
        trans.retry_on_empty = False
        trans.retry_on_invalid = False
        self.assertEqual(
            trans.execute(request).message, "[Input/Output] Wrong local echo"
        )
        client.handle_local_echo = False

        # retry on invalid response
        trans.retry_on_invalid = True
        trans._recv = MagicMock(  # pylint: disable=protected-access
            side_effect=iter([b"", b"abcdef", b"deadbe", b"123456"])
        )
        response = trans.execute(request)
        self.assertIsInstance(response, ModbusIOException)

        # Unable to decode response
        trans._recv = MagicMock(  # pylint: disable=protected-access
            side_effect=ModbusIOException()
        )
        client.framer.processIncomingPacket.side_effect = MagicMock(
            side_effect=ModbusIOException()
        )
        self.assertIsInstance(trans.execute(request), ModbusIOException)

        # Broadcast
        client.params.broadcast_enable = True
        request.unit_id = 0
        response = trans.execute(request)
        self.assertEqual(response, b"Broadcast write sent - no response expected")

    # ----------------------------------------------------------------------- #
    # Dictionary based transaction manager
    # ----------------------------------------------------------------------- #

    def test_dict_transaction_manager_tid(self):
        """Test the dict transaction manager TID"""
        for tid in range(1, self._manager.getNextTID() + 10):
            self.assertEqual(tid + 1, self._manager.getNextTID())
        self._manager.reset()
        self.assertEqual(1, self._manager.getNextTID())

    def test_get_dict_fifo_transaction_manager_transaction(self):
        """Test the dict transaction manager"""

        class Request:  # pylint: disable=too-few-public-methods
            """Request."""

        self._manager.reset()
        handle = Request()
        handle.transaction_id = (  # pylint: disable=attribute-defined-outside-init
            self._manager.getNextTID()
        )
        handle.message = b"testing"  # pylint: disable=attribute-defined-outside-init
        self._manager.addTransaction(handle)
        result = self._manager.getTransaction(handle.transaction_id)
        self.assertEqual(handle.message, result.message)

    def test_delete_dict_fifo_transaction_manager_transaction(self):
        """Test the dict transaction manager"""

        class Request:  # pylint: disable=too-few-public-methods
            """Request."""

        self._manager.reset()
        handle = Request()
        handle.transaction_id = (  # pylint: disable=attribute-defined-outside-init
            self._manager.getNextTID()
        )
        handle.message = b"testing"  # pylint: disable=attribute-defined-outside-init

        self._manager.addTransaction(handle)
        self._manager.delTransaction(handle.transaction_id)
        self.assertEqual(None, self._manager.getTransaction(handle.transaction_id))

    # ----------------------------------------------------------------------- #
    # Queue based transaction manager
    # ----------------------------------------------------------------------- #
    def test_fifo_transaction_manager_tid(self):
        """Test the fifo transaction manager TID"""
        for tid in range(1, self._queue_manager.getNextTID() + 10):
            self.assertEqual(tid + 1, self._queue_manager.getNextTID())
        self._queue_manager.reset()
        self.assertEqual(1, self._queue_manager.getNextTID())

    def test_get_fifo_transaction_manager_transaction(self):
        """Test the fifo transaction manager"""

        class Request:  # pylint: disable=too-few-public-methods
            """Request."""

        self._queue_manager.reset()
        handle = Request()
        handle.transaction_id = (  # pylint: disable=attribute-defined-outside-init
            self._queue_manager.getNextTID()
        )
        handle.message = b"testing"  # pylint: disable=attribute-defined-outside-init
        self._queue_manager.addTransaction(handle)
        result = self._queue_manager.getTransaction(handle.transaction_id)
        self.assertEqual(handle.message, result.message)

    def test_delete_fifo_transaction_manager_transaction(self):
        """Test the fifo transaction manager"""

        class Request:  # pylint: disable=too-few-public-methods
            """Request."""

        self._queue_manager.reset()
        handle = Request()
        handle.transaction_id = (  # pylint: disable=attribute-defined-outside-init
            self._queue_manager.getNextTID()
        )
        handle.message = b"testing"  # pylint: disable=attribute-defined-outside-init

        self._queue_manager.addTransaction(handle)
        self._queue_manager.delTransaction(handle.transaction_id)
        self.assertEqual(
            None, self._queue_manager.getTransaction(handle.transaction_id)
        )

    # ----------------------------------------------------------------------- #
    # TCP tests
    # ----------------------------------------------------------------------- #
    def test_tcp_framer_transaction_ready(self):
        """Test a tcp frame transaction"""
        msg = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self.assertFalse(self._tcp.isFrameReady())
        self.assertFalse(self._tcp.checkFrame())
        self._tcp.addToFrame(msg)
        self.assertTrue(self._tcp.isFrameReady())
        self.assertTrue(self._tcp.checkFrame())
        self._tcp.advanceFrame()
        self.assertFalse(self._tcp.isFrameReady())
        self.assertFalse(self._tcp.checkFrame())
        self.assertEqual(b"", self._ascii.getFrame())

    def test_tcp_framer_transaction_full(self):
        """Test a full tcp frame transaction"""
        msg = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self._tcp.addToFrame(msg)
        self.assertTrue(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg[7:], result)
        self._tcp.advanceFrame()

    def test_tcp_framer_transaction_half(self):
        """Test a half completed tcp frame transaction"""
        msg1 = b"\x00\x01\x12\x34\x00"
        msg2 = b"\x04\xff\x02\x12\x34"
        self._tcp.addToFrame(msg1)
        self.assertFalse(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(b"", result)
        self._tcp.addToFrame(msg2)
        self.assertTrue(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg2[2:], result)
        self._tcp.advanceFrame()

    def test_tcp_framer_transaction_half2(self):
        """Test a half completed tcp frame transaction"""
        msg1 = b"\x00\x01\x12\x34\x00\x04\xff"
        msg2 = b"\x02\x12\x34"
        self._tcp.addToFrame(msg1)
        self.assertFalse(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(b"", result)
        self._tcp.addToFrame(msg2)
        self.assertTrue(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg2, result)
        self._tcp.advanceFrame()

    def test_tcp_framer_transaction_half3(self):
        """Test a half completed tcp frame transaction"""
        msg1 = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12"
        msg2 = b"\x34"
        self._tcp.addToFrame(msg1)
        self.assertFalse(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg1[7:], result)
        self._tcp.addToFrame(msg2)
        self.assertTrue(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg1[7:] + msg2, result)
        self._tcp.advanceFrame()

    def test_tcp_framer_transaction_short(self):
        """Test that we can get back on track after an invalid message"""
        msg1 = b"\x99\x99\x99\x99\x00\x01\x00\x01"
        msg2 = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self._tcp.addToFrame(msg1)
        self.assertFalse(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(b"", result)
        self._tcp.advanceFrame()
        self._tcp.addToFrame(msg2)
        self.assertEqual(10, len(self._tcp._buffer))  # pylint: disable=protected-access
        self.assertTrue(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg2[7:], result)
        self._tcp.advanceFrame()

    def test_tcp_framer_populate(self):
        """Test a tcp frame packet build"""
        expected = ModbusRequest()
        expected.transaction_id = 0x0001
        expected.protocol_id = 0x1234
        expected.unit_id = 0xFF
        msg = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self._tcp.addToFrame(msg)
        self.assertTrue(self._tcp.checkFrame())
        actual = ModbusRequest()
        self._tcp.populateResult(actual)
        for name in ("transaction_id", "protocol_id", "unit_id"):
            self.assertEqual(getattr(expected, name), getattr(actual, name))
        self._tcp.advanceFrame()

    def test_tcp_framer_packet(self):
        """Test a tcp frame packet build"""
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: b""
        message = ModbusRequest()
        message.transaction_id = 0x0001
        message.protocol_id = 0x1234
        message.unit_id = 0xFF
        message.function_code = 0x01
        expected = b"\x00\x01\x12\x34\x00\x02\xff\x01"
        actual = self._tcp.buildPacket(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    # ----------------------------------------------------------------------- #
    # TLS tests
    # ----------------------------------------------------------------------- #
    def test_framer_tls_framer_transaction_ready(self):
        """Test a tls frame transaction"""
        msg = b"\x01\x12\x34\x00\x08"
        self.assertFalse(self._tls.isFrameReady())
        self.assertFalse(self._tls.checkFrame())
        self._tls.addToFrame(msg)
        self.assertTrue(self._tls.isFrameReady())
        self.assertTrue(self._tls.checkFrame())
        self._tls.advanceFrame()
        self.assertFalse(self._tls.isFrameReady())
        self.assertFalse(self._tls.checkFrame())
        self.assertEqual(b"", self._tls.getFrame())

    def test_framer_tls_framer_transaction_full(self):
        """Test a full tls frame transaction"""
        msg = b"\x01\x12\x34\x00\x08"
        self._tls.addToFrame(msg)
        self.assertTrue(self._tls.checkFrame())
        result = self._tls.getFrame()
        self.assertEqual(msg[0:], result)
        self._tls.advanceFrame()

    def test_framer_tls_framer_transaction_half(self):
        """Test a half completed tls frame transaction"""
        msg1 = b""
        msg2 = b"\x01\x12\x34\x00\x08"
        self._tls.addToFrame(msg1)
        self.assertFalse(self._tls.checkFrame())
        result = self._tls.getFrame()
        self.assertEqual(b"", result)
        self._tls.addToFrame(msg2)
        self.assertTrue(self._tls.checkFrame())
        result = self._tls.getFrame()
        self.assertEqual(msg2[0:], result)
        self._tls.advanceFrame()

    def test_framer_tls_framer_transaction_short(self):
        """Test that we can get back on track after an invalid message"""
        msg1 = b""
        msg2 = b"\x01\x12\x34\x00\x08"
        self._tls.addToFrame(msg1)
        self.assertFalse(self._tls.checkFrame())
        result = self._tls.getFrame()
        self.assertEqual(b"", result)
        self._tls.advanceFrame()
        self._tls.addToFrame(msg2)
        self.assertEqual(5, len(self._tls._buffer))  # pylint: disable=protected-access
        self.assertTrue(self._tls.checkFrame())
        result = self._tls.getFrame()
        self.assertEqual(msg2[0:], result)
        self._tls.advanceFrame()

    def test_framer_tls_framer_decode(self):
        """Testmessage decoding"""
        msg1 = b""
        msg2 = b"\x01\x12\x34\x00\x08"
        result = self._tls.decode_data(msg1)
        self.assertEqual({}, result)
        result = self._tls.decode_data(msg2)
        self.assertEqual({"fcode": 1}, result)
        self._tls.advanceFrame()

    def test_framer_tls_incoming_packet(self):
        """Framer tls incoming packet."""
        msg = b"\x01\x12\x34\x00\x08"

        unit = 0x01

        def mock_callback(self):  # pylint: disable=unused-argument
            """Mock callback."""

        self._tls._process = MagicMock()  # pylint: disable=protected-access
        self._tls.isFrameReady = MagicMock(return_value=False)
        self._tls.processIncomingPacket(msg, mock_callback, unit)
        self.assertEqual(msg, self._tls.getRawFrame())
        self._tls.advanceFrame()

        self._tls.isFrameReady = MagicMock(return_value=True)
        self._tls._validate_unit_id = MagicMock(  # pylint: disable=protected-access
            return_value=False
        )
        self._tls.processIncomingPacket(msg, mock_callback, unit)
        self.assertEqual(b"", self._tls.getRawFrame())
        self._tls.advanceFrame()

        self._tls._validate_unit_id = MagicMock(  # pylint: disable=protected-access
            return_value=True
        )
        self._tls.processIncomingPacket(msg, mock_callback, unit)
        self.assertEqual(msg, self._tls.getRawFrame())
        self._tls.advanceFrame()

    def test_framer_tls_process(self):
        """Framer tls process."""

        class MockResult:  # pylint: disable=too-few-public-methods
            """Mock result."""

            def __init__(self, code):
                """Init."""
                self.function_code = code

        def mock_callback(self):  # pylint: disable=unused-argument
            """Mock callback."""

        self._tls.decoder.decode = MagicMock(return_value=None)
        self.assertRaises(
            ModbusIOException,
            lambda: self._tls._process(  # pylint: disable=protected-access
                mock_callback
            ),
        )

        result = MockResult(0x01)
        self._tls.decoder.decode = MagicMock(return_value=result)
        self.assertRaises(
            InvalidMessageReceivedException,
            lambda: self._tls._process(  # pylint: disable=protected-access
                mock_callback, error=True
            ),
        )

        self._tls._process(mock_callback)  # pylint: disable=protected-access
        self.assertEqual(b"", self._tls.getRawFrame())

    def test_framer_tls_framer_populate(self):
        """Test a tls frame packet build"""
        ModbusRequest()
        msg = b"\x01\x12\x34\x00\x08"
        self._tls.addToFrame(msg)
        self.assertTrue(self._tls.checkFrame())
        actual = ModbusRequest()
        result = self._tls.populateResult(  # pylint: disable=assignment-from-none
            actual
        )
        self.assertEqual(None, result)
        self._tls.advanceFrame()

    def test_framer_tls_framer_packet(self):
        """Test a tls frame packet build"""
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: b""
        message = ModbusRequest()
        message.function_code = 0x01
        expected = b"\x01"
        actual = self._tls.buildPacket(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    # ----------------------------------------------------------------------- #
    # RTU tests
    # ----------------------------------------------------------------------- #
    def test_rtu_framer_transaction_ready(self):
        """Test if the checks for a complete frame work"""
        self.assertFalse(self._rtu.isFrameReady())

        msg_parts = [b"\x00\x01\x00", b"\x00\x00\x01\xfc\x1b"]
        self._rtu.addToFrame(msg_parts[0])
        self.assertFalse(self._rtu.isFrameReady())
        self.assertFalse(self._rtu.checkFrame())

        self._rtu.addToFrame(msg_parts[1])
        self.assertTrue(self._rtu.isFrameReady())
        self.assertTrue(self._rtu.checkFrame())

    def test_rtu_framer_transaction_full(self):
        """Test a full rtu frame transaction"""
        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        stripped_msg = msg[1:-2]
        self._rtu.addToFrame(msg)
        self.assertTrue(self._rtu.checkFrame())
        result = self._rtu.getFrame()
        self.assertEqual(stripped_msg, result)
        self._rtu.advanceFrame()

    def test_rtu_framer_transaction_half(self):
        """Test a half completed rtu frame transaction"""
        msg_parts = [b"\x00\x01\x00", b"\x00\x00\x01\xfc\x1b"]
        stripped_msg = b"".join(msg_parts)[1:-2]
        self._rtu.addToFrame(msg_parts[0])
        self.assertFalse(self._rtu.checkFrame())
        self._rtu.addToFrame(msg_parts[1])
        self.assertTrue(self._rtu.isFrameReady())
        self.assertTrue(self._rtu.checkFrame())
        result = self._rtu.getFrame()
        self.assertEqual(stripped_msg, result)
        self._rtu.advanceFrame()

    def test_rtu_framer_populate(self):
        """Test a rtu frame packet build"""
        request = ModbusRequest()
        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        self._rtu.addToFrame(msg)
        self._rtu.populateHeader()
        self._rtu.populateResult(request)

        header_dict = self._rtu._header  # pylint: disable=protected-access
        self.assertEqual(len(msg), header_dict["len"])
        self.assertEqual(int(msg[0]), header_dict["uid"])
        self.assertEqual(msg[-2:], header_dict["crc"])

        self.assertEqual(0x00, request.unit_id)

    def test_rtu_framer_packet(self):
        """Test a rtu frame packet build"""
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: b""
        message = ModbusRequest()
        message.unit_id = 0xFF
        message.function_code = 0x01
        expected = b"\xff\x01\x81\x80"  # only header + CRC - no data
        actual = self._rtu.buildPacket(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    def test_rtu_decode_exception(self):
        """Test that the RTU framer can decode errors"""
        message = b"\x00\x90\x02\x9c\x01"
        self._rtu.addToFrame(message)
        result = self._rtu.checkFrame()
        self.assertTrue(result)

    def test_process(self):
        """Test process."""

        class MockResult:  # pylint: disable=too-few-public-methods
            """Mock result."""

            def __init__(self, code):
                self.function_code = code

        def mock_callback(self):  # pylint: disable=unused-argument
            """Mock callback."""

        mock_result = MockResult(code=0)
        self._rtu.getRawFrame = self._rtu.getFrame = MagicMock()
        self._rtu.decoder = MagicMock()
        self._rtu.decoder.decode = MagicMock(return_value=mock_result)
        self._rtu.populateResult = MagicMock()
        self._rtu.advanceFrame = MagicMock()

        self._rtu._process(mock_callback)  # pylint: disable=protected-access
        self._rtu.populateResult.assert_called_with(mock_result)
        self._rtu.advanceFrame.assert_called_with()
        self.assertTrue(self._rtu.advanceFrame.called)

        # Check errors
        self._rtu.decoder.decode = MagicMock(return_value=None)
        self.assertRaises(
            ModbusIOException,
            lambda: self._rtu._process(  # pylint: disable=protected-access
                mock_callback
            ),
        )

    def test_rtu_process_incoming_packets(self):
        """Test rtu process incoming packets."""
        mock_data = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        unit = 0x00

        def mock_callback(self):  # pylint: disable=unused-argument
            """Mock callback."""

        self._rtu.addToFrame = MagicMock()
        self._rtu._process = MagicMock()  # pylint: disable=protected-access
        self._rtu.isFrameReady = MagicMock(return_value=False)
        self._rtu._buffer = mock_data  # pylint: disable=protected-access

        self._rtu.processIncomingPacket(mock_data, mock_callback, unit)

    # ----------------------------------------------------------------------- #
    # ASCII tests
    # ----------------------------------------------------------------------- #
    def test_ascii_framer_transaction_ready(self):
        """Test a ascii frame transaction"""
        msg = b":F7031389000A60\r\n"
        self.assertFalse(self._ascii.isFrameReady())
        self.assertFalse(self._ascii.checkFrame())
        self._ascii.addToFrame(msg)
        self.assertTrue(self._ascii.isFrameReady())
        self.assertTrue(self._ascii.checkFrame())
        self._ascii.advanceFrame()
        self.assertFalse(self._ascii.isFrameReady())
        self.assertFalse(self._ascii.checkFrame())
        self.assertEqual(b"", self._ascii.getFrame())

    def test_ascii_framer_transaction_full(self):
        """Test a full ascii frame transaction"""
        msg = b"sss:F7031389000A60\r\n"
        pack = a2b_hex(msg[6:-4])
        self._ascii.addToFrame(msg)
        self.assertTrue(self._ascii.checkFrame())
        result = self._ascii.getFrame()
        self.assertEqual(pack, result)
        self._ascii.advanceFrame()

    def test_ascii_framer_transaction_half(self):
        """Test a half completed ascii frame transaction"""
        msg1 = b"sss:F7031389"
        msg2 = b"000A60\r\n"
        pack = a2b_hex(msg1[6:] + msg2[:-4])
        self._ascii.addToFrame(msg1)
        self.assertFalse(self._ascii.checkFrame())
        result = self._ascii.getFrame()
        self.assertEqual(b"", result)
        self._ascii.addToFrame(msg2)
        self.assertTrue(self._ascii.checkFrame())
        result = self._ascii.getFrame()
        self.assertEqual(pack, result)
        self._ascii.advanceFrame()

    def test_ascii_framer_populate(self):
        """Test a ascii frame packet build"""
        request = ModbusRequest()
        self._ascii.populateResult(request)
        self.assertEqual(0x00, request.unit_id)

    def test_ascii_framer_packet(self):
        """Test a ascii frame packet build"""
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: b""
        message = ModbusRequest()
        message.unit_id = 0xFF
        message.function_code = 0x01
        expected = b":FF0100\r\n"
        actual = self._ascii.buildPacket(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    def test_ascii_process_incoming_packets(self):
        """Test ascii process incoming packet."""
        mock_data = b":F7031389000A60\r\n"
        unit = 0x00

        def mock_callback(
            mock_data, *args, **kwargs
        ):  # pylint: disable=unused-argument
            """Mock callback."""

        self._ascii.processIncomingPacket(mock_data, mock_callback, unit)

        # Test failure:
        self._ascii.checkFrame = MagicMock(return_value=False)
        self._ascii.processIncomingPacket(mock_data, mock_callback, unit)

    # ----------------------------------------------------------------------- #
    # Binary tests
    # ----------------------------------------------------------------------- #
    def test_binary_framer_transaction_ready(self):
        """Test a binary frame transaction"""
        msg = TEST_MESSAGE
        self.assertFalse(self._binary.isFrameReady())
        self.assertFalse(self._binary.checkFrame())
        self._binary.addToFrame(msg)
        self.assertTrue(self._binary.isFrameReady())
        self.assertTrue(self._binary.checkFrame())
        self._binary.advanceFrame()
        self.assertFalse(self._binary.isFrameReady())
        self.assertFalse(self._binary.checkFrame())
        self.assertEqual(b"", self._binary.getFrame())

    def test_binary_framer_transaction_full(self):
        """Test a full binary frame transaction"""
        msg = TEST_MESSAGE
        pack = msg[2:-3]
        self._binary.addToFrame(msg)
        self.assertTrue(self._binary.checkFrame())
        result = self._binary.getFrame()
        self.assertEqual(pack, result)
        self._binary.advanceFrame()

    def test_binary_framer_transaction_half(self):
        """Test a half completed binary frame transaction"""
        msg1 = b"\x7b\x01\x03\x00"
        msg2 = b"\x00\x00\x05\x85\xC9\x7d"
        pack = msg1[2:] + msg2[:-3]
        self._binary.addToFrame(msg1)
        self.assertFalse(self._binary.checkFrame())
        result = self._binary.getFrame()
        self.assertEqual(b"", result)
        self._binary.addToFrame(msg2)
        self.assertTrue(self._binary.checkFrame())
        result = self._binary.getFrame()
        self.assertEqual(pack, result)
        self._binary.advanceFrame()

    def test_binary_framer_populate(self):
        """Test a binary frame packet build"""
        request = ModbusRequest()
        self._binary.populateResult(request)
        self.assertEqual(0x00, request.unit_id)

    def test_binary_framer_packet(self):
        """Test a binary frame packet build"""
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: b""
        message = ModbusRequest()
        message.unit_id = 0xFF
        message.function_code = 0x01
        expected = b"\x7b\xff\x01\x81\x80\x7d"
        actual = self._binary.buildPacket(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    def test_binary_process_incoming_packet(self):
        """Test binary process incoming packet."""
        mock_data = TEST_MESSAGE
        unit = 0x00

        def mock_callback(mock_data):  # pylint: disable=unused-argument
            pass

        self._binary.processIncomingPacket(mock_data, mock_callback, unit)

        # Test failure:
        self._binary.checkFrame = MagicMock(return_value=False)
        self._binary.processIncomingPacket(mock_data, mock_callback, unit)
