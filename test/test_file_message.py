'''
Bit Message Test Fixture
--------------------------------
This fixture tests the functionality of all the 
bit based request/response messages:

* Read/Write Discretes
* Read Coils
'''
import unittest
from pymodbus.utilities import packBitsToString
from pymodbus.file_message import *
from pymodbus.mexceptions import *
from pymodbus.pdu import ModbusExceptions

#---------------------------------------------------------------------------#
# Mocks
#---------------------------------------------------------------------------#
class Context(object):
    def validate(self, a,b,c):
        return False

    def getValues(self, a, b, count):
        return [True] * count

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

    #-----------------------------------------------------------------------#
    # Read Fifo Queue
    #-----------------------------------------------------------------------#

    def testReadFifoQueueRequest(self):
        ''' Test basic bit message encoding/decoding '''
        context = Context()
        handle  = ReadFifoQueueRequest(0x1234)
        result  = handle.execute(context)
        self.assertTrue(isinstance(result, ReadFifoQueueResponse))

    def testReadFifoQueueResponseEncode(self):
        ''' Test that the read fifo queue response can encode '''
        message = '\x00\n\x00\x08\x00\x01\x00\x02\x00\x03\x00\x04'
        handle  = ReadFifoQueueResponse([1,2,3,4])
        result  = handle.encode()
        self.assertEqual(result, message)

    def testReadFifoQueueResponseDecode(self):
        ''' Test that the read fifo queue response can decode '''
        message = '\x00\n\x00\x08\x00\x01\x00\x02\x00\x03\x00\x04'
        handle  = ReadFifoQueueResponse([1,2,3,4])
        handle.decode(message)
        self.assertEqual(handle.values, [1,2,3,4])

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
