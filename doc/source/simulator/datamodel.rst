Data model configuration
------------------------
The simulator data model represent the registers and parameters of the simulated devices.
The data model is defined using :class:`SimData` and :class:`SimDevice` before starting the
server and cannot be changed without restarting the server.

:class:`SimData` defines a group of continuous identical registers. This is the basis of the model,
multiple :class:`SimData` are used to mirror the physical device.

:class:`SimDevice` defines device parameters and a list of :class:`SimData`. The
list of :class:`SimData` can be added as shared registers or as 4 separate blocks as defined in modbus.
:class:`SimDevice` are used to simulate a single device, while a list of
:class:`SimDevice` simulates a multipoint line (rs485 line) or a serial forwarder.

A server consist of communication parameters and a list of :class:`SimDevice`


Usage examples
^^^^^^^^^^^^^^
.. literalinclude:: ../../../examples/server_datamodel.py
    :language: python


Class definitions
^^^^^^^^^^^^^^^^^
.. autoclass:: pymodbus.constants.DataType
    :members:
    :undoc-members:
    :member-order: bysource

.. autoclass:: pymodbus.simulator.SimData
    :members:
    :undoc-members:
    :show-inheritance:
    :member-order: bysource

.. autoclass:: pymodbus.simulator.SimDevice
    :members:
    :undoc-members:
    :show-inheritance:
    :member-order: bysource


Action data class examples
^^^^^^^^^^^^^^^^^^^^^^^^^^


.. autoclass:: pymodbus.simulator.SimDataMinMax
    :members:
    :undoc-members:
    :show-inheritance:
    :member-order: bysource

.. autoclass:: pymodbus.simulator.SimDataIncrement
    :members:
    :undoc-members:
    :show-inheritance:
    :member-order: bysource
