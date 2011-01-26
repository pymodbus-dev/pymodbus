'''
Bit Message Test Fixture
--------------------------------
This fixture tests the functionality of all the 
bit based request/response messages:

* Read/Write Discretes
* Read Coils
'''
import unittest, struct
from pymodbus.bit_write_message import *
from pymodbus.exceptions import *
from pymodbus.pdu import ModbusExceptions

#---------------------------------------------------------------------------#
# Mocks
#---------------------------------------------------------------------------#
class Context(object):

    def validate(self, *args, **kwargs):
        return False

    def getValues(self, code, addr, count=1):
        return [True] * count

    def setValues(self, *args, **kwargs):
        pass

class FakeList(object):
    def __len__(self):
        return 0x12345678
    def __iter__(self):
        return []

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class ModbusBitMessageTests(unittest.TestCase):

    #-----------------------------------------------------------------------#
    # Setup/TearDown
    #-----------------------------------------------------------------------#

    def setUp(self):
        '''
        Initializes the test environment and builds request/result
        encoding pairs
        '''
        pass

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    def testBitWriteBaseRequests(self):
        messages = {
            WriteSingleCoilRequest(1, 0xabcd)      : '\x00\x01\xff\x00',
            WriteSingleCoilResponse(1, 0xabcd)     : '\x00\x01\xff\x00',
            WriteMultipleCoilsRequest(1, [True]*5) : '\x00\x01\x00\x05\x01\x1f',
            WriteMultipleCoilsResponse(1, 5)       : '\x00\x01\x00\x05',
        }
        for request, expected in messages.iteritems():
            self.assertEqual(request.encode(), expected)

    def testWriteMultipleCoilsRequest(self):
        request = WriteMultipleCoilsRequest(1, [True]*5)
        request.decode('\x00\x01\x00\x05\x01\x1f')
        self.assertEqual(request.byte_count, 1)
        self.assertEqual(request.address, 1)
        self.assertEqual(request.values, [True]*5)

    def testInvalidWriteMultipleCoilsRequest(self):
        self.assertRaises(ParameterException,
            lambda: WriteMultipleCoilsRequest(1, None))

    def testWriteSingleCoilExecute(self):
        context = Context()
        context.validate = lambda a,b,c: False
        request = WriteSingleCoilRequest(2, True)
        result  = request.execute(context)
        self.assertEqual(result.function_code, 0x85)

        context.validate = lambda a,b,c: True
        result  = request.execute(context)
        self.assertEqual(result.encode(), '\x00\x02\xff\x00')

    def testWriteMultipleCoilsExecute(self):
        context = Context()
        # too many values
        request = WriteMultipleCoilsRequest(2, FakeList())
        result  = request.execute(context)
        self.assertEqual(result.exception_code, 0x03)

        # bad byte count
        request = WriteMultipleCoilsRequest(2, FakeList())
        request.byte_count = 0x00
        result  = request.execute(context)
        self.assertEqual(result.exception_code, 0x03)

        # does not validate
        context.validate = lambda a,b,c: False
        request = WriteMultipleCoilsRequest(2, [0x00]*4)
        result  = request.execute(context)
        self.assertEqual(result.exception_code, 0x02)

        # validated request
        context.validate = lambda a,b,c: True
        result  = request.execute(context)
        self.assertEqual(result.encode(), '\x00\x02\x00\x04')


    def testWriteMultipleCoilsResponse(self):
        response = WriteMultipleCoilsResponse()
        response.decode('\x00\x80\x00\x08')
        self.assertEqual(response.address, 0x80)
        self.assertEqual(response.count, 0x08)

    def testSerializingToString(self):
        requests = [
            WriteSingleCoilRequest(1, 0xabcd),
            WriteSingleCoilResponse(1, 0xabcd),
            WriteMultipleCoilsRequest(1, [True]*5),
            WriteMultipleCoilsResponse(1, 5),
        ]
        for request in requests:
            self.assertTrue(str(request) != None)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
