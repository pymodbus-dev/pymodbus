#!/usr/bin/env python3
"""Pymodbus simulator datamodel examples.

This example shows how to configure the simulator datamodel to mimic a real
device.

There are different examples, to show the flexibility of the simulator datamodel.

.. tip:: This is NOT the pymodbus simulator, that is started as pymodbus.simulator.
"""

from pymodbus.simulator import SimCheckConfig, SimData, SimDataType, SimDevice


def define_registers():
    """Define simulator data model.

    Coils and direct inputs are expressed as bits representing a relay in the device.
    There are no real difference between coils and direct inputs, but historically
    they have been divided.

    Holding registers and input registers are the same, but historically they have
    been divided.

    Coils and direct inputs are handled differently in shared vs non-shared models.

    - In a non-shared model the address is the bit directly. It can be thought of as if a
    register only contains 1 bit.
    - In a shared model the address is the register containing the bits. So a single bit CANNOT
    be addressed directly.
    """
    # Define a group of coils (remark difference between shared and non-shared)
    block_coil = [SimData(0, count=100, datatype=SimDataType.DEFAULT),
                  SimData(0, True, 16)]
    block_coil_shared = [SimData(0, 0xFFFF, 16)]

    # SimData can be reused with copying
    block_direct = block_coil

    # Define a group of registers (remark NO difference between shared and non-shared)
    block_holding = [SimData(10, count=100, datatype=SimDataType.DEFAULT),
                    SimData(10, 123.4, datatype=SimDataType.FLOAT32),
                    SimData(12, 123456789.3, datatype=SimDataType.FLOAT64),
                    SimData(17, value=123, count=5, datatype=SimDataType.INT32),
                    SimData(27, "Hello ", datatype=SimDataType.STRING)]
    block_input = block_holding
    block_shared = [SimData(10, 123.4, datatype=SimDataType.FLOAT32),
                    SimData(12, 123456789.3, datatype=SimDataType.FLOAT64),
                    SimData(16, 0xf0f0, datatype=SimDataType.BITS),
                    SimData(17, value=123, count=5, datatype=SimDataType.INT32),
                    SimData(27, "Hello ", datatype=SimDataType.STRING)]

    device_block = SimDevice(1, False,
                            block_coil=block_coil,
                            block_direct=block_direct,
                            block_holding=block_holding,
                            block_input=block_input)
    device_shared = SimDevice(2, False,
                            block_shared=block_coil_shared+block_shared)
    assert not SimCheckConfig([device_block])
    assert not SimCheckConfig([device_shared])
    assert not SimCheckConfig([device_shared, device_block])

def main():
    """Combine setup and run."""
    define_registers()

if __name__ == "__main__":
    main()
