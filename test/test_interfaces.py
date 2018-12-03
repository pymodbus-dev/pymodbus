#!/usr/bin/env python
import unittest
from pymodbus.interfaces import *
from pymodbus.exceptions import NotImplementedException

class _SingleInstance(Singleton):
    pass

class ModbusInterfaceTestsTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.interfaces module
    '''

    def setUp(self):
        ''' Initializes the test environment '''
        pass

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    def testSingletonInterface(self):
        ''' Test that the singleton interface works '''
        first  = _SingleInstance()
        second = _SingleInstance()
        self.assertEqual(first, second)

    def testModbusDecoderInterface(self):
        ''' Test that the base class isn't implemented '''
        x = None
        instance = IModbusDecoder()
        self.assertRaises(NotImplementedException, lambda: instance.decode(x))
        self.assertRaises(NotImplementedException,
                          lambda: instance.lookupPduClass(x))
        self.assertRaises(NotImplementedException,
                          lambda: instance.register(x))

    def testModbusFramerInterface(self):
        ''' Test that the base class isn't implemented '''
        x = None
        instance = IModbusFramer()
        self.assertRaises(NotImplementedException, instance.checkFrame)
        self.assertRaises(NotImplementedException, instance.advanceFrame)
        self.assertRaises(NotImplementedException, instance.isFrameReady)
        self.assertRaises(NotImplementedException, instance.getFrame)
        self.assertRaises(NotImplementedException, lambda: instance.addToFrame(x))
        self.assertRaises(NotImplementedException, lambda: instance.populateResult(x))
        self.assertRaises(NotImplementedException, lambda: instance.processIncomingPacket(x,x))
        self.assertRaises(NotImplementedException, lambda: instance.buildPacket(x))

    def testModbusSlaveContextInterface(self):
        ''' Test that the base class isn't implemented '''
        x = None
        instance = IModbusSlaveContext()
        self.assertRaises(NotImplementedException, instance.reset)
        self.assertRaises(NotImplementedException, lambda: instance.validate(x,x,x))
        self.assertRaises(NotImplementedException, lambda: instance.getValues(x,x,x))
        self.assertRaises(NotImplementedException, lambda: instance.setValues(x,x,x))

    def testModbusPayloadBuilderInterface(self):
        ''' Test that the base class isn't implemented '''
        x = None
        instance = IPayloadBuilder()
        self.assertRaises(NotImplementedException, lambda: instance.build())

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
