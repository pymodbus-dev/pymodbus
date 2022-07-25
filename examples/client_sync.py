#!/usr/bin/env python3
"""Pymodbus Synchronous Client Example.

The following is an example of how to use the synchronous modbus client
implementation from pymodbus, it is divided in several methods to make it
easier to adapt.

Start it as:
    python3 client_sync.py

After connection the client makes different calls to a server.
The corresponding server must be started before e.g. as:
    python3 server_sync.py
"""

# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from examples.helper import _logger, get_commandline
from pymodbus.client.sync import (
    ModbusSerialClient,
    ModbusTcpClient,
    ModbusTlsClient,
    ModbusUdpClient,
)
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)

FRAMERS = {
    "ascii": ModbusAsciiFramer,
    "binary": ModbusBinaryFramer,
    "rtu": ModbusRtuFramer,
    "socket": ModbusSocketFramer,
    "tls": ModbusTlsFramer,
}
UNIT = 0x1


def setup_sync_client():
    """Run client setup.

    use --comm at command line to select the type of communication
    use --framer at command line to select the modbus framer
    use --log at command line to set logging level
    The remaining parameters are defined static.
    """
    args = get_commandline(False)
    _logger.info("### Create client object")
    if args.comm == "tcp":
        if not args.framer:
            args.framer = "socket"
        client = ModbusTcpClient(
            host="127.0.0.1",  # define tcp address where to connect to.
            port=5020,  # on which port
            framer=FRAMERS[args.framer],  # how to interpret the messages
            timeout=1,  # waiting time for request to complete
            retries=3,  # retries per transaction
            retry_on_empty=False,  # Is an empty response a retry
            # TBD   source_address="localhost",  # bind socket to address
            strict=True,  # use strict timing, t1.5 for Modbus RTU
        )
    elif args.comm == "udp":
        if not args.framer:
            args.framer = "socket"
        client = ModbusUdpClient(
            host="localhost",  # define tcp address where to connect to.
            port=5020,  # on which port
            framer=FRAMERS[args.framer],  # how to interpret the messages
            timeout=1,  # waiting time for request to complete
            retries=3,  # retries per transaction
            retry_on_empty=False,  # Is an empty response a retry
            # TBD    source_address="localhost",  # bind socket to address
            strict=True,  # use strict timing, t1.5 for Modbus RTU
        )
    elif args.comm == "serial":
        if not args.framer:
            args.framer = "rtu"
        client = ModbusSerialClient(
            port="/dev/ptyp0",  # serial port
            method=args.framer,  # how to interpret the messages
            # TBD    framer=FRAMERS[args.framer],  # how to interpret the messages
            stopbits=1,  # The number of stop bits to use
            bytesize=7,  # The bytesize of the serial messages
            parity="even",  # Which kind of parity to use
            baudrate=9600,  # The baud rate to use for the serial device
            handle_local_echo=False,  # Handle local echo of the USB-to-RS485 adaptor
            timeout=1,  # waiting time for request to complete
            strict=True,  # use strict timing, t1.5 for Modbus RTU
        )
    elif args.comm == "tls":
        if not args.framer:
            args.framer = "tls"
        client = ModbusTlsClient(
            host="localhost",  # define tcp address where to connect to.
            port=5020,  # on which port
            sslctx=None,  # ssl control
            certfile=None,  # certificate file
            keyfile=None,  # key file
            password=None,  # pass phrase
            framer=FRAMERS[args.framer],  # how to interpret the messages
            timeout=1,  # waiting time for request to complete
            retries=3,  # retries per transaction
            retry_on_empty=False,  # Is an empty response a retry
            # TBD   source_address="localhost",  # bind socket to address
            strict=True,  # use strict timing, t1.5 for Modbus RTU
        )
    return client, args.comm != "udp"


def handle_coils(client):
    """Read/Write coils."""
    _logger.info("### Reading Coil")
    rr = client.read_coils(1, 1, unit=UNIT)
    assert not rr.isError()  # test that call was OK
    txt = f"### coils response: {str(rr.bits)}"
    _logger.debug(txt)

    _logger.info("### Reading Coils to get bit 5")
    rr = client.read_coils(1, 5)
    assert not rr.isError()  # test that call was OK
    txt = f"### coils response: {str(rr.bits)}"
    _logger.debug(txt)

    _logger.info("### Write true to coil bit 0 and read to verify")
    rq = client.write_coil(0, True)
    rr = client.read_coils(0, 1)
    assert not rq.isError() and not rr.isError()  # test that calls was OK
    assert rr.bits[0]  # test the expected value
    txt = f"### coils response: {str(rr.bits)}"
    _logger.debug(txt)

    _logger.info("### Write true to multiple coils 1-8")
    rq = client.write_coils(1, [True] * 8, unit=UNIT)
    rr = client.read_coils(1, 21, unit=UNIT)
    assert not rq.isError() and not rr.isError()  # test that calls was OK
    resp = [True] * 21
    # If the returned output quantity is not a multiple of eight,
    # the remaining bits in the final data byte will be padded with zeros
    # (toward the high order end of the byte).
    resp.extend([False] * 3)
    assert rr.bits == resp  # test the expected value
    txt = f"### coils response: {str(rr.bits)}"
    _logger.debug(txt)

    _logger.info("### Write False to address 1-8 coils")
    rq = client.write_coils(1, [False] * 8, unit=UNIT)
    rr = client.read_coils(1, 8, unit=UNIT)
    assert not rq.isError() and not rr.isError()  # test that calls was OK
    assert rr.bits == [False] * 8  # test the expected value
    txt = f"### coils response: {str(rr.bits)}"
    _logger.debug(txt)


def handle_discrete_input(client):
    """Read discrete inputs."""
    _logger.info("### Reading discrete input, Read address:0-7")
    rr = client.read_discrete_inputs(0, 8, unit=UNIT)
    assert not rr.isError()  # nosec test that we are not an error
    txt = f"### address 0-7 is: {str(rr.bits)}"
    _logger.debug(txt)


def handle_holding_registers(client):
    """Read/write holding registers."""
    _logger.info("### write holding register and read holding registers")
    rq = client.write_register(1, 10, unit=UNIT)
    rr = client.read_holding_registers(1, 1, unit=UNIT)
    assert not rq.isError() and not rr.isError()  # test that calls was OK
    assert rr.registers[0] == 10  # nosec test the expected value
    txt = f"### address 1 is: {str(rr.registers[0])}"
    _logger.debug(txt)

    _logger.info("### write holding registers and read holding registers")
    rq = client.write_registers(1, [10] * 8, unit=UNIT)
    rr = client.read_holding_registers(1, 8, unit=UNIT)
    assert not rq.isError() and not rr.isError()  # test that calls was OK
    assert rr.registers == [10] * 8  # nosec test the expected value
    txt = f"### address 1-8 is: {str(rr.registers)}"
    _logger.debug(txt)

    _logger.info("### write read holding registers")
    arguments = {
        "read_address": 1,
        "read_count": 8,
        "write_address": 1,
        "write_registers": [256, 128, 100, 50, 25, 10, 5, 1],
    }
    rq = client.readwrite_registers(unit=UNIT, **arguments)
    rr = client.read_holding_registers(1, 8, unit=UNIT)
    assert not rq.isError() and not rr.isError()  # test that calls was OK
    assert rq.registers == arguments["write_registers"]
    assert rr.registers == arguments["write_registers"]
    txt = f"### Test 8 read result: address 1-8 is: {str(rr.registers)}"
    _logger.debug(txt)


def handle_input_registers(client):
    """Read input registers."""
    _logger.info("### read input registers")
    rr = client.read_input_registers(1, 8, unit=UNIT)
    assert not rr.isError()  # nosec test that we are not an error
    txt = f"### address 1 is: {str(rr.registers[0])}"
    _logger.debug(txt)


def run_sync_client():
    """Run sync client."""
    client, do_connect = setup_sync_client()

    if do_connect:
        _logger.info("### Connect to server")
        client.connect()

    _logger.info("### Client ready")
    handle_coils(client)
    handle_discrete_input(client)
    handle_holding_registers(client)
    handle_input_registers(client)

    if do_connect:
        _logger.info("### Close connection to server")
        client.close()
    _logger.info("### End of Program")


if __name__ == "__main__":
    run_sync_client()
