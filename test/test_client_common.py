#!/usr/bin/env python
import unittest
from pymodbus.client.common import ModbusClientMixin
from pymodbus.bit_read_message import *
from pymodbus.bit_write_message import *
from pymodbus.file_message import *
from pymodbus.register_read_message import *
from pymodbus.register_write_message import *

#---------------------------------------------------------------------------#
# Mocks
#---------------------------------------------------------------------------#
class MockClient(ModbusClientMixin):

    def execute(self, request):
        return request

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class ModbusCommonClientTests(unittest.TestCase):

    #-----------------------------------------------------------------------#
    # Setup/TearDown
    #-----------------------------------------------------------------------#
    def setUp(self):
        '''
        Initializes the test environment and builds request/result
        encoding pairs
        '''
        self.client = MockClient()

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.client

    #-----------------------------------------------------------------------#
    # Tests
    #-----------------------------------------------------------------------#
    def testModbusClientMixinMethods(self):
        ''' This tests that the mixing returns the correct request object '''
        arguments = {
            'read_address': 1, 'read_count': 1,
            'write_address': 1, 'write_registers': 1
        }
        self.assertTrue(isinstance(self.client.read_coils(1,1), ReadCoilsRequest))
        self.assertTrue(isinstance(self.client.read_discrete_inputs(1,1), ReadDiscreteInputsRequest))
        self.assertTrue(isinstance(self.client.write_coil(1,True), WriteSingleCoilRequest))
        self.assertTrue(isinstance(self.client.write_coils(1,[True]), WriteMultipleCoilsRequest))
        self.assertTrue(isinstance(self.client.write_register(1,0x00), WriteSingleRegisterRequest))
        self.assertTrue(isinstance(self.client.write_registers(1,[0x00]), WriteMultipleRegistersRequest))
        self.assertTrue(isinstance(self.client.read_holding_registers(1,1), ReadHoldingRegistersRequest))
        self.assertTrue(isinstance(self.client.read_input_registers(1,1), ReadInputRegistersRequest))
        self.assertTrue(isinstance(self.client.readwrite_registers(**arguments), ReadWriteMultipleRegistersRequest))
        self.assertTrue(isinstance(self.client.mask_write_register(1,0,0), MaskWriteRegisterRequest))
