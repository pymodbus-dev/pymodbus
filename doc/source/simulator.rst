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

For details please see:

- :ref:`Data model configuration`
- :ref:`Simulator server`

The web interface (activated optionally) allows the user to:

- introduce modbus errors (like e.g. wrong length),
- introduce communication errors (like splitting a message),
- monitor requests/responses,
- see/Change values online.
- inject modbus errors like malicious a response,
- run your test server in the cloud,

For details please see:

- :ref:`Web frontend`


The REST API allow the test process to be automated

- spin up a test server in your test harness,
- set expected responses with a simple REST API command,
- check the result with a simple REST API command,
- test your client app in a true end-to-end fashion.

The web server uses the REST API internally, which helps to ensure that it
actually works.

For details please see:

- :ref:`REST API`
