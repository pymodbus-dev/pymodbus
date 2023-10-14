Client
======

Pymodbus offers clients with transport different protocols:

- *Serial* (RS-485) typically using a dongle
- *TCP*
- *TLS*
- *UDP*

The application can use either a :mod:`synchronous client` or a :mod:`asynchronous client`.

Using pymodbus client to set/get information from a device (server)
is done in a few simple steps, like the following synchronous example::

    from pymodbus.client import ModbusTcpClient

    client = ModbusTcpClient('MyDevice.lan')   # Create client object
    client.connect()                           # connect to device, reconnect automatically
    client.write_coil(1, True, slave=1)        # set information in device
    result = client.read_coils(1, 1, slave=1)  # get information from device
    print(result.bits[0])                      # use information
    client.close()                             # Disconnect device


and a asynchronous example::

    from pymodbus.client import ModbusAsyncTcpClient

    client = ModbusAsyncTcpClient('MyDevice.lan')    # Create client object
    await client.connect()                           # connect to device, reconnect automatically
    await client.write_coil(1, True, slave=1)        # set information in device
    result = await client.read_coils(1, 1, slave=1)  # get information from device
    print(result.bits[0])                            # use information
    client.close()                                   # Disconnect device

Large parts of the implementation are shared between the different classes,
to ensure high stability and efficient maintenance.

The synchronous clients are not thread safe nor is a single client intended
to be used from multiple threads. Due to the nature of the modbus protocol,
it makes little sense to have client calls split over different threads,
however the application can do it with proper locking implemented.

The asynchronous client only runs in the thread where the asyncio loop is created,
it does not provide mechanisms to prevent (semi)parallel calls,
that must be prevented at application level.

Client classes
--------------

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
