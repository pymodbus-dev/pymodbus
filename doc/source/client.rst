Client
======
Pymodbus offers both a :mod:`synchronous client` and a :mod:`asynchronous client`.
Both clients offer simple calls for each type of request, as well as a unified response, removing
a lot of the complexities in the modbus protocol.

In addition to the "pure" client, pymodbus offers a set of utilities converting to/from registers to/from "normal" python values.

The client is NOT thread safe, meaning the application must ensure that calls are serialized.
This is only a problem for synchronous applications that use multiple threads or for asynchronous applications
that use multiple :mod:`asyncio.create_task`.

It is allowed to have multiple client objects that e.g. each communicate with a TCP based device.


Client performance
------------------
There are currently a big performance gab between the 2 clients
(try it on your computer :github:`examples/client_performance.py`).
This is due to a rather old implementation of the synchronous client, we are currently working to update the client code.
Our aim is to achieve a similar data rate with both clients and at least double the data rate while keeping the stability.
Table below is a test with 1000 calls each reading 10 registers.

.. list-table::
   :header-rows: 1

   * - **client**
     - **asynchronous**
     - **synchronous**
   * - total time
     - 0,33 sec
     - 114,10 sec
   * - ms/call
     - 0,33 ms
     - 114,10 ms
   * - ms/register
     - 0,03 ms
     - 11,41 ms
   * - calls/sec
     - 3.030
     - 8
   * - registers/sec
     - 30.300
     - 87


Client protocols/framers
------------------------
Pymodbus offers clients with transport different protocols and different framers

.. list-table::
   :header-rows: 1

   * - **protocol**
     - ASCII
     - RTU
     - RTU_OVER_TCP
     - Socket
     - TLS
   * - Serial (RS-485)
     - Yes
     - Yes
     - No
     - No
     - No
   * - TCP
     - Yes
     - No
     - Yes
     - Yes
     - No
   * - TLS
     - No
     - No
     - No
     - No
     - Yes
   * - UDP
     - Yes
     - No
     - Yes
     - Yes
     - No


Serial (RS-485)
^^^^^^^^^^^^^^^
Pymodbus do not connect to the device (server) but connects to a comm port or usb port on the local computer.

RS-485 is a half duplex protocol, meaning the servers do nothing until the client sends a request then the server
being addressed responds. The client controls the traffic and as a consequence one RS-485 line can only have 1 client
but upto 254 servers (physical devices).

RS-485 is a simple 2 wire cabling with a pullup resistor. It is important to note that many USB converters do not have a
builtin resistor, this must be added manually. When experiencing many faulty packets and retries this is often the problem.


TCP
^^^
Pymodbus connects directly to the device using a standard socket and have a one-to-one connection with the device.
In case of multiple TCP devices the application must instantiate multiple client objects one for each connection.

.. tip:: a TCP device often represent multiple physical devices (e.g Ethernet-RS485 converter), each of these devices
    can be addressed normally


TLS
^^^
A variant of **TCP** that uses encryption and certificates. **TLS** is mostly used when the devices are connected to the internet.


UDP
^^^
A broadcast variant of **TCP**. **UDP** allows addressing of many devices with a single request, however there are no control
that a device have received the packet.


Client usage
------------
Using pymodbus client to set/get information from a device (server)
is done in a few simple steps, like the following synchronous example::

    from pymodbus.client import ModbusTcpClient

    client = ModbusTcpClient('MyDevice.lan')   # Create client object
    client.connect()                           # connect to device, reconnect automatically
    client.write_coil(1, True, slave=1)        # set information in device
    result = client.read_coils(2, 3, slave=1)  # get information from device
    print(result.bits[0])                      # use information
    client.close()                             # Disconnect device


and a asynchronous example::

    from pymodbus.client import ModbusAsyncTcpClient

    client = ModbusAsyncTcpClient('MyDevice.lan')    # Create client object
    await client.connect()                           # connect to device, reconnect automatically
    await client.write_coil(1, True, slave=1)        # set information in device
    result = await client.read_coils(2, 3, slave=1)  # get information from device
    print(result.bits[0])                            # use information
    client.close()                                   # Disconnect device

The line :mod:`client = ModbusAsyncTcpClient('MyDevice.lan')` only creates the object it does not activate
anything.

The line :mod:`await client.connect()` connects to the device (or comm port), if this cannot connect successfully within
the timeout it throws an exception. If connected successfully reconnecting later is handled automatically

The line :mod:`await client.write_coil(1, True, slave=1)` is an example of a write request, set address 1 to True on device 1 (slave).

The line :mod:`result = await client.read_coils(2, 3, slave=1)` is an example of a read request, get the value of address 2, 3 and 4 (count = 3) from device 1 (slave).

The last line :mod:`client.close()` closes the connection and render the object inactive.

Large parts of the implementation are shared between the different classes,
to ensure high stability and efficient maintenance.

The synchronous clients are not thread safe nor is a single client intended
to be used from multiple threads. Due to the nature of the modbus protocol,
it makes little sense to have client calls split over different threads,
however the application can do it with proper locking implemented.

The asynchronous client only runs in the thread where the asyncio loop is created,
it does not provide mechanisms to prevent (semi)parallel calls,
that must be prevented at application level.


Client device addressing
------------------------

With **TCP**, **TLS** and **UDP**, the tcp/ip address of the physical device is defined when creating the object.
The logical devices represented by the device is addressed with the :mod:`slave=` parameter.

With **Serial**, the comm port is defined when creating the object.
The physical devices are addressed with the :mod:`slave=` parameter.

:mod:`slave=0` is used as broadcast in order to address all devices.
However experience shows that modern devices do not allow broadcast, mostly because it is
inheriently dangerous. With :mod:`slave=0` the application can get upto 254 responses on a single request!

The simple request calls (mixin) do NOT support broadcast, if an application wants to use broadcast
it must call :mod:`client.execute` and deal with the responses.



Client response handling
------------------------

All simple request calls (mixin) return a unified result independent whether it´s a read, write or diagnostic call.

The application should evaluate the result generically::

    try:
        rr = await client.read_coils(1, 1, slave=1)
    except ModbusException as exc:
        _logger.error(f"ERROR: exception in pymodbus {exc}")
        raise exc
    if rr.isError():
        _logger.error("ERROR: pymodbus returned an error!")
        raise ModbusException(txt)

:mod:`except ModbusException as exc:` happens generally when pymodbus experiences an internal error.
There are a few situation where a unexpected response from a device can cause an exception.

:mod:`rr.isError()` is set whenever the device reports a problem.

And in case of read retrieve the data depending on type of request

- :mod:`rr.bits` is set for coils / input_register requests
- :mod:`rr.registers` is set for other requests


Client interface classes
------------------------

There are a client class for each type of communication and for asynchronous/synchronous

.. list-table::

   * - **Serial**
     - :mod:`AsyncModbusSerialClient`
     - :mod:`ModbusSerialClient`
   * - **TCP**
     - :mod:`AsyncModbusTcpClient`
     - :mod:`ModbusTcpClient`
   * - **TLS**
     - :mod:`AsyncModbusTlsClient`
     - :mod:`ModbusTlsClient`
   * - **UDP**
     - :mod:`AsyncModbusUdpClient`
     - :mod:`ModbusUdpClient`

Client serial
^^^^^^^^^^^^^
.. autoclass:: pymodbus.client.AsyncModbusSerialClient
    :members:
    :member-order: bysource
    :show-inheritance:

.. autoclass:: pymodbus.client.ModbusSerialClient
    :members:
    :member-order: bysource
    :show-inheritance:

Client TCP
^^^^^^^^^^
.. autoclass:: pymodbus.client.AsyncModbusTcpClient
    :members:
    :member-order: bysource
    :show-inheritance:

.. autoclass:: pymodbus.client.ModbusTcpClient
    :members:
    :member-order: bysource
    :show-inheritance:

Client TLS
^^^^^^^^^^
.. autoclass:: pymodbus.client.AsyncModbusTlsClient
    :members:
    :member-order: bysource
    :show-inheritance:

.. autoclass:: pymodbus.client.ModbusTlsClient
    :members:
    :member-order: bysource
    :show-inheritance:

Client UDP
^^^^^^^^^^
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
