==================================================
Asynchronous Client Example
==================================================

The asynchronous client functions in the same way as the synchronous
client, however, the asynchronous client uses twisted to return deferreds
for the response result. Just like the synchronous version, it works against
TCP, UDP, serial ASCII, and serial RTU devices.

Below an asynchronous tcp client is demonstrated running against a
reference server. If you do not have a device to test with, feel free
to run a pymodbus server instance or start the reference tester in
the tools directory.

.. literalinclude:: ../../../examples/common/asynchronous-client.py

