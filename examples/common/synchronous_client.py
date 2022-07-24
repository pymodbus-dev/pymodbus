#!/usr/bin/env python3
"""Pymodbus Synchronous Client Examples.

The following is an example of how to use the synchronous modbus client
implementation from pymodbus.

    with ModbusClient("127.0.0.1") as client:
        result = client.read_coils(1,10)
        print result
"""
import logging

# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

# from pymodbus.client.sync import ModbusUdpClient as ModbusClient
# from pymodbus.client.sync import ModbusSerialClient as ModbusClient

# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #
FORMAT = (
    "%(asctime)-15s %(threadName)-15s "
    "%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

UNIT = 0x1


def run_sync_client():
    """Run sync client."""
    # ------------------------------------------------------------------------#
    # choose the client you want
    # ------------------------------------------------------------------------#
    # make sure to start an implementation to hit against. For this
    # you can use an existing device, the reference implementation in the tools
    # directory, or start a pymodbus server.
    #
    # If you use the UDP or TCP clients, you can override the framer being used
    # to use a custom implementation (say RTU over TCP). By default they use
    # the socket framer::
    #
    #    client = ModbusClient("localhost", port=5020, framer=ModbusRtuFramer)
    #
    # It should be noted that you can supply an ipv4 or an ipv6 host address
    # for both the UDP and TCP clients.
    #
    # There are also other options that can be set on the client that controls
    # how transactions are performed. The current ones are:
    #
    # * retries - Specify how many retries to allow per transaction (default=3)
    # * retry_on_empty - Is an empty response a retry (default = False)
    # * source_address - Specifies the TCP source address to bind to
    # * strict - Applicable only for Modbus RTU clients.
    #            Adheres to modbus protocol for timing restrictions
    #            (default = True).
    #            Setting this to False would disable the inter char timeout
    #            restriction (t1.5) for Modbus RTU
    #
    #
    # Here is an example of using these options::
    #
    #    client = ModbusClient("localhost", retries=3, retry_on_empty=True)
    # ------------------------------------------------------------------------#
    client = ModbusClient("localhost", port=5020)
    # from pymodbus.transaction import ModbusRtuFramer
    # client = ModbusClient("localhost", port=5020, framer=ModbusRtuFramer)
    # client = ModbusClient(method="binary", port="/dev/ptyp0", timeout=1)
    # client = ModbusClient(method="ascii", port="/dev/ptyp0", timeout=1)
    # client = ModbusClient(method="rtu", port="/dev/ptyp0", timeout=1,
    #                       baudrate=9600)
    log.debug("### Connecting to server")
    client.connect()

    # ------------------------------------------------------------------------#
    # specify slave to query
    # ------------------------------------------------------------------------#
    # The slave to query is specified in an optional parameter for each
    # individual request. This can be done by specifying the `unit` parameter
    # which defaults to `0x00`
    # ----------------------------------------------------------------------- #
    log.debug("### Reading Coils")
    rr = client.read_coils(1, 1, unit=UNIT)

    log.debug(
        "### printing the content of Reference Number:(index) 1 and  1 bit depth  "
    )
    log.debug(rr.bits[0])

    # ----------------------------------------------------------------------- #
    # example requests
    # ----------------------------------------------------------------------- #
    # simply call the methods that you would like to use. An example session
    # is displayed below along with some assert checks. Note that some modbus
    # implementations differentiate holding/input discrete/coils and as such
    # you will not be able to write to these, therefore the starting values
    # are not known to these tests. Furthermore, some use the same memory
    # blocks for the two sets, so a change to one is a change to the other.
    # Keep both of these cases in mind when testing as the following will
    # _only_ pass with the supplied asynchronous modbus server (script supplied).
    # ----------------------------------------------------------------------- #
    log.debug("### Test 1 Coil (output): Write 'TRUE' to address:0")
    rq = client.write_coil(0, True, unit=UNIT)

    log.debug("### Test 1 Coil (output): Reading back address:0")
    rr = client.read_coils(0, 1, unit=UNIT)

    txt = f"### address:0 is: {str(rr.bits[0])}"
    log.debug(txt)
    assert not rq.isError()  # nosec test that we are not an error
    assert not rr.isError()  # nosec test that we are not an error
    assert rr.bits[0]  # nosec test the expected value

    log.debug("### Test 2 Coil (output) multiple: Write True to 1-8  coils")
    rq = client.write_coils(1, [True] * 8, unit=UNIT)

    log.debug("### Test 2 Coil (output) multiple: Reading back address:1-21")
    rr = client.read_coils(1, 21, unit=UNIT)
    assert not rq.isError()  # nosec test that we are not an error
    assert not rr.isError()  # nosec test that we are not an error
    resp = [True] * 21

    # If the returned output quantity is not a multiple of eight,
    # the remaining bits in the final data byte will be padded with zeros
    # (toward the high order end of the byte).

    resp.extend([False] * 3)
    assert rr.bits == resp  # nosec test the expected value

    log.debug("### Test 3 Coil (output) multiple: Write False to address 1-8  coils")
    rq = client.write_coils(1, [False] * 8, unit=UNIT)

    log.debug("### Test 3 Coil (output) multiple: Reading back multiple address:1-8")
    rr = client.read_coils(1, 8, unit=UNIT)
    assert not rq.isError()  # nosec test that we are not an error
    assert not rr.isError()  # nosec test that we are not an error
    assert rr.bits == [False] * 8  # nosec test the expected value

    log.debug("### Test 4 discrete inputs: Read address:0-7 ")
    rr = client.read_discrete_inputs(0, 8, unit=UNIT)
    assert not rr.isError()  # nosec test that we are not an error
    txt = f"### address 0-7 is: {str(rr.bits)}"
    log.debug(txt)

    log.debug("### Test 5 register (Output): Write '10 'to address 1 of registers ")
    rq = client.write_register(1, 10, unit=UNIT)

    log.debug("### Test 5 register (Output): reading address 1 of registers")
    rr = client.read_holding_registers(1, 1, unit=UNIT)
    assert not rq.isError()  # nosec test that we are not an error
    assert not rr.isError()  # nosec test that we are not an error

    txt = f"### address 1 is: {str(rr.registers[0])}"
    log.debug(txt)
    assert rr.registers[0] == 10  # nosec test the expected value

    log.debug("### Test 6 registers multiple: Write '10' to 8 registers")
    rq = client.write_registers(1, [10] * 8, unit=UNIT)
    log.debug("### Test 6 registers multiple: reading address 1-8 registers")
    rr = client.read_holding_registers(1, 8, unit=UNIT)
    assert not rq.isError()  # nosec test that we are not an error
    assert not rr.isError()  # nosec test that we are not an error
    txt = f"### address 1-8 is: {str(rr.registers)}"
    log.debug(txt)
    assert rr.registers == [10] * 8  # nosec test the expected value

    log.debug("### Test 7 Read input registers")
    rr = client.read_input_registers(1, 8, unit=UNIT)
    assert not rr.isError()  # nosec test that we are not an error

    arguments = {
        "read_address": 1,
        "read_count": 8,
        "write_address": 1,
        "write_registers": [256, 128, 100, 50, 25, 10, 5, 1],
    }
    log.debug("### Test 8 Read write registers simultaneously: write")
    rq = client.readwrite_registers(unit=UNIT, **arguments)

    txt = f"### Test 8 readwrite result: address 1-8 is: {str(rq.registers)}"
    log.debug(txt)
    rr = client.read_holding_registers(1, 8, unit=UNIT)
    txt = f"### Test 8 read result: address 1-8 is: {str(rr.registers)}"
    log.debug(txt)
    assert not rq.isError()  # nosec test that we are not an error
    assert not rr.isError()  # nosec test that we are not an error
    assert rq.registers == arguments["write_registers"]  # nosec test the expected value
    assert rr.registers == arguments["write_registers"]  # nosec test the expected value

    # ----------------------------------------------------------------------- #
    # close the client
    # ----------------------------------------------------------------------- #
    log.debug("### End of Program")
    client.close()


if __name__ == "__main__":
    run_sync_client()
