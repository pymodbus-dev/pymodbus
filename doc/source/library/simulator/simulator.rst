Simulator
=========

The simulator is a full fledged modbus simulator, which is
constantly being evolved with user ideas / amendments.

The purpose of the simulator is to provide support for client
application test harnesses with end-to-end testing simulating real life
modbus devices.

The datastore simulator allows the user to (all automated)

- simulate a modbus device by adding a simple configuration,
- test how a client handles modbus exceptions,
- test a client apps correct use of the simulated device.

The web interface allows the user to (online / manual)

- test how a client handles modbus errors,
- test how a client handles communication errors like divided messages,
- run your test server in the cloud,
- monitor requests/responses,
- inject modbus errors like malicious a response,
- see/Change values online.

The REST API allow the test process to be automated

- spin up a test server with unix domain sockets in your test harness,
- set expected responses with a simple REST API command,
- check the result with another simple REST API command,
- test your client app in a true end-to-end fashion.

The simulator replaces :ref:`REPL server classes`
but not :ref:`REPL client classes`

.. toctree::
   :maxdepth: 4
   :hidden:

   config
   datastore
   web
   restapi
