#!/usr/bin/env python
import unittest
from binascii import a2b_hex
from pymodbus.pdu import *
from pymodbus.transaction import *
from pymodbus.transaction import (
    ModbusTransactionManager, ModbusSocketFramer, ModbusAsciiFramer,
    ModbusRtuFramer, ModbusBinaryFramer
)
from pymodbus.factory import ServerDecoder
from pymodbus.compat import byte2int
from mock import MagicMock
from pymodbus.exceptions import (
    NotImplementedException, ModbusIOException, InvalidMessageRecievedException
)

class ModbusTransactionTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.transaction module
    '''

    #---------------------------------------------------------------------------#
    # Test Construction
    #---------------------------------------------------------------------------#
    def setUp(self):
        ''' Sets up the test environment '''
        self.client   = None
        self.decoder  = ServerDecoder()
        self._tcp     = ModbusSocketFramer(decoder=self.decoder)
        self._rtu     = ModbusRtuFramer(decoder=self.decoder)
        self._ascii   = ModbusAsciiFramer(decoder=self.decoder)
        self._binary  = ModbusBinaryFramer(decoder=self.decoder)
        self._manager = DictTransactionManager(self.client)
        self._queue_manager = FifoTransactionManager(self.client)
        self._tm = ModbusTransactionManager(self.client)

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self._manager
        del self._tcp
        del self._rtu
        del self._ascii

    def testCalculateResponseLength(self):
        mock_expected_pdu_size = 10

        # test returns None when base adu size = -1
        self._tm.base_adu_size = -1
        self.assertEqual(
            self._tm._calculate_response_length(mock_expected_pdu_size), None
        )

        # test returns value when base adu size is > 0
        self._tm.base_adu_size = 10
        self.assertEqual(
            self._tm._calculate_response_length(mock_expected_pdu_size), 20
        )

    def testCalculateExceptionLength(self):
        mock_adu_size = 10
        self._tm.base_adu_size = mock_adu_size
        self._tm.client = MagicMock()

        self._tm.client.framer = ModbusSocketFramer(self.decoder)
        self.assertEqual(
            self._tm._calculate_exception_length(), 12
        )

        self._tm.client.framer = ModbusRtuFramer(self.decoder)
        self.assertEqual(
            self._tm._calculate_exception_length(), 12
        )

        self._tm.client.framer = ModbusBinaryFramer(self.decoder)
        self.assertEqual(
            self._tm._calculate_exception_length(), 12
        )

        self._tm.client.framer = ModbusAsciiFramer(self.decoder)
        self.assertEqual(
            self._tm._calculate_exception_length(), 14
        )

    def testCheckResponse(self):
        mock_adu_size = 10
        self._tm.base_adu_size = mock_adu_size
        self._tm.client = MagicMock()

        # case1: returns true:
        mock_response = "somethinglegal"
        self._tm.client.framer = ModbusSocketFramer
        self.assertTrue(self._tm._check_response(mock_response))

    def testExecute(self):
        mock_recv = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        class MockRequest(object):
            def __init__(self, tid=0, pdu=1024):
                self.transaction_id = tid
                self.pdu_size = pdu

            def get_response_pdu_size(self):
                return self.pdu_size

        mock_request = MockRequest()
        self._tm.client = MagicMock()
        self._tm.base_adu_size = 10
        self._tm.send = MagicMock()
        self._tm._recv = MagicMock(return_value=mock_recv)
        self._tm.getTransaction = MagicMock(return_value="mock_resp")
        self._tm.retries = 1

        # Test normal behaviour
        self.assertEqual(self._tm.execute(mock_request), "mock_resp")

        # no transaction
        self._tm.getTransaction = MagicMock(return_value=None)
        self._tm.transactions = ""
        mock_exception = 'No Response received from the remote unit'
        self.assertIsInstance(self._tm.execute(mock_request), ModbusIOException)

    def testRecv(self):
        self._tm.retries = 1
        self._tm.client = MagicMock()
        self._tm.client._recv = MagicMock(return_value="asd")
        self.assertIsNotNone(self._tm._recv(4))

        self._tm.client.framer = ModbusSocketFramer(self.decoder)
        self.assertIsNotNone(self._tm._recv(4))

        self._tm._calculate_exception_length = MagicMock(return_value=0)
        self._tm._check_response = MagicMock(retutn_value=True)

    def testAddTransaction(self):
        mock_trans = "some trans"
        self.assertRaises(
            NotImplementedException, lambda: self._tm.addTransaction(mock_trans)
        )
        self.assertRaises(
            NotImplementedException, lambda: self._tm.getTransaction(mock_trans)
        )
        self.assertRaises(
            NotImplementedException, lambda: self._tm.delTransaction(mock_trans)
        )

    def testGetNextTID(self):
        mock_tid = 10
        self._tm.tid = mock_tid
        self.assertEqual(self._tm.getNextTID(), mock_tid + 1)

    def testReset(self):
        self._tm.tid = 100
        self._tm.transactions = MagicMock()
        self._tm.reset()
        self.assertEqual(self._tm.tid, 0)
    #---------------------------------------------------------------------------#
    # Dictionary based transaction manager
    #---------------------------------------------------------------------------#
    def testDictTransactionManagerTID(self):
        ''' Test the dict transaction manager TID '''
        for tid in range(1, self._manager.getNextTID() + 10):
            self.assertEqual(tid+1, self._manager.getNextTID())
        self._manager.reset()
        self.assertEqual(1, self._manager.getNextTID())

    def testGetDictTransactionManagerTransaction(self):
        ''' Test the dict transaction manager '''
        class Request: pass
        self._manager.reset()
        handle = Request()
        handle.transaction_id = self._manager.getNextTID()
        handle.message = b"testing"
        self._manager.addTransaction(handle)
        result = self._manager.getTransaction(handle.transaction_id)
        self.assertEqual(handle.message, result.message)

    def testDeleteDictTransactionManagerTransaction(self):
        ''' Test the dict transaction manager '''
        class Request: pass
        self._manager.reset()
        handle = Request()
        handle.transaction_id = self._manager.getNextTID()
        handle.message = b"testing"

        self._manager.addTransaction(handle)
        self._manager.delTransaction(handle.transaction_id)
        self.assertEqual(None, self._manager.getTransaction(handle.transaction_id))

    #---------------------------------------------------------------------------#
    # Queue based transaction manager
    #---------------------------------------------------------------------------#
    def testFifoTransactionManagerTID(self):
        ''' Test the fifo transaction manager TID '''
        for tid in range(1, self._queue_manager.getNextTID() + 10):
            self.assertEqual(tid+1, self._queue_manager.getNextTID())
        self._queue_manager.reset()
        self.assertEqual(1, self._queue_manager.getNextTID())

    def testGetFifoTransactionManagerTransaction(self):
        ''' Test the fifo transaction manager '''
        class Request: pass
        self._queue_manager.reset()
        handle = Request()
        handle.transaction_id = self._queue_manager.getNextTID()
        handle.message = b"testing"
        self._queue_manager.addTransaction(handle)
        result = self._queue_manager.getTransaction(handle.transaction_id)
        self.assertEqual(handle.message, result.message)

    def testDeleteFifoTransactionManagerTransaction(self):
        ''' Test the fifo transaction manager '''
        class Request: pass
        self._queue_manager.reset()
        handle = Request()
        handle.transaction_id = self._queue_manager.getNextTID()
        handle.message = b"testing"

        self._queue_manager.addTransaction(handle)
        self._queue_manager.delTransaction(handle.transaction_id)
        self.assertEqual(None, self._queue_manager.getTransaction(handle.transaction_id))

    #---------------------------------------------------------------------------#
    # TCP tests
    #---------------------------------------------------------------------------#
    def testTCPFramerTransactionReady(self):
        ''' Test a tcp frame transaction '''
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
        ''' Test a full tcp frame transaction '''
        msg = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self._tcp.addToFrame(msg)
        self.assertTrue(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg[7:], result)
        self._tcp.advanceFrame()

    def testTCPFramerTransactionHalf(self):
        ''' Test a half completed tcp frame transaction '''
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
        ''' Test a half completed tcp frame transaction '''
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
        ''' Test a half completed tcp frame transaction '''
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
        ''' Test that we can get back on track after an invalid message '''
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
        ''' Test a tcp frame packet build '''
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
        ''' Test a tcp frame packet build '''
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

    #---------------------------------------------------------------------------#
    # RTU tests
    #---------------------------------------------------------------------------#
    def testRTUFramerTransactionReady(self):
        ''' Test if the checks for a complete frame work '''
        self.assertFalse(self._rtu.isFrameReady())

        msg_parts = [b"\x00\x01\x00", b"\x00\x00\x01\xfc\x1b"]
        self._rtu.addToFrame(msg_parts[0])
        self.assertTrue(self._rtu.isFrameReady())
        self.assertFalse(self._rtu.checkFrame())

        self._rtu.addToFrame(msg_parts[1])
        self.assertTrue(self._rtu.isFrameReady())
        self.assertTrue(self._rtu.checkFrame())

    def testRTUFramerTransactionFull(self):
        ''' Test a full rtu frame transaction '''
        msg = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"
        stripped_msg = msg[1:-2]
        self._rtu.addToFrame(msg)
        self.assertTrue(self._rtu.checkFrame())
        result = self._rtu.getFrame()
        self.assertEqual(stripped_msg, result)
        self._rtu.advanceFrame()

    def testRTUFramerTransactionHalf(self):
        ''' Test a half completed rtu frame transaction '''
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
        ''' Test a rtu frame packet build '''
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
        ''' Test a rtu frame packet build '''
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
        ''' Test that the RTU framer can decode errors '''
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

        #Check errors
        self._rtu.decoder.decode = MagicMock(return_value=None)
        self.assertRaises(ModbusIOException, lambda: self._rtu._process(mock_callback))

    def testRTUProcessIncomingPAkcets(self):
        mock_data = b"\x00\x01\x00\x00\x00\x01\xfc\x1b"

        def mock_callback(self):
            pass

        self._rtu.addToFrame = MagicMock()
        self._rtu._process = MagicMock()
        self._rtu.isFrameReady = MagicMock(return_value=False)
        self._rtu._buffer = mock_data

        self._rtu.processIncomingPacket(mock_data, mock_callback)

    #---------------------------------------------------------------------------#
    # ASCII tests
    #---------------------------------------------------------------------------#
    def testASCIIFramerTransactionReady(self):
        ''' Test a ascii frame transaction '''
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
        ''' Test a full ascii frame transaction '''
        msg = b'sss:F7031389000A60\r\n'
        pack = a2b_hex(msg[6:-4])
        self._ascii.addToFrame(msg)
        self.assertTrue(self._ascii.checkFrame())
        result = self._ascii.getFrame()
        self.assertEqual(pack, result)
        self._ascii.advanceFrame()

    def testASCIIFramerTransactionHalf(self):
        ''' Test a half completed ascii frame transaction '''
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
        ''' Test a ascii frame packet build '''
        request = ModbusRequest()
        self._ascii.populateResult(request)
        self.assertEqual(0x00, request.unit_id)

    def testASCIIFramerPacket(self):
        ''' Test a ascii frame packet build '''
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

        def mock_callback(mock_data):
            pass

        self._ascii.processIncomingPacket(mock_data, mock_callback)

        # Test failure:
        self._ascii.checkFrame = MagicMock(return_value=False)
        self._ascii.processIncomingPacket(mock_data, mock_callback)


    #---------------------------------------------------------------------------#
    # Binary tests
    #---------------------------------------------------------------------------#
    def testBinaryFramerTransactionReady(self):
        ''' Test a binary frame transaction '''
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
        ''' Test a full binary frame transaction '''
        msg  = b'\x7b\x01\x03\x00\x00\x00\x05\x85\xC9\x7d'
        pack = msg[2:-3]
        self._binary.addToFrame(msg)
        self.assertTrue(self._binary.checkFrame())
        result = self._binary.getFrame()
        self.assertEqual(pack, result)
        self._binary.advanceFrame()

    def testBinaryFramerTransactionHalf(self):
        ''' Test a half completed binary frame transaction '''
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
        ''' Test a binary frame packet build '''
        request = ModbusRequest()
        self._binary.populateResult(request)
        self.assertEqual(0x00, request.unit_id)

    def testBinaryFramerPacket(self):
        ''' Test a binary frame packet build '''
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

        def mock_callback(mock_data):
            pass

        self._binary.processIncomingPacket(mock_data, mock_callback)

        # Test failure:
        self._binary.checkFrame = MagicMock(return_value=False)
        self._binary.processIncomingPacket(mock_data, mock_callback)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
