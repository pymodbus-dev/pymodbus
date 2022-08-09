pymodbus\.client
================

Pymodbus offers clients with different transport protocols in 2 versions:

- synchronous,
- asynchronous (based on asyncio).

Using a client to set/get information from a device (server) is simple as seen in this
example (more details in below)::

    # create client object
    client = ModbusSerial("/dev/tty")

    # connect to device
    client.start()

    # set/set information
    client.read_coils(0x01)
    client.write_coil(0x01, values)
    ...

    # disconnect device
    client.stop()

.. toctree::

    pymodbus.client.setup

.. toctree::

    pymodbus.client.calls
