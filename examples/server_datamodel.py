#!/usr/bin/env python3
"""Pymodbus server datamodel examples.

This file shows examples of how to configure the datamodel for the server/simulator.

There are different examples showing the flexibility of the datamodel.
"""

from pymodbus.constants import DataType
from pymodbus.simulator import SimData, SimDevice


def define_datamodel():
    """Define register groups.

    Coils and discrete inputs are modeled as bits representing a relay in the device.
    There are no real difference between coils and discrete inputs, but historically
    they have been divided. Please be aware the coils and discrete inputs are addressed differently
    in shared vs non-shared models.
    - In a non-shared model the address is the bit directly.
      It can be thought of as if 1 register == 1 bit.
    - In a shared model the address is the register containing the bits.
      1 register == 16bit, so a single bit CANNOT be addressed directly.

    Holding registers and input registers are modeled as int/float/string representing a sensor in the device.
    There are no real difference between holding registers and input registers, but historically they have
    been divided.
    Please be aware that 1 sensor might be modeled as several register because it needs more than
    16 bit for accuracy (e.g. a INT32).
    """
    # SimData can be instantiated with positional or optional parameters:
    assert SimData(
            5, 10, 17, DataType.REGISTERS
        ) == SimData(
            address=5, values=17, count=10, datatype=DataType.REGISTERS
        )

    # Define a group of coils/discrete inputs non-shared (address=15..31 each 1 bit)
    #block1 = SimData(address=15, count=16, values=True, datatype=DataType.BITS)
    # Define a group of coils/discrete inputs shared (address=15..31 each 16 bit)
    #block2 = SimData(address=15, count=16, values=0xFFFF, datatype=DataType.BITS)

    # Define a group of holding/input registers (remark NO difference between shared and non-shared)
    #block3 = SimData(10, 1, 123.4, datatype=DataType.FLOAT32)
    #block4 = SimData(17, count=5, values=123, datatype=DataType.INT64)
    block5 = SimData(27, 1, "Hello ", datatype=DataType.STRING)

    block_def = SimData(0, count=1000, datatype=DataType.REGISTERS, default=True)

    # SimDevice can be instantiated with positional or optional parameters:
    assert SimDevice(
            5,
            [block_def, block5],
        ) == SimDevice(
            id=5, type_check=False, registers=[block_def, block5]
        )

    # SimDevice can define either a shared or a non-shared register model
    SimDevice(id=1, type_check=False, registers=[block_def, block5])
    #SimDevice(2, False,
    #          block_coil=[block1],
    #          block_discrete=[block1],
    #          block_holding=[block2],
    #          block_input=[block3, block4])
    # Remark: it is legal to reuse SimData, the object is only used for configuration,
    # not for runtime.

    # id=0 in a SimDevice act as a "catch all". Requests to an unknown id is executed in this SimDevice.
    #SimDevice(0, block_shared=[block2])


def main():
    """Combine setup and run."""
    define_datamodel()

if __name__ == "__main__":
    main()
