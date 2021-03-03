#!/usr/bin/env python
import pytest
import unittest
from itertools import count
from pymodbus.compat import IS_PYTHON3

if IS_PYTHON3:  # Python 3
    from unittest.mock import patch, Mock, MagicMock
else:  # Python 2
    from mock import patch, Mock, MagicMock

from binascii import a2b_hex
from pymodbus.pdu import *
from pymodbus.transaction import *
from pymodbus.transaction import (
    ModbusTransactionManager, ModbusSocketFramer, ModbusTlsFramer,
    ModbusAsciiFramer, ModbusRtuFramer, ModbusBinaryFramer
)
from pymodbus.factory import ServerDecoder
from pymodbus.compat import byte2int
from mock import MagicMock
from pymodbus.exceptions import (
    NotImplementedException, ModbusIOException, InvalidMessageReceivedException
)


class ModbusTransactionTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus.transaction module
    """

    # ----------------------------------------------------------------------- #
    # Test Construction
    # ----------------------------------------------------------------------- #
    def setUp(self):
        """ Sets up the test environment """
        self.client   = None
        self.decoder  = ServerDecoder()
        self._tcp     = ModbusSocketFramer(decoder=self.decoder, client=None)
        self._tls     = ModbusTlsFramer(decoder=self.decoder, client=None)
        self._rtu     = ModbusRtuFramer(decoder=self.decoder, client=None)
        self._ascii   = ModbusAsciiFramer(decoder=self.decoder, client=None)
        self._binary  = ModbusBinaryFramer(decoder=self.decoder, client=None)
        self._manager = DictTransactionManager(self.client)
        self._queue_manager = FifoTransactionManager(self.client)
        self._tm = ModbusTransactionManager(self.client)

    def tearDown(self):
        """ Cleans up the test environment """
        del self._manager
        del self._tcp
        del self._tls
        del self._rtu
        del self._ascii

    # ----------------------------------------------------------------------- #
    # Base transaction manager
    # ----------------------------------------------------------------------- #

    def testCalculateExpectedResponseLength(self):
        self._tm.client = MagicMock()
        self._tm.client.framer = MagicMock()
        self._tm._set_adu_size()
        self.assertEqual(self._tm._calculate_response_length(0), None)
        self._tm.base_adu_size = 10
        self.assertEqual(self._tm._calculate_response_length(5), 15)

    def testCalculateExceptionLength(self):
        for framer, exception_length in [('ascii', 11),
                                         ('binary', 7),
                                         ('rtu', 5),
                                         ('tcp', 9),
                                         ('tls', 2),
                                         ('dummy', None)]:
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

            self._tm._set_adu_size()
            self.assertEqual(self._tm._calculate_exception_length(),
                             exception_length)

    @patch('pymodbus.transaction.time')
    def testExecute(self, mock_time):
        mock_time.time.side_effect = count()

        client = MagicMock()
        client.framer = self._ascii
        client.framer._buffer = b'deadbeef'
        client.framer.processIncomingPacket = MagicMock()
        client.framer.processIncomingPacket.return_value = None
        client.framer.buildPacket = MagicMock()
        client.framer.buildPacket.return_value = b'deadbeef'
        client.framer.sendPacket = MagicMock()
        client.framer.sendPacket.return_value = len(b'deadbeef')
        client.framer.decode_data = MagicMock()
        client.framer.decode_data.return_value = {
            "unit": 1,
            "fcode": 222,
            "length": 27
        }
        request = MagicMock()
        request.get_response_pdu_size.return_value = 10
        request.unit_id = 1
        request.function_code = 222
        tm = ModbusTransactionManager(client)
        tm._recv = MagicMock(return_value=b'abcdef')
        self.assertEqual(tm.retries, 3)
        self.assertEqual(tm.retry_on_empty, False)
        # tm._transact = MagicMock()
        # some response
        # tm._transact.return_value = (b'abcdef', None)

        tm.getTransaction = MagicMock()
        tm.getTransaction.return_value = 'response'
        response = tm.execute(request)
        self.assertEqual(response, 'response')
        # No response
        tm._recv = MagicMock(return_value=b'abcdef')
        # tm._transact.return_value = (b'', None)
        tm.transactions = []
        tm.getTransaction = MagicMock()
        tm.getTransaction.return_value = None
        response = tm.execute(request)
        self.assertIsInstance(response, ModbusIOException)

        # No response with retries
        tm.retry_on_empty = True
        tm._recv = MagicMock(side_effect=iter([b'', b'abcdef']))
        # tm._transact.side_effect = [(b'', None), (b'abcdef', None)]
        response = tm.execute(request)
        self.assertIsInstance(response, ModbusIOException)

        # wrong handle_local_echo
        tm._recv = MagicMock(side_effect=iter([b'abcdef', b'deadbe', b'123456']))
        client.handle_local_echo = True
        tm.retry_on_empty = False
        tm.retry_on_invalid = False
        self.assertEqual(tm.execute(request).message,
                         '[Input/Output] Wrong local echo')
        client.handle_local_echo = False

        # retry on invalid response
        tm.retry_on_invalid = True
        tm._recv = MagicMock(side_effect=iter([b'', b'abcdef', b'deadbe', b'123456']))
        # tm._transact.side_effect = [(b'', None), (b'abcdef', None)]
        response = tm.execute(request)
        self.assertIsInstance(response, ModbusIOException)

        # Unable to decode response
        tm._recv = MagicMock(side_effect=ModbusIOException())
        # tm._transact.side_effect = [(b'abcdef', None)]
        client.framer.processIncomingPacket.side_effect = MagicMock(side_effect=ModbusIOException())
        self.assertIsInstance(tm.execute(request), ModbusIOException)

        # Broadcast
        client.broadcast_enable = True
        request.unit_id = 0
        response = tm.execute(request)
        self.assertEqual(response, b'Broadcast write sent - '
                                   b'no response expected')


    # ----------------------------------------------------------------------- #
    # Dictionary based transaction manager
    # ----------------------------------------------------------------------- #

    def testDictTransactionManagerTID(self):
        """ Test the dict transaction manager TID """
        for tid in range(1, self._manager.getNextTID() + 10):
            self.assertEqual(tid+1, self._manager.getNextTID())
        self._manager.reset()
        self.assertEqual(1, self._manager.getNextTID())

    def testGetDictTransactionManagerTransaction(self):
        """ Test the dict transaction manager """
        class Request: pass
        self._manager.reset()
        handle = Request()
        handle.transaction_id = self._manager.getNextTID()
        handle.message = b"testing"
        self._manager.addTransaction(handle)
        result = self._manager.getTransaction(handle.transaction_id)
        self.assertEqual(handle.message, result.message)

    def testDeleteDictTransactionManagerTransaction(self):
        """ Test the dict transaction manager """
        class Request: pass
        self._manager.reset()
        handle = Request()
        handle.transaction_id = self._manager.getNextTID()
        handle.message = b"testing"

        self._manager.addTransaction(handle)
        self._manager.delTransaction(handle.transaction_id)
        self.assertEqual(None, self._manager.getTransaction(handle.transaction_id))

    # ----------------------------------------------------------------------- #
    # Queue based transaction manager
    # ----------------------------------------------------------------------- #
    def testFifoTransactionManagerTID(self):
        """ Test the fifo transaction manager TID """
        for tid in range(1, self._queue_manager.getNextTID() + 10):
            self.assertEqual(tid+1, self._queue_manager.getNextTID())
        self._queue_manager.reset()
        self.assertEqual(1, self._queue_manager.getNextTID())

    def testGetFifoTransactionManagerTransaction(self):
        """ Test the fifo transaction manager """
        class Request: pass
        self._queue_manager.reset()
        handle = Request()
        handle.transaction_id = self._queue_manager.getNextTID()
        handle.message = b"testing"
        self._queue_manager.addTransaction(handle)
        result = self._queue_manager.getTransaction(handle.transaction_id)
        self.assertEqual(handle.message, result.message)

    def testDeleteFifoTransactionManagerTransaction(self):
        """ Test the fifo transaction manager """
        class Request: pass
        self._queue_manager.reset()
        handle = Request()
        handle.transaction_id = self._queue_manager.getNextTID()
        handle.message = b"testing"

        self._queue_manager.addTransaction(handle)
        self._queue_manager.delTransaction(handle.transaction_id)
        self.assertEqual(None, self._queue_manager.getTransaction(handle.transaction_id))

    # ----------------------------------------------------------------------- #
    # TCP tests
    # ----------------------------------------------------------------------- #
    def testTCPFramerTransactionReady(self):
        """ Test a tcp frame transaction """
        msg = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self.assertFalse(self._tcp.isFrameReady())
        self.assertFalse(self._tcp.checkFrame())
        self._tcp.addToFrame(msg)
        self.assertTrue(self._tcp.isFrameReady())
        self.assertTrue(self._tcp.checkFrame())
        self._tcp.advanceFrame()
        self.assertFalse(self._tcp.isFrameReady())
        self.assertFalse(self._tcp.checkFrame())
        self.assertEqual(b'', self._ascii.getFrame())

    def testTCPFramerTransactionFull(self):
        """ Test a full tcp frame transaction """
        msg = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self._tcp.addToFrame(msg)
        self.assertTrue(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg[7:], result)
        self._tcp.advanceFrame()

    def testTCPFramerTransactionHalf(self):
        """ Test a half completed tcp frame transaction """
        msg1 = b"\x00\x01\x12\x34\x00"
        msg2 = b"\x04\xff\x02\x12\x34"
        self._tcp.addToFrame(msg1)
        self.assertFalse(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(b'', result)
        self._tcp.addToFrame(msg2)
        self.assertTrue(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg2[2:], result)
        self._tcp.advanceFrame()

    def testTCPFramerTransactionHalf2(self):
        """ Test a half completed tcp frame transaction """
        msg1 = b"\x00\x01\x12\x34\x00\x04\xff"
        msg2 = b"\x02\x12\x34"
        self._tcp.addToFrame(msg1)
        self.assertFalse(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(b'', result)
        self._tcp.addToFrame(msg2)
        self.assertTrue(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg2, result)
        self._tcp.advanceFrame()

    def testTCPFramerTransactionHalf3(self):
        """ Test a half completed tcp frame transaction """
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

    def testTCPFramerTransactionShort(self):
        """ Test that we can get back on track after an invalid message """
        msg1 = b"\x99\x99\x99\x99\x00\x01\x00\x01"
        msg2 = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self._tcp.addToFrame(msg1)
        self.assertFalse(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(b'', result)
        self._tcp.advanceFrame()
        self._tcp.addToFrame(msg2)
        self.assertEqual(10, len(self._tcp._buffer))
        self.assertTrue(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg2[7:], result)
        self._tcp.advanceFrame()

    def testTCPFramerPopulate(self):
        """ Test a tcp frame packet build """
        expected = ModbusRequest()
        expected.transaction_id = 0x0001
        expected.protocol_id    = 0x1234
        expected.unit_id        = 0xff
        msg = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self._tcp.addToFrame(msg)
        self.assertTrue(self._tcp.checkFrame())
        actual = ModbusRequest()
        self._tcp.populateResult(actual)
        for name in ['transaction_id', 'protocol_id', 'unit_id']:
            self.assertEqual(getattr(expected, name), getattr(actual, name))
        self._tcp.advanceFrame()

    def testTCPFramerPacket(self):
        """ Test a tcp frame packet build """
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: b''
        message = ModbusRequest()
        message.transaction_id = 0x0001
        message.protocol_id    = 0x1234
        message.unit_id        = 0xff
        message.function_code  = 0x01
        expected = b"\x00\x01\x12\x34\x00\x02\xff\x01"
        actual = self._tcp.buildPacket(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    # ----------------------------------------------------------------------- #
    # TLS tests
    # ----------------------------------------------------------------------- #
    def testTLSFramerTransactionReady(self):
        """ Test a tls frame transaction """
        msg = b"\x01\x12\x34\x00\x08"
        self.assertFalse(self._tls.isFrameReady())
        self.assertFalse(self._tls.checkFrame())
        self._tls.addToFrame(msg)
        self.assertTrue(self._tls.isFrameReady())
        self.assertTrue(self._tls.checkFrame())
        self._tls.advanceFrame()
        self.assertFalse(self._tls.isFrameReady())
        self.assertFalse(self._tls.checkFrame())
        self.assertEqual(b'', self._tls.getFrame())

    def testTLSFramerTransactionFull(self):
        """ Test a full tls frame transaction """
        msg = b"\x01\x12\x34\x00\x08"
        self._tls.addToFrame(msg)
        self.assertTrue(self._tls.checkFrame())
        result = self._tls.getFrame()
        self.assertEqual(msg[0:], result)
        self._tls.advanceFrame()

    def testTLSFramerTransactionHalf(self):
        """ Test a half completed tls frame transaction """
        msg1 = b""
        msg2 = b"\x01\x12\x34\x00\x08"
        self._tls.addToFrame(msg1)
        self.assertFalse(self._tls.checkFrame())
        result = self._tls.getFrame()
        self.assertEqual(b'', result)
        self._tls.addToFrame(msg2)
        self.assertTrue(self._tls.checkFrame())
        result = self._tls.getFrame()
        self.assertEqual(msg2[0:], result)
        self._tls.advanceFrame()

    def testTLSFramerTransactionShort(self):
        """ Test that we can get back on track after an invalid message """
        msg1 = b""
        msg2 = b"\x01\x12\x34\x00\x08"
        self._tls.addToFrame(msg1)
        self.assertFalse(self._tls.checkFrame())
        result = self._tls.getFrame()
        self.assertEqual(b'', result)
        self._tls.advanceFrame()
        self._tls.addToFrame(msg2)
        self.assertEqual(5, len(self._tls._buffer))
        self.assertTrue(self._tls.checkFrame())
        result = self._tls.getFrame()
        self.assertEqual(msg2[0:], result)
        self._tls.advanceFrame()

    def testTLSFramerDecode(self):
        """ Testmessage decoding """
        msg1 = b""
        msg2 = b"\x01\x12\x34\x00\x08"
        result = self._tls.decode_data(msg1)
        self.assertEqual(dict(), result);
        result = self._tls.decode_data(msg2)
        self.assertEqual(dict(fcode=1), result);
        self._tls.advanceFrame()

    def testTLSIncomingPacket(self):
        msg = b"\x01\x12\x34\x00\x08"

        unit = 0x01
        def mock_callback(self):
            pass

        self._tls._process = MagicMock()
        self._tls.isFrameReady = MagicMock(return_value=False)
        self._tls.processIncomingPacket(msg, mock_callback, unit)
        self.assertEqual(msg, self._tls.getRawFrame())
        self._tls.advanceFrame()

        self._tls.isFrameReady = MagicMock(return_value=True)
        self._tls._validate_unit_id = MagicMock(return_value=False)
        self._tls.processIncomingPacket(msg, mock_callback, unit)
        self.assertEqual(b'', self._tls.getRawFrame())
        self._tls.advanceFrame()

        self._tls._validate_unit_id = MagicMock(return_value=True)
        self._tls.processIncomingPacket(msg, mock_callback, unit)
        self.assertEqual(msg, self._tls.getRawFrame())
        self._tls.advanceFrame()

    def testTLSProcess(self):
        class MockResult(object):
            def __init__(self, code):
                self.function_code = code

        def mock_callback(self):
            pass

        self._tls.decoder.decode = MagicMock(return_value=None)
        self.assertRaises(ModbusIOException,
                          lambda: self._tls._process(mock_callback))

        result = MockResult(0x01)
        self._tls.decoder.decode = MagicMock(return_value=result)
        self.assertRaises(InvalidMessageReceivedException,
                          lambda: self._tls._process(mock_callback, error=True))

        self._tls._process(mock_callback)
        self.assertEqual(b'', self._tls.getRawFrame())

    def testTLSFramerPopulate(self):
        """ Test a tls frame packet build """
        expected = ModbusRequest()
        msg = b"\x01\x12\x34\x00\x08"
        self._tls.addToFrame(msg)
        self.assertTrue(self._tls.checkFrame())
        actual = ModbusRequest()
        result = self._tls.populateResult(actual)
        self.assertEqual(None, result)
        self._tls.advanceFrame()

    def testTLSFramerPacket(self):
        """ Test a tls frame packet build """
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: b''
        message = ModbusRequest()
        message.function_code  = 0x01
        expected = b"\x01"
        actual = self._tls.buildPacket(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    # ----------------------------------------------------------------------- #
    # RTU tests
    # ----------------------------------------------------------------------- #
    def testRTUFramerTransactionReady(self):
        """ Test if the checks for a complete frame work """
        self.assertFalse(self._rtu.isFrameReady())

        msg_parts = [b"\x00\x01\x00", b"\x00\x00\x01\xfc\x1b"]
        self._rtu.addToFrame(msg_parts[0])
        self.assertFalse(self._rtu.isFrameReady())
        self.assertFalse(self._rtu.checkFrame())

        self._rtu.addToFrame(msg_parts[1])
        self.assertTrue(self._rtu.isFrameReady())
        self.assertTrue(self._rtu.checkFrame())

    def testRTUFramerTransactionFull(self):
        """ Test a full rtu frame transaction """
        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        stripped_msg = msg[1:-2]
        self._rtu.addToFrame(msg)
        self.assertTrue(self._rtu.checkFrame())
        result = self._rtu.getFrame()
        self.assertEqual(stripped_msg, result)
        self._rtu.advanceFrame()

    def testRTUFramerTransactionHalf(self):
        """ Test a half completed rtu frame transaction """
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

    def testRTUFramerPopulate(self):
        """ Test a rtu frame packet build """
        request = ModbusRequest()
        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        self._rtu.addToFrame(msg)
        self._rtu.populateHeader()
        self._rtu.populateResult(request)

        header_dict = self._rtu._header
        self.assertEqual(len(msg), header_dict['len'])
        self.assertEqual(byte2int(msg[0]), header_dict['uid'])
        self.assertEqual(msg[-2:], header_dict['crc'])

        self.assertEqual(0x00, request.unit_id)

    def testRTUFramerPacket(self):
        """ Test a rtu frame packet build """
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: b''
        message = ModbusRequest()
        message.unit_id        = 0xff
        message.function_code  = 0x01
        expected = b"\xff\x01\x81\x80" # only header + CRC - no data
        actual = self._rtu.buildPacket(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    def testRTUDecodeException(self):
        """ Test that the RTU framer can decode errors """
        message = b"\x00\x90\x02\x9c\x01"
        actual = self._rtu.addToFrame(message)
        result = self._rtu.checkFrame()
        self.assertTrue(result)

    def testProcess(self):
        class MockResult(object):
            def __init__(self, code):
                self.function_code = code

        def mock_callback(self):
            pass

        mock_result = MockResult(code=0)
        self._rtu.getRawFrame = self._rtu.getFrame = MagicMock()
        self._rtu.decoder = MagicMock()
        self._rtu.decoder.decode = MagicMock(return_value=mock_result)
        self._rtu.populateResult = MagicMock()
        self._rtu.advanceFrame = MagicMock()

        self._rtu._process(mock_callback)
        self._rtu.populateResult.assert_called_with(mock_result)
        self._rtu.advanceFrame.assert_called_with()
        self.assertTrue(self._rtu.advanceFrame.called)

        #Check errors
        self._rtu.decoder.decode = MagicMock(return_value=None)
        self.assertRaises(ModbusIOException, lambda: self._rtu._process(mock_callback))

    def testRTUProcessIncomingPAkcets(self):
        mock_data = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        unit = 0x00
        def mock_callback(self):
            pass

        self._rtu.addToFrame = MagicMock()
        self._rtu._process = MagicMock()
        self._rtu.isFrameReady = MagicMock(return_value=False)
        self._rtu._buffer = mock_data

        self._rtu.processIncomingPacket(mock_data, mock_callback, unit)

    # ----------------------------------------------------------------------- #
    # ASCII tests
    # ----------------------------------------------------------------------- #
    def testASCIIFramerTransactionReady(self):
        """ Test a ascii frame transaction """
        msg = b':F7031389000A60\r\n'
        self.assertFalse(self._ascii.isFrameReady())
        self.assertFalse(self._ascii.checkFrame())
        self._ascii.addToFrame(msg)
        self.assertTrue(self._ascii.isFrameReady())
        self.assertTrue(self._ascii.checkFrame())
        self._ascii.advanceFrame()
        self.assertFalse(self._ascii.isFrameReady())
        self.assertFalse(self._ascii.checkFrame())
        self.assertEqual(b'', self._ascii.getFrame())

    def testASCIIFramerTransactionFull(self):
        """ Test a full ascii frame transaction """
        msg = b'sss:F7031389000A60\r\n'
        pack = a2b_hex(msg[6:-4])
        self._ascii.addToFrame(msg)
        self.assertTrue(self._ascii.checkFrame())
        result = self._ascii.getFrame()
        self.assertEqual(pack, result)
        self._ascii.advanceFrame()

    def testASCIIFramerTransactionHalf(self):
        """ Test a half completed ascii frame transaction """
        msg1 = b'sss:F7031389'
        msg2 = b'000A60\r\n'
        pack = a2b_hex(msg1[6:] + msg2[:-4])
        self._ascii.addToFrame(msg1)
        self.assertFalse(self._ascii.checkFrame())
        result = self._ascii.getFrame()
        self.assertEqual(b'', result)
        self._ascii.addToFrame(msg2)
        self.assertTrue(self._ascii.checkFrame())
        result = self._ascii.getFrame()
        self.assertEqual(pack, result)
        self._ascii.advanceFrame()

    def testASCIIFramerPopulate(self):
        """ Test a ascii frame packet build """
        request = ModbusRequest()
        self._ascii.populateResult(request)
        self.assertEqual(0x00, request.unit_id)

    def testASCIIFramerPacket(self):
        """ Test a ascii frame packet build """
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: b''
        message = ModbusRequest()
        message.unit_id        = 0xff
        message.function_code  = 0x01
        expected = b":FF0100\r\n"
        actual = self._ascii.buildPacket(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    def testAsciiProcessIncomingPakcets(self):
        mock_data = msg = b':F7031389000A60\r\n'
        unit = 0x00
        def mock_callback(mock_data, *args, **kwargs):
            pass

        self._ascii.processIncomingPacket(mock_data, mock_callback, unit)

        # Test failure:
        self._ascii.checkFrame = MagicMock(return_value=False)
        self._ascii.processIncomingPacket(mock_data, mock_callback, unit)

    # ----------------------------------------------------------------------- #
    # Binary tests
    # ----------------------------------------------------------------------- #
    def testBinaryFramerTransactionReady(self):
        """ Test a binary frame transaction """
        msg  = b'\x7b\x01\x03\x00\x00\x00\x05\x85\xC9\x7d'
        self.assertFalse(self._binary.isFrameReady())
        self.assertFalse(self._binary.checkFrame())
        self._binary.addToFrame(msg)
        self.assertTrue(self._binary.isFrameReady())
        self.assertTrue(self._binary.checkFrame())
        self._binary.advanceFrame()
        self.assertFalse(self._binary.isFrameReady())
        self.assertFalse(self._binary.checkFrame())
        self.assertEqual(b'', self._binary.getFrame())

    def testBinaryFramerTransactionFull(self):
        """ Test a full binary frame transaction """
        msg  = b'\x7b\x01\x03\x00\x00\x00\x05\x85\xC9\x7d'
        pack = msg[2:-3]
        self._binary.addToFrame(msg)
        self.assertTrue(self._binary.checkFrame())
        result = self._binary.getFrame()
        self.assertEqual(pack, result)
        self._binary.advanceFrame()

    def testBinaryFramerTransactionHalf(self):
        """ Test a half completed binary frame transaction """
        msg1 = b'\x7b\x01\x03\x00'
        msg2 = b'\x00\x00\x05\x85\xC9\x7d'
        pack = msg1[2:] + msg2[:-3]
        self._binary.addToFrame(msg1)
        self.assertFalse(self._binary.checkFrame())
        result = self._binary.getFrame()
        self.assertEqual(b'', result)
        self._binary.addToFrame(msg2)
        self.assertTrue(self._binary.checkFrame())
        result = self._binary.getFrame()
        self.assertEqual(pack, result)
        self._binary.advanceFrame()

    def testBinaryFramerPopulate(self):
        """ Test a binary frame packet build """
        request = ModbusRequest()
        self._binary.populateResult(request)
        self.assertEqual(0x00, request.unit_id)

    def testBinaryFramerPacket(self):
        """ Test a binary frame packet build """
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: b''
        message = ModbusRequest()
        message.unit_id        = 0xff
        message.function_code  = 0x01
        expected = b'\x7b\xff\x01\x81\x80\x7d'
        actual = self._binary.buildPacket(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    def testBinaryProcessIncomingPacket(self):
        mock_data = b'\x7b\x01\x03\x00\x00\x00\x05\x85\xC9\x7d'
        unit = 0x00
        def mock_callback(mock_data):
            pass

        self._binary.processIncomingPacket(mock_data, mock_callback, unit)

        # Test failure:
        self._binary.checkFrame = MagicMock(return_value=False)
        self._binary.processIncomingPacket(mock_data, mock_callback, unit)

# ----------------------------------------------------------------------- #
# Main
# ----------------------------------------------------------------------- #


if __name__ == "__main__":
    pytest.main()
