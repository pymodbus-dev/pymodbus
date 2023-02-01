Server
======

Pymodbus offers servers with transport protocols for

- *Serial* (RS-485) typically using a dongle
- *TCP*
- *TLS*
- *UDP*
- possibility to add a custom transport protocol

communication in 2 versions:

- :mod:`synchronous server`,
- :mod:`asynchronous server` using asyncio.

*Remark* All servers are implemented with asyncio, and the
synchronous servers are just an interface layer allowing synchronous
applications to use the server as if it was synchronous.


.. automodule:: pymodbus.server
    :members:
    :undoc-members:
    :show-inheritance:
