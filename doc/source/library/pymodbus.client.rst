pymodbus\.client
================

Pymodbus offers a :mod:`synchronous client <pymodbus.client>` and a :mod:`client based on asyncio <pymodbus.client.asynchronous>`.

In general each transports (Serial, TCP, TLS and UDP) have its own class.
However the actual implementation is highly shared.

AsyncModbusSerialClient class
-----------------------------

.. automodule:: pymodbus.client.async_serial
    :members:

ModbusSerialClient class
------------------------

.. automodule:: pymodbus.client.sync_serial
    :members:

AsyncModbusTcpClient class
--------------------------

.. automodule:: pymodbus.client.async_tcp
    :members:

ModbusTcpClient class
---------------------

.. automodule:: pymodbus.client.sync_tcp
    :members:

AsyncModbusTlsClient class
--------------------------

.. automodule:: pymodbus.client.async_tls
    :members:

ModbusTlsClient class
---------------------

.. automodule:: pymodbus.client.sync_tls
    :members:

AsyncModbusUdpClient class
--------------------------

.. automodule:: pymodbus.client.async_udp
    :members:

ModbusUdpClient class
---------------------

.. automodule:: pymodbus.client.sync_udp
    :members:
