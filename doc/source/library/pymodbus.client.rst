================
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

Pymodbus offers Serial/TCP/TLS/UDP as transport protocols, with the option to add
custom protocols. Each transport protocol is implemented as
a :mod:`synchronous client` and a :mod:`asynchronous client`

Large parts of the actual implementation are shared between the different classes,
to ensure a higher stability and more efficient maintenance.

Client setup.
-------------

Common parameters/methods.
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pymodbus.client.base.ModbusBaseClient
    :members:
    :member-order: bysource

Serial RS-485 transport.
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pymodbus.client.async_serial.AsyncModbusSerialClient

.. autoclass:: pymodbus.client.sync_serial.ModbusSerialClient

TCP transport.
~~~~~~~~~~~~~~

.. autoclass:: pymodbus.client.async_tcp.AsyncModbusTcpClient

.. autoclass:: pymodbus.client.sync_tcp.ModbusTcpClient

TLS transport.
~~~~~~~~~~~~~~

.. autoclass:: pymodbus.client.async_tls.AsyncModbusTlsClient

.. autoclass:: pymodbus.client.sync_tls.ModbusTlsClient

UDP transport.
~~~~~~~~~~~~~~

.. autoclass:: pymodbus.client.async_udp.AsyncModbusUdpClient
    :members:

.. autoclass:: pymodbus.client.sync_udp.ModbusUdpClient
    :members:


Client device calls.
--------------------

Pymodbus makes a all standard modbus requests/responses available as simple calls.

All calls are available as synchronous and asynchronous (asyncio based).

Using Modbus<transport>Client.register() custom messagees can be added to pymodbus,
and handled automatically.

.. autoclass:: pymodbus.client.mixin.ModbusClientMixin
    :members:
