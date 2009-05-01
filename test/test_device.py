import unittest
from pymodbus.device import *
from pymodbus.mexceptions import *

class SimpleDataStoreTest(unittest.TestCase):
    '''
    This is the unittest for the pymod.mexceptions module
    '''

    def setUp(self):
        info = {
                0x00: 'Bashwork',                               # VendorName
                0x01: 'PTM',                                    # ProductCode
                0x02: '1.0',                                    # MajorMinorRevision
                0x03: 'http://internets.com',   # VendorUrl
                0x04: 'pymodbus',                               # ProductName
                0x05: 'bashwork',                               # ModelName
                0x06: 'unittest',                               # UserApplicationName
                0x07: 'x',                                              # reserved
                0x08: 'x',                                              # reserved
                0x10: 'private'                                 # private data
        }
        self.ident = ModbusDeviceIdentification(info)
        self.control = ModbusControlBlock()
        self.access = ModbusAccessControl()

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.ident
        del self.control
        del self.access

    def testBasicCommands(self):
        ''' Test device identification reading '''
        self.assertTrue(str(self.ident) == "DeviceIdentity")
        self.assertTrue(str(self.control) == "ModbusControl")

    def testModbusDeviceIdentificationGet(self):
        ''' Test device identification reading '''
        self.assertTrue(self.ident[0x00] == 'Bashwork')
        self.assertTrue(self.ident[0x01] == 'PTM')
        self.assertTrue(self.ident[0x02] == '1.0')
        self.assertTrue(self.ident[0x03] == 'http://internets.com')
        self.assertTrue(self.ident[0x04] == 'pymodbus')
        self.assertTrue(self.ident[0x05] == 'bashwork')
        self.assertTrue(self.ident[0x06] == 'unittest')
        self.assertTrue(self.ident[0x07] == 'x')
        self.assertTrue(self.ident[0x08] == 'x')
        self.assertTrue(self.ident[0x10] == 'private')
        self.assertTrue(self.ident[0x54] == '')

    def testModbusDeviceIdentificationSet(self):
        ''' Test a device identification writing '''
        self.ident[0x07] = 'y'
        self.ident[0x08] = 'y'
        self.ident[0x10] = 'public'
        self.ident[0x54] = 'testing'

        self.assertFalse(self.ident[0x07] == 'y')
        self.assertFalse(self.ident[0x08] == 'y')
        self.assertTrue(self.ident[0x10] == 'public')
        self.assertTrue(self.ident[0x54] == 'testing')

    def testModbusControlBlockAsciiModes(self):
        ''' Test a server control block ascii mode '''
        self.assertTrue(id(self.control) == id(ModbusControlBlock()))
        self.control.Identity = self.ident
        self.control.setMode('RTU')
        self.assertTrue(self.control.getMode() == 'RTU')
        self.control.setMode('FAKE')
        self.assertFalse(self.control.getMode() == 'FAKE')

    def testModbusControlBlockInvalidCounters(self):
        ''' Tests querying invalid MCB counters methods '''
        self.assertEqual(None, self.control.getCounter("InvalidCounter"))
        self.assertEqual(None, self.control.getCounter(None))
        self.assertEqual(None, self.control.getCounter(["BusMessage"]))

    def testModbusControlBlockCounters(self):
        ''' Tests the MCB counters methods '''
        self.assertTrue(self.control.getCounter("BusMessage") == 0)
        for i in range(10):
            self.control.incrementCounter("BusMessage")
            self.control.incrementCounter("SlaveMessage")
        self.assertTrue(self.control.getCounter("BusMessage") == 10)
        self.control.resetCounter("BusMessage")
        self.assertTrue(self.control.getCounter("BusMessage") == 0)
        self.assertTrue(self.control.getCounter("SlaveMessage") == 10)
        self.control.resetAllCounters()
        self.assertTrue(self.control.getCounter("SlaveMessage") == 0)

    def testModbusControlBlockListen(self):
        ''' Tests the MCB listen flag methods '''
        self.assertTrue(self.control.isListenOnly() == False)
        self.control.toggleListenOnly()
        self.assertTrue(self.control.isListenOnly() == True)

    def testModbusControlBlockDelimiter(self):
        ''' Tests the MCB delimiter setting methods '''
        self.assertTrue(self.control.getDelimiter() == '\r')
        self.control.setDelimiter('=')
        self.assertTrue(self.control.getDelimiter() == '=')
        self.control.setDelimiter(61)
        self.assertTrue(self.control.getDelimiter() == '=')

    def testModbusControlBlockDiagnostic(self):
        ''' Tests the MCB delimiter setting methods '''
        self.assertTrue(self.control.getDiagnosticRegister() == [False] * 16)
        for i in [1,3,4,6]:
            self.control.setDiagnostic({i:True});
        self.assertTrue(self.control.getDiagnostic(1) == True)
        self.assertTrue(self.control.getDiagnostic(2) == False)
        actual = [False, True, False, True, True, False, True] + [False] * 9
        self.assertTrue(self.control.getDiagnosticRegister() == actual)
        for i in range(16):
            self.control.setDiagnostic({i:False});

    def testModbusControlBlockInvalidDiagnostic(self):
        ''' Tests querying invalid MCB counters methods '''
        self.assertEqual(None, self.control.getDiagnostic(-1))
        self.assertEqual(None, self.control.getDiagnostic(17))
        self.assertEqual(None, self.control.getDiagnostic(None))
        self.assertEqual(None, self.control.getDiagnostic([1,2,3]))



    def testAddRemoveSingleClients(self):
        ''' Test adding and removing a host '''
        self.assertFalse(self.access.check("192.168.1.1"))
        self.access.add("192.168.1.1")
        self.assertTrue(self.access.check("192.168.1.1"))
        self.access.add("192.168.1.1")
        self.access.remove("192.168.1.1")
        self.assertFalse(self.access.check("192.168.1.1"))

    def testAddRemoveMultipleClients(self):
        ''' Test adding and removing a host '''
        list = ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
        self.access.add(list)
        for host in list:
            self.assertTrue(self.access.check(host))
        self.access.remove(list)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
