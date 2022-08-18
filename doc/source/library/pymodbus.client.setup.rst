Client setup.
=============

Pymodbus offers different transport protocols Serial/TCP/TLS/UDP,
which are implemented as separate classes.
Each class defines exactly on transport type.

Applications can add custom transport types as long as the new class inherits
from class ModbusBaseClient.

Applications can also use customer framers.

All transport types are supplied in 2 versions:

a :mod:`synchronous client <pymodbus.client>` and

a :mod:`asynchronous client based on asyncio <pymodbus.client.asynchronous>`.

Large parts of the actual implementation are shared between the different classes,
to ensure a higher stability and more efficient maintenance.

Common parameters/methods for all clients.
------------------------------------------

.. autoclass:: pymodbus.client.base.ModbusBaseClient
    :members:
    :member-order: bysource

Serial RS-485 transport.
------------------------

.. automodule:: pymodbus.client.async_serial
    :members:

.. automodule:: pymodbus.client.sync_serial
    :members:

TCP transport.
--------------

.. automodule:: pymodbus.client.async_tcp
    :members:

.. automodule:: pymodbus.client.sync_tcp
    :members:

TLS transport.
--------------

.. automodule:: pymodbus.client.async_tls
    :members:

.. automodule:: pymodbus.client.sync_tls
    :members:

UDP transport.
--------------

.. automodule:: pymodbus.client.async_udp
    :members:

.. automodule:: pymodbus.client.sync_udp
    :members:
