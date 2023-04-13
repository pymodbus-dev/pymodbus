Client
======

Pymodbus offers clients with transport protocols for

- *Serial* (RS-485) typically using a dongle
- *TCP*
- *TLS*
- *UDP*

communication can be either using a :mod:`synchronous client` or a :mod:`asynchronous client` using asyncio.

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

The synchronous clients are not thread safe nor is a single client intended to be used from multiple threads.
Due to the nature of the modbus protocol, it makes little sense to have client calls split over different threads,
however the application can do it with proper locking implemented.

The asynchronous client only runs in the thread where the asyncio loop is created, it does not provide mechanisms to
prevent (semi)parallel calls, that must be prevented at application level.

Transport classes
-----------------

.. autoclass:: pymodbus.client.ModbusBaseClient
    :members:
    :member-order: bysource
    :show-inheritance:

.. autoclass:: pymodbus.client.AsyncModbusSerialClient
    :members:
    :member-order: bysource
    :show-inheritance:

.. autoclass:: pymodbus.client.ModbusSerialClient
    :members:
    :member-order: bysource
    :show-inheritance:

.. autoclass:: pymodbus.client.AsyncModbusTcpClient
    :members:
    :member-order: bysource
    :show-inheritance:

.. autoclass:: pymodbus.client.ModbusTcpClient
    :members:
    :member-order: bysource
    :show-inheritance:

.. autoclass:: pymodbus.client.AsyncModbusTlsClient
    :members:
    :member-order: bysource
    :show-inheritance:

.. autoclass:: pymodbus.client.ModbusTlsClient
    :members:
    :member-order: bysource
    :show-inheritance:

.. autoclass:: pymodbus.client.AsyncModbusUdpClient
    :members:
    :member-order: bysource
    :show-inheritance:

.. autoclass:: pymodbus.client.ModbusUdpClient
    :members:
    :member-order: bysource
    :show-inheritance:


Modbus calls
------------

Pymodbus makes all standard modbus requests/responses available as simple calls.

Using Modbus<transport>Client.register() custom messagees can be added to pymodbus,
and handled automatically.

.. autoclass:: pymodbus.client.mixin.ModbusClientMixin
    :members:
    :member-order: bysource
    :show-inheritance:
