#!/usr/bin/env python3
"""Pymodbus Synchronous Client Example to showcase Device Information.

This client demonstrates the use of Device Information to get information
about servers connected to the client. This is part of the MODBUS specification,
and uses the MEI 0x2B 0x0E request / response.
"""
import logging

# --------------------------------------------------------------------------- #
# import the various server implementations
# --------------------------------------------------------------------------- #
from pymodbus.client import ModbusTcpClient as ModbusClient
from pymodbus.device import ModbusDeviceIdentification

# --------------------------------------------------------------------------- #
# import the request
# --------------------------------------------------------------------------- #
from pymodbus.mei_message import ReadDeviceInformationRequest


# from pymodbus.client import ModbusUdpClient as ModbusClient
# from pymodbus.client import ModbusSerialClient as ModbusClient


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
    client.connect()

    # ------------------------------------------------------------------------#
    # specify slave to query
    # ------------------------------------------------------------------------#
    # The slave to query is specified in an optional parameter for each
    # individual request. This can be done by specifying the `unit` parameter
    # which defaults to `0x00`
    # ----------------------------------------------------------------------- #
    log.debug("Reading Device Information")
    information = {}
    rr = None

    while not rr or rr.more_follows:
        next_object_id = rr.next_object_id if rr else 0
        rq = ReadDeviceInformationRequest(
            read_code=0x03, unit=UNIT, object_id=next_object_id
        )
        rr = client.execute(rq)
        information.update(rr.information)
        log.debug(rr)

    print("Device Information : ")
    for (
        key
    ) in (
        information.keys()
    ):  # pylint: disable=consider-iterating-dictionary,consider-using-dict-items
        print(key, information[key])

    # ----------------------------------------------------------------------- #
    # You can also have the information parsed through the
    # ModbusDeviceIdentificiation class, which gets you a more usable way
    # to access the Basic and Regular device information objects which are
    # specifically listed in the Modbus specification
    # ----------------------------------------------------------------------- #
    device_id = ModbusDeviceIdentification(info=information)
    print("Product Name : ", device_id.ProductName)

    # ----------------------------------------------------------------------- #
    # close the client
    # ----------------------------------------------------------------------- #
    client.close()


if __name__ == "__main__":
    run_sync_client()
