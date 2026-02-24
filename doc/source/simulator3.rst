Simulator (3.x)
===============

.. warning:: Beginning with v3.9.0 and ending with v4.0.0 this simulator will be removed by a new version.

**REMARK**: A simulator is a standard server with an additional http interface.

The core logic of the simulator (SimDevice/SimData) is fully integrated into the server to provide a more flexible data definition.

The purpose of the simulator is to:
- Provide a flexible data definition for both standard servers and simulation environments.
- Allow users to test how a client handles modbus exceptions.
- Allow users to test a client app's correct use of the simulated device.

The datamodel allows the user to:

- Define a modbus device using the ``SimDevice`` architecture.
- Handle data using ``SimData`` with specific ``DataType`` (Registers, Coils, etc.).

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

.. toctree::
   :maxdepth: 4
   :hidden:

   library/simulator/config
   library/simulator/datastore
   library/simulator/web
   library/simulator/restapi
