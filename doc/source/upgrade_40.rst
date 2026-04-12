Pymodbus 4.0 upgrade procedure
==============================

Pymodbus 4.0 contains a number of incompatibilities with Pymodbus 3.x, however
most of these are simple edits.

Convert to SimData/SimDevice
-----------------------------
The old datastores:

- ModbusSequentialDataBlock,
- ModbusSparseDataBlock,
- ModbusSimulatorContext

are due to be removed in v4.0.0, starting with v3.13.0 the internal
functionality are replaced by SimData/SimDevice.

However there is a simple path to upgrade:

ModbusSequentialDataBlock
^^^^^^^^^^^^^^^^^^^^^^^^^

This datastore makes sequential registers, corresponding to old style devices.

Example:
.. code-block::

    dev = ModbusDeviceContext(
                co=ModbusSequentialDataBlock(0x01, 15),
                di=ModbusSequentialDataBlock(0x01, [16]),
                hr=ModbusSequentialDataBlock(0x01, [17]),
                ir=ModbusSequentialDataBlock(0x01, [18])
    )
    server_context = ModbusServerContext(
                        devices={1: dev,
                                 0: dev
                                })
    await StartAsync**Server(context=server_context)

Device_id = 0 is at "catch-all", that handles all devices not defined.

This is very easily converted to SimData/SimDevice

.. code-block::

    from pymodbus.simulator import SimData, SimDevice, DataType

    devices = [SimDevice(1, simdata=(
                        SimData(0x01, values=15, datatype=DataType.REGISTERS),
                        SimData(0x01, values=[17], datatype=DataType.REGISTERS),
                        SimData(0x01, values=[17], datatype=DataType.REGISTERS),
                        SimData(0x01, values=[17], datatype=DataType.REGISTERS)
                    )
                ),
                SimDevice(1, simdata=(
                        SimData(0x01, values=15, datatype=DataType.REGISTERS),
                        SimData(0x01, values=[17], datatype=DataType.REGISTERS),
                        SimData(0x01, values=[17], datatype=DataType.REGISTERS),
                        SimData(0x01, values=[17], datatype=DataType.REGISTERS)
                    )
                )
    ]
    await StartAsync**Server(context=devices)


ModbusSparseDataBlock
^^^^^^^^^^^^^^^^^^^^^

This datastore makes registers, with missing registers.

Example:
.. code-block::

    dev = ModbusDeviceContext(
                co=ModbusSparseDataBlock([1, 2, 3]),
                di=ModbusSequentialDataBlock({
                    1: 6720,
                    30: 130
                }),
                hr=ModbusSparseDataBlock([4, 5, 6]),
                ir=ModbusSparseDataBlock([7, 8, 9])
    )
    server_context = ModbusServerContext(
                        devices={1: dev,
                                 0: dev
                                })
    await StartAsync**Server(context=server_context)

Device_id = 0 is at "catch-all", that handles all devices not defined.

This is very easily converted to SimData/SimDevice

.. code-block::

    from pymodbus.simulator import SimData, SimDevice, DataType

    devices = [SimDevice(1, simdata=(
                        SimData(1, values=[1,2,3], datatype=DataType.REGISTERS),
                        [SimData(1, values=6720, datatype=DataType.REGISTERS),
                         SimData(30, values=130, datatype=DataType.REGISTERS)
                        ],
                        SimData(0x01, values=[4,5,6], datatype=DataType.REGISTERS),
                        SimData(0x01, values=[7,8,9], datatype=DataType.REGISTERS)
                    )
                ),
                SimDevice(1, simdata=(
                        SimData(0x01, values=15, datatype=DataType.REGISTERS),
                        SimData(0x01, values=[17], datatype=DataType.REGISTERS),
                        SimData(0x01, values=[17], datatype=DataType.REGISTERS),
                        SimData(0x01, values=[17], datatype=DataType.REGISTERS)
                    )
                )
    ]
    await StartAsync**Server(context=devices)

ModbusSimulatorContext
^^^^^^^^^^^^^^^^^^^^^^

This datastore is a complicated setup with actions and typechecking.

There are no very simple conversion, the configuration is grouped by datatypes then address.

Basically convert each address set to a SimData with datatype= the type of the group.


**This will be amended, whenever there API changes are merged**