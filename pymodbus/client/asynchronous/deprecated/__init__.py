import warnings
warnings.simplefilter('always', DeprecationWarning)

WARNING = """
Usage of '{}' is deprecated from 2.0.0 and will be removed in future releases.
Use the new Async Modbus Client implementation based on Twisted, tornado 
and asyncio
------------------------------------------------------------------------

Example run::

    from pymodbus.client.asynchronous import schedulers

    # Import The clients

    from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient as Client
    from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient as Client
    from pymodbus.client.asynchronous.udp import AsyncModbusUDPClient as Client

    # For tornado based asynchronous client use
    event_loop, future = Client(schedulers.IO_LOOP, port=5020)

    # For twisted based asynchronous client use
    event_loop, deferred = Client(schedulers.REACTOR, port=5020)

    # For asyncio based asynchronous client use
    event_loop, client = Client(schedulers.ASYNC_IO, port=5020)

    # Here event_loop is a thread which would control the backend and future is
    # a Future/deffered object which would be used to
    # add call backs to run asynchronously.

    # The Actual client could be accessed with future.result() with Tornado
    # and future.result when using twisted

    # For asyncio the actual client is returned and event loop is asyncio loop

Refer:
https://pymodbus.readthedocs.io/en/dev/source/example/async_twisted_client.html
https://pymodbus.readthedocs.io/en/dev/source/example/async_tornado_client.html
https://pymodbus.readthedocs.io/en/dev/source/example/async_asyncio_client.html

"""


def deprecated(name):  # pragma: no cover
    warnings.warn(WARNING.format(name), DeprecationWarning)
