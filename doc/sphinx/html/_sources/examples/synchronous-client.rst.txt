==================================================
Synchronous Client Example
==================================================

It should be noted that each request will block waiting for the result. If asynchronous
behaviour is required, please use the asynchronous client implementations.
The synchronous client, works against TCP, UDP, serial ASCII, and serial RTU devices.

The synchronous client exposes the most popular methods of the modbus protocol,
however, if you want to execute other methods against the device,
simple create a request instance and pass it to the execute method.

Below an synchronous tcp client is demonstrated running against a
reference server. If you do not have a device to test with, feel free
to run a pymodbus server instance or start the reference tester in
the tools directory.

.. literalinclude:: ../../../examples/common/synchronous-client.py

