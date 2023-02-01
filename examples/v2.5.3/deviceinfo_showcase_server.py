#!/usr/bin/env python3
"""Pymodbus Synchronous Server Example to showcase Device Information.

This server demonstrates the use of Device Information to provide information
to clients about the device. This is part of the MODBUS specification, and
uses the MEI 0x2B 0x0E request / response. This example creates an otherwise
empty server.
"""
import logging

from serial import __version__ as pyserial_version

from pymodbus import __version__ as pymodbus_version
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext

# from pymodbus.server import StartUdpServer
# from pymodbus.server import StartSerialServer
# from pymodbus.transaction import ModbusRtuFramer, ModbusBinaryFramer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server import StartTcpServer

# --------------------------------------------------------------------------- #
# import the various server implementations
# --------------------------------------------------------------------------- #
from pymodbus.version import version


# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
FORMAT = (
    "%(asctime)-15s %(threadName)-15s"
    " %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)


def run_server():
    """Run server."""
    # ----------------------------------------------------------------------- #
    # initialize your data store
    # ----------------------------------------------------------------------- #
    store = ModbusSlaveContext()
    context = ModbusServerContext(slaves=store, single=True)

    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #
    # If you don't set this or any fields, they are defaulted to empty strings.
    # ----------------------------------------------------------------------- #
    identity = ModbusDeviceIdentification(
        info_name={
            "VendorName": "Pymodbus",
            "ProductCode": "PM",
            "VendorUrl": "https://github.com/pymodbus-dev/pymodbus/",
            "ProductName": "Pymodbus Server",
            "ModelName": "Pymodbus Server",
            "MajorMinorRevision": version.short(),
        }
    )

    # ----------------------------------------------------------------------- #
    # Add an example which is long enough to force the ReadDeviceInformation
    # request / response to require multiple responses to send back all of the
    # information.
    # ----------------------------------------------------------------------- #

    identity[0x80] = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing "
        "elit. Vivamus rhoncus massa turpis, sit amet "
        "ultrices orci semper ut. Aliquam tristique sapien in "
        "lacus pharetra, in convallis nunc consectetur. Nunc "
        "velit elit, vehicula tempus tempus sed. "
    )

    # ----------------------------------------------------------------------- #
    # Add an example with repeated object IDs. The MODBUS specification is
    # entirely silent on whether or not this is allowed. In practice, this
    # should be assumed to be contrary to the MODBUS specification and other
    # clients (other than pymodbus) might behave differently when presented
    # with an object ID occurring twice in the returned information.
    #
    # Use this at your discretion, and at the very least ensure that all
    # objects which share a single object ID can fit together within a single
    # ADU unit. In the case of Modbus RTU, this is about 240 bytes or so. In
    # other words, when the spec says "An object is indivisible, therefore
    # any object must have a size consistent with the size of transaction
    # response", if you use repeated OIDs, apply that rule to the entire
    # grouping of objects with the repeated OID.
    # ----------------------------------------------------------------------- #
    identity[0x81] = [f"pymodbus {pymodbus_version}", f"pyserial {pyserial_version}"]

    # ----------------------------------------------------------------------- #
    # run the server you want
    # ----------------------------------------------------------------------- #
    # Tcp:
    StartTcpServer(context, identity=identity, address=("localhost", 5020))

    # TCP with different framer
    # StartTcpServer(context, identity=identity,
    #                framer=ModbusRtuFramer, address=("0.0.0.0", 5020))

    # Udp:
    # StartUdpServer(context, identity=identity, address=("0.0.0.0", 5020))

    # Ascii:
    # StartSerialServer(context, identity=identity,
    #                    port="/dev/ttyp0", timeout=1)

    # RTU:
    # StartSerialServer(context, framer=ModbusRtuFramer, identity=identity,
    #                   port="/dev/ttyp0", timeout=.005, baudrate=9600)

    # Binary
    # StartSerialServer(context,
    #                   identity=identity,
    #                   framer=ModbusBinaryFramer,
    #                   port="/dev/ttyp0",
    #                   timeout=1)


if __name__ == "__main__":
    run_server()
