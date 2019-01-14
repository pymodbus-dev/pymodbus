#!/usr/bin/env python
import unittest
from pymodbus.factory import ServerDecoder, ClientDecoder
from pymodbus.exceptions import ModbusException, MessageRegisterException
from pymodbus.pdu import ModbusResponse, ModbusRequest

def _raise_exception(_):
    raise ModbusException('something')

class SimpleFactoryTest(unittest.TestCase):
    '''
    This is the unittest for the pymod.exceptions module
    '''

    def setUp(self):
        ''' Initializes the test environment '''
        self.client  = ClientDecoder()
        self.server  = ServerDecoder()
        self.request = (
                (0x01, b'\x01\x00\x01\x00\x01'),                       # read coils
                (0x02, b'\x02\x00\x01\x00\x01'),                       # read discrete inputs
                (0x03, b'\x03\x00\x01\x00\x01'),                       # read holding registers
                (0x04, b'\x04\x00\x01\x00\x01'),                       # read input registers
                (0x05, b'\x05\x00\x01\x00\x01'),                       # write single coil
                (0x06, b'\x06\x00\x01\x00\x01'),                       # write single register
                (0x07, b'\x07'),                                       # read exception status
                (0x08, b'\x08\x00\x00\x00\x00'),                       # read diagnostic
                (0x0b, b'\x0b'),                                       # get comm event counters
                (0x0c, b'\x0c'),                                       # get comm event log
                (0x0f, b'\x0f\x00\x01\x00\x08\x01\x00\xff'),           # write multiple coils
                (0x10, b'\x10\x00\x01\x00\x02\x04\0xff\xff'),          # write multiple registers
                (0x11, b'\x11'),                                       # report slave id
                (0x14, b'\x14\x0e\x06\x00\x04\x00\x01\x00\x02' \
                       b'\x06\x00\x03\x00\x09\x00\x02'),               # read file record
                (0x15, b'\x15\x0d\x06\x00\x04\x00\x07\x00\x03' \
                       b'\x06\xaf\x04\xbe\x10\x0d'),                   # write file record
                (0x16, b'\x16\x00\x01\x00\xff\xff\x00'),               # mask write register
                (0x17, b'\x17\x00\x01\x00\x01\x00\x01\x00\x01\x02\x12\x34'),# read/write multiple registers
                (0x18, b'\x18\x00\x01'),                               # read fifo queue
                (0x2b, b'\x2b\x0e\x01\x00'),                           # read device identification
        )

        self.response = (
                (0x01, b'\x01\x01\x01'),                               # read coils
                (0x02, b'\x02\x01\x01'),                               # read discrete inputs
                (0x03, b'\x03\x02\x01\x01'),                           # read holding registers
                (0x04, b'\x04\x02\x01\x01'),                           # read input registers
                (0x05, b'\x05\x00\x01\x00\x01'),                       # write single coil
                (0x06, b'\x06\x00\x01\x00\x01'),                       # write single register
                (0x07, b'\x07\x00'),                                   # read exception status
                (0x08, b'\x08\x00\x00\x00\x00'),                       # read diagnostic
                (0x0b, b'\x0b\x00\x00\x00\x00'),                       # get comm event counters
                (0x0c, b'\x0c\x08\x00\x00\x01\x08\x01\x21\x20\x00'),   # get comm event log
                (0x0f, b'\x0f\x00\x01\x00\x08'),                       # write multiple coils
                (0x10, b'\x10\x00\x01\x00\x02'),                       # write multiple registers
                (0x11, b'\x11\x03\x05\x01\x54'),                       # report slave id (device specific)
                (0x14, b'\x14\x0c\x05\x06\x0d\xfe\x00\x20\x05' \
                       b'\x06\x33\xcd\x00\x40'),                       # read file record
                (0x15, b'\x15\x0d\x06\x00\x04\x00\x07\x00\x03' \
                       b'\x06\xaf\x04\xbe\x10\x0d'),                   # write file record
                (0x16, b'\x16\x00\x01\x00\xff\xff\x00'),               # mask write register
                (0x17, b'\x17\x02\x12\x34'),                           # read/write multiple registers
                (0x18, b'\x18\x00\x01\x00\x01\x00\x00'),               # read fifo queue
                (0x2b, b'\x2b\x0e\x01\x01\x00\x00\x01\x00\x01\x77'),   # read device identification
        )

        self.exception = (
                (0x81, b'\x81\x01\xd0\x50'),                           # illegal function exception
                (0x82, b'\x82\x02\x90\xa1'),                           # illegal data address exception
                (0x83, b'\x83\x03\x50\xf1'),                           # illegal data value exception
                (0x84, b'\x84\x04\x13\x03'),                           # skave device failure exception
                (0x85, b'\x85\x05\xd3\x53'),                           # acknowledge exception
                (0x86, b'\x86\x06\x93\xa2'),                           # slave device busy exception
                (0x87, b'\x87\x08\x53\xf2'),                           # memory parity exception
                (0x88, b'\x88\x0a\x16\x06'),                           # gateway path unavailable exception
                (0x89, b'\x89\x0b\xd6\x56'),                           # gateway target failed exception
        )

        self.bad = (
                (0x80, b'\x80\x00\x00\x00'),                           # Unknown Function
                (0x81, b'\x81\x00\x00\x00'),                           # error message
        )

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.bad
        del self.request
        del self.response

    def testExceptionLookup(self):
        ''' Test that we can look up exception messages '''
        for func, _ in self.exception:
            response = self.client.lookupPduClass(func)
            self.assertNotEqual(response, None)

        for func, _ in self.exception:
            response = self.server.lookupPduClass(func)
            self.assertNotEqual(response, None)

    def testResponseLookup(self):
        ''' Test a working response factory lookup '''
        for func, _ in self.response:
            response = self.client.lookupPduClass(func)
            self.assertNotEqual(response, None)

    def testRequestLookup(self):
        ''' Test a working request factory lookup '''
        for func, _ in self.request:
            request = self.client.lookupPduClass(func)
            self.assertNotEqual(request, None)

    def testResponseWorking(self):
        ''' Test a working response factory decoders '''
        for func, msg in self.response:
            try:
                self.client.decode(msg)
            except ModbusException:
                self.fail("Failed to Decode Response Message", func)

    def testResponseErrors(self):
        ''' Test a response factory decoder exceptions '''
        self.assertRaises(ModbusException, self.client._helper, self.bad[0][1])
        self.assertEqual(self.client.decode(self.bad[1][1]).function_code, self.bad[1][0],
                "Failed to decode error PDU")

    def testRequestsWorking(self):
        ''' Test a working request factory decoders '''
        for func, msg in self.request:
            try:
                self.server.decode(msg)
            except ModbusException:
                self.fail("Failed to Decode Request Message", func)

    def testClientFactoryFails(self):
        ''' Tests that a client factory will fail to decode a bad message '''
        self.client._helper = _raise_exception
        actual = self.client.decode(None)
        self.assertEqual(actual, None)

    def testServerFactoryFails(self):
        ''' Tests that a server factory will fail to decode a bad message '''
        self.server._helper = _raise_exception
        actual = self.server.decode(None)
        self.assertEqual(actual, None)

    def testServerRegisterCustomRequest(self):
        class CustomRequest(ModbusRequest):
            function_code = 0xff
        self.server.register(CustomRequest)
        assert self.client.lookupPduClass(CustomRequest.function_code)
        CustomRequest.sub_function_code = 0xff
        self.server.register(CustomRequest)
        assert self.server.lookupPduClass(CustomRequest.function_code)

    def testClientRegisterCustomResponse(self):
        class CustomResponse(ModbusResponse):
            function_code = 0xff
        self.client.register(CustomResponse)
        assert self.client.lookupPduClass(CustomResponse.function_code)
        CustomResponse.sub_function_code = 0xff
        self.client.register(CustomResponse)
        assert self.client.lookupPduClass(CustomResponse.function_code)
#---------------------------------------------------------------------------#
# I don't actually know what is supposed to be returned here, I assume that
# since the high bit is set, it will simply echo the resulting message
#---------------------------------------------------------------------------#
    def testRequestErrors(self):
        ''' Test a request factory decoder exceptions '''
        for func, msg in self.bad:
            result = self.server.decode(msg)
            self.assertEqual(result.ErrorCode, 1,
                    "Failed to decode invalid requests")
            self.assertEqual(result.execute(None).function_code, func,
                    "Failed to create correct response message")

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
