NullModem
=========

Pymodbus offers a special NullModem transport to help end-to-end test without network.

The NullModem is activated by setting host= (port= for serial) to NULLMODEM_HOST (import pymodbus.transport)

The NullModem works with the normal transport types, and simply substitutes the physical connection:
- *Serial* (RS-485) typically using a dongle
- *TCP*
- *TLS*
- *UDP*

The NullModem is currently integrated in
- :mod:`Modbus<x>Client`
- :mod:`AsyncModbus<x>Client`
- :mod:`Modbus<x>Server`
- :mod:`AsyncModbus<x>Server`

Of course the NullModem requires that server and client(s) run in the same python instance.
