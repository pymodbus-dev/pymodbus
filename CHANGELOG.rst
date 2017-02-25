Version 1.2.0
------------------------------------------------------------

* Added ability to ignore missing slaves
* Added ability to revert to ZeroMode
* Passed a number of extra options through the stack
* Fixed documenation and added a number of examples

Version 1.2.0
------------------------------------------------------------

* Reworking the transaction managers to be more explicit and
  to handle modbus RTU over TCP.
* Adding examples for a number of unique requested use cases
* Allow RTU framers to fail fast instead of staying at fault
* Working on datastore saving and loading

Version 1.1.0
------------------------------------------------------------

* Fixing memory leak in clients and servers (removed __del__)
* Adding the ability to override the client framers
* Working on web page api and GUI
* Moving examples and extra code to contrib sections
* Adding more documentation

Version 1.0.0
------------------------------------------------------------

* Adding support for payload builders to form complex encoding
  and decoding of messages.
* Adding BCD and binary payload builders
* Adding support for pydev
* Cleaning up the build tools
* Adding a message encoding generator for testing.
* Now passing kwargs to base of PDU so arguments can be used
  correctly at all levels of the protocol.
* A number of bug fixes (see bug tracker and commit messages)

Version 0.9.0
------------------------------------------------------------

Please view the git commit log
