pymodbus\.client
================

Pymodbus offers clients with different transport protocols in 2 versions:

- synchronous,
- asynchronous (based on asyncio).

Using pymodbus client to set/get information from a device (server)
is done in a few simple steps, like the following synchronous example::

    # create client object
    client = ModbusSerial("/dev/tty")

    # connect to device
    client.connect()

    # set/set information
    rr = client.read_coils(0x01)
    client.write_coil(0x01, values)

    # disconnect device
    client.close()

or asynchronous example::

    # create client object
    async_client = AsyncModbusSerial("/dev/tty")

    # connect to device
    await async_client.connect()

    # set/set information
    rr = await async_client.read_coils(0x01)
    await async_client.write_coil(0x01, values)

    # disconnect device
    await async_client.close()


.. toctree::

    pymodbus.client.setup

.. toctree::

    pymodbus.client.calls
