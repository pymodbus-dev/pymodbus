==================================================
TK Frontend Example
==================================================

Main Program
--------------------------------------------------

This is an example simulator that is written using the native tk
toolkit.  Although it currently does not have a frontend for
modifying the context values, it does allow one to expose N
virtual modbus devices to a network which is useful for testing
data center monitoring tools.

.. note:: The virtual networking code will only work on linux

.. literalinclude:: ../../../examples/gui/tk/simulator.py

