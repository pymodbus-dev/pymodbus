==================================================
Glade/GTK Frontend Example
==================================================

Main Program
--------------------------------------------------

This is an example simulator that is written using the pygtk
bindings.  Although it currently does not have a frontend for
modifying the context values, it does allow one to expose N
virtual modbus devices to a network which is useful for testing
data center monitoring tools.

.. note:: The virtual networking code will only work on linux

.. literalinclude:: ../../../examples/gui/gtk/simulator.py
   :language: python

Glade Layout File
--------------------------------------------------

The following is the glade layout file that is used by this script:

.. literalinclude:: ../../../examples/gui/gtk/simulator.glade
   :language: xml

