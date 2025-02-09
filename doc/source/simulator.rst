Simulator
=========

**WORK IN PROGRESS, do NOT use**

The simulator is a full fledged modbus server/simulator.

The purpose of the simulator is to provide support for client
application test harnesses with end-to-end testing simulating real life
modbus devices.

The simulator allows the user to (all automated):

- simulate a modbus device by adding a simple configuration,
- simulate a multipoint line, but adding multiple device configurations,
- simulate devices that are not conforming to the protocol,
- simulate communication problems (data loss etc),
- test how a client handles modbus response and exceptions,
- test a client apps correct use of the simulated device.

The web interface (activated optionally) allows the user to:

- introduce modbus errors (like e.g. wrong length),
- introduce communication errors (like splitting a message),
- monitor requests/responses,
- see/Change values online.
- inject modbus errors like malicious a response,
- run your test server in the cloud,

The REST API allow the test process to be automated

- spin up a test server in your test harness,
- set expected responses with a simple REST API command,
- check the result with a simple REST API command,
- test your client app in a true end-to-end fashion.

The web server uses the REST API internally, which helps to ensure that it
actually works.


Data model configuration
------------------------

.. warning:: from v3.9.0 this is available as a "normal" datastore model.

The simulator data model represent the registers and parameters of the simulated devices.
The data model is defined using :class:`SimData` and :class:`SimDevice` before starting the
server and cannot be changed without restarting the server.

:class:`SimData` defines a group of continuous identical registers. This is the basis of the model,
multiple :class:`SimData` should be used to mirror the physical device.

:class:`SimDevice` defines device parameters and a list of :class:`SimData`.
The list of :class:`SimData` can added as shared registers or as the 4 blocks, defined in modbus.
:class:`SimDevice` can be used to simulate a single device, while a list of
:class:`SimDevice` simulates a multipoint line (simulating a rs485 line or a tcp based serial forwarder).

A server consist of communication parameters and a device or a list of devices

:class:`SimDataType` is a helper class that defines legal datatypes.

:class:`SimActions` is a helper class that defines built in actions.

:github:`examples/simulator_datamodel.py` contains usage examples.

SimData
^^^^^^^

.. autoclass:: pymodbus.simulator.SimData
    :members:
    :undoc-members:
    :show-inheritance:

SimDevice
^^^^^^^^^

.. autoclass:: pymodbus.simulator.SimDevice
    :members:
    :undoc-members:
    :show-inheritance:

SimDataType
^^^^^^^^^^^

.. autoclass:: pymodbus.simulator.SimDataType
    :members:
    :undoc-members:
    :show-inheritance:


Simulator server
----------------

.. note:: This is a v4.0.0 functionality currently not available, please see the 3x simulator server.


Web frontend
------------

.. note:: This is a v4.0.0 functionality currently not available, please see the 3x simulator server.


REST API
--------

.. note:: This is a v4.0.0 functionality currently not available, please see the 3x simulator server.
