#!/usr/bin/env python3
"""Build framer encode responses."""

from pymodbus.framer import (
    FramerAscii,
    FramerRTU,
    FramerSocket,
    FramerTLS,
)
from pymodbus.pdu import DecodePDU, ExceptionResponse
from pymodbus.pdu.register_message import (
    ReadHoldingRegistersRequest,
    ReadHoldingRegistersResponse,
)


def set_calls():
    """Define calls."""
    for framer in (FramerAscii, FramerRTU, FramerSocket, FramerTLS):
        print(f"framer --> {framer}")
        for dev_id in (0, 17, 255):
            print(f"  dev_id --> {dev_id}")
            for tid in (0, 3077):
                print(f"    tid --> {tid}")
                client = framer(DecodePDU(False))
                request = ReadHoldingRegistersRequest(address=124, count=2, slave_id=dev_id)
                request.transaction_id = tid
                result = client.buildFrame(request)
                print(f"      request --> {result}")
                print(f"      request --> {result.hex()}")
                server = framer(DecodePDU(True))
                response = ReadHoldingRegistersResponse(registers=[141,142])
                response.slave_id = dev_id
                response.transaction_id = tid
                result = server.buildFrame(response)
                print(f"      response --> {result}")
                print(f"      response --> {result.hex()}")
                exception = ExceptionResponse(request.function_code, ExceptionResponse.ILLEGAL_ADDRESS)
                exception.transaction_id = tid
                exception.slave_id = dev_id
                result = server.buildFrame(exception)
                print(f"      exception --> {result}")
                print(f"      exception --> {result.hex()}")

set_calls()
