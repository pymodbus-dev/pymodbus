Version 1.4.0
------------------------------------------------------------
* Bug fix Modbus TCP client reading incomplete data
* Check for slave unit id before processing the request for serial clients
* Bug fix serial servers with Modbus Binary Framer
* Bug fix header size for ModbusBinaryFramer
* Support Database slave contexts (SqlStore and RedisStore)
* Custom handlers could be passed to Modbus TCP servers
* Asynchronous Server could now be stopped when running on a seperate thread (StopServer)
* Signal handlers on Asyncronous servers are now handled based on current thread
* Registers in Database datastore could now be read from remote clients
* Fix examples in contrib (message_parser.py/message_generator.py/remote_server_context)
* Add new example for SqlStore and RedisStore (db store slave context)
* Fix minor comaptibility issues with utilities.
* Update test requirements
* Update/Add new unit tests
* Move twisted requirements to extra so that it is not installed by default on pymodbus installtion

Version 1.3.2
------------------------------------------------------------
* ModbusSerialServer could now be stopped when running on a seperate thread.
* Fix issue with server and client where in the frame buffer had values from previous unsuccesful transaction
* Fix response length calculation for ModbusASCII protocol
* Fix response length calculation ReportSlaveIdResponse, DiagnosticStatusResponse
* Fix never ending transaction case when response is recieved without header and CRC
* Fix tests

Version 1.3.1
------------------------------------------------------------
* Recall socket recv until get a complete response
* Register_write_message.py: Observe skip_encode option when encoding a single register request
* Fix wrong expected response length for coils and discrete inputs
* Fix decode errors with ReadDeviceInformationRequest and  ReportSlaveIdRequest on Python3
* Move MaskWriteRegisterRequest/MaskWriteRegisterResponse  to register_write_message.py from file_message.py
* Python3 compatible examples [WIP]
* Misc updates with examples

Version 1.3.0.rc2
------------------------------------------------------------
* Fix encoding problem for ReadDeviceInformationRequest method on python3
* Fix problem with the usage of ord in python3 while cleaning up receive buffer
* Fix struct unpack errors with BinaryPayloadDecoder on python3 - string vs bytestring error
* Calculate expected response size for ReadWriteMultipleRegistersRequest
* Enhancement for ModbusTcpClient, ModbusTcpClient can now accept connection timeout as one of the parameter
* Misc updates

Version 1.3.0.rc1
------------------------------------------------------------
* Timing improvements over MODBUS Serial interface
* Modbus RTU use 3.5 char silence before and after transactions
* Bug fix on FifoTransactionManager , flush stray data before transaction
* Update repository information
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
