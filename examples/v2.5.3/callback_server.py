#!/usr/bin/env python3
# pylint: disable=missing-type-doc,missing-param-doc,differing-param-doc
"""Pymodbus Server With Callbacks.

This is an example of adding callbacks to a running modbus server
when a value is written to it. In order for this to work, it needs
a device-mapping file.
"""
import logging
from multiprocessing import Queue
from threading import Thread

from pymodbus.datastore import (
    ModbusServerContext,
    ModbusSlaveContext,
    ModbusSparseDataBlock,
)
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server import StartTcpServer

# --------------------------------------------------------------------------- #
# import the modbus libraries we need
# --------------------------------------------------------------------------- #
from pymodbus.version import version


# from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer


# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- #
# create your custom data block with callbacks
# --------------------------------------------------------------------------- #


class CallbackDataBlock(ModbusSparseDataBlock):
    """A datablock that stores the new value in memory,

    and passes the operation to a message queue for further processing.
    """

    def __init__(self, devices, queue):
        """Initialize."""
        self.devices = devices
        self.queue = queue

        values = {k: 0 for k in devices.keys()}
        values[0xBEEF] = len(values)  # the number of devices
        super().__init__(values)

    def setValues(self, address, value):  # pylint: disable=arguments-differ
        """Set the requested values of the datastore

        :param address: The starting address
        :param values: The new values to be set
        """
        super().setValues(address, value)
        self.queue.put((self.devices.get(address, None), value))


# --------------------------------------------------------------------------- #
# define your callback process
# --------------------------------------------------------------------------- #


def rescale_value(value):
    """Rescale the input value from the range of 0..100 to -3200..3200.

    :param value: The input value to scale
    :returns: The rescaled value
    """
    scale = 1 if value >= 50 else -1
    cur = value if value < 50 else (value - 50)
    return scale * (cur * 64)


def device_writer(queue):
    """Process new messages from a queue to write to device outputs

    :param queue: The queue to get new messages from
    """
    while True:
        device, value = queue.get()
        rescale_value(value[0])
        txt = f"Write({device}) = {value}"
        log.debug(txt)
        if not device:
            continue
        # do any logic here to update your devices


# --------------------------------------------------------------------------- #
# initialize your device map
# --------------------------------------------------------------------------- #


def read_device_map(path):
    """Read the device path to address mapping from file::

       0x0001,/dev/device1
       0x0002,/dev/device2

    :param path: The path to the input file
    :returns: The input mapping file
    """
    devices = {}
    with open(path, "r") as stream:  # pylint: disable=unspecified-encoding
        for line in stream:
            piece = line.strip().split(",")
            devices[int(piece[0], 16)] = piece[1]
    return devices


def run_callback_server():
    """Run callback server."""
    # ----------------------------------------------------------------------- #
    # initialize your data store
    # ----------------------------------------------------------------------- #
    queue = Queue()
    devices = read_device_map("device-mapping")
    block = CallbackDataBlock(devices, queue)
    store = ModbusSlaveContext(di=block, co=block, hr=block, ir=block)
    context = ModbusServerContext(slaves=store, single=True)

    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #
    identity = ModbusDeviceIdentification(
        info_name={
            "VendorName": "pymodbus",
            "ProductCode": "PM",
            "VendorUrl": "https://github.com/pymodbus-dev/pymodbus/",
            "ProductName": "pymodbus Server",
            "ModelName": "pymodbus Server",
            "MajorMinorRevision": version.short(),
        }
    )

    # ----------------------------------------------------------------------- #
    # run the server you want
    # ----------------------------------------------------------------------- #
    thread = Thread(target=device_writer, args=(queue,))
    thread.start()
    StartTcpServer(context, identity=identity, address=("localhost", 5020))


if __name__ == "__main__":
    run_callback_server()
