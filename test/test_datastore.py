import unittest
from pymodbus.datastore import *
from pymodbus.exceptions import *

class SimpleDataStoreTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.datastore module
    '''

    def setUp(self):
        pass

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    def testModbusDataBlock(self):
        ''' Test a base data block store '''
        pass

    def testModbusSequentialDataBlock(self):
        ''' Test a sequential data block store '''
        pass

    def testModbusSparseDataBlock(self):
        ''' Test a sparse data block store '''
        pass

    def testServerContext(self):
        ''' Test a modbus server context '''
        pass

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()

    #c = ModbusServerContext(d=[0,100], c=[0,100], h=[0,100], i=[0,100])

    ## Test Coils
    ##-----------------------------------------------------------------------#
    #values = [True]*100
    #c.setCoilValues(0, values)
    #result = c.getCoilValues(0, 100)

    #if result == values: print "Coil Store Passed"

    ## Test Discretes
    ##-----------------------------------------------------------------------#
    #values = [False]*100
    #result = c.getDiscreteInputValues(0, 100)

    #if result == values: print "Discrete Store Passed"

    ## Test Holding Registers
    ##-----------------------------------------------------------------------#
    #values = [0xab]*100
    #c.setHoldingRegisterValues(0, values)
    #result = c.getHoldingRegisterValues(0, 100)

    #if result == values: print "Holding Register Store Passed"

    ## Test Input Registers
    ##-----------------------------------------------------------------------#
    #values = [0x00]*100
    #result = c.getInputRegisterValues(0, 100)

    #if result == values: print "Input Register Store Passed"
