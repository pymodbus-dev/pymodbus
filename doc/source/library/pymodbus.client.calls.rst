Device calls
============

Pymodbus makes a all standard modbus requests/responses available as simple calls.

All calls are available as synchronous and asynchronous (asyncio based).

Using Modbus<transport>Client.register() custom messagees can be added to pymodbus,
and handled automatically.

.. autoclass:: pymodbus.client.mixin.ModbusClientMixin
    :members:
