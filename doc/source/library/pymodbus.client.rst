================
pymodbus\.client
================

Pymodbus offers clients with transport protocols for

- *Serial* (RS-485) typically using a dongle
- *TCP*
- *TLS*
- *UDP*
- possibility to add a custom transport protocol

communication in 2 versions:

- :mod:`synchronous client`,
- :mod:`asynchronous client` using asyncio.

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

and a asynchronous example::

    # create client object
    async_client = AsyncModbusSerial("/dev/tty")

    # connect to device
    await async_client.connect()

    # set/set information
    rr = await async_client.read_coils(0x01)
    await async_client.write_coil(0x01, values)

    # disconnect device
    await async_client.close()

Large parts of the implementation are shared between the different classes,
to ensure high stability and efficient maintenance.

Client setup.
-------------

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

Pymodbus makes all standard modbus requests/responses available as simple calls.

Using Modbus<transport>Client.register() custom messagees can be added to pymodbus,
and handled automatically.

.. autoclass:: pymodbus.client.mixin.ModbusClientMixin
    :members:
