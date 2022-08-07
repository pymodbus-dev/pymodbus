pymodbus\.client
================

Pymodbus offers

a :mod:`synchronous client <pymodbus.client>` and

a :mod:`client based on asyncio <pymodbus.client.asynchronous>`.

Using a client to set/get information from a device (server) is simple as seen in this
example (more details in the chapters below)::

    # create client object
    client = ModbusSerial("/dev/tty")

    # connect to device
    client.start()

    # set/get information
    client.read_coils(0x01)
    ...

    # disconnect device
    client.stop()

The documentation is in 2 parts:

- connect/disconnect to device(s) with different transport protocols.
- set/get information independent of the chosen transport protocol.

.. toctree::

    pymodbus.client.setup

.. toctree::

    pymodbus.client.calls
