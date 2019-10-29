#!/usr/bin/env python
"""
Pymodbus Synchronous Server Example with Custom functions
--------------------------------------------------------------------------

Implements a custom function code not in standard modbus function code list
and its response which otherwise would throw  `IllegalFunction (0x1)` error.

Steps:
1. Create CustomModbusRequest class derived from ModbusRequest
    ```class CustomModbusRequest(ModbusRequest):
           function_code = 75   # Value less than 0x80)
           _rtu_frame_size = <some_value>  # Required only For RTU support

           def __init__(custom_arg=None, **kwargs)
                # Make sure the arguments has default values, will error out
                # while decoding otherwise
                ModbusRequest.__init__(self, **kwargs)
                self.custom_request_arg = custom_arg

            def encode(self):
                # Implement encoding logic

            def decode(self, data):
                # implement decoding logic

            def execute(self, context):
                # Implement execute logic
                ...
                return CustomModbusResponse(..)

    ```
2. Create CustomModbusResponse class derived from ModbusResponse
    ```class CustomModbusResponse(ModbusResponse):
           function_code = 75   # Value less than 0x80)
           _rtu_byte_count_pos = <some_value>  # Required only For RTU support

           def __init__(self, custom_args=None, **kwargs):
                # Make sure the arguments has default values, will error out
                # while decoding otherwise
                ModbusResponse.__init__(self, **kwargs)
                self.custom_reponse_values = values

            def encode(self):
                # Implement encoding logic
            def decode(self, data):
                # Implement decoding logic
    ```
3. Register with ModbusSlaveContext,
    if your request has to access some values from the data-store.
    ```store = ModbusSlaveContext(...)
       store.register(CustomModbusRequest.function_code, 'dummy_context_name')
    ```
4. Pass CustomModbusRequest class as argument to Start<protocol>Server
    ```
    StartTcpServer(..., custom_functions=[CustomModbusRequest]..)
    ```

"""
# --------------------------------------------------------------------------- #
# import the various server implementations
# --------------------------------------------------------------------------- #
from pymodbus.server.sync import StartTcpServer

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from custom_message import CustomModbusRequest

# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
import logging

FORMAT = ('%(asctime)-15s %(threadName)-15s'
          ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)


def run_server():
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17] * 100),
        co=ModbusSequentialDataBlock(0, [17] * 100),
        hr=ModbusSequentialDataBlock(0, [17] * 100),
        ir=ModbusSequentialDataBlock(0, [17] * 100))

    store.register(CustomModbusRequest.function_code, 'cm',
                   ModbusSequentialDataBlock(0, [17] * 100))
    context = ModbusServerContext(slaves=store, single=True)

    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #
    # If you don't set this or any fields, they are defaulted to empty strings.
    # ----------------------------------------------------------------------- #
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'Pymodbus'
    identity.ProductCode = 'PM'
    identity.VendorUrl = 'http://github.com/riptideio/pymodbus/'
    identity.ProductName = 'Pymodbus Server'
    identity.ModelName = 'Pymodbus Server'
    identity.MajorMinorRevision = '2.3.0'

    # ----------------------------------------------------------------------- #
    # run the server you want
    # ----------------------------------------------------------------------- #
    # Tcp:
    StartTcpServer(context, identity=identity, address=("localhost", 5020),
                   custom_functions=[CustomModbusRequest])


if __name__ == "__main__":
    run_server()

