import unittest
from pymodbus.bit_read_message import *
from pymodbus.bit_write_message import *
from pymodbus.register_read_message import *
from pymodbus.register_write_message import *

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class ModbusAllMessagesTests(unittest.TestCase):

    #-----------------------------------------------------------------------#
    # Setup/TearDown
    #-----------------------------------------------------------------------#

    def setUp(self):
        '''
        Initializes the test environment and builds request/result
        encoding pairs
        '''
        self.requests = [
            lambda unit: ReadCoilsRequest(1, 5, unit=unit),
            lambda unit: ReadDiscreteInputsRequest(1, 5, unit=unit),
            lambda unit: WriteSingleCoilRequest(1, 1, unit=unit),
            lambda unit: WriteMultipleCoilsRequest(1, [1], unit=unit),
            lambda unit: ReadHoldingRegistersRequest(1, 5, unit=unit),
            lambda unit: ReadInputRegistersRequest(1, 5, unit=unit),
            lambda unit: ReadWriteMultipleRegistersRequest(1, 5, 1, [1], unit=unit),
            lambda unit: WriteSingleRegisterRequest(1, 1, unit=unit),
            lambda unit: WriteMultipleRegistersRequest(1, [1], unit=unit),
        ]
        self.responses = [
            lambda unit: ReadCoilsResponse([1], unit=unit),
            lambda unit: ReadDiscreteInputsResponse([1], unit=unit),
            lambda unit: WriteSingleCoilResponse(1, 1, unit=unit),
            lambda unit: WriteMultipleCoilsResponse(1, [1], unit=unit),
            lambda unit: ReadHoldingRegistersResponse([1], unit=unit),
            lambda unit: ReadInputRegistersResponse([1], unit=unit),
            lambda unit: ReadWriteMultipleRegistersResponse([1], unit=unit),
            lambda unit: WriteSingleRegisterResponse(1, 1, unit=unit),
            lambda unit: WriteMultipleRegistersResponse(1, 1, unit=unit),
        ]

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    def testInitializingSlaveAddressRequest(self):
        ''' Test that every request can initialize the unit id '''
        unit_id = 0x12
        for factory in self.requests:
            request = factory(unit_id)
            self.assertEqual(request.unit_id, unit_id)

    def testInitializingSlaveAddressResponse(self):
        ''' Test that every response can initialize the unit id '''
        unit_id = 0x12
        for factory in self.responses:
            response = factory(unit_id)
            self.assertEqual(response.unit_id, unit_id)

