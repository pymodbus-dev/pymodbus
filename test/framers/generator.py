#!/usr/bin/env python3
"""Build framer encode responses."""

from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.framer import (
    ModbusAsciiFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)
from pymodbus.pdu import ModbusExceptions as merror
from pymodbus.pdu.register_read_message import (
    ReadHoldingRegistersRequest,
    ReadHoldingRegistersResponse,
)


def set_calls():
    """Define calls."""
    for framer in (ModbusAsciiFramer, ModbusRtuFramer, ModbusSocketFramer, ModbusTlsFramer):
        print(f"framer --> {framer}")
        for dev_id in (0, 17, 255):
            print(f"  dev_id --> {dev_id}")
            for tid in (0, 3077):
                print(f"    tid --> {tid}")
                client = framer(ClientDecoder())
                request = ReadHoldingRegistersRequest(124, 2, dev_id)
                request.transaction_id = tid
                result = client.buildPacket(request)
                print(f"      request --> {result}")
                print(f"      request --> {result.hex()}")
                server = framer(ServerDecoder())
                response = ReadHoldingRegistersResponse([141,142])
                response.slave_id = dev_id
                response.transaction_id = tid
                result = server.buildPacket(response)
                print(f"      response --> {result}")
                print(f"      response --> {result.hex()}")
                exception = request.doException(merror.IllegalAddress)
                exception.transaction_id = tid
                exception.slave_id = dev_id
                result = server.buildPacket(exception)
                print(f"      exception --> {result}")
                print(f"      exception --> {result.hex()}")

set_calls()
